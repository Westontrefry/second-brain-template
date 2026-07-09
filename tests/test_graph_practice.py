"""Practice layer: model/practice/*.yaml problem links land on the concept's
resolved node as UI-only data — never evidence."""
import datetime as dt

from brain.graph import build

TODAY = dt.date(2026, 7, 2)


def by_id(g):
    return {n["id"]: n for n in g["nodes"]}


def test_practice_links_attach_to_resolved_node(sandbox):
    pdir = sandbox / "model" / "practice"
    pdir.mkdir(parents=True, exist_ok=True)  # sandbox copies live model/
    (pdir / "test-list.yaml").write_text(
        "trees:\n  - name: Invert Binary Tree\n    url: https://example.com/invert\n",
        encoding="utf-8",
    )
    g = build(today=TODAY)
    practice = by_id(g)["trees"].get("practice", [])
    assert {"name": "Invert Binary Tree", "url": "https://example.com/invert"} in practice


def test_alias_refs_resolve_to_the_same_concept(sandbox):
    pdir = sandbox / "model" / "practice"
    pdir.mkdir(parents=True, exist_ok=True)
    # "priority queues" is an alias of the heaps concept in the registry
    (pdir / "test-list.yaml").write_text(
        "priority queues:\n  - name: Last Stone Weight\n    url: https://example.com/lsw\n",
        encoding="utf-8",
    )
    g = build(today=TODAY)
    practice = by_id(g)["heaps"].get("practice", [])
    assert {"name": "Last Stone Weight", "url": "https://example.com/lsw"} in practice


def test_roadmap_only_concept_accepts_practice(sandbox):
    # A roadmap topic the registry never seeded is an "extra" in the compiled
    # model — a real concept with a real node. Practice keyed to it must
    # resolve like any other, not be skipped as unknown.
    goals = sandbox / "goals" / "goals.yaml"
    goals.write_text(
        goals.read_text(encoding="utf-8")
        + "  - id: custom-goal\n    title: Custom goal\n    priority: 1\n",
        encoding="utf-8",
    )
    (sandbox / "goals" / "roadmaps" / "custom-goal.yaml").write_text(
        "goal: custom-goal\ntitle: Custom goal\ntopics:\n"
        "  - id: fresh-topic\n    name: Fresh Topic\n    required_level: 2\n",
        encoding="utf-8",
    )
    pdir = sandbox / "model" / "practice"
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "test-list.yaml").write_text(
        "fresh-topic:\n  - name: P1\n    url: https://example.com/p1\n",
        encoding="utf-8",
    )
    g = build(today=TODAY)
    practice = by_id(g)["fresh-topic"].get("practice", [])
    assert {"name": "P1", "url": "https://example.com/p1"} in practice


def test_unknown_practice_concept_skipped_not_fatal(sandbox, capsys):
    pdir = sandbox / "model" / "practice"
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "test-list.yaml").write_text(
        "no-such-concept:\n  - name: X\n    url: https://example.com/x\n",
        encoding="utf-8",
    )
    g = build(today=TODAY)  # must not raise
    assert "no-such-concept" in capsys.readouterr().out
    assert all("X" != p["name"] for n in g["nodes"] for p in n.get("practice", []))
