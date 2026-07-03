"""`brain readiness <track-or-goal>`: an explainable per-concept report.

Every line self-explains (the RFC's explainability requirement): the state's
reason string from compile.py plus, when prerequisites in THIS track lack any
evidence, a gaps.py-style "first: ..." hint. Goals with roadmaps are tracks
with the same slug, so one lookup serves both.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from .compile import CompiledModel, compile_model

READY_STATES = ("mastered", "learning")


@dataclass
class ReadinessLine:
    concept: str
    name: str
    state: str
    level: float
    blocked_by: list[str]  # prereq concepts in this track with zero evidence
    because: str


@dataclass
class ReadinessReport:
    track: str
    title: str
    lines: list[ReadinessLine]  # track unit order
    ready: bool                 # nothing missing/weak/stale

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for line in self.lines:
            out[line.state] = out.get(line.state, 0) + 1
        return out


def readiness(slug: str, today: dt.date | None = None,
              model: CompiledModel | None = None) -> ReadinessReport:
    model = model or compile_model(today)
    track = next((t for t in model.tracks if t.track == slug), None)
    if track is None:
        available = ", ".join(sorted(t.track for t in model.tracks))
        raise ValueError(f"unknown track or goal {slug!r} — available: {available}")

    prereqs: dict[str, list[str]] = {}
    for e in track.edges:
        if e.kind == "prereq":
            src, dst = model.resolve_ref(e.source), model.resolve_ref(e.target)
            if src != dst and src not in prereqs.setdefault(dst, []):
                prereqs[dst].append(src)

    lines: list[ReadinessLine] = []
    for ref in track.concept_ids():
        cid = model.resolve_ref(ref)
        if any(line.concept == cid for line in lines):
            continue
        c = model.concepts[cid]
        blocked = [p for p in prereqs.get(cid, []) if model.concepts[p].level == 0]
        because = c.reason
        if blocked:
            because += f" — first: {', '.join(blocked)}"
        lines.append(ReadinessLine(cid, c.name, c.state, c.level, blocked, because))

    ready = all(line.state in READY_STATES for line in lines)
    return ReadinessReport(track.track, track.title, lines, ready)
