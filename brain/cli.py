"""Command-line interface. Run as `python -m brain <command>`."""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from .config import knowledge_dir, load_config
from .schema import validate_file
from .util import slugify


def cmd_validate(args: argparse.Namespace) -> int:
    targets: list[Path] = []
    for raw in args.paths or [knowledge_dir()]:
        p = Path(raw)
        if p.is_dir():
            targets.extend(sorted(p.rglob("*.md")))
        else:
            targets.append(p)

    if not targets:
        print("no notes found")
        return 1

    failed = 0
    for path in targets:
        errors = validate_file(path)
        if errors:
            failed += 1
            print(f"FAIL {path}")
            for e in errors:
                print(f"  - {e}")
        elif args.verbose:
            print(f"ok   {path}")

    print(f"\n{len(targets) - failed}/{len(targets)} notes valid")
    return 1 if failed else 0


def cmd_add(args: argparse.Namespace) -> int:
    from .ingest import sync

    slug = slugify(args.title)
    if not slug:
        print("title produced an empty slug")
        return 1
    note_id = f"{dt.date.today().isoformat()}-{slug}"
    path = knowledge_dir() / args.domain / f"{note_id}.md"
    if path.exists():
        print(f"already exists: {path}")
        return 1

    body = args.body if args.body else sys.stdin.read()
    today = dt.date.today().isoformat()
    topics = ", ".join(t.strip() for t in args.topics.split(","))
    goals = ", ".join(g.strip() for g in args.goals.split(",")) if args.goals else ""
    frontmatter = (
        f"---\n"
        f"id: {note_id}\n"
        f"domain: {args.domain}\n"
        f"topics: [{topics}]\n"
        f"source: {args.source}\n"
        f"confidence: {args.confidence}\n"
        f"ai_confidence: null\n"
        f"ai_confidence_rationale: null\n"
        f"last_assessed: null\n"
        f"importance: {args.importance}\n"
        f"goals: [{goals}]\n"
        f"created: {today}\n"
        f"last_reviewed: {today}\n"
        f"exposure_count: 1\n"
        f"---\n\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter + body.strip() + "\n", encoding="utf-8")

    errors = validate_file(path)
    if errors:
        path.unlink()
        print("note rejected (file not created):")
        for e in errors:
            print(f"  - {e}")
        return 1

    sync()
    print(f"added and indexed: {path}")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    from .importer import import_dir

    src = Path(args.src)
    if not src.is_dir():
        print(f"not a directory: {src}")
        return 1
    result = import_dir(
        src, domain=args.domain, dry_run=args.dry_run,
        confidence=args.confidence, importance=args.importance,
    )
    for path, reason in result.skipped:
        print(f"skipped {path}: {reason}")
    verb = "would import" if args.dry_run else "imported"
    print(f"{verb} {len(result.created)} note(s), skipped {len(result.skipped)}")
    if result.created and not args.dry_run:
        print("imported notes have no goal links yet — run the /ingest skill to enrich them")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    from .ingest import sync

    stats = sync(full=args.full)
    print(
        f"indexed {stats['indexed']}, unchanged {stats['unchanged']},"
        f" removed {stats['removed']}, invalid {stats['invalid']}"
    )
    return 1 if stats["invalid"] else 0


def cmd_rebuild(args: argparse.Namespace) -> int:
    args.full = True
    return cmd_ingest(args)


def cmd_search(args: argparse.Namespace) -> int:
    from .retrieve import search

    hits = search(
        args.query, k=args.k, domain=args.domain, goal=args.goal,
        min_confidence=args.min_confidence,
    )
    if not hits:
        print("no results (is the index built? try: python -m brain ingest)")
        return 1
    for h in hits:
        rel = Path(h.path).relative_to(Path.cwd()) if Path(h.path).is_relative_to(Path.cwd()) else h.path
        print(f"{h.score:.3f}  [{h.domain}] {h.note_id}  (confidence {h.confidence})")
        print(f"       {rel}")
        snippet = " ".join(h.snippet.split())
        print(f"       {snippet[:200]}{'…' if len(snippet) > 200 else ''}\n")
    return 0


def cmd_gaps(args: argparse.Namespace) -> int:
    from .gaps import analyze

    try:
        gaps = analyze(goal_id=args.goal)
    except ValueError as e:
        print(e)
        return 1
    if not gaps:
        print("no gaps found" + (f" for goal {args.goal}" if args.goal else "") +
              " (or no roadmap exists yet)")
        return 0
    for g in gaps[: args.n]:
        line = f"{g.score:5.1f}  [{g.goal}] {g.name} — {g.action}"
        if g.blocked_by:
            line += f"  (first: {', '.join(g.blocked_by)})"
        print(line)
    if len(gaps) > args.n:
        print(f"... and {len(gaps) - args.n} more (use -n)")
    return 0


def cmd_assess(args: argparse.Namespace) -> int:
    from .assess import assess
    from .ingest import sync

    try:
        paths = assess(args.topic, args.level, args.rationale,
                       [e.strip() for e in args.evidence.split(",") if e.strip()])
    except ValueError as e:
        print(e)
        return 1
    sync()
    for p in paths:
        print(f"assessed {args.topic} = {args.level} on {p.name}")
    return 0


def cmd_log_exposure(args: argparse.Namespace) -> int:
    from .assess import log_exposure
    from .ingest import sync

    try:
        paths = log_exposure(args.topic)
    except ValueError as e:
        print(e)
        return 1
    sync()
    print(f"exposure logged for {args.topic!r} on {len(paths)} note(s)")
    return 0


def cmd_graph(args: argparse.Namespace) -> int:
    from .graph import export

    data_js = export()
    print(f"graph exported: {data_js.parent / 'graph.json'} and {data_js}")
    return 0


def cmd_ui(args: argparse.Namespace) -> int:
    import webbrowser

    from .config import root
    from .graph import export

    export()
    page = root() / "ui" / "index.html"
    print(f"opening {page}")
    webbrowser.open(page.as_uri())
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    import hashlib
    import sqlite3

    from . import store

    files = sorted(knowledge_dir().rglob("*.md"))
    print(f"notes on disk: {len(files)}")
    by_domain: dict[str, int] = {}
    for f in files:
        by_domain[f.parent.name] = by_domain.get(f.parent.name, 0) + 1
    for d in sorted(by_domain):
        print(f"  {d}: {by_domain[d]}")

    if not store.db_path().exists():
        print("index: not built (run: python -m brain ingest)")
        return 0
    con = store.connect()
    n_notes = con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    n_chunks = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    hashes = dict(con.execute("SELECT id, content_hash FROM notes").fetchall())
    con.close()

    stale = 0
    for f in files:
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        if hashes.get(f.stem) != h:
            stale += 1
    print(f"index: {n_notes} notes, {n_chunks} chunks", end="")
    print(f", {stale} pending change(s) (run: python -m brain ingest)" if stale else ", up to date")
    return 0


def build_parser() -> argparse.ArgumentParser:
    cfg = load_config()
    parser = argparse.ArgumentParser(prog="brain", description="Second Brain CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="validate note frontmatter against the schema")
    p.add_argument("paths", nargs="*", help="note files or directories (default: knowledge/)")
    p.add_argument("-v", "--verbose", action="store_true", help="also list valid notes")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("add", help="create a note and index it")
    p.add_argument("--domain", required=True, choices=cfg["domains"])
    p.add_argument("--title", required=True, help="used to generate the id slug")
    p.add_argument("--topics", required=True, help="comma-separated")
    p.add_argument("--goals", default="", help="comma-separated goal ids")
    p.add_argument("--source", default="study-session", choices=cfg["sources"])
    p.add_argument("--confidence", type=int, default=2)
    p.add_argument("--importance", type=int, default=3)
    p.add_argument("--body", help="note body (default: read from stdin)")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("import", help="import external markdown (Joplin/Obsidian exports)")
    p.add_argument("src", help="directory of exported .md files")
    p.add_argument("--domain", choices=cfg["domains"],
                   help="domain for all imported notes (default: map folder names)")
    p.add_argument("--dry-run", action="store_true", help="show what would be imported")
    p.add_argument("--confidence", type=int, default=2)
    p.add_argument("--importance", type=int, default=2)
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("ingest", help="sync notes into the index (incremental)")
    p.add_argument("--full", action="store_true", help="wipe and re-embed everything")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("rebuild", help="wipe the index and rebuild from markdown")
    p.set_defaults(func=cmd_rebuild)

    p = sub.add_parser("search", help="semantic search over the knowledge base")
    p.add_argument("query")
    p.add_argument("-k", type=int, default=5, help="max results")
    p.add_argument("--domain", choices=cfg["domains"])
    p.add_argument("--goal", help="filter by goal id")
    p.add_argument("--min-confidence", type=int)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("gaps", help="ranked goal-relevant knowledge gaps")
    p.add_argument("--goal", help="limit to one goal id")
    p.add_argument("-n", type=int, default=10, help="max gaps to show")
    p.set_defaults(func=cmd_gaps)

    p = sub.add_parser("assess", help="record an evidence-based ai_confidence level")
    p.add_argument("topic")
    p.add_argument("--level", type=float, required=True, help="rubric level 0-5")
    p.add_argument("--rationale", required=True,
                   help="which evidence, classified at what rubric level, with quotes")
    p.add_argument("--evidence", required=True, help="comma-separated note ids")
    p.set_defaults(func=cmd_assess)

    p = sub.add_parser("log-exposure", help="record a review event on a topic")
    p.add_argument("topic")
    p.set_defaults(func=cmd_log_exposure)

    p = sub.add_parser("graph", help="export ui/graph.json + ui/graph.data.js")
    p.set_defaults(func=cmd_graph)

    p = sub.add_parser("ui", help="regenerate graph data and open the UI")
    p.set_defaults(func=cmd_ui)

    p = sub.add_parser("status", help="counts and index freshness")
    p.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
