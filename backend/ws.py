"""WebSocket endpoint for command streaming."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import signal as signal_mod
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.runner import ClientAttachment, Run, RunManager

logger = logging.getLogger("cliws.ws")
router = APIRouter()


async def _send_json(websocket: WebSocket, payload: dict[str, Any]) -> None:
  await websocket.send_text(json.dumps(payload))


async def _pump_output(websocket: WebSocket, attachment: ClientAttachment, run: Run) -> None:
  while True:
    chunk = await attachment.queue.get()
    if chunk is None:
      break
    await websocket.send_bytes(chunk)
  if not run.running and run.exit_code is not None:
    await _send_json(websocket, {"type": "exit", "run_id": run.run_id, "code": run.exit_code})


@router.websocket("/ws/run")
async def ws_run(websocket: WebSocket) -> None:
  await websocket.accept()
  manager: RunManager = websocket.app.state.run_manager
  run: Run | None = None
  attachment: ClientAttachment | None = None
  pump_task: asyncio.Task[None] | None = None
  client_key = str(id(websocket))

  try:
    while True:
      message = await websocket.receive()
      if message.get("type") == "websocket.disconnect":
        break

      if "text" not in message or message["text"] is None:
        continue

      payload = json.loads(message["text"])
      msg_type = payload.get("type")

      if msg_type == "start":
        entry_id = int(payload["entry_id"])
        cols = int(payload.get("cols", 120))
        rows = int(payload.get("rows", 30))
        run = await manager.start_run(entry_id, cols=cols, rows=rows)
        attachment = ClientAttachment(queue=asyncio.Queue(maxsize=68))
        run.clients[client_key] = attachment
        snapshot = run.ring_snapshot()
        if snapshot:
          attachment.queue.put_nowait(snapshot)
        pump_task = asyncio.create_task(_pump_output(websocket, attachment, run))
        await _send_json(
            websocket,
            {
                "type": "started",
                "run_id": run.run_id,
                "pid": run.process.pid,
                "entry_id": run.entry.id,
                "entry_name": run.entry.name,
                "cmd": run.entry.cmd,
            },
        )

      elif msg_type == "attach":
        run_id = payload["run_id"]
        run, attachment = await manager.attach(run_id)
        run.clients[client_key] = attachment
        snapshot = run.ring_snapshot()
        if snapshot:
          attachment.queue.put_nowait(snapshot)
        pump_task = asyncio.create_task(_pump_output(websocket, attachment, run))
        await _send_json(
            websocket,
            {
                "type": "attached",
                "run_id": run.run_id,
                "pid": run.process.pid,
                "running": run.running,
                "exit_code": run.exit_code,
            },
        )

      elif msg_type == "input" and run:
        data = payload.get("data", "")
        await run.write_input(data.encode("utf-8", errors="ignore"))

      elif msg_type == "resize" and run:
        cols = int(payload.get("cols", run.cols))
        rows = int(payload.get("rows", run.rows))
        run.set_winsize(cols, rows)

      elif msg_type == "signal" and run:
        sig_name = payload.get("signal", "SIGINT")
        sig = getattr(signal_mod, sig_name, signal_mod.SIGINT)
        await run.send_signal(sig)

      elif msg_type == "stop" and run:
        await manager.stop_run(run.run_id)
        await _send_json(websocket, {"type": "stopping", "run_id": run.run_id})

      elif msg_type == "ping":
        await _send_json(websocket, {"type": "pong"})

  except WebSocketDisconnect:
    logger.info("WebSocket disconnected")
  except Exception as exc:
    logger.exception("WebSocket error: %s", exc)
    with contextlib.suppress(Exception):
      await _send_json(websocket, {"type": "error", "message": str(exc)})
  finally:
    if pump_task:
      pump_task.cancel()
      with contextlib.suppress(asyncio.CancelledError):
        await pump_task
    if run and attachment:
      run.clients.pop(client_key, None)
