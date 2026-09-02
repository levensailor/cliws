"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_app_dir() -> Path:
    env_value = os.getenv("CLIWS_APP_DIR")
    if env_value:
        return Path(env_value).resolve()
    return Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
  model_config = SettingsConfigDict(
      env_file=".env",
      env_file_encoding="utf-8",
      extra="ignore",
  )

  app_dir: Path = Field(default_factory=_default_app_dir, validation_alias="CLIWS_APP_DIR")
  host: str = Field(default="0.0.0.0", validation_alias="CLIWS_HOST")
  port: int = Field(default=443, validation_alias="CLIWS_PORT")
  ssl_certfile: Path | None = Field(default=None, validation_alias="CLIWS_SSL_CERTFILE")
  ssl_keyfile: Path | None = Field(default=None, validation_alias="CLIWS_SSL_KEYFILE")
  http_redirect_port: int = Field(default=0, validation_alias="CLIWS_HTTP_REDIRECT_PORT")
  shell: str = Field(default="/bin/bash", validation_alias="CLIWS_SHELL")
  db_path: str = Field(default="data/cliws.db", validation_alias="CLIWS_DB_PATH")
  schema_version: int = Field(default=2, validation_alias="CLIWS_SCHEMA_VERSION")
  run_retention_seconds: int = Field(default=300, validation_alias="CLIWS_RUN_RETENTION_SECONDS")
  log_level: str = Field(default="INFO", validation_alias="CLIWS_LOG_LEVEL")
  log_dir: str = Field(default="logs", validation_alias="CLIWS_LOG_DIR")

  @property
  def database_path(self) -> Path:
    db = Path(self.db_path)
    if db.is_absolute():
      return db
    return self.app_dir / db

  @property
  def log_directory(self) -> Path:
    log_dir = Path(self.log_dir)
    if log_dir.is_absolute():
      return log_dir
    return self.app_dir / log_dir

  @property
  def frontend_dir(self) -> Path:
    return self.app_dir / "frontend"

  @property
  def icon_index_path(self) -> Path:
    return self.frontend_dir / "vendor" / "icons" / "index.json"


@lru_cache
def get_settings() -> Settings:
  return Settings()
