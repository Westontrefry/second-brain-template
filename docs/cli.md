# CLI reference

All commands: `.venv/bin/python -m brain <command>` from the repo root (or activate
the venv and use `python -m brain`). Exit code 0 = success. Terms: [glossary.md](glossary.md).

## validate
Check notes against the schema. `brain validate [paths...] [-v]`
- Default target: all of `knowledge/`. Exit 1 if any note fails, listing every error.

## add
Create a note and index it. The only way to create notes by hand.
```
brain add --domain cs --title "MLFQ review" --topics "os,scheduling" \
  --goals uf-cs-degree --source study-session --confidence 2 --importance 3 \
  --body "..."          # omit --body to read from stdin
```
- Title becomes the id slug (`2026-07-02-mlfq-review`). Rejects invalid notes.

## import
Bring external markdown exports into the knowledge base.
```
brain import ~/joplin-export --dry-run          # preview
brain import ~/joplin-export --domain cs        # all notes into one domain
brain import ~/export                           # map folder names to domains
```
- Joplin "MD - Markdown + Front Matter" exports: title/created/updated/tags preserved,
  notebook folder becomes a topic.
- Idempotent: identical content is skipped on re-runs (content-hash dedup).
- Imported notes get `source: import`, `goals: []` — enrich via the /ingest skill.

## ingest / rebuild
Sync `knowledge/` into the index. `ingest` is incremental (content hash); `rebuild`
wipes and re-embeds everything. First run downloads the embedding model (~90MB) once.

## search
Semantic search. `brain search "query" [-k 5] [--domain d] [--goal g] [--min-confidence n]`
- Prints score, note id, path, and snippet; best chunk per note.

## gaps
Ranked goal-relevant knowledge gaps. `brain gaps [--goal g] [-n 10]`
- Score = gap × goal priority × deadline urgency; prereq-blocked topics are
  deprioritized and annotated `(first: <prereq>)`.

## status
Note counts per domain, index size, and freshness (pending changes).

## graph
Export the knowledge graph: `ui/graph.json` (tooling) + `ui/graph.data.js` (bundled
data the page loads without fetch, so file:// works). Pathway overlays in
`ui/paths/*.json` are bundled in.

## ui
Regenerate graph data and open `ui/index.html` in the browser. Features: force
layout, pan/zoom, node size = weight, color = strength tier, per-goal filter,
gap toggle, divergence toggle, pathway picker, node drill-down (ego-network
focus + detail panel with evidence mix, requirements, notes, breadcrumbs),
suggestions tab, and a "? reference" tab — a filterable dictionary of every
skill and CLI command, derived at export time from SKILL.md frontmatter and
the argument parser (it can't drift from reality).

## model import
Teach the knowledge model a learning resource (the Knowledge Model Engine —
see [architecture.md](architecture.md)).
```
brain model import ~/Downloads/course-syllabus.md --dry-run    # preview
brain model import syllabus.md --track os-course               # slug override
brain model import some-plan.yaml --adapter roadmap            # roadmap-format file
```
- Adapters: `outline` (markdown headings = units, list items = concept terms;
  order-based prereq edges at confidence 0.5) and `roadmap` (explicit prereqs,
  confidence 1.0). Default by extension (.md outline, .yaml roadmap).
- Writes `model/tracks/<slug>.yaml`; unknown terms are appended to
  `model/concepts.yaml` as new concepts (known vocabulary canonicalizes via
  aliases — same slug-join rule as roadmaps). Re-import is idempotent.
- In-repo roadmaps never need importing: they load as tracks automatically.

## model build
Compile the model (registry + tracks + learning state) and print a summary:
concepts/edges/tracks, per-state counts (mastered / learning / weak / stale /
missing — thresholds in config.yaml `model.state`), coverage vs the knowledge
base, and the most-converged concepts (touched by multiple tracks).

## readiness
Explainable per-concept readiness for any track or goal. `brain readiness example-cert`
- One line per concept in track order: state, level, and a "because" that
  self-explains (evidence level, staleness age, or `first: <prereq>` blockers).
- Exit codes: 0 ready (everything mastered/learning), 1 not ready, 2 unknown track.

## context
One-screen YAML learning-state export for pasting into any AI assistant.
`brain context [--track X] [--goal Y]`
- Active tracks with readiness + goal deadlines/priorities, per-state concept
  lists, top gaps with reasons (round-robin across tracks, highest-priority
  goal first). Topic names and states only — no note contents.

## assess
The only setter of ai_confidence. Requires receipts:
```
brain assess databases --level 4 --evidence 2026-07-02-btree-vs-hash-indexes \
  --rationale "quiz 2026-07-03: applied tradeoff to novel case, quoted '...'"
```
Writes ai_confidence + rationale + last_assessed onto the evidence notes (which must
carry the topic); self-assessed `confidence` is never touched. Used by /quiz.
Also appends one line to `events.jsonl` (append-only history for time-series views).

## log-exposure
`brain log-exposure <topic>` — records a review event: bumps exposure_count and
last_reviewed on every note carrying the topic (refreshes decay). Used by /review.
Also appends one line to `events.jsonl`.
