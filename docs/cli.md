# CLI reference

Install once with `pip install -e .` (inside the venv) and every command is
`brain <command>` from anywhere. `python -m brain <command>` still works and is
equivalent. Exit code 0 = success. Terms: [glossary.md](glossary.md).

## validate
Check notes against the schema. `brain validate [paths...] [-v]`
- Default target: all of `knowledge/`. Exit 1 if any note fails, listing every error.

## add
Create a note and index it. The only way to create notes by hand.
```
brain add --domain cs --title "MLFQ review" --topics "os,scheduling" \
  --goals cs-degree --source study-session --confidence 2 --importance 3 \
  --body "..."          # omit --body to read from stdin
```
- Title becomes the id slug (`2026-07-02-mlfq-review`). Rejects invalid notes.

## import
Bring external markdown exports — or a text-layer PDF — into the knowledge base.
```
brain import ~/joplin-export --dry-run           # preview a folder of markdown
brain import ~/joplin-export --domain cs         # all notes into one domain
brain import ~/export                            # map folder names to domains
brain import ~/books/system-design.pdf --domain cs --dry-run   # preview a PDF
brain import ~/books/system-design.pdf --domain cs             # book -> per-chapter notes
```
- Joplin "MD - Markdown + Front Matter" exports: title/created/updated/tags preserved,
  notebook folder becomes a topic.
- **PDF** (text-layer books/manuals): splits by the embedded outline (one note per
  chapter; no outline -> a single note), tags every note with the book slug so they
  group on the map. Running headers/footers and page numbers are stripped
  deterministically (no AI). `--domain` is required (a PDF has no folder to map).
  Needs the optional `pypdf` dep: `pip install -e ".[pdf]"`.
- Scanned or handwritten PDFs have no text layer — they are detected and refused, not
  imported as empty notes. For handwritten notes, drop a photo into a /log or /ingest
  session and Claude transcribes it via vision ($0).
- Idempotent: identical content is skipped on re-runs (content-hash dedup).
- Imported notes get `source: import`, `goals: []`, confidence 1 — enrich via the
  /ingest skill.

## inbox
Sweep the `Ingest/` drop folder into the knowledge base. `brain inbox [--dry-run] [--force]`
- Drop `.pdf` / `.md` files (or whole export folders) into `Ingest/<domain>/` —
  the subfolder names the domain, same rule as the markdown importer; files at
  the root are reported, never guessed into a domain. First run creates the
  domain subfolders so the drop target is visible in Finder.
- Routes each entry through `brain import` (PDFs need the `.[pdf]` extra), then
  moves originals to `Ingest/processed/<domain>/`. The whole tree is gitignored:
  copyrighted sources never reach git, only derived notes do.
- Dedup is layered: processed files leave the scan set; a PDF whose basename
  already sits in `Ingest/processed/` (or whose book-slug tag already has notes)
  is refused unless `--force`; and identical content is content-hash-skipped.
  The content hash ignores any trailing `## Related` block, so re-sweeping an
  enriched book still dedups. The filename guard survives a later retag — the
  book-slug tag guard alone does not.
- No daemon — the folder is checked, not watched: the home screen prints an
  "N file(s) waiting" nudge and the cockpit dock has an Inbox button.
- Imports land unenriched (`source: import`, confidence 1) — the sweep ends by
  pointing at the /ingest skill for topics, goals, and level judgment.

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

## brain (no command)
The home screen: note/topic counts, index freshness, an inbox nudge when
files are waiting in `Ingest/`, a "Since last time"
recap (notes added, levels proven, topics gone stale — from events.jsonl +
git history, previous activity day included), the top three gaps, and three
things to try (conversational forms first). Empty brain prints the
getting-started pointer instead. Usage lives under `brain --help`.

## demo
Install or remove the starter demo pack. `brain demo --install | --remove`
- Eight synthetic notes from `examples/starter/` (6 CS on dsa-interviews + 2
  non-CS for domain-agnosticism), all `source: demo`, never assessed.
- Install is idempotent; remove deletes every `source: demo` note and re-syncs
  the index — zero trace (assessment history never cites demo content).

## status
Note counts per domain, index size, and freshness (pending changes).

## backup
Opt-in off-machine copy. `brain backup --setup | brain backup`
- `--setup` inspects state and prints the walk (git init / gh repo create
  --private / manual remote add) — it changes nothing and pushes nothing.
- Bare `brain backup` pushes the current branch to origin: the only command in
  the product that sends notes anywhere. Everything else is local snapshots.

## doctor
Seven health checks — python/venv, dependencies, embedding-model cache, note
validity, index freshness, map-data freshness, git presence — each failure
paired with the one command that fixes it. Exit 1 if anything needs fixing.
Automates the debugging-playbook basics; users should never need that skill.

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
the argument parser (it can't drift from reality). The header shows "data
generated <ago>" so a stale tab self-diagnoses. `--toured` (used by /start
step 4 only) opens with `?toured=1`, which retires the Map view's first-visit
coach-mark — the tour just taught the same ground.

## cockpit
Launch the local web cockpit (Arc B rung 2): the same map, plus a dock that
drives your skills. `brain cockpit [--host 127.0.0.1] [--port 8765]`
- Opt-in surface — needs the optional server extra. Install it once with
  `pip install -e ".[cockpit]"` (adds fastapi + uvicorn). Without it the command
  prints that install hint, never a traceback.
- The map is unchanged; a "Cockpit" button appears in the header only when this
  server answers. Over `file://` (or `brain ui`, which has no API) the button
  stays hidden, so the file-first behaviour is untouched.
- Dock buttons: Log / Quiz / Review run the matching skill in a headless
  `claude -p` session (subscription-covered, still $0 — no API keys) and stream
  the reply back live; a reply box continues multi-turn quiz/review. Inbox /
  Ingest / Graph / Gaps / Status / Doctor run in-process with no AI.
- Topic selection is guided, not free-typed: the dock's Quiz/Review composer
  autocompletes from your real topic names (blank still = let it choose), and
  clicking a node on the map adds Quiz / Review / Log / Expand buttons to its
  detail card that act on that topic directly — Quiz/Review/Expand fire at once
  (Expand runs the /frontier skill to propose related topics you don't have yet),
  Log seeds the note with the topic. Those per-node buttons appear only when the
  cockpit is live.
- The server never writes knowledge, events, or scores itself — every write goes
  through a skill inside the headless session, the same sanctioned path as chat.
- localhost, single user. The headless turn runs with bypassPermissions so it
  can run the skills' own `brain` write commands unattended; the skills still
  enforce their evidence discipline in their own text.

## model import
Teach the knowledge model a learning resource (KME — see PLAN-KME.md).
```
brain model import ~/Downloads/course-syllabus.md --dry-run   # preview
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

## frontier add
Append confirmed frontier topics (the "unknown unknowns" the /frontier skill
proposes) to a goal's roadmap, then re-sync the registry and rebuild the graph
so they render as dashed nodes.
`brain frontier add --goal <goal> --spec <topics.json> [--max 8]`
- `--spec` is a JSON list of `{id, name, required_level, prereqs, aliases}`.
- Guards: skips ids already in the roadmap (dedup), skips an id that resolves to
  a different existing concept (collision), drops any alias that belongs to
  another concept (would silently un-dash a blind spot), and caps additions per
  call at `--max` (governor). Reports added / skipped / dropped for each.
- Extends an existing roadmap only; it won't create one from nothing (that's
  `/path`). Normally driven by the /frontier skill or the cockpit Expand button,
  not by hand.

## readiness
Explainable per-concept readiness for any track or goal. `brain readiness gcp-cdl`
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
Optional `--source <skill>` (e.g. `quiz`, `debrief`) tags the event so first-touch
detection can tell producing skills apart; written only when given.

## set-confidence
Manual override for SELF-assessed confidence: `brain set-confidence <note-id> --level <n>`
- Rewrites the note's `confidence` frontmatter and logs a set-confidence event.
  Touches only self/observed confidence; ai_confidence stays quiz-only. Use it to
  correct individual calls the enrichment heuristic got wrong (e.g. a prose-only
  note you actually wrote yourself).

## log-exposure
`brain log-exposure <topic>` — records a review event: bumps exposure_count and
last_reviewed on every note carrying the topic (refreshes decay). Used by /review.
Also appends one line to `events.jsonl`. Optional `--source <skill>` (e.g. `review`)
tags the event for first-touch detection; written only when given.

## first-touch
`brain first-touch <skill>` — prints a one-time explainer the first time a user
runs a skill, and nothing thereafter (`skill` ∈ quiz, review, ingest, path, debrief).
Read-only and self-healing: "first time" is derived from state the skill itself
changes on its first run — a source-tagged `assess`/`exposure` event (quiz, debrief,
review), a note with `source: import` (ingest), or an overlay under `ui/paths/`
(path) — so there is no separate "seen" flag to store. Each skill calls this at the
start of a run and prepends any output. Detection logic and the explainer copy both
live in `brain/first_touch.py`.
