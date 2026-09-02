"""REST API routes for dashboard tree management."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.config import get_settings
from backend.models import (
    EntryCreate,
    EntryOut,
    EntryUpdate,
    ReorderRequest,
    SectionCreate,
    SectionOut,
    SectionUpdate,
    SettingsOut,
    SettingsUpdate,
    SubsectionCreate,
    SubsectionOut,
    SubsectionUpdate,
    TreeOut,
)
from backend import repo

router = APIRouter(prefix="/api", tags=["tree"])


@router.get("/tree", response_model=TreeOut)
def read_tree() -> TreeOut:
  return repo.get_tree()


@router.post("/sections", response_model=SectionOut)
def create_section(payload: SectionCreate) -> SectionOut:
  return repo.create_section(payload)


@router.patch("/sections/{section_id}", response_model=SectionOut)
def update_section(section_id: int, payload: SectionUpdate) -> SectionOut:
  section = repo.update_section(section_id, payload)
  if not section:
    raise HTTPException(status_code=404, detail="Section not found")
  return section


@router.delete("/sections/{section_id}")
def delete_section(section_id: int) -> dict[str, bool]:
  deleted = repo.delete_section(section_id)
  if not deleted:
    raise HTTPException(status_code=404, detail="Section not found")
  return {"ok": True}


@router.post("/subsections", response_model=SubsectionOut)
def create_subsection(payload: SubsectionCreate) -> SubsectionOut:
  return repo.create_subsection(payload)


@router.patch("/subsections/{subsection_id}", response_model=SubsectionOut)
def update_subsection(subsection_id: int, payload: SubsectionUpdate) -> SubsectionOut:
  subsection = repo.update_subsection(subsection_id, payload)
  if not subsection:
    raise HTTPException(status_code=404, detail="Subsection not found")
  return subsection


@router.delete("/subsections/{subsection_id}")
def delete_subsection(subsection_id: int) -> dict[str, bool]:
  deleted = repo.delete_subsection(subsection_id)
  if not deleted:
    raise HTTPException(status_code=404, detail="Subsection not found")
  return {"ok": True}


@router.post("/entries", response_model=EntryOut)
def create_entry(payload: EntryCreate) -> EntryOut:
  return repo.create_entry(payload)


@router.patch("/entries/{entry_id}", response_model=EntryOut)
def update_entry(entry_id: int, payload: EntryUpdate) -> EntryOut:
  entry = repo.update_entry(entry_id, payload)
  if not entry:
    raise HTTPException(status_code=404, detail="Entry not found")
  return entry


@router.delete("/entries/{entry_id}")
def delete_entry(entry_id: int) -> dict[str, bool]:
  deleted = repo.delete_entry(entry_id)
  if not deleted:
    raise HTTPException(status_code=404, detail="Entry not found")
  return {"ok": True}


@router.post("/reorder")
def reorder(payload: ReorderRequest) -> dict[str, bool]:
  repo.reorder(payload.entity, payload.items)
  return {"ok": True}


@router.get("/settings", response_model=SettingsOut)
def read_settings() -> SettingsOut:
  return SettingsOut(settings=repo.get_settings())


@router.patch("/settings", response_model=SettingsOut)
def patch_settings(payload: SettingsUpdate) -> SettingsOut:
  return SettingsOut(settings=repo.update_settings(payload.settings))


@router.get("/icons")
def read_icons() -> list[dict]:
  settings = get_settings()
  icon_path: Path = settings.icon_index_path
  if not icon_path.exists():
    return []
  with icon_path.open("r", encoding="utf-8") as handle:
    return json.load(handle)
