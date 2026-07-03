# Architecture

Terms used here are defined in [glossary.md](glossary.md).

## The one principle

**Markdown is the source of truth; everything else is derived and disposable.**
`knowledge/` + `goals/` + `rubrics/` + `config.yaml` fully determine the system's
state. The index (`brain.db`), graph JSON, and any UI can be deleted and rebuilt
losslessly. This is what makes the knowledge vendor- and model-portable.

## Data flow

```
knowledge/*.md  goals/*.yaml  rubrics/depth.yaml        (source of truth, git-versioned)
      │
      ▼
   brain/  (deterministic Python)
      ├── schema.py     parse + validate notes
      ├── ingest.py     chunk -> embed (local) -> index          } write path
      ├── importer.py   external exports -> notes                } write path
      ├── store.py      SQLite index (derived)
      ├── retrieve.py   semantic search + metadata filters
      ├── weights.py    topic weight + evidenced level (no DB needed)
      ├── gaps.py       roadmap diff -> ranked gaps
      └── llm/          provider interface (claude_code now, APIs later)
      │
      ▼
  derived views: search results, gap reports, ui/graph.json ->
      ui/index.html (D3 graph) + ui/dashboard.html (readiness radar,
      confidence-divergence scatter — same bundled graph.data.js, no server)
      │
      ▼
  .claude/skills/  (reasoning layer: /log /ingest /query, later /quiz /review /path)
```

## Invariants (enforced by convention + tests)

1. $0 operating cost: local embeddings, no paid services, reasoning via Claude Code.
2. Views and skills never write to `knowledge/` directly — writes go through
   validated paths (`brain add`, `brain import`, `brain assess`), with one exception:
   enrichment edits frontmatter metadata in place, then re-validates.
3. `confidence` is the user's; `ai_confidence` is written only by assessment events
   with a rationale. Neither is ever silently changed.
3a. Frontmatter holds only the LATEST assessment/exposure state; `events.jsonl`
   (append-only, committed, path in config) keeps the full history. `brain assess`
   and `brain log-exposure` append one JSON line per event — this is what future
   time-series views (confidence-over-time, goal burndown) will read.
4. Domains are data (`config.yaml`), never hardcoded.
5. The index must always be rebuildable: `brain rebuild` after deleting `brain.db`
   restores equivalent state.

## Module boundaries

- `cli.py` is thin: argument parsing + printing. Logic lives in the modules, which
  are import-safe for future consumers (web cockpit, dashboards) — nothing is
  CLI-only.
- `weights.py` and `gaps.py` read markdown directly (not the DB) so gap analysis
  works even without an index and stays deterministic.
- Heavy deps (sentence-transformers) are imported lazily inside functions so
  `validate`/`gaps`/`status` stay fast.
