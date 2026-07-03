"""`brain model import`: a learning resource in, a committed track out.

Pipeline: adapter parses the file -> terms canonicalize through the registry
(unknown terms become new concepts, appended to model/concepts.yaml with the
merge dedup rules) -> track written to model/tracks/<slug>.yaml. Dry runs do
everything except write, and return exactly what WOULD be written.

Adapters: `outline` (markdown syllabus; order-based prereq edges between
consecutive units, confidence < 1 because order only implies dependency) and
`roadmap` (a roadmap-format YAML at any path; explicit prereqs, confidence
1.0). In-repo roadmaps never need importing — tracks.load_tracks() converts
them in memory.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ..util import slugify
from . import registry as reg_mod
from .outline import parse_outline
from .registry import Concept, Registry
from .tracks import Edge, Track, Unit, save_track, track_to_yaml, tracks_dir, validate_track

OUTLINE_EDGE_CONFIDENCE = 0.5  # order implies, never proves, a dependency

ADAPTER_BY_SUFFIX = {".md": "outline", ".markdown": "outline", ".txt": "outline",
                     ".yaml": "roadmap", ".yml": "roadmap"}


@dataclass
class ImportResult:
    track: Track
    track_yaml: str
    track_path: Path
    new_concepts: list[Concept]
    notes: list[str]      # merge collisions etc.
    written: bool


def _from_outline(path: Path, slug: str | None) -> tuple[Track, list[Concept], dict]:
    title, units = parse_outline(path.read_text(encoding="utf-8"))
    title = title or path.stem
    parsed = [u for u in units if u.terms]
    if not parsed:
        raise ValueError(f"no units with list items found in {path} "
                         "(expected headings with -/*/numbered items under them)")
    track = Track(
        track=slug or slugify(title), title=title,
        source=f"outline: {path}", adapter="outline",
    )
    terms = {t for u in parsed for t in u.terms}
    return track, [Concept(slugify(t), t) for t in sorted(terms)], {
        "units": parsed  # finished in import_resource once resolution exists
    }


def _from_roadmap_file(path: Path, slug: str | None) -> tuple[Track, list[Concept], dict]:
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or not isinstance(data.get("topics"), list):
        raise ValueError(f"{path} is not roadmap-format YAML (needs a 'topics' list)")
    topics = data["topics"]
    slug = slug or data.get("goal") or slugify(path.stem)
    track = Track(
        track=slug, title=data.get("title") or slug,
        source=f"roadmap: {path}", adapter="roadmap",
        units=[Unit(t["name"], [t["id"]]) for t in topics],
        edges=[Edge(p, t["id"], "prereq", 1.0, f"roadmap prereqs: {path.name}")
               for t in topics for p in t.get("prereqs", [])],
    )
    concepts = [Concept(t["id"], t["name"], list(t.get("aliases", []))) for t in topics]
    return track, concepts, {}


def import_resource(path: Path, adapter: str | None = None, slug: str | None = None,
                    dry_run: bool = False) -> ImportResult:
    if not path.is_file():
        raise ValueError(f"not a file: {path}")
    adapter = adapter or ADAPTER_BY_SUFFIX.get(path.suffix.lower())
    if adapter is None:
        raise ValueError(f"can't infer adapter for {path.name} — pass --adapter outline|roadmap")

    existing = reg_mod.load()
    if adapter == "outline":
        track, incoming, extra = _from_outline(path, slug)
    else:
        track, incoming, extra = _from_roadmap_file(path, slug)

    # Only terms the registry doesn't already know become new concepts.
    incoming = [c for c in incoming if existing.resolve(c.id) is None]
    merged, notes = reg_mod.merge(existing.concepts, incoming)
    new_concepts = merged[len(existing.concepts):]
    registry = Registry(merged)

    if adapter == "outline":
        # Resolve terms to canonical ids now that new concepts exist; dedupe
        # within units; prereq edges between consecutive units (order-based).
        for u in extra["units"]:
            ids = [registry.resolve(t) for t in u.terms]
            track.units.append(Unit(u.name, list(dict.fromkeys(ids))))
        seen: set[tuple[str, str]] = set()
        for prev, unit in zip(track.units, track.units[1:]):
            for a in prev.concepts:
                for b in unit.concepts:
                    if a != b and (a, b) not in seen:
                        seen.add((a, b))
                        track.edges.append(Edge(a, b, "prereq", OUTLINE_EDGE_CONFIDENCE,
                                                f"outline order: {prev.name} before {unit.name}"))

    errors = validate_track(yaml.safe_load(track_to_yaml(track)), registry)
    if errors:  # adapter bug, not user error — fail loudly
        raise ValueError(f"adapter produced an invalid track:\n" +
                         "\n".join(f"  - {e}" for e in errors))

    track_path = tracks_dir() / f"{track.track}.yaml"
    written = False
    if not dry_run:
        if merged != existing.concepts:
            reg_mod.save(merged, header=reg_mod.file_header())
        save_track(track)
        written = True
    return ImportResult(track, track_to_yaml(track), track_path, new_concepts, notes, written)
