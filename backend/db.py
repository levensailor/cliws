"""SQLite database helpers."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from backend.config import Settings, get_settings

logger = logging.getLogger("cliws.db")


def ensure_database_directory(db_path: Path) -> None:
  db_path.parent.mkdir(parents=True, exist_ok=True)


def connect(db_path: Path | None = None) -> sqlite3.Connection:
  settings = get_settings()
  path = db_path or settings.database_path
  ensure_database_directory(path)
  conn = sqlite3.connect(path, check_same_thread=False)
  conn.row_factory = sqlite3.Row
  conn.execute("PRAGMA foreign_keys = ON")
  return conn


@contextmanager
def get_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
  conn = connect(db_path)
  try:
    yield conn
    conn.commit()
  except Exception:
    conn.rollback()
    raise
  finally:
    conn.close()


def get_user_version(conn: sqlite3.Connection) -> int:
  row = conn.execute("PRAGMA user_version").fetchone()
  return int(row[0]) if row else 0


def validate_schema(settings: Settings | None = None) -> None:
  settings = settings or get_settings()
  db_path = settings.database_path
  if not db_path.exists():
    msg = (
        f"Database not found at {db_path}. "
        "Run install.sh to initialize the schema from sql/*.sql"
    )
    logger.error(msg)
    raise RuntimeError(msg)

  with get_connection(db_path) as conn:
    current = get_user_version(conn)
    expected = settings.schema_version
    if current != expected:
      msg = (
          f"Database schema version mismatch: found {current}, expected {expected}. "
          "Apply pending sql/*.sql files manually; CLIWS does not auto-migrate."
      )
      logger.error(msg)
      raise RuntimeError(msg)
    logger.info("Database schema validated (user_version=%s)", current)
