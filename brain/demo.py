"""The starter demo pack: install/remove examples/starter/ notes.

Locked decisions 7+8 (PLAN-UX): the pack is ~8 synthetic notes, all
`source: demo`, never assessed — so removal deletes files and re-syncs the
index, and nothing else in the system ever knew they existed (events.jsonl
is untouched because no assessment may ever cite demo content).
"""
from __future__ import annotations

from pathlib import Path

from .config import knowledge_dir, root
from .schema import parse_note, validate_file


def pack_dir() -> Path:
    return root() / "examples" / "starter"


def pack_notes() -> list[Path]:
    d = pack_dir()
    return sorted(p for p in d.glob("*.md") if p.name != "README.md") if d.is_dir() else []


def installed() -> list[Path]:
    """Every note in knowledge/ carrying source: demo."""
    found = []
    for path in sorted(knowledge_dir().rglob("*.md")):
        note, _errors = parse_note(path)
        if note is not None and note.meta.get("source") == "demo":
            found.append(path)
    return found


def install() -> tuple[list[Path], list[Path]]:
    """Copy pack notes into knowledge/<domain>/. Idempotent.

    Returns (copied, skipped). A pack note that fails validation after the
    copy is deleted again rather than left in the knowledge base.
    """
    copied: list[Path] = []
    skipped: list[Path] = []
    for src in pack_notes():
        note, errors = parse_note(src)
        if note is None:
            raise ValueError(f"unreadable pack note: {src.name}")
        dest = knowledge_dir() / note.meta["domain"] / src.name
        if dest.exists():
            skipped.append(dest)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        if validate_file(dest):
            dest.unlink()
            raise ValueError(f"pack note failed validation, not installed: {src.name}")
        copied.append(dest)
    return copied, skipped


def remove() -> list[Path]:
    """Delete every source: demo note from knowledge/. Returns what was removed."""
    removed = installed()
    for path in removed:
        path.unlink()
    return removed
