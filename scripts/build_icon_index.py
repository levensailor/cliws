#!/usr/bin/env python3
"""Build a slim searchable icon index from Font Awesome metadata."""

from __future__ import annotations

import json
import sys
from pathlib import Path

STYLE_PREFIX = {
    "solid": "fa-solid",
    "regular": "fa-regular",
    "brands": "fa-brands",
}


def build_index(metadata_path: Path, output_path: Path) -> int:
  with metadata_path.open("r", encoding="utf-8") as handle:
    metadata = json.load(handle)

  icons = []
  for name, data in metadata.items():
    styles = data.get("free") or []
    label = data.get("label", name)
    terms = [str(term).lower() for term in data.get("search", {}).get("terms", [])]
    categories = data.get("categories", [])
    for style in styles:
      prefix = STYLE_PREFIX.get(style)
      if not prefix:
        continue
      icons.append(
          {
              "name": name,
              "style": prefix,
              "label": label,
              "terms": terms,
              "categories": categories,
          }
      )

  icons.sort(key=lambda item: (item["label"].lower(), item["name"]))
  output_path.parent.mkdir(parents=True, exist_ok=True)
  with output_path.open("w", encoding="utf-8") as handle:
    json.dump(icons, handle, separators=(",", ":"))
  return len(icons)


def main() -> int:
  if len(sys.argv) != 3:
    print("Usage: build_icon_index.py <metadata/icons.json> <output/index.json>")
    return 1

  metadata_path = Path(sys.argv[1])
  output_path = Path(sys.argv[2])
  if not metadata_path.exists():
    print(f"Metadata not found: {metadata_path}")
    return 1

  count = build_index(metadata_path, output_path)
  print(f"Wrote {count} icons to {output_path}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
