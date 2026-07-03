import datetime as dt

import pytest

from brain.assess import assess, log_exposure
from brain.schema import parse_note, validate_file
from brain.weights import collect

from conftest import write_note

TODAY = dt.date(2026, 7, 2)


def test_assess_writes_receipts_and_raises_evidenced_level(sandbox):
    path = write_note(sandbox, "2026-07-01-target", topics=["assesstest"], confidence=2)
    assess("assesstest", 4, "quiz 2026-07-02: applied X to novel case, quoted '...'",
           ["2026-07-01-target"], today=TODAY)
    assert validate_file(path) == []
    note, _ = parse_note(path)
    assert note.meta["ai_confidence"] == 4
    assert "quiz" in note.meta["ai_confidence_rationale"]
    assert note.meta["last_assessed"] == "2026-07-02"
    assert note.meta["confidence"] == 2  # self-rating untouched
    assert collect(today=TODAY)["assesstest"].evidenced_level == 4


def test_assess_requires_topic_on_evidence_note(sandbox):
    write_note(sandbox, "2026-07-01-other", topics=["something-else"])
    with pytest.raises(ValueError, match="does not carry topic"):
        assess("assesstest", 3, "r", ["2026-07-01-other"], today=TODAY)


def test_assess_requires_rationale_and_evidence(sandbox):
    with pytest.raises(ValueError, match="evidence"):
        assess("t", 3, "rationale", [], today=TODAY)
    write_note(sandbox, "2026-07-01-x", topics=["t"])
    with pytest.raises(ValueError, match="rationale"):
        assess("t", 3, "  ", ["2026-07-01-x"], today=TODAY)


def test_log_exposure_bumps_count_and_recency(sandbox):
    path = write_note(sandbox, "2026-06-01-exp", topics=["exptest"],
                      last_reviewed="2026-06-01")
    log_exposure("exptest", today=TODAY)
    note, _ = parse_note(path)
    assert note.meta["exposure_count"] == 2
    assert str(note.meta["last_reviewed"]) == "2026-07-02"
    assert validate_file(path) == []


def test_log_exposure_unknown_topic(sandbox):
    with pytest.raises(ValueError, match="no notes carry"):
        log_exposure("never-studied", today=TODAY)


def test_rewrite_preserves_body(sandbox):
    body = "First paragraph.\n\nSecond with [[a-link]] and `code`."
    path = write_note(sandbox, "2026-07-01-body", topics=["bodytest"], body=body)
    assess("bodytest", 3, "r", ["2026-07-01-body"], today=TODAY)
    note, _ = parse_note(path)
    assert note.body.strip() == body
