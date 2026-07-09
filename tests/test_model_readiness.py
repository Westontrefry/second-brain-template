import datetime as dt
from pathlib import Path

import pytest

from brain.model.imports import import_resource
from brain.model.readiness import readiness

from conftest import write_note

TODAY = dt.date(2026, 7, 2)
FIXTURE = Path(__file__).parent / "fixtures" / "syllabus.md"


def test_every_line_self_explains(sandbox):
    report = readiness("gcp-cdl", today=TODAY)
    assert report.title and len(report.lines) == 9  # one per roadmap topic
    for line in report.lines:
        assert line.because, f"{line.concept} has no because"
        assert line.state in ("mastered", "learning", "weak", "stale", "missing")


def test_blocked_concepts_show_their_prereq(sandbox):
    report = readiness("dsa-interviews", today=TODAY)
    trees = next(ln for ln in report.lines if ln.concept == "trees")
    assert "recursion-backtracking" in trees.blocked_by  # matches gaps.py blocking
    assert "first: recursion-backtracking" in trees.because


def test_not_ready_until_everything_evidenced(sandbox):
    report = readiness("dsa-interviews", today=TODAY)
    assert not report.ready
    assert report.counts().get("missing", 0) > 0


def test_ready_track_exits_clean(sandbox):
    write_note(sandbox, "2026-06-30-ht", topics=["hash tables"], confidence=3)
    write_note(sandbox, "2026-06-29-tr", topics=["trees"], confidence=3)
    write_note(sandbox, "2026-06-28-aa", topics=["amortized analysis"], confidence=2)
    write_note(sandbox, "2026-06-27-uf", topics=["union by rank"], confidence=2)
    write_note(sandbox, "2026-06-26-pc", topics=["path compression"], confidence=2)
    import_resource(FIXTURE, slug="adv-ds")
    report = readiness("adv-ds", today=TODAY)
    assert report.ready
    assert all(ln.state in ("mastered", "learning") for ln in report.lines)
    assert all(not ln.blocked_by for ln in report.lines)


def test_imported_track_readiness_uses_canonical_ids(sandbox):
    import_resource(FIXTURE, slug="adv-ds")
    report = readiness("adv-ds", today=TODAY)
    ids = [ln.concept for ln in report.lines]
    assert "hash-maps" in ids and "trees" in ids     # aliases canonicalized
    assert len(ids) == len(set(ids))                 # trees appears once, not per unit


def test_unknown_track_lists_available(sandbox):
    with pytest.raises(ValueError, match="dsa-interviews"):
        readiness("not-a-track", today=TODAY)
