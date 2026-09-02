"""Centralized logging configuration."""

from __future__ import annotations

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo

from backend.config import Settings

EST = ZoneInfo("America/New_York")
LOG_FORMAT = "%(asctime)s EST | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class EstFormatter(logging.Formatter):
  """Formatter that renders timestamps in US Eastern time."""

  def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
    dt = datetime.fromtimestamp(record.created, tz=EST)
    if datefmt:
      return dt.strftime(datefmt)
    return dt.strftime(DATE_FORMAT)


def configure_logging(settings: Settings) -> logging.Logger:
  log_dir = settings.log_directory
  log_dir.mkdir(parents=True, exist_ok=True)
  log_file = log_dir / "cliws.log"

  formatter = EstFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)
  root = logging.getLogger()
  root.handlers.clear()
  root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

  console_handler = logging.StreamHandler()
  console_handler.setFormatter(formatter)
  root.addHandler(console_handler)

  file_handler = RotatingFileHandler(
      log_file,
      maxBytes=1_000_000,
      backupCount=3,
      encoding="utf-8",
  )
  file_handler.setFormatter(formatter)
  root.addHandler(file_handler)

  logger = logging.getLogger("cliws")
  logger.info("Logging configured; file=%s", log_file)
  return logger
