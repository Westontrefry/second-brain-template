"""Canonical concept registry: model/concepts.yaml loader, validator, resolver.

COMMITTED SOURCE, same status as goals/roadmaps/. The registry centralizes what
roadmap `aliases:` lists do per-file: it maps vocabulary (note topics, syllabus
terms) onto one canonical concept id per idea. The join rule is util.slug_keys —
identical to how gaps.py and graph.py match roadmap topics to note topics.
Note topics are never renamed; aliases absorb vocabulary differences.

An alias may belong to exactly ONE concept — a slug claimed by two concepts is
ambiguous and rejected by the validator. merge() enforces this on import by
dropping colliding aliases (first claim wins) and reporting each drop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..config import load_config, root
from ..util import slug_keys, slugify


@dataclass
class Concept:
    id: str
    name: str
    aliases: list[str] = field(default_factory=list)

    def keys(self) -> set[str]:
        return slug_keys(self.id, self.aliases)


class Registry:
    """Validated concept set with slug-based term resolution."""

    def __init__(self, concepts: list[Concept]):
        self.concepts = concepts
        self.by_id: dict[str, Concept] = {c.id: c for c in concepts}
        self._key_to_id: dict[str, str] = {}
        for c in concepts:
            for k in c.keys():
                self._key_to_id[k] = c.id

    def resolve(self, term: str) -> str | None:
        """Canonical concept id for a free-form term (note topic, syllabus
        heading, roadmap alias), or None if the vocabulary doesn't match."""
        return self._key_to_id.get(slugify(term))

    def __len__(self) -> int:
        return len(self.concepts)


def registry_path() -> Path:
    return root() / load_config()["paths"]["concepts_file"]


def validate(data: object) -> list[str]:
    """Structural errors in raw concepts.yaml data. Empty list = valid."""
    if not isinstance(data, dict) or not isinstance(data.get("concepts"), list):
        return ["top level must be a mapping with a 'concepts' list"]

    errors: list[str] = []
    seen_ids: set[str] = set()
    claimed: dict[str, str] = {}  # slug key -> concept id that owns it
    for i, c in enumerate(data["concepts"]):
        label = f"concepts[{i}]"
        if not isinstance(c, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        cid = c.get("id")
        if not isinstance(cid, str) or not cid:
            errors.append(f"{label}: missing id")
            continue
        label = f"concepts[{i}] ({cid})"
        if cid in seen_ids:
            errors.append(f"{label}: duplicate concept id")
        seen_ids.add(cid)
        if cid != slugify(cid):
            errors.append(f"{label}: id must be a canonical slug (got {cid!r}, want {slugify(cid)!r})")
        if not isinstance(c.get("name"), str) or not c["name"]:
            errors.append(f"{label}: missing name")
        aliases = c.get("aliases", [])
        if not isinstance(aliases, list) or not all(isinstance(a, str) and a for a in aliases):
            errors.append(f"{label}: aliases must be a list of non-empty strings")
            aliases = []
        for key in sorted(slug_keys(cid, aliases)):
            owner = claimed.get(key)
            if owner is None:
                claimed[key] = cid
            elif owner != cid:
                errors.append(f"{label}: alias {key!r} already belongs to concept {owner!r}")
    return errors


def load(path: Path | None = None) -> Registry:
    """Load and validate the registry. Raises ValueError listing every problem;
    a missing file is an empty (not invalid) registry."""
    path = path or registry_path()
    if not path.exists():
        return Registry([])
    with open(path) as f:
        data = yaml.safe_load(f)
    errors = validate(data)
    if errors:
        raise ValueError(f"invalid registry {path}:\n" + "\n".join(f"  - {e}" for e in errors))
    return Registry([
        Concept(id=c["id"], name=c["name"], aliases=list(c.get("aliases", [])))
        for c in data["concepts"]
    ])


def merge(existing: list[Concept], incoming: list[Concept]) -> tuple[list[Concept], list[str]]:
    """Fold incoming concepts into existing ones, dedup by slug; first claim wins.

    Same id -> union of aliases. An incoming alias whose slug is already owned
    by a different concept is dropped, with a human-readable note (the source
    vocabulary still resolves — just to the earlier concept). Returns the merged
    list (insertion order) and the drop notes.
    """
    merged: list[Concept] = [Concept(c.id, c.name, list(c.aliases)) for c in existing]
    by_id = {c.id: c for c in merged}
    claimed: dict[str, str] = {k: c.id for c in merged for k in c.keys()}
    notes: list[str] = []

    for inc in incoming:
        target = by_id.get(claimed.get(slugify(inc.id), inc.id))
        if target is None:
            target = Concept(inc.id, inc.name, [])
            merged.append(target)
            by_id[inc.id] = target
            claimed[slugify(inc.id)] = inc.id
        for alias in inc.aliases:
            key = slugify(alias)
            owner = claimed.get(key)
            if owner is None:
                target.aliases.append(alias)
                claimed[key] = target.id
            elif owner != target.id:
                notes.append(f"dropped alias {alias!r} from {target.id!r}: already belongs to {owner!r}")
    return merged, notes


def harvest_roadmaps() -> tuple[list[Concept], list[str]]:
    """Seed concepts from every goals/roadmaps/*.yaml: one concept per roadmap
    topic, aliases carried over, merged across roadmaps in filename order."""
    roadmaps_dir = root() / load_config()["paths"]["roadmaps_dir"]
    concepts: list[Concept] = []
    notes: list[str] = []
    for path in sorted(roadmaps_dir.glob("*.yaml")):
        with open(path) as f:
            roadmap = yaml.safe_load(f)
        incoming = [
            Concept(id=t["id"], name=t["name"], aliases=list(t.get("aliases", [])))
            for t in roadmap.get("topics", [])
        ]
        concepts, dropped = merge(concepts, incoming)
        notes.extend(f"{path.name}: {n}" for n in dropped)
    return concepts, notes


def file_header(path: Path | None = None) -> str:
    """The leading comment block of an existing registry file, so save()
    callers can carry it over instead of silently dropping it."""
    path = path or registry_path()
    if not path.exists():
        return ""
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            break
        lines.append(line)
    return "\n".join(lines)


def save(concepts: list[Concept], path: Path | None = None, header: str = "") -> Path:
    """Write concepts.yaml (sorted by id for stable diffs)."""
    path = path or registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"concepts": [
        {"id": c.id, "name": c.name, "aliases": sorted(c.aliases, key=slugify)}
        for c in sorted(concepts, key=lambda c: c.id)
    ]}
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)
    path.write_text((header + "\n" if header else "") + text, encoding="utf-8")
    return path
