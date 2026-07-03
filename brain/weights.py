"""Computed topic weights and evidenced levels.

Deterministic: reads the markdown source of truth directly (no embeddings, no DB).
Weight = evidence_multiplier(source) x confidence x exposure_count x recency decay,
summed over all notes touching the topic.

Evidenced level (vs the rubric): ai_confidence when an assessment exists, otherwise
self-confidence CAPPED AT 3 — levels 4-5 require demonstrated evidence (quiz,
application under pressure), which self-report alone can't establish.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .config import knowledge_dir, load_config
from .schema import parse_note, validate_note

SOURCE_CLASS = {"project": "application_note", "quiz": "quiz"}
DEFAULT_CLASS = "note"
SELF_CONFIDENCE_LEVEL_CAP = 3


@dataclass
class TopicStats:
    topic: str
    weight: float = 0.0
    evidenced_level: float = 0.0
    last_reviewed: str = ""
    note_ids: list[str] = field(default_factory=list)


def _decay(age_days: int, half_life_days: float) -> float:
    return 0.5 ** (age_days / half_life_days)


def collect(today: dt.date | None = None) -> dict[str, TopicStats]:
    """Aggregate stats per topic across every valid note."""
    cfg = load_config()["weights"]
    today = today or dt.date.today()
    stats: dict[str, TopicStats] = {}

    for path in sorted(knowledge_dir().rglob("*.md")):
        note, errors = parse_note(path)
        if note is None or validate_note(note):
            continue
        m = note.meta
        cls = SOURCE_CLASS.get(m["source"], DEFAULT_CLASS)
        multiplier = cfg["evidence_multiplier"].get(cls, 1.0)
        half_life = cfg["decay_half_life_days"].get(cls, 180)
        reviewed = dt.date.fromisoformat(str(m["last_reviewed"]))
        age = max((today - reviewed).days, 0)
        contribution = multiplier * m["confidence"] * m["exposure_count"] * _decay(age, half_life)

        if m.get("ai_confidence") is not None:
            level = float(m["ai_confidence"])
        else:
            level = float(min(m["confidence"], SELF_CONFIDENCE_LEVEL_CAP))

        for topic in m["topics"]:
            s = stats.setdefault(topic, TopicStats(topic=topic))
            s.weight += contribution
            s.evidenced_level = max(s.evidenced_level, level)
            s.last_reviewed = max(s.last_reviewed, str(m["last_reviewed"]))
            s.note_ids.append(m["id"])

    return stats
