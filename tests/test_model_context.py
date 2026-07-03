import datetime as dt
from pathlib import Path

import pytest
import yaml

from brain.model.context import MAX_GAPS, build_context, render_context
from brain.model.imports import import_resource

TODAY = dt.date(2026, 7, 2)
FIXTURE = Path(__file__).parent / "fixtures" / "syllabus.md"


def test_render_is_valid_yaml_under_100_lines(sandbox):
    text = render_context(today=TODAY)
    assert len(text.splitlines()) < 100
    data = yaml.safe_load(text)  # header comments don't break parsing
    assert data["generated"] == "2026-07-02"
    assert {"tracks", "concepts", "top_gaps"} <= set(data)


def test_gaps_carry_because_and_respect_cap(sandbox):
    data = build_context(today=TODAY)
    assert 0 < len(data["top_gaps"]) <= MAX_GAPS
    assert all(g["because"] and g["concept"] and g["track"] for g in data["top_gaps"])


def test_goal_priority_orders_tracks_and_gaps(sandbox):
    import_resource(FIXTURE, slug="adv-ds")  # no goal -> sorts last
    data = build_context(today=TODAY)
    slugs = [t["track"] for t in data["tracks"]]
    assert slugs[0] == "dsa-interviews"      # priority 5
    assert slugs.index("adv-ds") > slugs.index("gcp-cdl")  # goalless tracks sort last
    assert data["top_gaps"][0]["track"] == "dsa-interviews"
    # round-robin: the first len(tracks-with-gaps) gaps are all distinct tracks
    first = [g["track"] for g in data["top_gaps"][:len(set(g["track"] for g in data["top_gaps"]))]]
    assert len(set(first)) == len(first)


def test_track_filter_scopes_everything(sandbox):
    data = build_context(track="gcp-cdl", today=TODAY)
    assert [t["track"] for t in data["tracks"]] == ["gcp-cdl"]
    assert all(g["track"] == "gcp-cdl" for g in data["top_gaps"])
    in_scope = {c for ids in data["concepts"].values() for c in ids}
    assert "big-o" not in in_scope           # dsa concept filtered out
    assert data["tracks"][0]["deadline"]     # goal metadata present


def test_unknown_filter_raises(sandbox):
    with pytest.raises(ValueError, match="unknown track or goal"):
        build_context(track="nope", today=TODAY)
