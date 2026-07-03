import datetime as dt

from brain.gaps import analyze

from conftest import write_note

TODAY = dt.date(2026, 7, 2)


def by_topic(gaps, goal, topic_id):
    return next((g for g in gaps if g.goal == goal and g.topic_id == topic_id), None)


def test_partial_evidence_reported_as_close(sandbox):
    gaps = analyze(goal_id="gcp-ace", today=TODAY)
    iam = by_topic(gaps, "gcp-ace", "iam")
    assert iam is not None
    assert iam.evidenced == 2 and iam.required == 3
    assert "close" in iam.action


def test_satisfied_topic_absent(sandbox):
    gaps = analyze(goal_id="dsa-interviews", today=TODAY)
    assert by_topic(gaps, "dsa-interviews", "databases") is None


def test_alias_counts_as_evidence(sandbox):
    write_note(sandbox, "2026-07-01-k8s", domain="cloud", topics=["kubernetes"],
               confidence=3, goals=["gcp-ace"])
    gaps = analyze(goal_id="gcp-ace", today=TODAY)
    assert by_topic(gaps, "gcp-ace", "gke") is None  # alias satisfied required 3


def test_prereq_blocking_deprioritizes(sandbox):
    gaps = analyze(goal_id="dsa-interviews", today=TODAY)
    trees = by_topic(gaps, "dsa-interviews", "trees")
    assert trees is not None and "recursion-backtracking" in trees.blocked_by
    unblocked_same_gap = by_topic(gaps, "dsa-interviews", "big-o")
    assert unblocked_same_gap.score > trees.score


def test_unknown_goal_raises(sandbox):
    import pytest

    with pytest.raises(ValueError):
        analyze(goal_id="not-a-goal", today=TODAY)
