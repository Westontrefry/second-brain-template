import datetime as dt

import pytest
import yaml

from brain.gaps import analyze, load_roadmap
from brain.model import registry
from brain.model.tracks import (
    blocking, evidence_levels, from_roadmap, load_track, load_tracks,
    validate_track,
)
from brain.weights import collect

from conftest import write_note

TODAY = dt.date(2026, 7, 2)


def write_track(sandbox, slug: str, data: dict):
    path = sandbox / "model" / "tracks" / f"{slug}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


SAMPLE = {
    "track": "os-course", "title": "Operating Systems",
    "source": "syllabus: fixture", "adapter": "outline",
    "units": [{"name": "Week 1", "concepts": ["trees"]},
              {"name": "Week 2", "concepts": ["graphs"]}],
    "edges": [{"from": "trees", "to": "graphs", "kind": "prereq",
               "confidence": 0.7, "provenance": "outline order"}],
}


def test_roadmap_adapter_shape(sandbox):
    track = from_roadmap("dsa-interviews")
    roadmap = load_roadmap("dsa-interviews")
    assert track.adapter == "roadmap"
    assert "goals/roadmaps/dsa-interviews.yaml" in track.source
    assert [u.concepts for u in track.units] == [[t["id"]] for t in roadmap["topics"]]
    n_prereqs = sum(len(t.get("prereqs", [])) for t in roadmap["topics"])
    assert len(track.edges) == n_prereqs
    assert all(e.kind == "prereq" and e.confidence == 1.0 and "roadmap" in e.provenance
               for e in track.edges)
    # every concept ref resolves against the seeded registry
    reg = registry.load()
    assert all(reg.resolve(c) == c for c in track.concept_ids())


def test_load_tracks_merges_files_and_roadmaps(sandbox):
    write_track(sandbox, "os-course", SAMPLE)
    tracks = {t.track: t for t in load_tracks(registry.load())}
    assert "os-course" in tracks and tracks["os-course"].adapter == "outline"
    for gid in ("dsa-interviews", "gcp-ace", "gcp-cdl"):
        assert tracks[gid].adapter == "roadmap"
    assert tracks["dsa-interviews"].title  # title comes from goals.yaml


def test_materialized_track_shadows_roadmap(sandbox):
    shadow = dict(SAMPLE, track="dsa-interviews", title="Snapshot")
    write_track(sandbox, "dsa-interviews", shadow)
    tracks = {t.track: t for t in load_tracks()}
    assert tracks["dsa-interviews"].adapter == "outline"


def test_validate_track_errors():
    assert "missing track" in validate_track({})[0]
    bad_edge = dict(SAMPLE, edges=[{"from": "trees"}])
    assert any("missing to" in e for e in validate_track(bad_edge))
    bad_kind = dict(SAMPLE, edges=[{"from": "a", "to": "b", "kind": "vibes"}])
    assert any("unknown kind" in e for e in validate_track(bad_kind))
    bad_conf = dict(SAMPLE, edges=[{"from": "a", "to": "b", "confidence": 2}])
    assert any("confidence" in e for e in validate_track(bad_conf))
    assert validate_track(SAMPLE) == []


def test_unknown_concept_ref_caught_with_registry(sandbox):
    reg = registry.load()
    stray = dict(SAMPLE, units=[{"name": "W1", "concepts": ["quantum-basket-weaving"]}])
    errors = validate_track(stray, reg)
    assert any("quantum-basket-weaving" in e for e in errors)
    path = write_track(sandbox, "stray", stray)
    with pytest.raises(ValueError, match="quantum-basket-weaving"):
        load_track(path, reg)


def test_evidence_levels_join_via_aliases(sandbox):
    write_note(sandbox, "2026-07-01-k8s", domain="cloud", topics=["kubernetes"],
               confidence=3, goals=["gcp-ace"])
    levels = evidence_levels(registry.load(), collect(TODAY))
    assert levels["gke"] == 3  # note topic "kubernetes" is a gke alias


def test_dsa_track_reproduces_gaps_blocking(sandbox):
    """M2 acceptance: the roadmap track's blocking analysis matches gaps.py
    on the same data — same blocked topics, same blocking prereqs, in order."""
    track = from_roadmap("dsa-interviews")
    levels = evidence_levels(registry.load(), collect(TODAY))
    blocked = blocking(track, levels)

    gaps = analyze(goal_id="dsa-interviews", today=TODAY)
    assert gaps and any(g.blocked_by for g in gaps)  # non-trivial comparison
    for g in gaps:
        assert blocked.get(g.topic_id, []) == g.blocked_by
