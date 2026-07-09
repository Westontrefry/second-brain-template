"""Sweep the Ingest/ drop folder into the knowledge base.

The inbox is checked, not watched: no daemon, no filesystem-watcher dependency.
`brain inbox` sweeps whatever is waiting; the home screen and cockpit surface a
"files waiting" nudge so the folder gets swept at the moments you already look.

Layout is the routing: `Ingest/<domain>/` subfolders name the target domain
(same folder->domain rule as the markdown importer), because guessing domains
is how 335 gen-ed notes once landed in `cs`. Files at the root are reported,
never guessed. Originals move to `Ingest/processed/<domain>/` after a
successful import — the whole tree is gitignored, so copyrighted sources never
reach git; only derived notes do.

Everything here is deterministic and $0. Enrichment (topics, goals, the
confidence judgment) stays with the /ingest skill — the sweep ends by saying so.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .config import load_config, root

PROCESSED = "processed"


def inbox_dir() -> Path:
    return root() / "Ingest"


def waiting_files() -> list[Path]:
    """Files eligible for a sweep (excludes processed/ and dotfiles).

    Read-only — safe for the home screen and cockpit health probes.
    """
    base = inbox_dir()
    if not base.is_dir():
        return []
    return sorted(
        p for p in base.rglob("*")
        if p.is_file()
        and PROCESSED not in p.relative_to(base).parts
        and not any(part.startswith(".") for part in p.relative_to(base).parts)
    )


def ensure_layout() -> None:
    """Create Ingest/ with one subfolder per domain so the drop target is
    self-documenting in Finder. Idempotent; the tree is gitignored."""
    for domain in load_config()["domains"]:
        (inbox_dir() / domain).mkdir(parents=True, exist_ok=True)


@dataclass
class SweepResult:
    created: list[Path] = field(default_factory=list)    # notes written
    moved: list[Path] = field(default_factory=list)      # originals -> processed/
    skipped: list[tuple[Path, str]] = field(default_factory=list)  # left in place


def _existing_book_tags() -> dict[str, int]:
    """topic -> note count, for the book-slug collision guard."""
    from .config import knowledge_dir
    from .schema import parse_note

    counts: dict[str, int] = {}
    for p in knowledge_dir().rglob("*.md"):
        note, _ = parse_note(p)
        if note is None:
            continue
        for t in note.meta.get("topics") or []:
            counts[str(t)] = counts.get(str(t), 0) + 1
    return counts


def _processed_names() -> set[str]:
    """Basenames of every source already imported (sitting under processed/).

    The book-slug tag guard (`_existing_book_tags`) is defeated when a book's
    notes are retagged after import — re-deriving the slug from the filename no
    longer matches any note's topics, so the guard silently passes. Since every
    imported original is moved into `Ingest/processed/`, its basename is a stable
    record of "already handled" that survives any retag or enrichment. This guard
    catches the retagged-book re-sweep the tag guard misses.
    """
    base = inbox_dir() / PROCESSED
    if not base.is_dir():
        return set()
    return {p.name for p in base.rglob("*") if p.is_file()}


def _move_to_processed(entry: Path, domain: str) -> Path:
    dest_dir = inbox_dir() / PROCESSED / domain
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / entry.name
    n = 2
    while dest.exists():
        dest = dest_dir / f"{entry.stem}-{n}{entry.suffix}"
        n += 1
    shutil.move(str(entry), str(dest))
    return dest


def _sweep_pdf(pdf: Path, domain: str, res: SweepResult, *,
               dry_run: bool, force: bool, book_tags: dict[str, int],
               processed_names: set[str]) -> None:
    from .importer import book_slug, import_pdf
    from .pdfextract import ScannedPdfError, missing_deps

    if missing_deps():
        res.skipped.append((pdf, 'PDF import needs pypdf — pip install -e ".[pdf]"'))
        return
    if not force and pdf.name in processed_names:
        res.skipped.append((
            pdf,
            f"'{pdf.name}' was already imported (in Ingest/processed/) — "
            "rerun with --force to re-import",
        ))
        return
    tag = book_slug(pdf.stem)
    if not force and book_tags.get(tag):
        res.skipped.append((
            pdf,
            f"{book_tags[tag]} note(s) tagged '{tag}' already exist — "
            "rerun with --force to re-import",
        ))
        return
    try:
        result = import_pdf(pdf, domain=domain, dry_run=dry_run)
    except ScannedPdfError as e:
        res.skipped.append((pdf, f"{e} (scanned/handwritten — use vision via /log)"))
        return
    res.created.extend(result.created)
    res.skipped.extend(result.skipped)
    if not dry_run:
        res.moved.append(_move_to_processed(pdf, domain))


def _sweep_markdown(entry: Path, domain: str, res: SweepResult, *,
                    dry_run: bool) -> None:
    """One dropped entry (a .md file or an export folder) -> import_dir.

    A lone .md file is staged into a tempdir because import_dir walks
    directories. Dedup skips count as success (already in the brain); a
    validation failure leaves the entry in place so it stays visible.
    """
    import tempfile

    from .importer import import_dir

    if entry.is_file():
        with tempfile.TemporaryDirectory() as td:
            staged = Path(td) / entry.name
            shutil.copy2(entry, staged)
            result = import_dir(Path(td), domain=domain, dry_run=dry_run)
    else:
        result = import_dir(entry, domain=domain, dry_run=dry_run)

    res.created.extend(result.created)
    hard_failures = [
        (p, r) for p, r in result.skipped if r.startswith("failed validation")
    ]
    res.skipped.extend(result.skipped)
    if not dry_run and not hard_failures:
        res.moved.append(_move_to_processed(entry, domain))


def sweep(dry_run: bool = False, force: bool = False) -> SweepResult:
    """Route every waiting entry through the existing import pipeline."""
    ensure_layout()
    cfg = load_config()
    res = SweepResult()
    book_tags = _existing_book_tags()
    processed_names = _processed_names()

    for child in sorted(inbox_dir().iterdir()):
        if child.name.startswith(".") or child.name == PROCESSED:
            continue
        if child.is_file():
            res.skipped.append(
                (child, f"move into Ingest/<domain>/ so it lands in the right "
                        f"domain (yours: {', '.join(cfg['domains'])})"))
            continue
        domain = child.name.lower()
        if domain not in cfg["domains"]:
            res.skipped.append(
                (child, f"'{child.name}' is not a domain "
                        f"(yours: {', '.join(cfg['domains'])})"))
            continue
        for entry in sorted(child.iterdir()):
            if entry.name.startswith("."):
                continue
            if entry.is_file() and entry.suffix.lower() == ".pdf":
                _sweep_pdf(entry, domain, res,
                           dry_run=dry_run, force=force, book_tags=book_tags,
                           processed_names=processed_names)
            elif entry.is_dir() or entry.suffix.lower() == ".md":
                _sweep_markdown(entry, domain, res, dry_run=dry_run)
            else:
                res.skipped.append((entry, "not a .pdf, .md, or export folder"))
    return res
