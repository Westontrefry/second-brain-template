import datetime as dt

from brain.graph import build, export

from conftest import write_note

TODAY = dt.date(2026, 7, 2)


def edge_between(g, a, b):
    key = (min(a, b), max(a, b))
    return next((e for e in g["edges"] if (e["source"], e["target"]) == key), None)


def test_requirement_annotated_on_exact_match(sandbox):
    g = build(today=TODAY)
    byid = {n["id"]: n for n in g["nodes"]}
    reqs = byid["databases"]["requirements"]
    assert reqs and reqs[0]["goal"] == "dsa-interviews" and reqs[0]["gap"] == 0


def test_unevidenced_roadmap_topic_is_missing_node(sandbox):
    g = build(today=TODAY)
    byid = {n["id"]: n for n in g["nodes"]}
    assert byid["gke"]["type"] == "missing"
    assert byid["gke"]["requirements"][0]["gap"] == 3


def test_prereq_edges_connect_roadmap_skeleton(sandbox):
    g = build(today=TODAY)
    e = edge_between(g, "compute-engine", "gke")
    assert e is not None and e["kind"] == "prereq"


def test_cooccur_and_wikilink_edges(sandbox):
    g = build(today=TODAY)
    cooccur = edge_between(g, "databases", "indexing")
    assert cooccur is not None and cooccur["kind"] == "cooccur"
    # the ebapp auth note [[links]] the b-tree note -> cross-note topic edge
    wikilink = edge_between(g, "authentication", "databases")
    assert wikilink is not None and wikilink["kind"] == "wikilink"


def test_alias_evidence_merges_into_topic_node(sandbox):
    write_note(sandbox, "2026-07-01-k8s", domain="cloud", topics=["kubernetes"],
               confidence=3, goals=["gcp-ace"])
    g = build(today=TODAY)
    byid = {n["id"]: n for n in g["nodes"]}
    assert "gke" not in byid  # matched via alias, no missing node
    assert byid["kubernetes"]["requirements"][0]["topicId"] == "gke"


def test_export_writes_file_uri_safe_data_js(sandbox):
    path = export(today=TODAY)
    text = path.read_text(encoding="utf-8")
    assert text.startswith("window.GRAPH = ")
    assert "window.PATHS = " in text
    assert "window.REFERENCE = " in text
    assert (sandbox / "ui" / "graph.json").exists()


def test_reference_derived_from_skills_and_parser(sandbox):
    from brain.graph import _load_reference

    ref = _load_reference()
    skill_names = [s["name"] for s in ref["skills"]]
    assert "interview-pack" in skill_names and "quiz" in skill_names
    assert all(s["description"] for s in ref["skills"])
    cli_names = [c["name"] for c in ref["cli"]]
    assert "assess" in cli_names and "gaps" in cli_names and "ui" in cli_names
