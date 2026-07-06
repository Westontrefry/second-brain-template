"""Shipped mnemonics data files.

The mnemonics/ files are written by skills, not by brain/ code, so these
tests guard the shipped shape the skills rely on: parseable YAML, the
documented record fields, and the locked pack rule (starter vs personal —
the starter pack is the only thing that ever ships publicly).
"""
from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
MNEMONICS = REPO / "mnemonics"

SYMBOL_FIELDS = {"name", "pack", "flavors", "used_for"}
SCENE_FIELDS = {"topic", "line", "hook", "symbols", "origin", "created"}
ORIGINS = {"quiz-miss", "review-miss", "dictated"}


def load(name: str) -> dict:
    return yaml.safe_load((MNEMONICS / name).read_text(encoding="utf-8"))


def test_vocabulary_parses_with_symbol_shape():
    symbols = load("vocabulary.yaml")["symbols"]
    assert symbols, "shipped vocabulary must not be empty"
    for entry in symbols:
        assert set(entry) == SYMBOL_FIELDS, entry.get("name")
        assert entry["pack"] in {"starter", "personal"}, entry["name"]
        assert entry["flavors"] and isinstance(entry["flavors"], list), entry["name"]
        assert isinstance(entry["used_for"], list), entry["name"]


def test_vocabulary_names_are_unique():
    names = [e["name"] for e in load("vocabulary.yaml")["symbols"]]
    assert len(names) == len(set(names))


def test_vocabulary_ships_a_starter_pack():
    packs = {e["pack"] for e in load("vocabulary.yaml")["symbols"]}
    assert "starter" in packs


def test_scenes_parse_with_record_shape():
    scenes = load("scenes.yaml")["scenes"]
    assert isinstance(scenes, list)
    known = {e["name"] for e in load("vocabulary.yaml")["symbols"]}
    for scene in scenes:
        assert set(scene) == SCENE_FIELDS, scene.get("topic")
        assert scene["origin"] in ORIGINS, scene["topic"]
        # ledger integrity: every symbol a scene cites exists in the vocabulary
        assert set(scene["symbols"]) <= known, scene["topic"]
