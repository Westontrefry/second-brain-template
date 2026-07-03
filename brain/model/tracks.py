"""Tracks: one imported learning resource each — ordered units of concept refs
plus prerequisite edges that carry provenance and confidence.

Materialized tracks (model/tracks/*.yaml, COMMITTED SOURCE) are adapter output,
written by `brain model import`. Roadmaps are the exception: they stay the
single source under goals/roadmaps/ and are converted to tracks IN MEMORY on
every load — materializing them would create a second copy that drifts when a
roadmap is edited (the "no parallel systems" rule). gaps.py stays untouched;
the acceptance bar is that a roadmap track reproduces its blocking analysis
(tests/test_model_tracks.py).

evidence_levels/blocking are the first slice of per-concept learning state;
M4's compile step builds on them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..config import load_config, root
from ..gaps import load_goals, load_roadmap
from ..weights import TopicStats
from .registry import Registry

EDGE_KINDS = ("prereq",)


@dataclass
class Unit:
    name: str
    concepts: list[str]


@dataclass
class Edge:
    source: str  # prerequisite: source is required by target
    target: str
    kind: str = "prereq"
    confidence: float = 1.0  # 1.0 = explicit in the resource; <1 = inferred
    provenance: str = ""


@dataclass
class Track:
    track: str  # slug
    title: str
    source: str  # where the resource came from (provenance)
    adapter: str
    units: list[Unit] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    def concept_ids(self) -> list[str]:
        """Every concept the track touches, unit order first, then edge-only refs."""
        seen: list[str] = []
        for u in self.units:
            seen.extend(c for c in u.concepts if c not in seen)
        for e in self.edges:
            seen.extend(c for c in (e.source, e.target) if c not in seen)
        return seen


def tracks_dir() -> Path:
    return root() / load_config()["paths"]["tracks_dir"]


def validate_track(data: object, registry: Registry | None = None) -> list[str]:
    """Structural errors in raw track YAML data. With a registry, every concept
    ref must resolve — `brain model import` guarantees that by appending new
    concepts to the registry, so an unresolved ref means the two files drifted."""
    if not isinstance(data, dict):
        return ["track file must be a mapping"]

    errors: list[str] = []
    for key in ("track", "title", "source", "adapter"):
        if not isinstance(data.get(key), str) or not data.get(key):
            errors.append(f"missing {key}")

    refs: list[str] = []
    units = data.get("units", [])
    if not isinstance(units, list):
        errors.append("units must be a list")
        units = []
    for i, u in enumerate(units):
        if not isinstance(u, dict) or not isinstance(u.get("name"), str) or not u.get("name"):
            errors.append(f"units[{i}]: missing name")
            continue
        concepts = u.get("concepts", [])
        if not isinstance(concepts, list) or not all(isinstance(c, str) and c for c in concepts):
            errors.append(f"units[{i}] ({u['name']}): concepts must be a list of non-empty strings")
            continue
        refs.extend(concepts)

    edges = data.get("edges", [])
    if not isinstance(edges, list):
        errors.append("edges must be a list")
        edges = []
    for i, e in enumerate(edges):
        label = f"edges[{i}]"
        if not isinstance(e, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        for key in ("from", "to"):
            if not isinstance(e.get(key), str) or not e.get(key):
                errors.append(f"{label}: missing {key}")
            else:
                refs.append(e[key])
        if e.get("kind", "prereq") not in EDGE_KINDS:
            errors.append(f"{label}: unknown kind {e.get('kind')!r} (expected one of {EDGE_KINDS})")
        conf = e.get("confidence", 1.0)
        if not isinstance(conf, (int, float)) or not 0 < conf <= 1:
            errors.append(f"{label}: confidence must be a number in (0, 1], got {conf!r}")
        if not isinstance(e.get("provenance", ""), str):
            errors.append(f"{label}: provenance must be a string")

    if registry is not None:
        for ref in dict.fromkeys(refs):  # ordered dedup
            if registry.resolve(ref) is None:
                errors.append(f"unknown concept {ref!r} (not in the registry — add it or an alias)")
    return errors


def _track_from_data(data: dict) -> Track:
    return Track(
        track=data["track"], title=data["title"], source=data["source"],
        adapter=data["adapter"],
        units=[Unit(u["name"], list(u.get("concepts", []))) for u in data.get("units", [])],
        edges=[Edge(e["from"], e["to"], e.get("kind", "prereq"),
                    float(e.get("confidence", 1.0)), e.get("provenance", ""))
               for e in data.get("edges", [])],
    )


def track_to_yaml(track: Track) -> str:
    """Serialize in the model/tracks/*.yaml shape (from/to edge keys)."""
    data = {
        "track": track.track, "title": track.title, "source": track.source,
        "adapter": track.adapter,
        "units": [{"name": u.name, "concepts": list(u.concepts)} for u in track.units],
        "edges": [{"from": e.source, "to": e.target, "kind": e.kind,
                   "confidence": e.confidence, "provenance": e.provenance}
                  for e in track.edges],
    }
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)


def save_track(track: Track) -> Path:
    path = tracks_dir() / f"{track.track}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(track_to_yaml(track), encoding="utf-8")
    return path


def load_track(path: Path, registry: Registry | None = None) -> Track:
    with open(path) as f:
        data = yaml.safe_load(f)
    errors = validate_track(data, registry)
    if errors:
        raise ValueError(f"invalid track {path}:\n" + "\n".join(f"  - {e}" for e in errors))
    return _track_from_data(data)


def from_roadmap(goal_id: str, title: str | None = None) -> Track:
    """Roadmap adapter: goals/roadmaps/<goal>.yaml as a track, unchanged.
    One unit per topic in file order; prereq edges with confidence 1.0
    (explicit in source)."""
    roadmap = load_roadmap(goal_id)
    if roadmap is None:
        raise ValueError(f"no roadmap for goal: {goal_id}")
    topics = roadmap["topics"]
    return Track(
        track=goal_id,
        title=title or goal_id,
        source=f"roadmap: goals/roadmaps/{goal_id}.yaml",
        adapter="roadmap",
        units=[Unit(t["name"], [t["id"]]) for t in topics],
        edges=[Edge(p, t["id"], "prereq", 1.0, f"roadmap prereqs: {goal_id}.yaml")
               for t in topics for p in t.get("prereqs", [])],
    )


def roadmap_tracks() -> list[Track]:
    return [from_roadmap(gid, title=g.get("title"))
            for gid, g in sorted(load_goals().items()) if load_roadmap(gid) is not None]


def load_tracks(registry: Registry | None = None) -> list[Track]:
    """All tracks: materialized model/tracks/*.yaml plus in-memory roadmap
    tracks. A materialized track shadows a roadmap with the same slug."""
    tracks: dict[str, Track] = {}
    d = tracks_dir()
    for path in sorted(d.glob("*.yaml")) if d.is_dir() else []:
        t = load_track(path, registry)
        tracks[t.track] = t
    for t in roadmap_tracks():
        tracks.setdefault(t.track, t)
    return list(tracks.values())


def evidence_levels(registry: Registry, stats: dict[str, TopicStats]) -> dict[str, float]:
    """Best evidenced level per concept: note topics join via the registry's
    alias vocabulary (same slug rule gaps.py applies per roadmap)."""
    levels: dict[str, float] = {}
    for topic, s in stats.items():
        cid = registry.resolve(topic)
        if cid is not None:
            levels[cid] = max(levels.get(cid, 0.0), s.evidenced_level)
    return levels


def blocking(track: Track, levels: dict[str, float]) -> dict[str, list[str]]:
    """Per concept, the prerequisite concepts with zero evidence — the same
    blocking rule gaps.py annotates with its "first:" hint."""
    blocked: dict[str, list[str]] = {}
    for e in track.edges:
        if e.kind == "prereq" and levels.get(e.source, 0.0) == 0:
            blocked.setdefault(e.target, []).append(e.source)
    return blocked
