"""Command-line interface. Run as `python -m brain <command>`."""
from __future__ import annotations

import argparse
import datetime as dt
import json
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
        f"title: {json.dumps(args.title)}\n"
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
        print(f"imported at confidence {args.confidence} "
              f"({'awareness' if args.confidence == 1 else 'known'}) — "
              "run the /ingest skill to add goal links and let the AI judge each "
              "note's level; import a folder of known material with --confidence 2 "
              "for exact control")
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
        print("no results (is the index built? try: brain ingest)")
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
                       [e.strip() for e in args.evidence.split(",") if e.strip()],
                       source=args.source)
    except ValueError as e:
        print(e)
        return 1
    sync()
    for p in paths:
        print(f"assessed {args.topic} = {args.level} on {p.name}")
    return 0


def cmd_set_confidence(args: argparse.Namespace) -> int:
    from .assess import set_confidence
    from .ingest import sync

    try:
        path = set_confidence(args.note_id, args.level)
    except ValueError as e:
        print(e)
        return 1
    sync()
    print(f"set confidence = {args.level} on {path.name}")
    return 0


def cmd_log_exposure(args: argparse.Namespace) -> int:
    from .assess import log_exposure
    from .ingest import sync

    try:
        paths = log_exposure(args.topic, source=args.source)
    except ValueError as e:
        print(e)
        return 1
    sync()
    print(f"exposure logged for {args.topic!r} on {len(paths)} note(s)")
    return 0


def cmd_first_touch(args: argparse.Namespace) -> int:
    from .first_touch import explainer

    try:
        text = explainer(args.skill)
    except ValueError as e:
        print(e)
        return 1
    if text:
        print(text)
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    from collections import Counter

    from .demo import install, remove
    from .ingest import sync

    if args.install:
        try:
            copied, skipped = install()
        except ValueError as e:
            print(e)
            return 1
        if not copied and not skipped:
            print("no demo pack found (expected notes in examples/starter/)")
            return 1
        if copied:
            sync()
        by_domain = Counter(p.parent.name for p in copied)
        print(f"installed {len(copied)} demo note(s)"
              + (f" ({', '.join(f'{d}: {n}' for d, n in sorted(by_domain.items()))})"
                 if copied else "")
              + (f", {len(skipped)} already installed" if skipped else ""))
        print("they are synthetic, marked source: demo, and never touch your own notes")
        print("see them on the map: brain ui")
        print("remove anytime: brain demo --remove")
        return 0

    removed = remove()
    if not removed:
        print("no demo notes installed, nothing to remove")
        return 0
    sync()
    print(f"removed {len(removed)} demo note(s)")
    print("zero trace left: demo notes are never assessed, so no history mentions them")
    return 0


def cmd_model_import(args: argparse.Namespace) -> int:
    from .model.imports import import_resource

    try:
        result = import_resource(Path(args.src), adapter=args.adapter,
                                 slug=args.track, dry_run=args.dry_run)
    except ValueError as e:
        print(e)
        return 1

    t = result.track
    print(f"track: {t.track} ({t.title}) — {len(t.units)} units, "
          f"{len(t.edges)} edges, adapter {t.adapter}")
    for c in result.new_concepts:
        print(f"  new concept: {c.id} ({c.name})")
    for n in result.notes:
        print(f"  note: {n}")
    if result.written:
        print(f"wrote {result.track_path}"
              + (f" and added {len(result.new_concepts)} concept(s) to the registry"
                 if result.new_concepts else ""))
    else:
        print("\n--- dry run: would write "
              f"{result.track_path} ---\n{result.track_yaml}", end="")
    return 0


def cmd_model_build(args: argparse.Namespace) -> int:
    from collections import Counter

    from .model.compile import STATES, compile_model

    model = compile_model()
    n_roadmap = sum(1 for t in model.tracks if t.adapter == "roadmap")
    print(f"model: {len(model.concepts)} concepts, {len(model.edges)} edges, "
          f"{len(model.tracks)} track(s) ({n_roadmap} from roadmaps, "
          f"{len(model.tracks) - n_roadmap} imported)")
    counts = Counter(c.state for c in model.concepts.values())
    print("state: " + ", ".join(f"{counts.get(s, 0)} {s}" for s in STATES))
    evidenced = sum(1 for c in model.concepts.values() if c.level > 0)
    print(f"coverage: {evidenced}/{len(model.concepts)} concepts evidenced; "
          f"{model.kb_topics_matched}/{model.kb_topics_total} note topics in the model")
    converged = [c for c in model.concepts.values() if c.convergence > 1]
    if converged:
        top = sorted(converged, key=lambda c: -c.convergence)[:5]
        print("convergence: " + ", ".join(f"{c.id} x{c.convergence}" for c in top))
    return 0


def cmd_readiness(args: argparse.Namespace) -> int:
    from .model.readiness import readiness

    try:
        report = readiness(args.track)
    except ValueError as e:
        print(e)
        return 2

    counts = report.counts()
    on_track = sum(counts.get(s, 0) for s in ("mastered", "learning"))
    print(f"readiness: {report.track} ({report.title}) — "
          f"{on_track}/{len(report.lines)} concepts on track"
          + ("" if report.ready else " — NOT ready: "
             + ", ".join(f"{counts[s]} {s}" for s in ("missing", "weak", "stale") if counts.get(s))))
    for line in report.lines:
        print(f"  {line.state:<8} {line.level:>3g}  {line.concept:<24} {line.because}")
    return 0 if report.ready else 1


def cmd_context(args: argparse.Namespace) -> int:
    from .model.context import render_context

    try:
        print(render_context(track=args.track, goal=args.goal), end="")
    except ValueError as e:
        print(e)
        return 1
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
    uri = page.as_uri()
    if getattr(args, "toured", False):
        # /start step 4 only: the tour just explained the map, so the page
        # retires the map coach-mark (localStorage sb-hint-map) on load.
        uri += "?toured=1"
    print(f"opening {page}")
    webbrowser.open(uri)
    return 0


def cmd_cockpit(args: argparse.Namespace) -> int:
    from .cockpit import missing_deps, serve

    miss = missing_deps()
    if miss:
        # Optional extra not installed — hint, don't traceback (ux.md #8).
        print("the cockpit needs its optional server deps. install them with:")
        print('  pip install -e ".[cockpit]"')
        print(f"(missing: {', '.join(miss)})")
        return 1
    serve(host=args.host, port=args.port)
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    from .backup import push, setup_text

    if args.setup:
        print(setup_text(), end="")
        return 0
    ok, message = push()
    print(message)
    return 0 if ok else 1


def cmd_doctor(args: argparse.Namespace) -> int:
    from .doctor import render, run_checks

    checks = run_checks()
    print(render(checks), end="")
    return 0 if all(c.ok for c in checks) else 1


def cmd_status(args: argparse.Namespace) -> int:
    import hashlib

    from . import store

    files = sorted(knowledge_dir().rglob("*.md"))
    print(f"notes on disk: {len(files)}")
    by_domain: dict[str, int] = {}
    for f in files:
        by_domain[f.parent.name] = by_domain.get(f.parent.name, 0) + 1
    for d in sorted(by_domain):
        print(f"  {d}: {by_domain[d]}")

    if not store.db_path().exists():
        print("index: not built (run: brain ingest)")
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
    print(f", {stale} pending change(s) (run: brain ingest)" if stale else ", up to date")
    return 0


def cmd_frontier_add(args: argparse.Namespace) -> int:
    import json

    from .frontier import Proposed, add_topics

    try:
        raw = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"could not read spec: {e}")
        return 1
    if not isinstance(raw, list):
        print("spec must be a JSON list of topic objects")
        return 1
    try:
        proposed = [Proposed(id=t["id"], name=t["name"],
                             required_level=int(t.get("required_level", 2)),
                             prereqs=list(t.get("prereqs", [])),
                             aliases=list(t.get("aliases", []))) for t in raw]
    except (KeyError, TypeError) as e:
        print(f"malformed topic in spec: {e}")
        return 1

    try:
        result = add_topics(args.goal, proposed, max_add=args.max)
    except ValueError as e:
        print(e)
        return 1

    for p in result.added:
        print(f"  added: {p.id} ({p.name}) — required_level {p.required_level}")
    for pid, alias, concept in result.dropped_aliases:
        print(f"  dropped alias '{alias}' from {pid} (belongs to concept '{concept}')")
    for pid, reason in result.skipped:
        print(f"  skipped: {pid} — {reason}")
    if result.added:
        print(f"appended {len(result.added)} topic(s) to {result.roadmap_path}; "
              f"registry re-synced, graph rebuilt. "
              f"{result.dashed_total} dashed frontier nodes now on the map.")
    else:
        print("nothing added.")
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
    p.add_argument("--confidence", type=int, default=1,
                   help="1 = you have/recognize the material (default); "
                        "2 = material you already know")
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
    p.add_argument("--source", help="skill that produced this assessment "
                                    "(e.g. quiz, debrief) — powers first-touch detection")
    p.set_defaults(func=cmd_assess)

    p = sub.add_parser("set-confidence",
                       help="override a note's self/observed confidence (awareness->known); "
                            "does not touch quiz-based ai_confidence")
    p.add_argument("note_id")
    p.add_argument("--level", type=int, required=True,
                   help="1 = awareness (have it), 2 = known, up to 5")
    p.set_defaults(func=cmd_set_confidence)

    p = sub.add_parser("log-exposure", help="record a review event on a topic")
    p.add_argument("topic")
    p.add_argument("--source", help="skill that produced this exposure "
                                    "(e.g. review) — powers first-touch detection")
    p.set_defaults(func=cmd_log_exposure)

    p = sub.add_parser("first-touch",
                       help="print a one-time explainer the first time a skill is used "
                            "(empty output after); read-only, powers skill first-touches")
    p.add_argument("skill", choices=["quiz", "review", "ingest", "path", "debrief"])
    p.set_defaults(func=cmd_first_touch)

    p = sub.add_parser("demo", help="install or remove the starter demo pack "
                                    "(synthetic notes, source: demo, removable without trace)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--install", action="store_true", help="copy examples/starter/ notes in")
    g.add_argument("--remove", action="store_true", help="delete every source: demo note")
    p.set_defaults(func=cmd_demo)

    p = sub.add_parser("model", help="knowledge model: import learning resources as tracks")
    msub = p.add_subparsers(dest="model_command", required=True)
    mp = msub.add_parser("import", help="import a syllabus/outline/roadmap file as a track")
    mp.add_argument("src", help="markdown outline or roadmap-format YAML")
    mp.add_argument("--adapter", choices=["outline", "roadmap"],
                    help="default: by extension (.md outline, .yaml roadmap)")
    mp.add_argument("--track", help="track slug (default: derived from the title)")
    mp.add_argument("--dry-run", action="store_true",
                    help="print the would-be track, write nothing")
    mp.set_defaults(func=cmd_model_import)
    mp = msub.add_parser("build", help="compile the model and print a summary")
    mp.set_defaults(func=cmd_model_build)

    p = sub.add_parser("frontier",
                       help="expand a goal's roadmap with proposed frontier topics "
                            "(guarded: dedup, alias-collision, governor cap)")
    frsub = p.add_subparsers(dest="frontier_command", required=True)
    frp = frsub.add_parser("add", help="append confirmed frontier topics from a JSON spec")
    frp.add_argument("--goal", required=True, help="goal id whose roadmap to expand")
    frp.add_argument("--spec", required=True,
                     help="JSON file: list of {id, name, required_level, prereqs, aliases}")
    frp.add_argument("--max", type=int, default=8,
                     help="governor: max topics to add per call (default 8)")
    frp.set_defaults(func=cmd_frontier_add)

    p = sub.add_parser("readiness",
                       help="explainable per-concept readiness for a track or goal "
                            "(exit 0 ready, 1 not ready, 2 unknown track)")
    p.add_argument("track", help="track slug or goal id (e.g. gcp-cdl)")
    p.set_defaults(func=cmd_readiness)

    p = sub.add_parser("context",
                       help="compact learning-state YAML for pasting into any AI assistant")
    p.add_argument("--track", help="limit to one track slug")
    p.add_argument("--goal", help="limit to one goal id")
    p.set_defaults(func=cmd_context)

    p = sub.add_parser("graph", help="export ui/graph.json + ui/graph.data.js")
    p.set_defaults(func=cmd_graph)

    p = sub.add_parser("ui", help="regenerate graph data and open the UI")
    p.add_argument("--toured", action="store_true",
                   help="mark the map coach-mark seen on load (used by the /start tour "
                        "after it has explained the map itself)")
    p.set_defaults(func=cmd_ui)

    p = sub.add_parser("cockpit",
                       help="launch the local web cockpit (opt-in; buttons drive "
                            "quiz/log/review via headless Claude, plus no-AI ops)")
    p.add_argument("--host", default="127.0.0.1", help="bind address (default: localhost)")
    p.add_argument("--port", type=int, default=8765, help="port (default: 8765)")
    p.set_defaults(func=cmd_cockpit)

    p = sub.add_parser("status", help="counts and index freshness")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("doctor", help="health checks with the one fixing command each "
                                      "(exit 1 if anything needs fixing)")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("backup", help="push local snapshots to your private remote "
                                      "(the only command that pushes anything)")
    p.add_argument("--setup", action="store_true",
                   help="walk through wiring up a private remote (prints steps, "
                        "changes nothing)")
    p.set_defaults(func=cmd_backup)

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        # Bare `brain` is the home screen, not usage (PLAN-UX U1);
        # argparse help stays under `brain --help`.
        from .home import render_home

        print(render_home(), end="")
        return 0
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
