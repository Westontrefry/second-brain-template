# AI-SETUP.md — runbook for the recipient's AI assistant

You are an AI assistant (Claude Code or similar) helping a new user personalize
this second-brain template. Follow this document top to bottom. The human gave
you this repo precisely so you could do this — ask them the interview questions,
then do the mechanical work yourself.

## What this system is (read first)

- `knowledge/**/*.md` — THE knowledge base. Markdown + YAML frontmatter is the
  source of truth. Everything else is derived and rebuildable.
- `brain/` — Python CLI: `validate | add | import | ingest | search | gaps |
  assess | log-exposure | graph | ui | rebuild | status | model import |
  model build | readiness | context`. Run as
  `.venv/bin/python -m brain <cmd>`. See `docs/cli.md`.
- `goals/goals.yaml` — the user's goals. `goals/roadmaps/<goal-id>.yaml` — per-
  goal skill checklists with `required_level` (vs `rubrics/depth.yaml`) and
  `aliases`, which join note topics to roadmap topics.
- `model/` — the knowledge model (KME): `concepts.yaml` is the canonical
  concept registry (ids + aliases; an alias joins the user's note vocabulary
  to a concept — add aliases here, never rename their topics), and
  `tracks/*.yaml` are imported learning resources (`brain model import`).
- `.claude/skills/` — the AI layer: /log, /ingest, /query, /quiz, /review,
  /path, /interview-pack, /debrief. Read each SKILL.md before using it.
- `docs/architecture.md` and `docs/glossary.md` — read both before editing code.

## Hard rules (non-negotiable, from the original design)

1. `confidence` is the user's SELF-assessment. `ai_confidence` is evidence-based
   and is written ONLY by `brain assess` with a rationale and note-id receipts.
   NEVER set or edit `ai_confidence` by hand, and never conflate the two.
2. Never edit `id`, `created`, `source`, or note bodies during enrichment —
   enrichment touches only `topics`, `goals`, `importance`.
3. Where the user's note vocabulary doesn't match a roadmap topic, add an
   **alias to the roadmap file** — do not rename the user's topics.
4. All writes to knowledge/ go through validated paths (`brain add`,
   `brain assess`, or frontmatter edits followed by `brain validate`).
5. After any change: `brain validate`, then `pytest -m "not e2e"`, then commit.
   Run commands one at a time — never chained with `&&` or `;`.
6. No new dependencies, no servers, no paid APIs. The $0 constraint is a
   feature, not an accident.

## Setup sequence

### 1. Environment
```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m brain validate
.venv/bin/python -m pytest -q -m "not e2e"
```
Both must pass before you change anything.

### 2. Interview the user
Ask, minimally:
- What are you working toward? (jobs, certs, degrees, projects — get 3–6 goals
  with rough priorities and deadlines)
- What clusters does your knowledge naturally fall into? (these become domains —
  4–6 folders, e.g. `cs`, `music`, `medicine`, `business`)
- Do you have existing notes to import, and from what app? (Joplin "MD -
  Markdown + Front Matter" export is first-class; plain markdown and Obsidian
  vaults also work)

### 3. Configure
- Rewrite `goals/goals.yaml` with their real goals (keep the schema).
- Rename/replace the seed domains in `config.yaml` AND create matching folders
  under `knowledge/`.
- For each goal that deserves gap analysis, write
  `goals/roadmaps/<goal-id>.yaml`. Base cert roadmaps on the REAL exam guide,
  not memory. Set `required_level` honestly against `rubrics/depth.yaml`
  (conceptual cert ≈ 2, hands-on cert ≈ 3, timed interviews ≈ 4).
- Delete the example goal/roadmap/sample notes once real content exists.

### 4. Import + enrich (if they have notes)
- `brain import <dir> --dry-run` first; map each notebook/folder to a domain
  with `--domain`. Park anything ambiguous and ask the user rather than guess.
- Imported notes arrive with `goals: []` and placeholder topics. Enrich in
  batches of ~10: read each note body, then set real `topics` (2–5 from the
  emerging vocabulary), `goals` (only where genuinely earned), `importance`.
- After each batch: `brain validate` → `pytest -m "not e2e"` → commit.
  Every few batches: `brain ingest` and `brain graph`.
- After enrichment, diff the note-topic vocabulary against roadmap aliases and
  add the missing aliases (rule 3).

### 5. Verify end-to-end
- `brain ingest` → `brain status` (all notes indexed)
- `brain search "<something they know>"` returns the right note
- `brain gaps --goal <id>` produces a sensible ranked list
- `brain ui` renders the graph with their domains and goals

### 6. Hand back
Show the user: their graph, their top 3 gaps per goal, and how to log their
first study session with /log. Suggest /quiz once they have 20+ notes in one
topic — that is how `ai_confidence` evidence starts accumulating.
