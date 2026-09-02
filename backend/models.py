"""Pydantic models for CLIWS API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EntryOut(BaseModel):
  id: int
  name: str
  cmd: str
  icon: str
  position: int


class SubsectionOut(BaseModel):
  id: int
  name: str
  position: int
  entries: list[EntryOut] = Field(default_factory=list)


class SectionOut(BaseModel):
  id: int
  name: str
  layout: Literal["grid", "list"]
  position: int
  subsections: list[SubsectionOut] = Field(default_factory=list)


class TreeOut(BaseModel):
  sections: list[SectionOut] = Field(default_factory=list)


class SectionCreate(BaseModel):
  name: str
  layout: Literal["grid", "list"] = "grid"
  position: int | None = None


class SectionUpdate(BaseModel):
  name: str | None = None
  layout: Literal["grid", "list"] | None = None
  position: int | None = None


class SubsectionCreate(BaseModel):
  section_id: int
  name: str
  position: int | None = None


class SubsectionUpdate(BaseModel):
  name: str | None = None
  position: int | None = None


class EntryCreate(BaseModel):
  subsection_id: int
  name: str
  cmd: str
  icon: str = "fa-solid fa-terminal"
  position: int | None = None


class EntryUpdate(BaseModel):
  name: str | None = None
  cmd: str | None = None
  icon: str | None = None
  position: int | None = None


class ReorderItem(BaseModel):
  id: int
  position: int


class ReorderRequest(BaseModel):
  entity: Literal["sections", "subsections", "entries"]
  items: list[ReorderItem]


class SettingsOut(BaseModel):
  settings: dict[str, str]


class SettingsUpdate(BaseModel):
  settings: dict[str, str]


class RunOut(BaseModel):
  run_id: str
  entry_id: int
  entry_name: str
  cmd: str
  pid: int | None = None
  running: bool
  exit_code: int | None = None


class IconOut(BaseModel):
  name: str
  style: str
  label: str
  terms: list[str] = Field(default_factory=list)
  categories: list[str] = Field(default_factory=list)
