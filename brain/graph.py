"""Export the knowledge graph for the static UI.

Derived view over the markdown source of truth. Nodes are topics — annotated with
roadmap requirements where a roadmap topic matches via aliases — plus "missing"
nodes for roadmap topics with no matching knowledge topic. Edges: prereq (roadmap
skeleton), cooccur (topics sharing a note), wikilink (topics of [[linked]] notes).

Writes ui/graph.json (for tooling) and ui/graph.data.js (script-included by the
page, so it works from file:// without fetch/CORS). Pathway overlays found in
ui/paths/*.json are bundled into the data file.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from .config import knowledge_dir, load_config, root
from .gaps import load_goals, load_roadmap
from .schema import parse_note, validate_note
from .util import slug_keys, slugify
from .weights import collect

WIKILINK_RE = re.compile(r"\[\[([a-zA-Z0-9-]+)\]\]")


def _note_records() -> list[dict]:
    records = []
    for path in sorted(knowledge_dir().rglob("*.md")):
        note, _ = parse_note(path)
        if note is None or validate_note(note):
            continue
        m = note.meta
        records.append({
            "id": m["id"], "title": m.get("title"), "path": str(path), "domain": m["domain"],
            "topics": m["topics"], "goals": m["goals"],
            "confidence": m["confidence"], "ai_confidence": m.get("ai_confidence"),
            "last_reviewed": str(m["last_reviewed"]),
            "source": m["source"], "links": WIKILINK_RE.findall(note.body),
        })
    return records


def build(today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    stats = collect(today)
    notes = _note_records()
    goals = load_goals()

    nodes: dict[str, dict] = {}
    for topic, s in stats.items():
        nodes[topic] = {
            "id": topic, "label": topic, "type": "topic",
            "weight": round(s.weight, 2), "evidenced": s.evidenced_level,
            "lastReviewed": s.last_reviewed, "selfConfidence": 0,
            "aiConfidence": None, "goals": set(), "domains": Counter(),
            "sources": Counter(), "notes": [], "requirements": [],
        }
    for rec in notes:
        for topic in rec["topics"]:
            n = nodes[topic]
            n["selfConfidence"] = max(n["selfConfidence"], rec["confidence"])
            if rec["ai_confidence"] is not None:
                prev = n["aiConfidence"]
                n["aiConfidence"] = rec["ai_confidence"] if prev is None else max(prev, rec["ai_confidence"])
            n["goals"].update(rec["goals"])
            n["domains"][rec["domain"]] += 1
            n["sources"][rec["source"]] += 1
            n["notes"].append({
                "id": rec["id"], "title": rec["title"], "path": rec["path"],
                "confidence": rec["confidence"], "lastReviewed": rec["last_reviewed"],
            })

    edges: dict[tuple[str, str], dict] = {}

    def add_edge(a: str, b: str, kind: str, strength: float) -> None:
        if a == b:
            return
        key = (min(a, b), max(a, b))
        e = edges.setdefault(key, {"source": key[0], "target": key[1],
                                   "kinds": set(), "strength": 0.0})
        e["kinds"].add(kind)
        e["strength"] += strength

    note_by_id = {r["id"]: r for r in notes}
    for rec in notes:
        for i, a in enumerate(rec["topics"]):
            for b in rec["topics"][i + 1:]:
                add_edge(a, b, "cooccur", 1.0)
        for linked_id in rec["links"]:
            other = note_by_id.get(linked_id)
            if other:
                for a in rec["topics"]:
                    for b in other["topics"]:
                        add_edge(a, b, "wikilink", 0.5)

    # Roadmap layer: match roadmap topics to knowledge topics via aliases;
    # unmatched become "missing" nodes. Prereq edges connect resolved node ids.
    slug_to_topic = {slugify(t): t for t in stats}
    goal_resolved: dict[str, dict[str, str]] = {}
    for gid in goals:
        roadmap = load_roadmap(gid)
        if roadmap is None:
            continue
        resolved: dict[str, str] = goal_resolved.setdefault(gid, {})
        for entry in roadmap["topics"]:
            keys = slug_keys(entry["id"], entry.get("aliases", []))
            matches = [slug_to_topic[k] for k in keys if k in slug_to_topic]
            if matches:
                rep = sorted(
                    matches,
                    key=lambda t: (slugify(t) == slugify(entry["id"]),
                                   nodes[t]["weight"], t),
                )[-1]
            else:
                rep = entry["id"]
                if rep not in nodes:
                    nodes[rep] = {
                        "id": rep, "label": entry["name"], "type": "missing",
                        "weight": 0.0, "evidenced": 0.0, "lastReviewed": "",
                        "selfConfidence": 0, "aiConfidence": None, "goals": set(),
                        "domains": Counter(), "sources": Counter(), "notes": [],
                        "requirements": [],
                    }
            resolved[entry["id"]] = rep
            node = nodes[rep]
            node["goals"].add(gid)
            node["requirements"].append({
                "goal": gid, "topicId": entry["id"], "name": entry["name"],
                "required": entry["required_level"],
                "gap": max(entry["required_level"] - node["evidenced"], 0),
            })
        for entry in roadmap["topics"]:
            for prereq in entry.get("prereqs", []):
                if prereq in resolved:
                    add_edge(resolved[prereq], resolved[entry["id"]], "prereq", 1.5)

    def kind_of(kinds: set[str]) -> str:
        for k in ("prereq", "cooccur", "wikilink"):
            if k in kinds:
                return k
        return "cooccur"

    from .gaps import analyze

    # Full lists, no silent cap — the panel scrolls, and a truncated ranking
    # reads as "that's everything" when it isn't.
    suggestions: dict[str, list[dict]] = {}
    for gid, resolved in goal_resolved.items():
        suggestions[gid] = [
            {"nodeId": resolved.get(gp.topic_id, gp.topic_id), "name": gp.name,
             "action": gp.action, "score": round(gp.score, 1),
             "blockedBy": gp.blocked_by}
            for gp in analyze(goal_id=gid, today=today)
        ]

    # KME track layer: imported tracks (model/tracks/*.yaml) join the map
    # exactly like roadmap layers — same dropdown, gaps overlay, drill-down
    # requirements and suggestions panel; no second UI. Roadmap-derived
    # tracks are skipped (the goal layer above already renders them).
    # Convergence (tracks touching a concept) lands on every matched node.
    from .model import registry as reg_mod
    from .model.compile import compile_model, thresholds
    from .model.readiness import READY_STATES, readiness

    TRACK_ACTIONS = {"missing": "no evidence — start here",
                     "weak": "weak — study and practice", "stale": "stale — refresh"}
    model = compile_model(today)
    aliases = {c.id: c.aliases for c in reg_mod.load().concepts}
    required = thresholds()["learning_level"]
    track_entries = []

    def concept_node(cid: str) -> str:
        """Representative node for a concept, roadmap-layer rules: alias match
        into the topic map, otherwise a 'missing' node keyed by concept id."""
        keys = slug_keys(cid, aliases.get(cid, []))
        matches = [slug_to_topic[k] for k in keys if k in slug_to_topic]
        if matches:
            return sorted(matches, key=lambda t: (slugify(t) == cid,
                                                  nodes[t]["weight"], t))[-1]
        if cid not in nodes:
            nodes[cid] = {
                "id": cid, "label": model.concepts[cid].name, "type": "missing",
                "weight": 0.0, "evidenced": 0.0, "lastReviewed": "",
                "selfConfidence": 0, "aiConfidence": None, "goals": set(),
                "domains": Counter(), "sources": Counter(), "notes": [],
                "requirements": [],
            }
        return cid

    for track in model.tracks:
        if track.adapter == "roadmap":
            continue
        track_entries.append({"id": track.track, "title": f"{track.title} (track)",
                              "priority": 0})
        resolved = {}
        for ref in track.concept_ids():
            cid = model.resolve_ref(ref)
            rep = concept_node(cid)
            resolved[cid] = rep
            node = nodes[rep]
            node["goals"].add(track.track)
            node["requirements"].append({
                "goal": track.track, "topicId": cid,
                "name": model.concepts[cid].name, "required": required,
                "gap": max(required - node["evidenced"], 0),
            })
        for e in track.edges:
            src, dst = model.resolve_ref(e.source), model.resolve_ref(e.target)
            if e.kind == "prereq" and src in resolved and dst in resolved:
                add_edge(resolved[src], resolved[dst], "prereq", 1.5 * e.confidence)
        gaps_lines = [l for l in readiness(track.track, model=model).lines
                      if l.state not in READY_STATES]
        suggestions[track.track] = [
            {"nodeId": resolved.get(l.concept, l.concept), "name": l.name,
             "action": TRACK_ACTIONS.get(l.state, l.state),
             "score": len(gaps_lines) - i, "blockedBy": l.blocked_by}
            for i, l in enumerate(gaps_lines)
        ]

    for cid, cs in model.concepts.items():
        if cs.convergence == 0:
            continue
        for key in slug_keys(cid, aliases.get(cid, [])):
            topic = slug_to_topic.get(key)
            if topic in nodes:
                nodes[topic]["convergence"] = max(nodes[topic].get("convergence", 0),
                                                  cs.convergence)
        if cid in nodes:  # missing nodes are keyed by concept id
            nodes[cid]["convergence"] = cs.convergence

    return {
        "suggestions": suggestions,
        "generated": today.isoformat(),
        "goals": [{"id": g["id"], "title": g["title"], "priority": g["priority"]}
                  for g in goals.values()] + track_entries,
        "nodes": [
            {**n, "goals": sorted(n["goals"]),
             "domain": n["domains"].most_common(1)[0][0] if n["domains"] else None,
             "domains": None, "sources": dict(n["sources"])}
            for n in nodes.values()
        ],
        "edges": [
            {"source": e["source"], "target": e["target"],
             "kind": kind_of(e["kinds"]), "strength": round(e["strength"], 2)}
            for e in edges.values()
        ],
    }


def _load_reference() -> dict:
    """Command dictionary for the UI's reference tab — derived, never hand-listed:
    skill descriptions from SKILL.md frontmatter, CLI entries from the parser."""
    from .cli import build_parser
    from .importer import _split_frontmatter

    sub = build_parser()._subparsers._group_actions[0]
    cli = [{"name": a.dest, "description": a.help or ""} for a in sub._choices_actions]

    skills = []
    skills_dir = root() / ".claude" / "skills"
    for f in sorted(skills_dir.glob("*/SKILL.md")) if skills_dir.is_dir() else []:
        meta, _ = _split_frontmatter(f.read_text(encoding="utf-8"))
        skills.append({
            "name": meta.get("name", f.parent.name),
            "description": meta.get("description", ""),
        })
    return {"skills": skills, "cli": cli}


def _note_bodies() -> dict[str, str]:
    """Full note bodies keyed by id, bundled for the UI's markdown viewer.
    Written to a separate data file so graph.json stays lean."""
    bodies: dict[str, str] = {}
    for path in sorted(knowledge_dir().rglob("*.md")):
        note, _ = parse_note(path)
        if note is None or validate_note(note):
            continue
        bodies[note.meta["id"]] = note.body
    return bodies


def _load_paths() -> list[dict]:
    paths_dir = root() / "ui" / "paths"
    overlays = []
    for p in sorted(paths_dir.glob("*.json")) if paths_dir.is_dir() else []:
        try:
            overlay = json.loads(p.read_text(encoding="utf-8"))
            overlay["slug"] = p.stem
            overlays.append(overlay)
        except json.JSONDecodeError:
            print(f"skipping invalid pathway overlay: {p}")
    return overlays


def export(today: dt.date | None = None) -> Path:
    graph = build(today)
    for node in graph["nodes"]:
        node.pop("domains", None)
    ui_dir = root() / "ui"
    ui_dir.mkdir(exist_ok=True)
    (root() / load_config()["paths"]["graph_json"]).write_text(
        json.dumps(graph, indent=1), encoding="utf-8"
    )
    data_js = ui_dir / "graph.data.js"
    data_js.write_text(
        "window.GRAPH = " + json.dumps(graph) + ";\n"
        + "window.PATHS = " + json.dumps(_load_paths()) + ";\n"
        + "window.REFERENCE = " + json.dumps(_load_reference()) + ";\n",
        encoding="utf-8",
    )
    (ui_dir / "notes.data.js").write_text(
        "window.NOTES = " + json.dumps(_note_bodies()) + ";\n",
        encoding="utf-8",
    )
    return data_js
