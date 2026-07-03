import datetime as dt

from brain.weights import collect

from conftest import write_note

TODAY = dt.date(2026, 7, 2)


def test_self_confidence_capped_at_level_3(sandbox):
    write_note(sandbox, "2026-07-01-cap", topics=["captest"], confidence=5)
    stats = collect(today=TODAY)
    assert stats["captest"].evidenced_level == 3


def test_ai_confidence_overrides_cap(sandbox):
    write_note(sandbox, "2026-07-01-assessed", topics=["aitest"],
               confidence=5, ai_confidence=4)
    stats = collect(today=TODAY)
    assert stats["aitest"].evidenced_level == 4


def test_decay_halves_at_half_life(sandbox):
    write_note(sandbox, "2026-07-01-fresh", topics=["freshtest"], confidence=3)
    write_note(sandbox, "2026-01-03-old", topics=["oldtest"], confidence=3,
               last_reviewed="2026-01-03")  # 180 days before TODAY = note half-life
    stats = collect(today=TODAY)
    ratio = stats["oldtest"].weight / stats["freshtest"].weight
    assert abs(ratio - 0.5) < 0.01


def test_one_note_strengthens_many_topics(sandbox):
    write_note(sandbox, "2026-07-01-multi", topics=["alpha", "beta", "gamma"],
               source="project", confidence=4)
    stats = collect(today=TODAY)
    assert stats["alpha"].weight == stats["beta"].weight == stats["gamma"].weight > 0
    assert "2026-07-01-multi" in stats["gamma"].note_ids


def test_project_evidence_outweighs_note_evidence(sandbox):
    write_note(sandbox, "2026-07-01-proj", topics=["projtest"], source="project")
    write_note(sandbox, "2026-07-01-note", topics=["notetest"], source="study-session")
    stats = collect(today=TODAY)
    assert stats["projtest"].weight > stats["notetest"].weight
