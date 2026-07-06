"""Frontier expansion write-path: guarded roadmap append + registry re-sync.

Runs against the frozen fixture goals/model (tests/fixtures/*), so it references
only fixture goals: dsa-interviews (has a roadmap), gcp-ace (has a roadmap, with
a gke concept aliased 'kubernetes'), and sideproject (a real goal with NO
roadmap file).
"""
from __future__ import annotations

import datetime as dt

import pytest

from brain.frontier import Proposed, add_topics, roadmap_path
from brain.graph import build
from brain.model import registry

TODAY = dt.date(2026, 7, 6)


def _p(id, name="X", level=3, prereqs=None, aliases=None):
    return Proposed(id=id, name=name, required_level=level,
                    prereqs=prereqs or [], aliases=aliases or [])


def test_add_appends_registers_and_dashes(sandbox):
    # a genuinely-absent topic: not in the roadmap, not a concept, no note
    res = add_topics("dsa-interviews", [_p("network-flow", "Network flow",
                     prereqs=["graphs"], aliases=["max flow", "min cut"])],
                     today=TODAY, rebuild=False)
    assert [p.id for p in res.added] == ["network-flow"]

    # written into the roadmap file, comments preserved (old content still there)
    text = roadmap_path("dsa-interviews").read_text()
    assert "id: network-flow" in text and "System design fundamentals" in text

    # registered as a concept and renders as a dashed (missing) node on the map
    assert registry.load().resolve("max flow") == "network-flow"
    node = next(n for n in build(TODAY)["nodes"] if n["id"] == "network-flow")
    assert node["type"] == "missing" and "dsa-interviews" in node["goals"]


def test_duplicate_id_is_skipped(sandbox):
    # 'graphs' is already a topic in the dsa roadmap
    res = add_topics("dsa-interviews", [_p("graphs", "already here")],
                     today=TODAY, rebuild=False)
    assert not res.added
    assert res.skipped and res.skipped[0][0] == "graphs"
    assert "already in this roadmap" in res.skipped[0][1]


def test_alias_belonging_to_another_concept_is_dropped(sandbox):
    # 'hashing' is an alias of the hash-maps concept; proposing it as an alias
    # would silently un-dash the new node onto hash-maps' evidence.
    res = add_topics("dsa-interviews", [_p("edge-topic", "Edge topic",
                     aliases=["hashing", "a genuinely new alias"])],
                     today=TODAY, rebuild=False)
    assert [p.id for p in res.added] == ["edge-topic"]
    assert res.dropped_aliases == [("edge-topic", "hashing", "hash-maps")]
    # the surviving alias is kept
    assert res.added[0].aliases == ["a genuinely new alias"]


def test_id_colliding_with_existing_concept_is_skipped(sandbox):
    # 'kubernetes' resolves to the gke concept -> adding it as a new id collides
    res = add_topics("gcp-ace", [_p("kubernetes", "K8s dup")],
                     today=TODAY, rebuild=False)
    assert not res.added
    assert res.skipped[0][0] == "kubernetes"
    assert "collides with existing concept 'gke'" in res.skipped[0][1]


def test_governor_caps_additions(sandbox):
    proposed = [_p(f"frontier-cap-{i}", f"Cap {i}") for i in range(5)]
    res = add_topics("dsa-interviews", proposed, max_add=2, today=TODAY, rebuild=False)
    assert len(res.added) == 2
    over = [r for r in res.skipped if "governor cap" in r[1]]
    assert len(over) == 3


def test_unknown_goal_and_missing_roadmap_raise(sandbox):
    with pytest.raises(ValueError, match="unknown goal"):
        add_topics("no-such-goal", [_p("x")], today=TODAY, rebuild=False)
    # sideproject is a real fixture goal with no roadmap file
    with pytest.raises(ValueError, match="no roadmap"):
        add_topics("sideproject", [_p("x")], today=TODAY, rebuild=False)
