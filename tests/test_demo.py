"""Demo pack install/remove — PLAN-UX U2 (locked decisions 7+8)."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from brain import demo
from brain.schema import validate_file

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture()
def with_pack(sandbox) -> Path:
    shutil.copytree(REPO / "examples", sandbox / "examples")
    return sandbox


def test_install_copies_all_pack_notes_into_domains(with_pack):
    copied, skipped = demo.install()
    assert len(copied) == len(demo.pack_notes()) == 8
    assert not skipped
    for path in copied:
        assert path.parent.parent.name == "knowledge"
        assert validate_file(path) == []
    assert {p.name for p in demo.installed()} == {p.name for p in copied}


def test_install_is_idempotent(with_pack):
    demo.install()
    copied, skipped = demo.install()
    assert not copied
    assert len(skipped) == 8


def test_remove_leaves_zero_trace(with_pack):
    before = {p for p in (with_pack / "knowledge").rglob("*.md")}
    demo.install()
    removed = demo.remove()
    assert len(removed) == 8
    after = {p for p in (with_pack / "knowledge").rglob("*.md")}
    assert after == before
    assert demo.installed() == []


def test_remove_without_install_is_a_noop(with_pack):
    assert demo.remove() == []


def test_pack_notes_excludes_readme(with_pack):
    assert all(p.name != "README.md" for p in demo.pack_notes())
