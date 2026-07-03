# CLAUDE.md

Working rules for this repo. New here? Read AI-SETUP.md — it is the full
personalization runbook.

## Command discipline

- Run commands individually — one tool call per command. Do NOT chain with `&&`
  or `;`. Each `brain` subcommand, each `pytest` run, and each `git` command is
  its own call, so a failure is visible and isolated.
- Update markdown files with the Edit tool, never via shell redirection
  (`>>`, `sed -i`, `tee`).

## Knowledge-base integrity

- `ai_confidence` is written ONLY by `brain assess` (with rationale +
  note-id receipts). Never set it by hand. `confidence` is the user's
  self-assessment — never change it on their behalf.
- Enrichment of imported notes edits ONLY `topics`, `goals`, `importance`.
  NEVER touch `confidence`, `ai_confidence`, `id`, `created`, `source`, or
  the note body.
- Where note vocabulary doesn't match a roadmap alias, add the alias to the
  roadmap file (`goals/roadmaps/*.yaml`) — do not rename the note's topics.
- After each batch of changes: `brain validate`, then `pytest -m "not e2e"`,
  then commit. Every few batches: `brain ingest` and `brain graph`.

## Design constraints (do not erode)

- $0 operating cost: no paid APIs, no servers, no new heavyweight dependencies.
- Markdown is the source of truth; SQLite/embeddings are disposable derived state.
- Domains are unbounded — a folder under knowledge/ plus a config.yaml entry.
  Never enumerate domains in code.
