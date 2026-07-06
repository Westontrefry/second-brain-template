"""First-touch detection: fires once per skill, then goes quiet. Read-only and
derived from state each skill changes on its first run (source-tagged events,
import-source notes, ui/paths overlays) so no separate 'mark seen' step exists."""
from __future__ import annotations

import json

from brain.assess import assess, log_exposure
from brain.first_touch import explainer, is_first_touch
from conftest import write_note


def test_quiz_fires_then_quiet(sandbox):
    write_note(sandbox, "2026-02-01-q", topics=["testing"])
    assert is_first_touch("quiz")
    assert explainer("quiz").startswith("First quiz")
    assess("testing", 3, "quiz receipts", ["2026-02-01-q"], source="quiz")
    assert not is_first_touch("quiz")
    assert explainer("quiz") == ""


def test_quiz_and_debrief_are_independent(sandbox):
    # both write `assess` events; the source tag keeps their first-touches separate
    write_note(sandbox, "2026-02-01-q", topics=["testing"])
    assess("testing", 3, "quiz receipts", ["2026-02-01-q"], source="quiz")
    assert not is_first_touch("quiz")
    assert is_first_touch("debrief")  # a quiz does not count as a debrief


def test_review_fires_via_exposure_source(sandbox):
    write_note(sandbox, "2026-02-01-r", topics=["testing"])
    assert is_first_touch("review")
    log_exposure("testing", source="review")
    assert not is_first_touch("review")


def test_legacy_sourceless_event_does_not_silence(sandbox):
    # an old assessment written before source tags still leaves 'first quiz' true;
    # the next sourced quiz silences it (self-healing)
    write_note(sandbox, "2026-02-01-q", topics=["testing"])
    assess("testing", 3, "no source", ["2026-02-01-q"])  # legacy, sourceless
    assert is_first_touch("quiz")


def test_ingest_fires_until_an_import_note_exists(sandbox):
    assert is_first_touch("ingest")  # fixtures are study-session, none imported
    write_note(sandbox, "2026-02-01-imp", topics=["testing"], source="import")
    assert not is_first_touch("ingest")


def test_path_fires_until_an_overlay_exists(sandbox):
    assert is_first_touch("path")
    overlay = sandbox / "ui" / "paths" / "demo.json"
    overlay.parent.mkdir(parents=True, exist_ok=True)
    overlay.write_text(json.dumps({"segments": []}), encoding="utf-8")
    assert not is_first_touch("path")


def test_unknown_skill_raises(sandbox):
    try:
        is_first_touch("log")
    except ValueError as e:
        assert "unknown skill" in str(e)
    else:
        raise AssertionError("expected ValueError for unknown skill")
