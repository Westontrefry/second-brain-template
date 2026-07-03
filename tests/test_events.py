"""Event log: assess and log_exposure append one JSON line each to events.jsonl.
The log is append-only history — frontmatter keeps only the latest state."""
from __future__ import annotations

import json

from brain.assess import assess, log_exposure
from brain.events import events_path
from conftest import write_note


def read_events(sandbox):
    path = sandbox / "events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_assess_appends_event(sandbox):
    write_note(sandbox, "2026-02-01-evt-note", topics=["testing"])
    assess("testing", 3, "clear explanation of edge cases", ["2026-02-01-evt-note"])
    events = read_events(sandbox)
    assert len(events) == 1
    e = events[0]
    assert e["kind"] == "assess"
    assert e["topic"] == "testing"
    assert e["level"] == 3
    assert e["evidence"] == ["2026-02-01-evt-note"]
    assert "ts" in e


def test_log_exposure_appends_event(sandbox):
    write_note(sandbox, "2026-02-01-evt-a", topics=["testing"])
    write_note(sandbox, "2026-02-02-evt-b", topics=["testing"])
    log_exposure("testing")
    events = read_events(sandbox)
    assert len(events) == 1
    assert events[0]["kind"] == "exposure"
    assert events[0]["topic"] == "testing"
    assert events[0]["notes"] == 2


def test_events_accumulate_append_only(sandbox):
    write_note(sandbox, "2026-02-01-evt-note", topics=["testing"])
    assess("testing", 2, "first pass", ["2026-02-01-evt-note"])
    assess("testing", 3, "second pass, deeper", ["2026-02-01-evt-note"])
    log_exposure("testing")
    events = read_events(sandbox)
    assert [e["kind"] for e in events] == ["assess", "assess", "exposure"]
    # history preserved even though frontmatter holds only the latest level
    assert [e.get("level") for e in events[:2]] == [2, 3]


def test_events_path_respects_sandbox(sandbox):
    assert events_path() == sandbox / "events.jsonl"
