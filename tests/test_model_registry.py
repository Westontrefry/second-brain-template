import pytest

from brain.model.registry import Concept, harvest_roadmaps, load, merge, save, validate


def test_load_seeded_registry_and_resolve(sandbox):
    reg = load()
    assert len(reg) >= 30  # 36 seeded from the three roadmaps
    assert reg.resolve("big-o") == "big-o"                # by id
    assert reg.resolve("kubernetes") == "gke"             # by alias
    assert reg.resolve("Time Complexity!") == "big-o"     # slugify normalizes
    assert reg.resolve("underwater basket weaving") is None


def test_missing_file_is_empty_registry(sandbox, tmp_path):
    reg = load(tmp_path / "nope.yaml")
    assert len(reg) == 0 and reg.resolve("anything") is None


def test_validate_duplicate_id():
    data = {"concepts": [{"id": "big-o", "name": "A"}, {"id": "big-o", "name": "B"}]}
    errors = validate(data)
    assert any("duplicate concept id" in e for e in errors)


def test_validate_alias_collision_across_concepts():
    data = {"concepts": [
        {"id": "trees", "name": "Trees", "aliases": ["bst"]},
        {"id": "graphs", "name": "Graphs", "aliases": ["BST"]},  # same slug key
    ]}
    errors = validate(data)
    assert any("'bst'" in e and "trees" in e for e in errors)


def test_validate_alias_colliding_with_other_id():
    data = {"concepts": [
        {"id": "trees", "name": "Trees"},
        {"id": "graphs", "name": "Graphs", "aliases": ["trees"]},
    ]}
    assert validate(data)


def test_validate_shape_errors():
    assert validate(["not", "a", "mapping"])
    assert validate({"concepts": [{"name": "no id"}]})
    assert validate({"concepts": [{"id": "x", "name": ""}]})
    assert validate({"concepts": [{"id": "Not A Slug", "name": "X"}]})
    assert validate({"concepts": [{"id": "x", "name": "X", "aliases": [1]}]})
    assert validate({"concepts": [{"id": "ok", "name": "OK", "aliases": ["fine"]}]}) == []


def test_load_rejects_invalid(sandbox, tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("concepts:\n- id: a\n  name: A\n- id: a\n  name: B\n")
    with pytest.raises(ValueError, match="duplicate concept id"):
        load(p)


def test_merge_unions_aliases_on_same_id():
    merged, notes = merge(
        [Concept("trees", "Trees", ["bst"])],
        [Concept("trees", "Trees and BSTs", ["binary trees", "bst"])],
    )
    assert len(merged) == 1 and notes == []
    assert set(merged[0].aliases) == {"bst", "binary trees"}


def test_merge_drops_colliding_alias_with_note():
    merged, notes = merge(
        [Concept("operations", "Ops", ["observability"])],
        [Concept("scaling-operations", "Scaling ops", ["observability", "sre"])],
    )
    scaling = next(c for c in merged if c.id == "scaling-operations")
    assert scaling.aliases == ["sre"]
    assert len(notes) == 1 and "observability" in notes[0] and "operations" in notes[0]


def test_merge_folds_incoming_id_owned_by_alias():
    # incoming topic id matches an existing concept's alias -> same concept
    merged, _ = merge(
        [Concept("gke", "Google Kubernetes Engine", ["kubernetes"])],
        [Concept("kubernetes", "Kubernetes", ["k8s"])],
    )
    assert len(merged) == 1
    assert merged[0].id == "gke" and "k8s" in merged[0].aliases


def test_harvest_matches_roadmaps(sandbox):
    import yaml

    concepts, notes = harvest_roadmaps()
    ids = {c.id for c in concepts}
    for name in ("dsa-interviews", "gcp-ace", "gcp-cdl"):
        with open(sandbox / "goals" / "roadmaps" / f"{name}.yaml") as f:
            for t in yaml.safe_load(f)["topics"]:
                assert t["id"] in ids
    # harvested set is a valid registry and round-trips through save/load
    path = save(concepts, sandbox / "model" / "harvested.yaml")
    assert len(load(path)) == len(concepts)
    # known cross-roadmap collision resolved first-claim-wins, with a note
    assert any("bigquery" in n for n in notes)
    reg = load(path)
    assert reg.resolve("bigquery") == "managed-databases"
