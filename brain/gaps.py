"""Gap analysis: diff each goal's roadmap against evidenced knowledge.

gap = required_level - evidenced_level, scored by goal priority and deadline
urgency. Topics whose prerequisites are themselves unevidenced are deprioritized
(learn the prerequisite first) and annotated.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import yaml

from .config import load_config, root
from .util import slugify
from .weights import TopicStats, collect

STALE_DAYS = 120


@dataclass
class Gap:
    goal: str
    topic_id: str
    name: str
    required: int
    evidenced: float
    score: float
    action: str
    blocked_by: list[str]


def load_goals() -> dict[str, dict]:
    with open(root() / load_config()["paths"]["goals_file"]) as f:
        return {g["id"]: g for g in yaml.safe_load(f)["goals"]}


def load_roadmap(goal_id: str) -> dict | None:
    path = root() / load_config()["paths"]["roadmaps_dir"] / f"{goal_id}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)


def _urgency(deadline: object, today: dt.date) -> float:
    if not deadline:
        return 1.0
    d = deadline if isinstance(deadline, dt.date) else dt.date.fromisoformat(str(deadline))
    days = (d - today).days
    if days <= 90:
        return 1.5
    if days <= 180:
        return 1.2
    return 1.0


def _topic_evidence(entry: dict, stats: dict[str, TopicStats]) -> tuple[float, str]:
    """Best evidenced level and latest review date across the topic's aliases."""
    keys = {slugify(entry["id"])} | {slugify(a) for a in entry.get("aliases", [])}
    level, last = 0.0, ""
    for topic, s in stats.items():
        if slugify(topic) in keys:
            level = max(level, s.evidenced_level)
            last = max(last, s.last_reviewed)
    return level, last


def analyze(goal_id: str | None = None, today: dt.date | None = None) -> list[Gap]:
    today = today or dt.date.today()
    goals = load_goals()
    if goal_id and goal_id not in goals:
        raise ValueError(f"unknown goal: {goal_id}")
    targets = [goal_id] if goal_id else list(goals)

    stats = collect(today)
    result: list[Gap] = []

    for gid in targets:
        roadmap = load_roadmap(gid)
        if roadmap is None:
            continue
        goal = goals[gid]
        urgency = _urgency(goal.get("deadline"), today)
        evidence = {t["id"]: _topic_evidence(t, stats) for t in roadmap["topics"]}

        for t in roadmap["topics"]:
            level, last = evidence[t["id"]]
            required = t["required_level"]
            gap = max(required - level, 0.0)
            stale = bool(last) and (today - dt.date.fromisoformat(last)).days > STALE_DAYS
            if gap == 0 and not stale:
                continue

            blocked_by = [p for p in t.get("prereqs", []) if evidence.get(p, (0, ""))[0] == 0]
            score = max(gap, 0.5) * goal.get("priority", 3) * urgency
            if blocked_by:
                score *= 0.6

            if level == 0:
                action = "no evidence — start here"
            elif gap >= 2:
                action = f"weak (level {level:.0f} of {required}) — study and practice"
            elif gap > 0:
                action = f"close (level {level:.0f} of {required}) — practice to close"
            else:
                action = "stale — refresh"

            result.append(Gap(gid, t["id"], t["name"], required, level, score, action, blocked_by))

    result.sort(key=lambda g: g.score, reverse=True)
    return result
