# Glossary — canonical terminology

Use these terms (and only these) in code, CLI output, docs, and skills. If a concept
needs a name, it gets defined here first.

## Content

- **note** — one markdown file in `knowledge/<domain>/` with YAML frontmatter + body.
  The atomic unit of the knowledge base. Created only through `brain add` or
  `brain import`.
- **frontmatter** — the YAML metadata block of a note (schema in PLAN.md, enforced by
  `brain validate`).
- **body** — the markdown content of a note below the frontmatter.
- **domain** — top-level folder a note lives in (`cs`, `cloud`, `career`, `projects`,
  …). An organizational cluster, never a boundary: unbounded set, defined in
  `config.yaml`.
- **topic** — a lowercase tag in a note's `topics:` list. Topics are the graph's
  nodes and the join key to roadmaps. (Always "topic", never "tag".)
- **source** — how a note came to exist (`study-session`, `course`, `project`,
  `import`, `quiz`, `ai-conversation`). Determines its evidence class.
- **wiki-link** — `[[note-id]]` in a body; becomes a graph edge.

## Goals and pathways

- **goal** — an objective in `goals/goals.yaml` (id, priority, deadline). Notes link
  to goals; goals cut across domains.
- **roadmap** — per-goal YAML in `goals/roadmaps/<goal-id>.yaml`: the topics a goal
  requires, each with a required level and prerequisites. Where industry standards
  live.
- **roadmap topic** — one entry in a roadmap; matched against note topics via its id
  and **aliases** (alternate spellings that count as evidence).
- **prerequisite (prereq)** — roadmap topic that should be evidenced before another;
  gives the graph its branch skeleton.
- **pathway** — a route through topics toward an objective. Goal pathways come from
  roadmaps; ad-hoc pathways are compiled by the /path skill into an **overlay**
  (`ui/paths/<slug>.json`) the UI renders.

## Knowledge measurement

- **rubric / depth level** — the universal 0–5 scale in `rubrics/depth.yaml`
  (0 no evidence, 1 exposure, 2 comprehension, 3 application, 4 fluency, 5 mastery).
- **confidence** — SELF-assessed 1–5 in frontmatter. Never modified by AI.
- **ai_confidence** — evidence-based 0–5, written only by assessment events
  (`brain assess`), always with a rationale citing evidence. Null = unassessed.
- **divergence** — disagreement between confidence and ai_confidence; a first-class
  signal, not an error.
- **evidence** — anything that supports a level classification: note content, quiz
  results, project work, external validation. Has an **evidence class**
  (`note`, `application_note`, `quiz`, `external_validation`) with a config
  multiplier and decay half-life.
- **evidenced level** — the depth level the evidence actually supports:
  ai_confidence when assessed, else self-confidence capped at level 3.
- **exposure** — a study/apply event on a topic; `exposure_count` in frontmatter.
- **decay** — recency discount on evidence weight: 0.5^(age / half-life).
- **weight** — computed topic strength: evidence multiplier × confidence × exposure ×
  decay, summed over notes. Never stored; always derived (`brain/weights.py`).
- **gap** — required level (roadmap) minus evidenced level, for one roadmap topic.
- **gap score** — gap × goal priority × deadline urgency; prereq-blocked topics
  deprioritized. Output of `brain gaps`.
- **stale** — evidenced but not reviewed within 120 days; flagged for refresh.
- **suggestion** — a ranked next action shown in the UI: derived from gap analysis
  (goal selection) or authored into an overlay by /path (pathway selection).
- **assessment** — a /quiz-driven event that sets ai_confidence via `brain assess`,
  always with rationale + evidence note ids ("receipts").
- **exposure event** — a review recorded by `brain log-exposure`: bumps
  exposure_count and last_reviewed, refreshing decay.

## Knowledge model (KME)

- **concept** — one canonical entry in `model/concepts.yaml` (the **registry**):
  a slug id, display name, and aliases. The cross-domain unit of the knowledge
  model; note topics join concepts by the same slugify rule roadmaps use. An
  alias belongs to exactly one concept.
- **track** — one imported learning resource (`model/tracks/<slug>.yaml`):
  ordered **units** of concept refs plus prereq edges, each edge carrying
  **provenance** (why the edge exists, quoting its source) and **confidence**
  (1.0 = explicit in the source, lower = inferred, e.g. 0.5 from outline
  order). Roadmaps load as tracks in memory — they are never materialized.
- **adapter** — the parser that turns a resource into a track (`outline` for
  markdown syllabi, `roadmap` for roadmap-format YAML).
- **learning state** — the named classification of a concept's existing
  evidence: **mastered / learning / weak / stale / missing** (thresholds in
  `config.yaml model.state`). A thin layer over weights.py + events.jsonl —
  never a second store. Every state carries its **reason** ("because").
- **convergence** — how many tracks touch a concept; high convergence = learn
  it once, it pays off in several places. Shown in the UI drill-down panel.
- **readiness** — per-track report (`brain readiness`) where every line
  self-explains; **context export** — the one-screen YAML (`brain context`)
  that ports learning state into any AI assistant.

## Pipeline

- **import** — bringing EXTERNAL files (Joplin/Obsidian exports) into `knowledge/`
  as notes (`brain import`). Not to be confused with:
- **ingest** — syncing `knowledge/` INTO the index (chunk → embed → store), done by
  `brain ingest` (incremental, by content hash) or `brain rebuild` (from scratch).
- **enrichment** — the /ingest skill's metadata pass over imported notes (topics,
  goals, importance). Never touches confidence, ai_confidence, or body.
- **chunk** — a piece of a note body sized for embedding.
- **embedding** — local sentence-transformers vector for a chunk.
- **index** — the SQLite database (`brain.db`). Derived and disposable; rebuildable
  from markdown at any time. Markdown is the **source of truth**.
- **sandbox** — a temporary copy of the repo's data used by tests, selected via the
  `BRAIN_ROOT` environment variable.
