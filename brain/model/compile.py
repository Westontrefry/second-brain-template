"""Compile the knowledge model: registry + tracks + per-concept learning state.

DERIVED, never committed — rebuildable from source (concepts.yaml, tracks,
notes, events.jsonl) at any time. Learning state is NOT a new store: level
comes from weights.py evidence, recency from note last_reviewed plus
events.jsonl, and this module only names what they already say (mastered /
learning / weak / stale / missing, thresholds in config.yaml under model.state).
Every ConceptState carries a human-readable reason — the "because" that
readiness reports and context exports repeat verbatim.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field

from ..config import load_config
from ..events import events_path
from ..util import slugify
from ..weights import collect
from . import registry as reg_mod
from .registry import Registry
from .tracks import Track, evidence_levels, load_tracks

STATES = ("mastered", "learning", "weak", "stale", "missing")


@dataclass
class ConceptState:
    id: str
    name: str
    state: str
    level: float
    last_touch: str  # ISO date, "" when never touched
    convergence: int  # how many tracks touch this concept
    tracks: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class CompiledModel:
    generated: str
    concepts: dict[str, ConceptState]  # keyed by id, sorted
    edges: list[dict]  # union of track edges, each with its track slug
    tracks: list[Track]
    ref_ids: dict[str, str]  # raw track ref -> concept id, as resolved here
    kb_topics_total: int    # distinct note topics in the knowledge base
    kb_topics_matched: int  # of those, how many the registry resolves

    def resolve_ref(self, ref: str) -> str:
        return self.ref_ids.get(ref, ref)


def thresholds() -> dict:
    cfg = load_config().get("model", {}).get("state", {})
    return {"mastered_level": cfg.get("mastered_level", 4),
            "learning_level": cfg.get("learning_level", 2),
            "stale_days": cfg.get("stale_days", 120)}


def classify(level: float, last_touch: str, today: dt.date,
             th: dict | None = None) -> tuple[str, str]:
    """(state, reason). Missing beats stale beats the level bands — matching
    gaps.py, where 'stale — refresh' applies even with no gap."""
    th = th or thresholds()
    if level == 0:
        return "missing", "no note topics match this concept or its aliases"
    age = (today - dt.date.fromisoformat(last_touch)).days if last_touch else None
    if age is not None and age > th["stale_days"]:
        return "stale", (f"last touched {last_touch} ({age}d ago, > {th['stale_days']}d); "
                         f"evidenced level {level:g}")
    if level >= th["mastered_level"]:
        return "mastered", f"evidenced level {level:g} >= {th['mastered_level']}"
    if level >= th["learning_level"]:
        return "learning", (f"evidenced level {level:g} — at least {th['learning_level']}, "
                            f"below mastered ({th['mastered_level']})")
    return "weak", f"evidenced level {level:g} below learning threshold ({th['learning_level']})"


def _event_touches(registry: Registry) -> dict[str, str]:
    """Latest events.jsonl touch date per concept (assess + exposure kinds)."""
    path = events_path()
    touches: dict[str, str] = {}
    if not path.exists():
        return touches
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        cid = registry.resolve(rec["topic"]) if rec.get("topic") else None
        if cid and rec.get("ts"):
            touches[cid] = max(touches.get(cid, ""), str(rec["ts"])[:10])
    return touches


def compile_model(today: dt.date | None = None) -> CompiledModel:
    today = today or dt.date.today()
    th = thresholds()
    registry = reg_mod.load()
    tracks = load_tracks(registry)
    stats = collect(today)

    levels = evidence_levels(registry, stats)
    touches = _event_touches(registry)
    for topic, s in stats.items():
        cid = registry.resolve(topic)
        if cid and s.last_reviewed:
            touches[cid] = max(touches.get(cid, ""), s.last_reviewed)

    # Union of concepts: the whole registry, plus any track ref the registry
    # doesn't know (a roadmap edited after seeding) — surfaced, not crashed on.
    names = {c.id: c.name for c in registry.concepts}
    track_ids: dict[str, list[str]] = {}
    ref_ids: dict[str, str] = {}
    extras: list[str] = []
    for t in tracks:
        for ref in t.concept_ids():
            cid = registry.resolve(ref)
            if cid is None:
                cid = slugify(ref)
                if cid not in names:
                    names[cid] = ref
                    extras.append(cid)
            ref_ids[ref] = cid
            track_ids.setdefault(cid, []).append(t.track)

    # Evidence for extras: direct slug match against note topics.
    slug_levels: dict[str, float] = {}
    slug_touches: dict[str, str] = {}
    for topic, s in stats.items():
        key = slugify(topic)
        slug_levels[key] = max(slug_levels.get(key, 0.0), s.evidenced_level)
        slug_touches[key] = max(slug_touches.get(key, ""), s.last_reviewed)

    concepts: dict[str, ConceptState] = {}
    for cid in sorted(names):
        if cid in extras:
            level = slug_levels.get(cid, 0.0)
            touch = slug_touches.get(cid, "")
        else:
            level = levels.get(cid, 0.0)
            touch = touches.get(cid, "")
        state, reason = classify(level, touch, today, th)
        if cid in extras:
            reason += " [not in the registry — add it to model/concepts.yaml or re-import]"
        touching = sorted(set(track_ids.get(cid, [])))
        concepts[cid] = ConceptState(
            id=cid, name=names[cid], state=state, level=level, last_touch=touch,
            convergence=len(touching), tracks=touching, reason=reason,
        )

    edges = [{"source": e.source, "target": e.target, "kind": e.kind,
              "confidence": e.confidence, "provenance": e.provenance,
              "track": t.track}
             for t in tracks for e in t.edges]

    matched = sum(1 for topic in stats if registry.resolve(topic) is not None)
    return CompiledModel(
        generated=today.isoformat(), concepts=concepts, edges=edges,
        tracks=tracks, ref_ids=ref_ids,
        kb_topics_total=len(stats), kb_topics_matched=matched,
    )
