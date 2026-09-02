PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    layout TEXT NOT NULL DEFAULT 'grid' CHECK (layout IN ('grid', 'list')),
    position INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS subsections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subsection_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    cmd TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT 'fa-solid fa-terminal',
    position INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (subsection_id) REFERENCES subsections(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sections_position ON sections(position);
CREATE INDEX IF NOT EXISTS idx_subsections_section_position ON subsections(section_id, position);
CREATE INDEX IF NOT EXISTS idx_entries_subsection_position ON entries(subsection_id, position);

PRAGMA user_version = 1;
