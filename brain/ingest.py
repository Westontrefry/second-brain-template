"""Sync the markdown knowledge base into the SQLite index: chunk, embed, store.

Incremental by content hash — unchanged notes are skipped, changed notes are
re-embedded, notes whose files vanished are removed.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

from .config import knowledge_dir, load_config
from .schema import parse_note, validate_note
from . import store


def chunk_text(body: str) -> list[str]:
    """Paragraph-aware chunking: pack paragraphs up to max_chars, with overlap."""
    cfg = load_config()["chunking"]
    max_chars, overlap = cfg["max_chars"], cfg["overlap_chars"]

    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for p in paragraphs:
        candidate = f"{current}\n\n{p}" if current else p
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            chunks.append(current)
            current = current[-overlap:] + "\n\n" + p if overlap else p
    if current:
        chunks.append(current)
    return chunks


def sync(full: bool = False) -> dict[str, int]:
    """Sync all notes. Returns counts. full=True wipes and re-embeds everything."""
    from .embeddings import embed_texts

    if full:
        store.wipe()
    con = store.connect()
    stats = {"indexed": 0, "unchanged": 0, "removed": 0, "invalid": 0}
    seen: set[str] = set()

    for path in sorted(knowledge_dir().rglob("*.md")):
        note, errors = parse_note(path)
        if note is not None:
            errors = validate_note(note)
        if errors:
            stats["invalid"] += 1
            print(f"skip (invalid) {path}: {errors[0]}")
            continue

        assert note is not None  # a None note leaves errors set, handled above
        m = note.meta
        seen.add(m["id"])
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        row = con.execute(
            "SELECT content_hash FROM notes WHERE id = ?", (m["id"],)
        ).fetchone()
        if row and row[0] == content_hash:
            stats["unchanged"] += 1
            continue

        con.execute("DELETE FROM notes WHERE id = ?", (m["id"],))
        con.execute(
            "INSERT INTO notes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                m["id"], str(path), content_hash, m["domain"], m["source"],
                m["confidence"], m.get("ai_confidence"), m["importance"],
                json.dumps(m["topics"]), json.dumps(m["goals"]),
                str(m["created"]), str(m["last_reviewed"]),
                str(m["last_assessed"]) if m.get("last_assessed") else None,
                m["exposure_count"],
            ),
        )
        chunks = chunk_text(note.body)
        vectors = embed_texts(chunks)
        con.executemany(
            "INSERT INTO chunks (note_id, seq, text, embedding) VALUES (?,?,?,?)",
            [
                (m["id"], i, text, np.asarray(vec, dtype=np.float32).tobytes())
                for i, (text, vec) in enumerate(zip(chunks, vectors))
            ],
        )
        stats["indexed"] += 1

    gone = [
        r[0] for r in con.execute("SELECT id FROM notes").fetchall() if r[0] not in seen
    ]
    for note_id in gone:
        con.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        stats["removed"] += 1

    con.commit()
    con.close()
    return stats
