"""SQLite index over the markdown knowledge base.

Derived data only: every row here is rebuildable from knowledge/*.md with
`brain rebuild`. Embeddings are stored as float32 blobs and searched with a
numpy dot product — exact, and instant at personal scale (a 100k-chunk corpus
would still search in milliseconds).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import load_config, root

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    domain TEXT NOT NULL,
    source TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    ai_confidence REAL,
    importance INTEGER NOT NULL,
    topics TEXT NOT NULL,
    goals TEXT NOT NULL,
    created TEXT NOT NULL,
    last_reviewed TEXT NOT NULL,
    last_assessed TEXT,
    exposure_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id TEXT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    seq INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_note ON chunks(note_id);
"""


def db_path() -> Path:
    return root() / load_config()["paths"]["db_path"]


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(db_path())
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con


def wipe() -> None:
    p = db_path()
    if p.exists():
        p.unlink()
