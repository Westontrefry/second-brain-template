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

## assess
The only setter of ai_confidence. Requires receipts:
```
brain assess databases --level 4 --evidence 2026-07-02-btree-vs-hash-indexes \
  --rationale "quiz 2026-07-03: applied tradeoff to novel case, quoted '...'"
```
Writes ai_confidence + rationale + last_assessed onto the evidence notes (which must
carry the topic); self-assessed `confidence` is never touched. Used by /quiz.

## log-exposure
`brain log-exposure <topic>` — records a review event: bumps exposure_count and
last_reviewed on every note carrying the topic (refreshes decay). Used by /review.
