---
name: ingest
description: Bulk-import external notes (Joplin/Obsidian/markdown exports) into the second-brain and enrich imported notes with topics, goal links, and importance. Use when the user points at an export folder or asks to enrich imported notes.
---

# /ingest — bulk import + AI enrichment

Two phases; either can run alone.

## Phase A — import (when given a folder)

1. Preview: `.venv/bin/python -m brain import <dir> --dry-run` (add `--domain <d>`
   when notebook folders don't match config domains — typical for Joplin exports
   named after courses).
2. Show the user the plan (count, domains, any skipped files) and run it for real.
   Re-runs are safe: content-hash dedup skips anything already imported.

## Phase B — enrichment (imported notes awaiting metadata)

Imported notes arrive with `source: import`, `goals: []`, conservative scores.
Find them: `grep -rl "source: import" knowledge/ | xargs grep -l "goals: \[\]"`.

For each (batch in groups of ~10, largest/most goal-relevant first):
1. Read the note body.
2. Improve ONLY metadata, editing frontmatter in place (this is the one sanctioned
   direct edit, because `brain add` can't retro-edit):
   - topics: replace placeholder tags with 2–5 real ones from the existing vocabulary
   - goals: link goals the content genuinely serves (check goals/goals.yaml)
   - importance: raise/lower per goal relevance
   - NEVER change: confidence, ai_confidence (enrichment is metadata, not assessment),
     id, created, source, body content.
3. After each batch: `.venv/bin/python -m brain validate && .venv/bin/python -m brain ingest`
   — validation failure means revert that file and report it.
4. Summarize: how many enriched, notable clusters found, anything the user should review.
