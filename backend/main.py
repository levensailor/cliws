"""CLIWS FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api_runs import router as runs_router
from backend.api_tree import router as tree_router
from backend.config import get_settings
from backend.db import validate_schema
from backend.logging_setup import configure_logging
from backend.runner import RunManager
from backend.ws import router as ws_router

logger = logging.getLogger("cliws")


@asynccontextmanager
async def lifespan(app: FastAPI):
  settings = get_settings()
  configure_logging(settings)
  validate_schema(settings)
  app.state.run_manager = RunManager(settings)
  logger.info("CLIWS started; serving from %s", settings.app_dir)
  yield
  logger.info("CLIWS shutting down")


app = FastAPI(title="CLIWS", version="1.0.0", lifespan=lifespan)
app.include_router(tree_router)
app.include_router(runs_router)
app.include_router(ws_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
  return {"status": "ok"}


settings = get_settings()
frontend_dir = settings.frontend_dir

if frontend_dir.exists():
  app.mount("/css", StaticFiles(directory=frontend_dir / "css"), name="css")
  app.mount("/js", StaticFiles(directory=frontend_dir / "js"), name="js")
  vendor_dir = frontend_dir / "vendor"
  if vendor_dir.exists():
    app.mount("/vendor", StaticFiles(directory=vendor_dir), name="vendor")


@app.get("/")
def index() -> FileResponse:
  index_path = frontend_dir / "index.html"
  return FileResponse(index_path)
