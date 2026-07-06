"""Import external markdown exports into the knowledge base.

First-class: Joplin "MD - Markdown + Front Matter" exports (title/created/updated/
tags in frontmatter, notes organized in notebook folders). Also handles plain
markdown and Obsidian vaults (no frontmatter; [[links]] preserved as-is).

Imported notes land at confidence 1 (awareness) — you have the material but
haven't necessarily internalized it. The AI enrichment pass promotes a note to
2 when its body shows real engagement. Combined with source "import" and no goal
links, that is the flag the /ingest skill uses to find notes awaiting enrichment
(topic suggestions, goal alignment, confidence judgment).
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

import hashlib

from .config import knowledge_dir, load_config
from .schema import parse_note, validate_file
from .util import slugify


@dataclass
class ImportResult:
    created: list[Path] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """Tolerant frontmatter split: returns ({}, body) when absent or unparsable."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            try:
                meta = yaml.safe_load(text[4:end])
                if isinstance(meta, dict):
                    return meta, text[end + 5:]
            except yaml.YAMLError:
                pass
    return {}, text


def _coerce_date(value: object, fallback: str) -> str:
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, str):
        m = re.match(r"\d{4}-\d{2}-\d{2}", value.strip())
        if m:
            return m.group(0)
    return fallback


def _title_of(meta: dict, body: str, path: Path) -> str:
    if meta.get("title"):
        return str(meta["title"])
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def import_dir(
    src: Path,
    domain: str | None = None,
    dry_run: bool = False,
    confidence: int = 1,
    importance: int = 2,
) -> ImportResult:
    cfg = load_config()
    result = ImportResult()
    files = [
        p for p in sorted(src.rglob("*.md"))
        if "_resources" not in p.parts and not p.name.startswith(".")
    ]
    used_ids = {p.stem for p in knowledge_dir().rglob("*.md")}
    existing_bodies: set[str] = set()
    for p in knowledge_dir().rglob("*.md"):
        note, _ = parse_note(p)
        if note is not None:
            existing_bodies.add(hashlib.sha256(note.body.strip().encode()).hexdigest())
    today = dt.date.today().isoformat()

    for path in files:
        meta, body = _split_frontmatter(path.read_text(encoding="utf-8"))
        rel = path.relative_to(src)
        folder = rel.parts[0] if len(rel.parts) > 1 else None

        note_domain = domain
        if note_domain is None and folder and folder.lower() in cfg["domains"]:
            note_domain = folder.lower()
        if note_domain is None:
            result.skipped.append((path, "no domain mapping (pass --domain)"))
            continue

        title = _title_of(meta, body, path)
        created = _coerce_date(meta.get("created"), today)
        updated = _coerce_date(meta.get("updated"), created)

        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        topics = [str(t).lower() for t in tags if t]
        if folder and folder.lower() not in topics:
            topics.append(folder.lower())
        if not topics:
            topics = ["unsorted"]

        slug = slugify(title) or slugify(path.stem) or "note"
        note_id = f"{created}-{slug}"
        n = 2
        while note_id in used_ids:
            note_id = f"{created}-{slug}-{n}"
            n += 1

        body = body.strip()
        if not body:
            result.skipped.append((path, "empty body"))
            continue
        if not body.startswith("#"):
            body = f"# {title}\n\n{body}"
        body_hash = hashlib.sha256(body.encode()).hexdigest()
        if body_hash in existing_bodies:
            result.skipped.append((path, "already imported (identical content)"))
            continue

        target = knowledge_dir() / note_domain / f"{note_id}.md"
        if dry_run:
            print(f"would import {path} -> {target}  topics={topics}")
            used_ids.add(note_id)
            result.created.append(target)
            continue

        frontmatter = {
            "id": note_id,
            "title": title,
            "domain": note_domain,
            "topics": topics,
            "source": "import",
            "confidence": confidence,
            "ai_confidence": None,
            "ai_confidence_rationale": None,
            "last_assessed": None,
            "importance": importance,
            "goals": [],
            "created": created,
            "last_reviewed": updated,
            "exposure_count": 1,
        }
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "---\n"
            + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
            + "---\n\n"
            + body
            + "\n",
            encoding="utf-8",
        )
        errors = validate_file(target)
        if errors:
            target.unlink()
            result.skipped.append((path, f"failed validation: {errors[0]}"))
            continue
        used_ids.add(note_id)
        existing_bodies.add(body_hash)
        result.created.append(target)

    if result.created and not dry_run:
        from .ingest import sync

        sync()
    return result
