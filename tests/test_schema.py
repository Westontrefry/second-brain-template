from pathlib import Path

from brain.schema import validate_file

from conftest import write_note


def test_seed_notes_valid(sandbox: Path):
    notes = sorted((sandbox / "knowledge").rglob("*.md"))
    assert notes, "sandbox should contain the seed notes"
    for note in notes:
        assert validate_file(note) == [], f"{note} should be valid"


def test_valid_synthetic_note(sandbox: Path):
    path = write_note(sandbox, "2026-01-15-synthetic", goals=["gcp-ace"])
    assert validate_file(path) == []


def test_malformed_note_reports_all_errors(sandbox: Path):
    path = sandbox / "knowledge" / "cs" / "2026-01-15-bad.md"
    path.write_text(
        "---\n"
        "id: Bad_ID\ndomain: quantum\ntopics: []\nsource: telepathy\n"
        "confidence: 9\nimportance: 3\ngoals: [world-domination]\n"
        "created: not-a-date\nlast_reviewed: 2026-01-15\nexposure_count: 0\n"
        "---\n",
        encoding="utf-8",
    )
    errors = validate_file(path)
    for fragment in ("id must match", "domain", "source", "topics", "confidence",
                     "unknown goal", "created", "exposure_count", "body is empty"):
        assert any(fragment in e for e in errors), f"expected an error about {fragment}"


def test_domain_folder_mismatch(sandbox: Path):
    path = write_note(sandbox, "2026-01-15-misplaced", domain="cs")
    target = sandbox / "knowledge" / "career" / path.name
    path.rename(target)
    errors = validate_file(target)
    assert any("career" in e and "domain" in e for e in errors)
