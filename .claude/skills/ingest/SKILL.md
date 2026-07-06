---
name: ingest
description: Bulk-import external notes (Joplin/Obsidian/markdown exports) into the second-brain and enrich imported notes with topics, goal links, and importance. Use when the user points at an export folder or asks to enrich imported notes.
---

# /ingest — bulk import + AI enrichment

**First-touch (run this first):** `.venv/bin/python -m brain first-touch ingest`. If it
prints a paragraph, this is the user's first import — open your reply with that text
verbatim, then continue. If it prints nothing, skip it and proceed. (No source flag to
set here: the explainer retires on its own once the first `source: import` note lands.)

Two phases; either can run alone.

## Phase A — import (when given a folder)

1. Preview: `.venv/bin/python -m brain import <dir> --dry-run` (add `--domain <d>`
   when notebook folders don't match config domains — typical for Joplin exports
   named after courses).
2. Show the user the plan (count, domains, any skipped files) and run it for real.
   Re-runs are safe: content-hash dedup skips anything already imported.
3. Tell him: bulk imports land at confidence 1 (awareness), and the AI will judge
   each note's real level (1 vs 2) during enrichment. If he already knows a folder
   is material he's fluent in, import that folder on its own with `--confidence 2`
   for exact control instead of letting the AI infer it.

## Phase B — enrichment (imported notes awaiting metadata + level)

Imported notes arrive with `source: import`, `goals: []`, confidence 1 (awareness).
- Metadata enrichment (needs topics/goals): `grep -rl "source: import" knowledge/ | xargs grep -l "goals: \[\]"`.
- Confidence sweep over the whole back-catalog (re-judge level 1 vs 2): every
  `source: import` note — `grep -rl "source: import" knowledge/`.

For each (batch in groups of ~10, largest/most goal-relevant first):
1. Read the note body.
2. Improve metadata + confidence, editing frontmatter in place (this is the one
   sanctioned direct edit, because `brain add` can't retro-edit):
   - topics: replace placeholder tags with 2–5 real ones from the existing vocabulary
   - goals: link goals the content genuinely serves (check goals/goals.yaml)
   - importance: raise/lower per goal relevance
   - confidence: judge from the body — `1` = awareness (material on hand but not
     internalized: a resource, or a doc known by title/ToC only) vs `2` = the body
     shows real engagement (worked problems, first-person reasoning, your own
     explanation). When unsure, leave it at 1. Note the reason per note in the summary.
   - wikilinks: append a trailing `## Related` section with 2–5 `[[note-id]]` links
     to genuinely related notes (find candidates via `brain search` on the note's
     core concepts), one bullet per link with a short reason. This is the only
     sanctioned body edit; never alter existing body text. If the section already
     exists, update it in place instead of appending a duplicate. These links feed
     the graph's cross-note edges and let agents walk the vault link-to-link.
   - NEVER change: ai_confidence (evidence-based — only `brain assess`/`/quiz` sets it),
     id, created, source, or any body content outside the `## Related` section.
3. After each batch: `.venv/bin/python -m brain validate`, then
   `.venv/bin/python -m brain ingest` (separate tool calls — a failure must be
   visible and isolated). Validation failure means revert that file and report it.
4. Summarize: how many enriched, the confidence calls (which stayed at 1 vs promoted
   to 2 and why), notable clusters found, anything the user should review.

**Finish every run (ux.md #2/#3/#6 — one command per tool call):**
1. `.venv/bin/python -m brain ingest`, then `.venv/bin/python -m brain graph`.
2. Snapshot: `git add` the imported/enriched notes, then
   `git commit -m "snapshot: ingest: <n> notes from <source>"`. No git? One
   line: snapshot skipped, notes still saved.
3. End with the receipt block (docs/ux.md #2): counts (imported, enriched,
   skipped — list everything skipped, no silent truncation); confidence calls
   stated as claimed levels; "map data refreshed — reload the tab"; "saved a
   local snapshot — nothing leaves your machine"; next action.
