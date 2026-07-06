"""Frontier expansion: safely append proposed roadmap topics, then re-sync.

The /frontier skill does the reasoning — which topics lie *outside* current
coverage (world knowledge the deterministic layer can't derive). This module
does the guarded WRITE: append the confirmed topics to a roadmap (preserving its
hand-written comments via text append, never a YAML round-trip), re-sync the
concept registry, and rebuild the graph so the new nodes render dashed.

The guards mirror the exact failure modes hit when this was first done by hand:
- collision: a proposed id/alias that resolves to a *different* existing concept
  would silently merge or un-dash a real blind spot — dropped and reported.
- duplicate: a proposed id already in the target roadmap — skipped.
- governor: cap topics added per call, so one run can't flood `brain gaps` with
  no-evidence nodes and drown genuine weak-but-important gaps.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

from .config import load_config, root
from .gaps import load_goals, load_roadmap
from .model import registry as reg_mod

DEFAULT_MAX = 8


@dataclass
class Proposed:
    id: str
    name: str
    required_level: int = 2
    prereqs: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)


@dataclass
class AddResult:
    added: list[Proposed] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)          # (id, reason)
    dropped_aliases: list[tuple[str, str, str]] = field(default_factory=list)  # (id, alias, concept)
    roadmap_path: Path | None = None
    dashed_total: int = 0


def roadmap_path(goal_id: str) -> Path:
    return root() / load_config()["paths"]["roadmaps_dir"] / f"{goal_id}.yaml"


def _render_topic(p: Proposed) -> str:
    return (f"  - id: {p.id}\n"
            f"    name: {p.name}\n"
            f"    required_level: {p.required_level}\n"
            f"    prereqs: [{', '.join(p.prereqs)}]\n"
            f"    aliases: [{', '.join(p.aliases)}]\n")


def _resync_registry() -> None:
    """Harvest-first merge so fresh roadmap aliases win over stale registry
    entries, while imported course-track concepts (not roadmap-derived) survive."""
    harvested, _ = reg_mod.harvest_roadmaps()
    merged, _ = reg_mod.merge(harvested, reg_mod.load().concepts)
    reg_mod.save(merged, header=reg_mod.file_header())


def add_topics(goal_id: str, proposed: list[Proposed], *,
               max_add: int = DEFAULT_MAX, today: dt.date | None = None,
               rebuild: bool = True) -> AddResult:
    """Append guarded frontier topics to a goal's roadmap and re-sync the model.

    Raises ValueError if the goal or its roadmap file doesn't exist — a frontier
    expansion extends an existing path; creating a path from nothing is /path's job.
    """
    today = today or dt.date.today()
    goals = load_goals()
    if goal_id not in goals:
        raise ValueError(f"unknown goal: {goal_id}")
    roadmap = load_roadmap(goal_id)
    if roadmap is None:
        raise ValueError(
            f"no roadmap for goal {goal_id}; create goals/roadmaps/{goal_id}.yaml first")

    existing_ids = {t["id"] for t in roadmap["topics"]}
    reg = reg_mod.load()
    result = AddResult(roadmap_path=roadmap_path(goal_id))

    accepted: list[Proposed] = []
    for p in proposed:
        if len(accepted) >= max_add:
            result.skipped.append((p.id, f"over governor cap ({max_add})"))
            continue
        if p.id in existing_ids:
            result.skipped.append((p.id, "already in this roadmap"))
            continue
        # A proposed id that resolves to a *different* concept would collide on
        # merge; resolving to itself (a shared node across goals) is fine.
        resolved = reg.resolve(p.id)
        if resolved is not None and resolved != p.id:
            result.skipped.append((p.id, f"id collides with existing concept '{resolved}'"))
            continue
        # Drop aliases that belong to another concept — else the new node would
        # silently resolve onto existing evidence and never render dashed.
        clean: list[str] = []
        for a in p.aliases:
            r = reg.resolve(a)
            if r is not None and r != p.id:
                result.dropped_aliases.append((p.id, a, r))
            else:
                clean.append(a)
        accepted.append(Proposed(p.id, p.name, p.required_level, p.prereqs, clean))
        existing_ids.add(p.id)

    if accepted:
        path = result.roadmap_path
        text = path.read_text(encoding="utf-8").rstrip("\n") + "\n"
        block = (f"\n  # --- frontier expansion ({today.isoformat()}) ---\n"
                 + "".join(_render_topic(p) for p in accepted))
        path.write_text(text + block, encoding="utf-8")
        result.added = accepted
        _resync_registry()
        if rebuild:
            from .graph import export
            export(today)

    from .graph import build
    g = build(today)
    result.dashed_total = sum(1 for n in g["nodes"] if n["type"] == "missing")
    return result
