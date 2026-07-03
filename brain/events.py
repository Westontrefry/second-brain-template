"""Append-only event log — the history the frontmatter can't hold.

Frontmatter stores only the LATEST ai_confidence / exposure state; this log keeps
every assessment and exposure event as one JSON line, enabling time-series views
(confidence-over-time, goal burndown) later. Plain text file at the repo root,
committed to git: it is source data, not derived state. Never rewritten, only
appended.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .config import load_config, root


def events_path() -> Path:
    rel = load_config()["paths"].get("events_file", "events.jsonl")
    return root() / rel


def append_event(kind: str, **fields) -> Path:
    """Append one event line: {"ts": ..., "kind": kind, **fields}."""
    record = {"ts": dt.datetime.now().isoformat(timespec="seconds"),
              "kind": kind, **fields}
    path = events_path()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return path
