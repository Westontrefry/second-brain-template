"""Home screen (bare `brain`) — PLAN-UX U1/U4."""
from __future__ import annotations

import datetime as dt
import json

from conftest import write_note

from brain.cli import main
from brain.home import render_home, since_last_time


def test_bare_brain_prints_home_screen(sandbox, capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "Second Brain" in out
    assert "notes in" in out
    assert "brain --help" in out


def test_home_screen_populated(sandbox):
    out = render_home()
    assert "topics tracked" in out
    # index never built in the sandbox: stated as a fact with the fix
    assert "index: not built yet" in out
    assert "Try:" in out
    assert 'say "quiz me on' in out
    assert "brain ui" in out


def test_since_last_time_empty_without_history(sandbox):
    assert since_last_time(dt.date(2026, 7, 5)) == []


def test_since_last_time_reports_changes_after_boundary(sandbox):
    today = dt.date(2026, 7, 5)
    events = [
        {"ts": "2026-07-03T10:00:00", "kind": "exposure", "topic": "testing"},
        {"ts": "2026-07-04T20:00:00", "kind": "assess", "topic": "graphs", "level": 3.0},
    ]
    (sandbox / "events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    write_note(sandbox, "2026-07-04-brand-new-note", topics=["graphs"])
    out = since_last_time(today)
    text = "\n".join(out)
    # boundary = 2026-07-04, the last activity day before today, INCLUDED —
    # that day's assess and new note are exactly the "last session" recap
    assert "Since last time (2026-07-04)" in text
    assert "1 note(s) added" in text
    assert "graphs is now 3" in text


def test_since_last_time_flags_topics_crossing_stale_line(sandbox):
    today = dt.date(2026, 7, 5)
    (sandbox / "events.jsonl").write_text(
        json.dumps({"ts": "2026-07-03T10:00:00", "kind": "exposure",
                    "topic": "testing"}) + "\n", encoding="utf-8")
    lr = (today - dt.timedelta(days=121)).isoformat()
    write_note(sandbox, f"{lr}-fading-topic", topics=["fading topic"],
               last_reviewed=lr)
    out = "\n".join(since_last_time(today))
    assert "went stale" in out
    assert "fading topic" in out


def test_home_screen_empty_brain_offers_tour(sandbox):
    for f in (sandbox / "knowledge").rglob("*.md"):
        f.unlink()
    out = render_home()
    assert "No notes yet" in out
    assert "/start" in out
    assert "/log" in out
    # no gap machinery output on an empty brain
    assert "Where to focus next" not in out
