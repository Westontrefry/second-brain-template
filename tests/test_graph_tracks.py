"""KME track layer in the graph export (M7): imported tracks render exactly
like roadmap layers — goals list, node membership, requirements, prereq
edges, suggestions — plus convergence as a node metric."""
import datetime as dt
from pathlib import Path

from brain.graph import build
from brain.model.imports import import_resource

from conftest import write_note

TODAY = dt.date(2026, 7, 2)
FIXTURE = Path(__file__).parent / "fixtures" / "syllabus.md"


def by_id(g):
    return {n["id"]: n for n in g["nodes"]}


def test_imported_track_joins_goal_dropdown(sandbox):
    import_resource(FIXTURE, slug="adv-ds")
    g = build(today=TODAY)
    entry = next((e for e in g["goals"] if e["id"] == "adv-ds"), None)
    assert entry and "(track)" in entry["title"]
    # roadmap-derived tracks are NOT duplicated in the list
    assert sum(1 for e in g["goals"] if e["id"] == "dsa-interviews") == 1


def test_track_concepts_annotate_or_create_nodes(sandbox):
    write_note(sandbox, "2026-07-01-ht", topics=["hash tables"], confidence=3)
    import_resource(FIXTURE, slug="adv-ds")
    g = build(today=TODAY)
    nodes = by_id(g)
    ht = nodes["hash tables"]                     # evidenced topic annotated in place
    assert "adv-ds" in ht["goals"]
    assert any(r["goal"] == "adv-ds" and r["topicId"] == "hash-maps"
               for r in ht["requirements"])
    uf = nodes["union-find"]                      # unevidenced concept -> missing node
    assert uf["type"] == "missing" and "adv-ds" in uf["goals"]


def test_track_prereq_edges_and_suggestions(sandbox):
    import_resource(FIXTURE, slug="adv-ds")
    g = build(today=TODAY)
    key = tuple(sorted(("amortized-analysis", "union-find")))
    e = next((e for e in g["edges"] if (e["source"], e["target"]) == key), None)
    assert e is not None and e["kind"] == "prereq"
    sugg = g["suggestions"]["adv-ds"]
    assert sugg and all(s["nodeId"] and s["action"] for s in sugg)
    assert sugg[0]["score"] >= sugg[-1]["score"]


def test_convergence_on_nodes(sandbox):
    write_note(sandbox, "2026-07-01-tr", topics=["trees"], confidence=3)
    import_resource(FIXTURE, slug="adv-ds")       # trees now in dsa roadmap + adv-ds
    g = build(today=TODAY)
    nodes = by_id(g)
    assert nodes["trees"]["convergence"] == 2
    assert nodes["union-find"]["convergence"] == 1
    assert "convergence" not in nodes.get("authentication", {})  # off-model topic
