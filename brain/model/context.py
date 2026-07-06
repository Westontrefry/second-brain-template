"""`brain context`: the AI context layer — a compact learning-state export.

One screen of YAML (target < 100 lines) that any assistant can consume with
zero other context: active tracks with readiness, per-state concept lists,
and the top gaps each carrying its "because". Derived, never stored; regenerate
whenever it's needed.
"""
from __future__ import annotations

import datetime as dt

import yaml

from ..gaps import load_goals
from .compile import compile_model, thresholds
from .readiness import READY_STATES, readiness

MAX_GAPS = 8

HEADER = """\
# Second Brain learning-state export (generated {generated}) — safe to paste
# into any AI assistant as study-planning context. States come from evidence:
# notes, quizzes, and time decay. mastered >= level {mastered}, learning >= {learning},
# stale = untouched for {stale_days}+ days, missing = no evidence at all.
# Levels are 0-5 (rubric: 4 = fluent under pressure). 'first:' = do that first.
"""


def build_context(track: str | None = None, goal: str | None = None,
                  today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    model = compile_model(today)
    goals = load_goals()

    slugs = [s for s in (track, goal) if s]
    if slugs:
        known = {t.track for t in model.tracks}
        for s in slugs:
            if s not in known:
                raise ValueError(f"unknown track or goal {s!r} — available: "
                                 + ", ".join(sorted(known)))
        selected = [t for t in model.tracks if t.track in slugs]
    else:
        selected = model.tracks

    # Goal-backed tracks lead, highest priority first — the export's order IS
    # its advice, so it must reflect what the user cares about most.
    selected = sorted(selected, key=lambda t: -(goals.get(t.track, {}).get("priority") or 0))
    reports = [readiness(t.track, model=model) for t in selected]

    tracks_out = []
    for rep in reports:
        counts = rep.counts()
        entry = {
            "track": rep.track, "title": rep.title,
            "on_track": f"{sum(counts.get(s, 0) for s in READY_STATES)}/{len(rep.lines)}",
        }
        g = goals.get(rep.track)
        if g:
            if g.get("deadline"):
                entry["deadline"] = str(g["deadline"])
            if g.get("priority") is not None:
                entry["priority"] = g["priority"]
        tracks_out.append(entry)

    in_scope = {line.concept for rep in reports for line in rep.lines}
    by_state: dict[str, list[str]] = {}
    for cid in sorted(in_scope):
        by_state.setdefault(model.concepts[cid].state, []).append(cid)

    # Round-robin across tracks (each already in study order) so one long
    # track can't crowd the others out of the top slots.
    queues: list[tuple[str, list]] = []
    seen: set[str] = set()
    for rep in reports:
        q = []
        for line in rep.lines:
            if line.state not in READY_STATES and line.concept not in seen:
                seen.add(line.concept)
                q.append(line)
        if q:
            queues.append((rep.track, q))
    gaps = []
    for i in range(max((len(q) for _, q in queues), default=0)):
        for slug, q in queues:
            if i < len(q):
                gaps.append({"concept": q[i].concept, "track": slug, "because": q[i].because})
    dropped = max(len(gaps) - MAX_GAPS, 0)

    out: dict[str, object] = {
        "generated": today.isoformat(),
        "tracks": tracks_out,
        "concepts": {s: by_state[s] for s in
                     ("mastered", "learning", "weak", "stale", "missing") if s in by_state},
        "top_gaps": gaps[:MAX_GAPS],
    }
    if dropped:
        out["more_gaps_not_shown"] = dropped
    return out


def render_context(track: str | None = None, goal: str | None = None,
                   today: dt.date | None = None) -> str:
    data = build_context(track=track, goal=goal, today=today)
    th = thresholds()
    header = HEADER.format(generated=data["generated"], mastered=th["mastered_level"],
                           learning=th["learning_level"], stale_days=th["stale_days"])
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True,
                          width=100, default_flow_style=None)
    return header + body
