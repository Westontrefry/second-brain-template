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
    assert entry and entry["kind"] == "track"
    # title stays clean — the UI groups tracks under their own heading
    assert "(track)" not in entry["title"]
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


def test_imported_roadmap_format_track_renders(sandbox):
    # A roadmap-FORMAT file imported as a track (brain model import x.yaml) is
    # a real track, not an in-repo goal roadmap — the graph's skip for
    # goal-mirroring tracks must match by id, never by adapter, or the
    # imported track silently never reaches the map.
    spec = sandbox / "plan.yaml"
    spec.write_text(
        "title: Imported Plan\n"
        "topics:\n"
        "  - id: plan-basics\n    name: Plan basics\n    prereqs: []\n"
        "  - id: plan-advanced\n    name: Plan advanced\n    prereqs: [plan-basics]\n",
        encoding="utf-8",
    )
    import_resource(spec, adapter="roadmap", slug="imported-plan")
    g = build(today=TODAY)
    entry = next((e for e in g["goals"] if e["id"] == "imported-plan"), None)
    assert entry and entry["kind"] == "track"
    nodes = by_id(g)
    assert nodes["plan-basics"]["type"] == "missing"
    assert "imported-plan" in nodes["plan-advanced"]["goals"]
    assert g["suggestions"]["imported-plan"]
    # ...while goal-mirroring roadmap tracks stay deduplicated
    assert sum(1 for e in g["goals"] if e["id"] == "dsa-interviews") == 1


def test_convergence_on_nodes(sandbox):
    write_note(sandbox, "2026-07-01-tr", topics=["trees"], confidence=3)
    import_resource(FIXTURE, slug="adv-ds")       # trees now in dsa roadmap + adv-ds
    g = build(today=TODAY)
    nodes = by_id(g)
    assert nodes["trees"]["convergence"] == 2
    assert nodes["union-find"]["convergence"] == 1
    assert "convergence" not in nodes.get("authentication", {})  # off-model topic
