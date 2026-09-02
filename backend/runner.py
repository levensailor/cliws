"""PTY-based command runner with WebSocket streaming."""

from __future__ import annotations

import asyncio
import collections
import fcntl
import logging
import os
import pty
import signal
import struct
import termios
import uuid
from dataclasses import dataclass, field
from typing import Any

from backend.config import Settings, get_settings
from backend.models import EntryOut, RunOut
from backend import repo

logger = logging.getLogger("cliws.runner")

RING_BUFFER_MAX = 512 * 1024
FLUSH_INTERVAL = 0.025
PENDING_FLUSH_THRESHOLD = 32 * 1024
SOCKET_QUEUE_MAX = 64
TRUNCATION_MARKER = b"\r\n[cliws: output truncated]\r\n"


@dataclass
class ClientAttachment:
  queue: asyncio.Queue[bytes | None]
  dropped: bool = False


@dataclass
class Run:
  run_id: str
  entry: EntryOut
  settings: Settings
  master_fd: int
  slave_fd: int
  process: asyncio.subprocess.Process
  cols: int = 120
  rows: int = 30
  ring_buffer: collections.deque[bytes] = field(default_factory=collections.deque)
  ring_size: int = 0
  pending: bytearray = field(default_factory=bytearray)
  clients: dict[str, ClientAttachment] = field(default_factory=dict)
  exit_code: int | None = None
  running: bool = True
  flush_task: asyncio.Task[None] | None = None
  reader_registered: bool = False
  loop: asyncio.AbstractEventLoop | None = None

  def _append_ring(self, data: bytes) -> None:
    self.ring_buffer.append(data)
    self.ring_size += len(data)
    while self.ring_size > RING_BUFFER_MAX and self.ring_buffer:
      removed = self.ring_buffer.popleft()
      self.ring_size -= len(removed)

  def ring_snapshot(self) -> bytes:
    return b"".join(self.ring_buffer)

  def set_winsize(self, cols: int, rows: int) -> None:
    self.cols = cols
    self.rows = rows
    if not self.running or self.master_fd < 0:
      return
    winsize = struct.pack("HHHH", rows, cols, 0, 0)
    try:
      fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
    except OSError as exc:
      logger.debug("Ignoring PTY resize for run %s: %s", self.run_id, exc)

  async def start_flush_loop(self) -> None:
    self.loop = asyncio.get_running_loop()
    self.flush_task = asyncio.create_task(self._flush_loop())

  async def _flush_loop(self) -> None:
    while self.running or self.pending:
      if len(self.pending) >= PENDING_FLUSH_THRESHOLD:
        await self._flush_pending()
      else:
        await asyncio.sleep(FLUSH_INTERVAL)
        if self.pending:
          await self._flush_pending()
    await self._flush_pending()

  async def _flush_pending(self) -> None:
    if not self.pending:
      return
    chunk = bytes(self.pending)
    self.pending.clear()
    self._append_ring(chunk)
    for attachment in list(self.clients.values()):
      await self._enqueue(attachment, chunk)

  async def _enqueue(self, attachment: ClientAttachment, chunk: bytes) -> None:
    if attachment.queue.qsize() >= SOCKET_QUEUE_MAX:
      attachment.dropped = True
      try:
        attachment.queue.put_nowait(TRUNCATION_MARKER)
      except asyncio.QueueFull:
        pass
      return
    try:
      attachment.queue.put_nowait(chunk)
    except asyncio.QueueFull:
      attachment.dropped = True

  def on_readable(self) -> None:
    if self.master_fd < 0:
      return
    try:
      data = os.read(self.master_fd, 65536)
    except OSError:
      return
    if not data:
      return
    self.pending.extend(data)

  async def write_input(self, data: bytes) -> None:
    if not self.running or self.master_fd < 0:
      return
    try:
      os.write(self.master_fd, data)
    except OSError as exc:
      logger.warning("Failed writing to PTY for run %s: %s", self.run_id, exc)

  async def send_signal(self, sig: int) -> None:
    if not self.running or not self.process.pid:
      return
    try:
      os.killpg(os.getpgid(self.process.pid), sig)
    except ProcessLookupError:
      pass
    except OSError as exc:
      logger.debug("Ignoring signal for run %s: %s", self.run_id, exc)

  async def stop(self) -> None:
    if not self.running:
      return
    await self.send_signal(signal.SIGTERM)
    await asyncio.sleep(1.0)
    if self.running and self.process.pid:
      try:
        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
      except ProcessLookupError:
        pass
      except OSError:
        pass

  async def finalize(self) -> None:
    self.running = False
    if self.flush_task:
      await self.flush_task
    for attachment in self.clients.values():
      try:
        attachment.queue.put_nowait(None)
      except asyncio.QueueFull:
        pass
    if self.master_fd >= 0:
      try:
        os.close(self.master_fd)
      except OSError:
        pass
      self.master_fd = -1


class RunManager:
  def __init__(self, settings: Settings | None = None) -> None:
    self.settings = settings or get_settings()
    self.runs: dict[str, Run] = {}
    self._cleanup_tasks: dict[str, asyncio.Task[None]] = {}

  def list_runs(self) -> list[RunOut]:
    result: list[RunOut] = []
    for run in self.runs.values():
      result.append(
          RunOut(
              run_id=run.run_id,
              entry_id=run.entry.id,
              entry_name=run.entry.name,
              cmd=run.entry.cmd,
              pid=run.process.pid,
              running=run.running,
              exit_code=run.exit_code,
          )
      )
    return result

  async def start_run(self, entry_id: int, cols: int = 120, rows: int = 30) -> Run:
    entry = repo.get_entry(entry_id)
    if not entry:
      raise ValueError(f"Entry {entry_id} not found")

    master_fd, slave_fd = pty.openpty()
    env = os.environ.copy()
    env.update(
        {
            "TERM": "xterm-256color",
            "HOME": "/root",
            "PATH": env.get("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
        }
    )

    process = await asyncio.create_subprocess_exec(
        self.settings.shell,
        "-lc",
        entry.cmd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        start_new_session=True,
        env=env,
        close_fds=True,
    )
    os.close(slave_fd)

    run_id = str(uuid.uuid4())
    run = Run(
        run_id=run_id,
        entry=entry,
        settings=self.settings,
        master_fd=master_fd,
        slave_fd=slave_fd,
        process=process,
        cols=cols,
        rows=rows,
    )
    run.set_winsize(cols, rows)
    self.runs[run_id] = run

    loop = asyncio.get_running_loop()
    loop.add_reader(master_fd, run.on_readable)
    run.reader_registered = True
    await run.start_flush_loop()

    asyncio.create_task(self._watch_process(run))
    logger.info("Started run %s for entry %s pid=%s", run_id, entry_id, process.pid)
    return run

  async def _watch_process(self, run: Run) -> None:
    code = await run.process.wait()
    run.exit_code = code
    run.running = False
    if run.reader_registered and run.loop:
      try:
        run.loop.remove_reader(run.master_fd)
      except Exception:
        pass
    await run.finalize()
    logger.info("Run %s exited with code %s", run.run_id, code)
    self._schedule_cleanup(run.run_id)

  def _schedule_cleanup(self, run_id: str) -> None:
    if run_id in self._cleanup_tasks:
      return

    async def _cleanup() -> None:
      await asyncio.sleep(self.settings.run_retention_seconds)
      self.runs.pop(run_id, None)
      self._cleanup_tasks.pop(run_id, None)

    self._cleanup_tasks[run_id] = asyncio.create_task(_cleanup())

  def get_run(self, run_id: str) -> Run | None:
    return self.runs.get(run_id)

  async def attach(self, run_id: str) -> tuple[Run, ClientAttachment]:
    run = self.get_run(run_id)
    if not run:
      raise ValueError(f"Run {run_id} not found")
    attachment = ClientAttachment(queue=asyncio.Queue(maxsize=SOCKET_QUEUE_MAX + 4))
    return run, attachment

  def detach(self, run: Run, attachment: ClientAttachment) -> None:
    for client_id, client in list(run.clients.items()):
      if client is attachment:
        run.clients.pop(client_id, None)
        break

  async def stop_run(self, run_id: str) -> None:
    run = self.get_run(run_id)
    if run:
      await run.stop()
