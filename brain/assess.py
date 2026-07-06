"""Assessment write paths.

`assess` is the ONLY setter of ai_confidence — it requires evidence note ids and
a rationale, so every score carries its receipts. `log_exposure` records a review
event (exposure_count + last_reviewed). Both rewrite frontmatter in place and
re-validate; callers re-index afterwards.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import yaml

from .config import knowledge_dir
from .schema import parse_note, validate_file


def _find_note(note_id: str) -> Path:
    for path in knowledge_dir().rglob(f"{note_id}.md"):
        return path
    raise ValueError(f"note not found: {note_id}")


def _rewrite_frontmatter(path: Path, updates: dict) -> None:
    note, errors = parse_note(path)
    if note is None:
        raise ValueError(f"{path}: {errors[0]}")
    meta = {**note.meta, **updates}
    body = note.body
    if not body.startswith("\n"):
        body = "\n\n" + body
    path.write_text(
        "---\n" + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True) + "---" + body,
        encoding="utf-8",
    )
    errors = validate_file(path)
    if errors:
        raise ValueError(f"{path} failed validation after rewrite: {errors[0]}")


def assess(topic: str, level: float, rationale: str, evidence_ids: list[str],
           today: dt.date | None = None, source: str | None = None) -> list[Path]:
    """Record an evidence-based level for a topic on the notes that evidence it.

    `source` (optional) tags which skill produced the assessment, e.g. "quiz" or
    "debrief". It is written only when given, so legacy sourceless events stay as
    they are; first-touch detection keys off it (see brain/first_touch.py)."""
    today = today or dt.date.today()
    if not evidence_ids:
        raise ValueError("assessment requires at least one evidence note id")
    if not rationale.strip():
        raise ValueError("assessment requires a rationale")
    if not 0 <= level <= 5:
        raise ValueError("level must be 0-5")

    paths = []
    for note_id in evidence_ids:
        path = _find_note(note_id)
        note, _ = parse_note(path)
        assert note is not None  # _find_note returned a path that parses
        if topic not in note.meta["topics"]:
            raise ValueError(f"note {note_id} does not carry topic {topic!r}")
        paths.append(path)

    for path in paths:
        _rewrite_frontmatter(path, {
            "ai_confidence": level,
            "ai_confidence_rationale": rationale,
            "last_assessed": today.isoformat(),
        })
    from .events import append_event
    fields = dict(topic=topic, level=level, rationale=rationale, evidence=evidence_ids)
    if source:
        fields["source"] = source
    append_event("assess", **fields)
    return paths


def set_confidence(note_id: str, level: int) -> Path:
    """Manually override a note's self/observed `confidence` (the awareness->known
    rating). Use this to correct a level the AI misjudged at ingest. Does NOT touch
    `ai_confidence` — if the note was quiz-assessed, that evidence-based score still
    governs the displayed level by design (re-quiz to change it)."""
    if not isinstance(level, int) or isinstance(level, bool) or not 1 <= level <= 5:
        raise ValueError("level must be an integer 1-5")
    path = _find_note(note_id)
    _rewrite_frontmatter(path, {"confidence": level})
    from .events import append_event
    append_event("set-confidence", note=note_id, level=level)
    return path


def log_exposure(topic: str, today: dt.date | None = None,
                 source: str | None = None) -> list[Path]:
    """Record a review event on every note carrying the topic.

    `source` (optional) tags the producing skill, e.g. "review" (written only when
    given). First-touch detection keys off it (see brain/first_touch.py)."""
    today = today or dt.date.today()
    updated = []
    for path in sorted(knowledge_dir().rglob("*.md")):
        note, _ = parse_note(path)
        if note is None or topic not in note.meta.get("topics", []):
            continue
        _rewrite_frontmatter(path, {
            "exposure_count": note.meta["exposure_count"] + 1,
            "last_reviewed": today.isoformat(),
        })
        updated.append(path)
    if not updated:
        raise ValueError(f"no notes carry topic {topic!r}")
    from .events import append_event
    fields = dict(topic=topic, notes=len(updated))
    if source:
        fields["source"] = source
    append_event("exposure", **fields)
    return updated
