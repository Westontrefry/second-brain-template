from pathlib import Path

import pytest

from brain.model import registry
from brain.model.imports import OUTLINE_EDGE_CONFIDENCE, import_resource
from brain.model.outline import clean_term, parse_outline
from brain.model.tracks import load_track, load_tracks

FIXTURE = Path(__file__).parent / "fixtures" / "syllabus.md"


def test_parse_outline_fixture():
    title, units = parse_outline(FIXTURE.read_text())
    assert title == "Advanced Data Structures (COP9999)"
    assert [u.name for u in units] == [
        "Week 1 — Review", "Week 2 — Amortized analysis", "Week 3 — Disjoint sets"]
    assert units[0].terms == ["Hash tables", "Trees"]
    assert units[1].terms == ["Amortized analysis", "Splay trees"]  # ':' desc cut, bold stripped
    assert units[2].terms == ["Union-find", "Path compression"]     # numbered + link


def test_clean_term():
    assert clean_term("**Deadlock**") == "Deadlock"
    assert clean_term("IPC: pipes, signals") == "IPC"
    assert clean_term("[Union-find](https://x.dev)") == "Union-find"
    assert clean_term("Paging — virtual memory") == "Paging"


def test_import_dry_run_writes_nothing(sandbox):
    before = registry.load()
    result = import_resource(FIXTURE, dry_run=True)
    assert not result.written
    assert not result.track_path.exists()
    assert len(registry.load()) == len(before)
    assert "track: advanced-data-structures-cop9999" in result.track_yaml


def test_import_outline(sandbox):
    result = import_resource(FIXTURE, slug="adv-ds")
    assert result.written

    # known vocabulary canonicalizes, unknown terms became concepts
    assert {c.id for c in result.new_concepts} == {
        "amortized-analysis", "union-find", "path-compression"}
    reg = registry.load()
    assert reg.resolve("amortized analysis") == "amortized-analysis"

    track = load_track(result.track_path, reg)  # validates refs
    assert track.track == "adv-ds" and track.adapter == "outline"
    # 'Hash tables' -> hash-maps alias; 'Splay trees' -> trees alias
    assert track.units[0].concepts == ["hash-maps", "trees"]
    assert track.units[1].concepts == ["amortized-analysis", "trees"]

    # order-based edges: adjacent units only, inferred confidence, no self-loops
    pairs = {(e.source, e.target) for e in track.edges}
    assert ("hash-maps", "amortized-analysis") in pairs
    assert ("amortized-analysis", "union-find") in pairs
    assert ("hash-maps", "union-find") not in pairs  # units 1->3 not adjacent
    assert ("trees", "trees") not in pairs           # Trees then Splay trees
    assert all(e.confidence == OUTLINE_EDGE_CONFIDENCE and "outline order" in e.provenance
               for e in track.edges)

    # the imported track shows up alongside the roadmap tracks
    assert "adv-ds" in {t.track for t in load_tracks(reg)}


def test_import_is_idempotent_and_keeps_registry_header(sandbox):
    header_before = registry.file_header()
    assert header_before.startswith("#")
    import_resource(FIXTURE, slug="adv-ds")
    n = len(registry.load())
    import_resource(FIXTURE, slug="adv-ds")  # re-import: no dup concepts
    assert len(registry.load()) == n
    assert registry.file_header() == header_before


def test_import_roadmap_format_file(sandbox):
    src = sandbox / "goals" / "roadmaps" / "dsa-interviews.yaml"
    result = import_resource(src, dry_run=True)
    assert result.track.adapter == "roadmap"
    assert result.track.track == "dsa-interviews"
    assert result.new_concepts == []  # all seeded already
    assert all(e.confidence == 1.0 for e in result.track.edges)


def test_import_rejects_junk(sandbox, tmp_path):
    empty = tmp_path / "empty.md"
    empty.write_text("just prose, no headings or lists\n")
    with pytest.raises(ValueError, match="no units"):
        import_resource(empty)
    with pytest.raises(ValueError, match="not a file"):
        import_resource(tmp_path / "nope.md")
