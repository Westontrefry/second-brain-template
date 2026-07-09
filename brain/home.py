"""The home screen bare `brain` prints (ux.md #1: conversation is the front door).

Read-only. Counts come straight from the markdown source of truth
(weights.collect); the index is only consulted for freshness, and its absence
is a stated fact with a fix, never an error (ux.md #5).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import subprocess

from .config import knowledge_dir, root
from .schema import parse_note
from . import store

STALE_DAYS = 120  # matches gaps.py / config model.state.stale_days


def _index_line(files: list) -> str:
    if not store.db_path().exists():
        return "index: not built yet (fix: brain ingest)"
    con = store.connect()
    hashes = dict(con.execute("SELECT id, content_hash FROM notes").fetchall())
    con.close()
    stale = sum(
        1 for f in files
        if hashes.get(f.stem) != hashlib.sha256(f.read_bytes()).hexdigest()
    )
    if stale:
        return (f"index: {stale} note change(s) not yet synced "
                "(any skill will sync them, or run: brain ingest)")
    return "index: up to date"


def _inbox_line() -> str:
    from .inbox import waiting_files

    waiting = waiting_files()
    if not waiting:
        return ""
    return (f"inbox: {len(waiting)} file(s) waiting in Ingest/ "
            "(run: brain inbox)")


def _gap_lines(n: int = 3) -> list[str]:
    from .gaps import analyze

    try:
        gaps = analyze()
    except (ValueError, FileNotFoundError, KeyError):
        return []
    lines = []
    for g in gaps[:n]:
        line = f"{g.name} ({g.goal}): {g.action}"
        if g.blocked_by:
            line += f"  (first: {', '.join(g.blocked_by)})"
        lines.append(line)
    return lines


def _events() -> list[dict]:
    path = root() / "events.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _git_dates() -> set[dt.date]:
    """Dates of commits touching notes or history — activity the events can't see."""
    if shutil.which("git") is None or not (root() / ".git").exists():
        return set()
    r = subprocess.run(
        ["git", "-C", str(root()), "log", "--format=%as", "--", "knowledge/", "events.jsonl"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return set()
    return {dt.date.fromisoformat(s) for s in r.stdout.split() if s}


def since_last_time(today: dt.date | None = None) -> list[str]:
    """What changed since (and during) the previous activity day.

    "Last time" = the most recent day before today with recorded activity
    (events.jsonl + git log). That day is INCLUDED: every level change is
    itself activity, so an exclusive boundary could never report one. This
    is the "what happened in my last session" recap at session start.
    No activity history yet -> [].
    """
    today = today or dt.date.today()
    events = _events()
    days = {dt.date.fromisoformat(e["ts"][:10]) for e in events if e.get("ts")}
    days |= _git_dates()
    prior = sorted(d for d in days if d < today)
    if not prior:
        return []
    boundary = prior[-1]

    lines: list[str] = []
    added = 0
    for f in sorted(knowledge_dir().rglob("*.md")):
        note, _errs = parse_note(f)
        if note is None:
            continue
        created = str(note.meta.get("created", ""))
        if created and dt.date.fromisoformat(created) >= boundary:
            added += 1
    if added:
        lines.append(f"{added} note(s) added")

    changed = [(e["topic"], e["level"]) for e in events
               if e.get("kind") == "assess" and e.get("ts")
               and dt.date.fromisoformat(e["ts"][:10]) >= boundary]
    if changed:
        detail = ", ".join(f"{t} is now {g:g}" for t, g in changed[:3])
        more = f" (+{len(changed) - 3} more)" if len(changed) > 3 else ""
        lines.append(f"{len(changed)} level(s) proven: {detail}{more}")

    from .weights import collect

    went_stale = [
        s.topic for s in collect(today).values()
        if s.last_reviewed
        and boundary - dt.timedelta(days=STALE_DAYS)
        <= dt.date.fromisoformat(s.last_reviewed[:10])
        <= today - dt.timedelta(days=STALE_DAYS)
    ]
    if went_stale:
        shown = ", ".join(sorted(went_stale)[:3])
        more = f" (+{len(went_stale) - 3} more)" if len(went_stale) > 3 else ""
        lines.append(f"{len(went_stale)} topic(s) went stale: {shown}{more}")

    if lines:
        lines.insert(0, f"Since last time ({boundary.isoformat()}):")
    return lines


def render_home() -> str:
    files = sorted(knowledge_dir().rglob("*.md"))
    out: list[str] = ["Second Brain"]

    if not files:
        out += [
            "  No notes yet. This brain is empty and ready.",
            "",
            "In a Claude Code session here:",
            '  say "/start" for the guided tour',
            '  or say "/log" plus one sentence about anything you studied this week',
            "",
            "All commands: brain --help",
        ]
        inbox = _inbox_line()
        if inbox:
            out.insert(2, f"  {inbox}")
        return "\n".join(out) + "\n"

    from .weights import collect

    domains = {f.parent.name for f in files}
    topics = collect()
    out.append(f"  {len(files)} notes in {len(domains)} domain(s), "
               f"{len(topics)} topics tracked")
    out.append(f"  {_index_line(files)}")
    inbox = _inbox_line()
    if inbox:
        out.append(f"  {inbox}")

    since = since_last_time()
    if since:
        out.append("")
        out.append(since[0])
        for line in since[1:]:
            out.append(f"  {line}")

    gaps = _gap_lines()
    if gaps:
        out.append("")
        out.append("Where to focus next:")
        for line in gaps:
            out.append(f"  {line}")

    top_topic = gaps[0].split(" (")[0] if gaps else next(iter(topics))
    out += [
        "",
        "Try:",
        f'  say "quiz me on {top_topic}"',
        '  say "what should I study next"',
        "  brain ui    opens your knowledge map",
        "",
        "All commands: brain --help",
    ]
    return "\n".join(out) + "\n"
