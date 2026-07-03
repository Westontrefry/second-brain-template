"""Note frontmatter schema: parsing and validation.

A note is a markdown file with YAML frontmatter delimited by `---` lines.
Markdown is the source of truth; everything downstream (embeddings, weights,
graph) is derived from what this module accepts.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .config import load_config, goal_ids

ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$")

REQUIRED = (
    "id", "domain", "topics", "source", "confidence", "importance",
    "goals", "created", "last_reviewed", "exposure_count",
)
OPTIONAL = ("ai_confidence", "ai_confidence_rationale", "last_assessed", "title")


@dataclass
class Note:
    path: Path
    meta: dict
    body: str


def parse_note(path: Path) -> tuple[Note | None, list[str]]:
    """Parse a note file. Returns (note, errors); note is None on parse failure."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, ["missing frontmatter: file must start with '---'"]
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, ["unterminated frontmatter: no closing '---' line"]
    try:
        meta = yaml.safe_load(text[4:end])
    except yaml.YAMLError as e:
        return None, [f"invalid YAML in frontmatter: {e}"]
    if not isinstance(meta, dict):
        return None, ["frontmatter is not a mapping"]
    return Note(path=path, meta=meta, body=text[end + 5:]), []


def _is_date(value: object) -> bool:
    if isinstance(value, dt.date):
        return True
    if isinstance(value, str):
        try:
            dt.date.fromisoformat(value)
            return True
        except ValueError:
            return False
    return False


def validate_note(note: Note) -> list[str]:
    """Validate a parsed note against the schema. Returns a list of errors."""
    cfg = load_config()
    m = note.meta
    errors: list[str] = []

    for f in REQUIRED:
        if f not in m:
            errors.append(f"missing required field: {f}")
    if errors:
        return errors
    unknown = set(m) - set(REQUIRED) - set(OPTIONAL)
    if unknown:
        errors.append(f"unknown fields: {', '.join(sorted(unknown))}")

    if not isinstance(m["id"], str) or not ID_RE.match(m["id"]):
        errors.append(f"id must match YYYY-MM-DD-slug, got: {m['id']!r}")
    elif m["id"] != note.path.stem:
        errors.append(f"id {m['id']!r} does not match filename {note.path.stem!r}")

    if m["domain"] not in cfg["domains"]:
        errors.append(f"domain {m['domain']!r} not in config.yaml domains")
    elif note.path.parent.name != m["domain"]:
        errors.append(f"note is in {note.path.parent.name}/ but domain is {m['domain']!r}")

    if m["source"] not in cfg["sources"]:
        errors.append(f"source {m['source']!r} not in config.yaml sources")

    if not isinstance(m["topics"], list) or not m["topics"] or \
            not all(isinstance(t, str) and t for t in m["topics"]):
        errors.append("topics must be a non-empty list of strings")

    for f in ("confidence", "importance"):
        if not isinstance(m[f], int) or isinstance(m[f], bool) or not 1 <= m[f] <= 5:
            errors.append(f"{f} must be an integer 1-5, got: {m[f]!r}")

    ai = m.get("ai_confidence")
    if ai is not None and (not isinstance(ai, (int, float)) or isinstance(ai, bool)
                           or not 0 <= ai <= 5):
        errors.append(f"ai_confidence must be null or a number 0-5, got: {ai!r}")

    known_goals = goal_ids()
    if not isinstance(m["goals"], list) or not all(isinstance(g, str) for g in m["goals"]):
        errors.append("goals must be a list of goal ids")
    else:
        for g in m["goals"]:
            if g not in known_goals:
                errors.append(f"unknown goal id: {g!r} (see goals/goals.yaml)")

    for f in ("created", "last_reviewed"):
        if not _is_date(m[f]):
            errors.append(f"{f} must be an ISO date, got: {m[f]!r}")
    if m.get("last_assessed") is not None and not _is_date(m["last_assessed"]):
        errors.append(f"last_assessed must be null or an ISO date, got: {m['last_assessed']!r}")

    ec = m["exposure_count"]
    if not isinstance(ec, int) or isinstance(ec, bool) or ec < 1:
        errors.append(f"exposure_count must be an integer >= 1, got: {ec!r}")

    if not note.body.strip():
        errors.append("note body is empty")

    return errors


def validate_file(path: Path) -> list[str]:
    note, errors = parse_note(path)
    if note is None:
        return errors
    return validate_note(note)
