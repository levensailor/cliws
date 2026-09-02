"""Data access layer for CLIWS."""

from __future__ import annotations

import sqlite3
from typing import Any

from backend.db import get_connection
from backend.models import (
    EntryCreate,
    EntryOut,
    EntryUpdate,
    ReorderItem,
    SectionCreate,
    SectionOut,
    SectionUpdate,
    SubsectionCreate,
    SubsectionOut,
    SubsectionUpdate,
    TreeOut,
)


def _next_position(conn: sqlite3.Connection, table: str, where_clause: str, params: tuple[Any, ...]) -> int:
  row = conn.execute(
      f"SELECT COALESCE(MAX(position), -1) + 1 FROM {table} WHERE {where_clause}",
      params,
  ).fetchone()
  return int(row[0])


def get_tree() -> TreeOut:
  with get_connection() as conn:
    sections = conn.execute(
        "SELECT id, name, layout, position FROM sections ORDER BY position, id"
    ).fetchall()
    subsections = conn.execute(
        "SELECT id, section_id, name, position FROM subsections ORDER BY position, id"
    ).fetchall()
    entries = conn.execute(
        "SELECT id, subsection_id, name, cmd, icon, position FROM entries ORDER BY position, id"
    ).fetchall()

  entries_by_sub: dict[int, list[EntryOut]] = {}
  for row in entries:
    entry = EntryOut(
        id=row["id"],
        name=row["name"],
        cmd=row["cmd"],
        icon=row["icon"],
        position=row["position"],
    )
    entries_by_sub.setdefault(row["subsection_id"], []).append(entry)

  subs_by_section: dict[int, list[SubsectionOut]] = {}
  for row in subsections:
    sub = SubsectionOut(
        id=row["id"],
        name=row["name"],
        position=row["position"],
        entries=entries_by_sub.get(row["id"], []),
    )
    subs_by_section.setdefault(row["section_id"], []).append(sub)

  section_models = [
      SectionOut(
          id=row["id"],
          name=row["name"],
          layout=row["layout"],
          position=row["position"],
          subsections=subs_by_section.get(row["id"], []),
      )
      for row in sections
  ]
  return TreeOut(sections=section_models)


def create_section(payload: SectionCreate) -> SectionOut:
  with get_connection() as conn:
    position = payload.position
    if position is None:
      position = _next_position(conn, "sections", "1=1", ())
    cur = conn.execute(
        "INSERT INTO sections (name, layout, position) VALUES (?, ?, ?)",
        (payload.name, payload.layout, position),
    )
    section_id = int(cur.lastrowid)
  return SectionOut(id=section_id, name=payload.name, layout=payload.layout, position=position, subsections=[])


def update_section(section_id: int, payload: SectionUpdate) -> SectionOut | None:
  with get_connection() as conn:
    row = conn.execute("SELECT * FROM sections WHERE id = ?", (section_id,)).fetchone()
    if not row:
      return None
    name = payload.name if payload.name is not None else row["name"]
    layout = payload.layout if payload.layout is not None else row["layout"]
    position = payload.position if payload.position is not None else row["position"]
    conn.execute(
        "UPDATE sections SET name = ?, layout = ?, position = ? WHERE id = ?",
        (name, layout, position, section_id),
    )
  tree = get_tree()
  for section in tree.sections:
    if section.id == section_id:
      return section
  return None


def delete_section(section_id: int) -> bool:
  with get_connection() as conn:
    cur = conn.execute("DELETE FROM sections WHERE id = ?", (section_id,))
    return cur.rowcount > 0


def create_subsection(payload: SubsectionCreate) -> SubsectionOut:
  with get_connection() as conn:
    position = payload.position
    if position is None:
      position = _next_position(conn, "subsections", "section_id = ?", (payload.section_id,))
    cur = conn.execute(
        "INSERT INTO subsections (section_id, name, position) VALUES (?, ?, ?)",
        (payload.section_id, payload.name, position),
    )
    subsection_id = int(cur.lastrowid)
  return SubsectionOut(id=subsection_id, name=payload.name, position=position, entries=[])


def update_subsection(subsection_id: int, payload: SubsectionUpdate) -> SubsectionOut | None:
  with get_connection() as conn:
    row = conn.execute("SELECT * FROM subsections WHERE id = ?", (subsection_id,)).fetchone()
    if not row:
      return None
    name = payload.name if payload.name is not None else row["name"]
    position = payload.position if payload.position is not None else row["position"]
    conn.execute(
        "UPDATE subsections SET name = ?, position = ? WHERE id = ?",
        (name, position, subsection_id),
    )
  tree = get_tree()
  for section in tree.sections:
    for subsection in section.subsections:
      if subsection.id == subsection_id:
        return subsection
  return None


def delete_subsection(subsection_id: int) -> bool:
  with get_connection() as conn:
    cur = conn.execute("DELETE FROM subsections WHERE id = ?", (subsection_id,))
    return cur.rowcount > 0


def create_entry(payload: EntryCreate) -> EntryOut:
  with get_connection() as conn:
    position = payload.position
    if position is None:
      position = _next_position(conn, "entries", "subsection_id = ?", (payload.subsection_id,))
    cur = conn.execute(
        "INSERT INTO entries (subsection_id, name, cmd, icon, position) VALUES (?, ?, ?, ?, ?)",
        (payload.subsection_id, payload.name, payload.cmd, payload.icon, position),
    )
    entry_id = int(cur.lastrowid)
  return EntryOut(
      id=entry_id,
      name=payload.name,
      cmd=payload.cmd,
      icon=payload.icon,
      position=position,
  )


def update_entry(entry_id: int, payload: EntryUpdate) -> EntryOut | None:
  with get_connection() as conn:
    row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    if not row:
      return None
    name = payload.name if payload.name is not None else row["name"]
    cmd = payload.cmd if payload.cmd is not None else row["cmd"]
    icon = payload.icon if payload.icon is not None else row["icon"]
    position = payload.position if payload.position is not None else row["position"]
    conn.execute(
        "UPDATE entries SET name = ?, cmd = ?, icon = ?, position = ? WHERE id = ?",
        (name, cmd, icon, position, entry_id),
    )
  return EntryOut(id=entry_id, name=name, cmd=cmd, icon=icon, position=position)


def delete_entry(entry_id: int) -> bool:
  with get_connection() as conn:
    cur = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    return cur.rowcount > 0


def get_entry(entry_id: int) -> EntryOut | None:
  with get_connection() as conn:
    row = conn.execute(
        "SELECT id, name, cmd, icon, position FROM entries WHERE id = ?",
        (entry_id,),
    ).fetchone()
  if not row:
    return None
  return EntryOut(
      id=row["id"],
      name=row["name"],
      cmd=row["cmd"],
      icon=row["icon"],
      position=row["position"],
  )


def reorder(entity: str, items: list[ReorderItem]) -> None:
  table_map = {
      "sections": "sections",
      "subsections": "subsections",
      "entries": "entries",
  }
  table = table_map[entity]
  with get_connection() as conn:
    for item in items:
      conn.execute(
          f"UPDATE {table} SET position = ? WHERE id = ?",
          (item.position, item.id),
      )


def get_settings() -> dict[str, str]:
  with get_connection() as conn:
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
  return {row["key"]: row["value"] for row in rows}


def update_settings(values: dict[str, str]) -> dict[str, str]:
  with get_connection() as conn:
    for key, value in values.items():
      conn.execute(
          "INSERT INTO settings (key, value) VALUES (?, ?) "
          "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
          (key, value),
      )
  return get_settings()
