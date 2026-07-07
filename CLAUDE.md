# CLAUDE.md

Working rules for this repo. New here? Read AI-SETUP.md — it is the full
personalization runbook.

## Session start (the conversational front door)

- On the first user message of a session, glance at the brain's state: if
  `knowledge/` has no user-authored notes (notes with `source: demo` and the
  two sample notes don't count) or no real goals are defined, offer the
  /start tour in one friendly sentence — offer, don't launch.
- Map natural language to capabilities proactively (docs/ux.md #1): "show my
  map" → run `brain ui`; "quiz me on X" → /quiz; "what should I study" →
  `brain gaps` or /review; "save this" / "I just learned…" → /log; "am I
  ready for X" → `brain readiness`; "remember it as X" / "make me a
  mnemonic" / "forget that mnemonic" → /mnemonic; "what don't I know about X" /
  "expand the frontier on X" / "grow the map around X" → /frontier; "tag my
  X stuff" / "group these under X" / "add X to the Y tag" → /tag. Never make
  the user learn a skill or command name to reach a feature.

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
- Enrichment of imported notes edits `topics`, `goals`, `importance`, and
  `confidence` in the frontmatter. Set `confidence` from the note body: `1` =
  awareness (material on hand but not internalized) vs `2` = the body shows
  real engagement (worked problems, first-person reasoning, the user's own
  explanation). When unsure, leave it at 1, and state the reason per note.
- Enrichment may also append (or update) a trailing `## Related` section in
  the body with 2–5 `[[note-id]]` links to genuinely related notes. That
  section is the ONLY sanctioned body edit — never alter existing body text.
- NEVER touch `ai_confidence` (only `brain assess`/`/quiz` sets it), `id`,
  `created`, `source`, or any body content outside `## Related`.
- Where note vocabulary doesn't match a roadmap alias, add the alias to the
  roadmap file (`goals/roadmaps/*.yaml`) — do not rename the note's topics.
- When a batch introduces new topics, check them against the lenses in
  `tags.yaml`: if one plausibly belongs to an existing tag, flag it in the
  batch summary as a /tag candidate — propose, don't add (tags stay curated).
- After each batch of changes: `brain validate`, then `pytest -m "not e2e"`,
  then commit. Every few batches: `brain ingest` and `brain graph`.

## Docs stay current

- docs/demo-guide.md is the layman's tour the user shares when demoing the
  system. Any change that adds, removes, or renames a user-facing capability
  (skill, CLI command, UI view) updates that guide in the same commit, in the
  same casual plain-English voice.

## Design constraints (do not erode)

- $0 operating cost: no paid APIs, no servers, no new heavyweight dependencies.
- Markdown is the source of truth; SQLite/embeddings are disposable derived state.
- Domains are unbounded — a folder under knowledge/ plus a config.yaml entry.
  Never enumerate domains in code.
