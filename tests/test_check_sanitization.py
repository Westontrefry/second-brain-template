"""The sanitization gate's patterns, pinned by tests.

Every leak class the gate promises to catch gets a planted sample here, so a
future edit that loosens a regex fails loudly. Samples are built by string
concatenation so this file itself stays clean under the gate (it is scanned
like any other tracked file).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_sanitization.py"
spec = importlib.util.spec_from_file_location("check_sanitization", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def hits(text: str) -> set[str]:
    return {why for pat, why in gate.FORBIDDEN if pat.search(text)}


def test_each_leak_class_is_caught():
    samples = {
        "personal email": "wes" + "ton.tre" + "fry@example.org",
        "personal-provider email address": "someone" + "@gm" + "ail.com",
        "personal project (eb" + ".app)": "shipped on " + "eb" + ".app today",
        "personal project goal/topic (eb" + "app)": "goals: [" + "eb" + "app]",
        "private business repo": "see " + "second-brain" + "-hq for plans",
        "unrelated personal repo": "like the " + "midi" + "-maker repo",
        "unrelated business identifier": "team@" + "process" + "wizard.ai",
        "private config repo": "synced from " + "claude" + "-config",
        "institution identifier": "at the University " + "of Florida",
        "UF-tied slug (goal names use cs-degree here)": "--goals " + "uf" + "-cs-degree",
        "university course code": "syllabus for " + "COP" + "4610",
        "absolute macOS home path": "/Us" + "ers/someone/Desktop/x",
        "personal-only content marker": "pack: " + "personal",
        "markdown link to an upstream-only doc": "see [the plan](" + "../PLAN" + "-UX.md)",
    }
    for why, sample in samples.items():
        assert why in hits(sample), f"gate no longer catches: {why}"


def test_benign_lookalikes_pass():
    benign = [
        "Advanced Data Structures (COP" + "9999)",   # the fictional fixture course
        "track: advanced-data-structures-cop" + "9999",
        "Joplin and Obsidian exports are supported",
        "a web.application server",  # 'eb' mid-word must not trip the project pattern
        "documented per-milestone in PROGRESS.md",    # prose mention, not a link
        "user@example.com",
        "goals: [cs-degree, dsa-interviews]",
    ]
    for sample in benign:
        assert not hits(sample), f"false positive on: {sample!r} -> {hits(sample)}"


def test_author_name_rule():
    assert gate.NAME_RE.search("reviewed by Wes" + "ton yesterday")
    assert not gate.NAME_RE.search("the western frontier")  # substring must not match
    assert "LICENSE" in gate.NAME_ALLOWED_FILES


def test_upstream_artifact_lists_cover_known_classes():
    for rel in ["PLAN-UX.md", "docs/template-sync.md", ".templateignore",
                "launcher", "brain.db", "ui/graph.data.js"]:
        assert rel in gate.FORBIDDEN_PATHS
    assert "HANDOFF*.md" in gate.FORBIDDEN_PATH_GLOBS
