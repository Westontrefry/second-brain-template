"""Test fixtures. Every test runs against a sandbox in tmp_path (selected via
BRAIN_ROOT) built ENTIRELY from frozen fixtures (tests/fixtures/{goals,rubrics,
knowledge}) plus the live config.yaml. Goals and rubrics are frozen too, so
personalizing goals/goals.yaml or roadmaps never breaks the suite; tests never
touch the real knowledge base or index."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture()
def sandbox(tmp_path, monkeypatch) -> Path:
    shutil.copy(REPO / "config.yaml", tmp_path / "config.yaml")
    for d in ("goals", "rubrics", "knowledge"):
        shutil.copytree(REPO / "tests" / "fixtures" / d, tmp_path / d)
    shutil.copytree(REPO / ".claude" / "skills", tmp_path / ".claude" / "skills")
    monkeypatch.setenv("BRAIN_ROOT", str(tmp_path))
    return tmp_path


def write_note(sandbox: Path, note_id: str, domain: str = "cs", *,
               topics: list[str] | None = None, source: str = "study-session",
               confidence: int = 3, importance: int = 3,
               goals: list[str] | None = None, ai_confidence: float | None = None,
               last_reviewed: str | None = None, exposure_count: int = 1,
               body: str = "A test note body with enough substance to chunk.") -> Path:
    created = note_id[:10]
    topics_s = ", ".join(topics or ["testing"])
    goals_s = ", ".join(goals or [])
    ai = "null" if ai_confidence is None else ai_confidence
    text = (
        f"---\n"
        f"id: {note_id}\n"
        f"domain: {domain}\n"
        f"topics: [{topics_s}]\n"
        f"source: {source}\n"
        f"confidence: {confidence}\n"
        f"ai_confidence: {ai}\n"
        f"ai_confidence_rationale: null\n"
        f"last_assessed: null\n"
        f"importance: {importance}\n"
        f"goals: [{goals_s}]\n"
        f"created: {created}\n"
        f"last_reviewed: {last_reviewed or created}\n"
        f"exposure_count: {exposure_count}\n"
        f"---\n\n{body}\n"
    )
    path = sandbox / "knowledge" / domain / f"{note_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
