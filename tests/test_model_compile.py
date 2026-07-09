import datetime as dt
import json
from pathlib import Path

from brain.model.compile import classify, compile_model
from brain.model.imports import import_resource

from conftest import write_note

TODAY = dt.date(2026, 7, 2)
FIXTURE = Path(__file__).parent / "fixtures" / "syllabus.md"


def test_classify_bands():
    assert classify(0.0, "", TODAY)[0] == "missing"
    assert classify(1.0, "2026-06-30", TODAY)[0] == "weak"
    assert classify(2.0, "2026-06-30", TODAY)[0] == "learning"
    assert classify(4.5, "2026-06-30", TODAY)[0] == "mastered"
    # stale overrides the level bands (matches gaps.py "stale — refresh")
    state, reason = classify(4.5, "2025-12-01", TODAY)
    assert state == "stale" and "2025-12-01" in reason and "level 4.5" in reason


def test_states_from_real_notes(sandbox):
    write_note(sandbox, "2026-06-30-dp", topics=["dynamic programming"],
               confidence=2)                                   # learning (level 2)
    write_note(sandbox, "2026-06-29-lists", topics=["linked lists"],
               confidence=1)                                   # weak
    write_note(sandbox, "2026-06-28-sort", topics=["quicksort"],
               confidence=3, ai_confidence=4.5)                # mastered via assessment
    write_note(sandbox, "2025-11-01-heap", topics=["priority queues"],
               confidence=3)                                   # stale (>120d)

    m = compile_model(TODAY)
    assert m.concepts["dynamic-programming"].state == "learning"
    assert m.concepts["linked-lists"].state == "weak"
    assert m.concepts["sorting"].state == "mastered"    # quicksort is an alias
    assert m.concepts["heaps"].state == "stale"
    assert m.concepts["two-pointers"].state == "missing"
    assert all(c.reason for c in m.concepts.values())   # every line has its because


def test_recent_event_unstales_a_concept(sandbox):
    write_note(sandbox, "2025-11-01-heap", topics=["priority queues"], confidence=3)
    (sandbox / "events.jsonl").write_text(json.dumps(
        {"ts": "2026-06-20T10:00:00", "kind": "exposure", "topic": "priority queues"}
    ) + "\n")
    m = compile_model(TODAY)
    assert m.concepts["heaps"].state == "learning"
    assert m.concepts["heaps"].last_touch == "2026-06-20"


def test_convergence_counts_tracks(sandbox):
    # relative, not absolute: the sandbox copies the LIVE model/, so real
    # tracks touching "trees" vary — assert the counting behavior instead
    m = compile_model(TODAY)
    before = m.concepts["trees"].convergence
    assert before >= 1 and "dsa-interviews" in m.concepts["trees"].tracks
    import_resource(FIXTURE, slug="adv-ds")            # fixture also covers trees
    m = compile_model(TODAY)
    assert m.concepts["trees"].convergence == before + 1
    assert "adv-ds" in m.concepts["trees"].tracks
    assert m.concepts["big-o"].convergence == 1
    assert m.concepts["union-by-rank"].convergence == 1   # imported concept classified too
    assert m.concepts["union-by-rank"].state == "missing"


def test_edges_carry_track_and_provenance(sandbox):
    import_resource(FIXTURE, slug="adv-ds")
    m = compile_model(TODAY)
    assert all(e["track"] and e["provenance"] for e in m.edges)
    kinds = {(e["track"], e["confidence"] == 1.0) for e in m.edges}
    assert ("dsa-interviews", True) in kinds           # roadmap edges explicit
    assert ("adv-ds", False) in kinds                  # outline edges inferred


def test_unregistered_roadmap_topic_surfaces_not_crashes(sandbox):
    rm = sandbox / "goals" / "roadmaps" / "dsa-interviews.yaml"
    rm.write_text(rm.read_text() + (
        "\n  - id: quantum-sort\n    name: Quantum sorting\n"
        "    required_level: 3\n    prereqs: []\n    aliases: []\n"))
    m = compile_model(TODAY)
    qc = m.concepts["quantum-sort"]
    assert qc.state == "missing" and "not in the registry" in qc.reason
    assert "dsa-interviews" in qc.tracks
