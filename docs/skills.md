# Skills — the conversational layer

Skills live in `.claude/skills/` and run inside Claude Code sessions opened in this
repo. They are the reasoning layer ($0 — covered by subscription); the CLI is the
mechanical layer. Skills never write to `knowledge/` directly except the sanctioned
enrichment edit (see [architecture.md](architecture.md) invariant 2).

**First-touch explainers:** /quiz, /review, /ingest, /path, and /debrief each start
by running `brain first-touch <skill>` — the first time a user ever runs the skill it
prints a one-paragraph explainer the skill prepends to its reply, then never again.
Detection is read-only, derived from state the skill itself changes on its first run
(source-tagged events, an imported note, a pathway overlay), so there is no "seen"
flag anywhere; wiping the data honestly resets the guidance (ux.md #5, #7). The
explainer never asks a question or adds a message — the skill proceeds in the same
turn (ux.md #4, #9).

**Skills fail soft (ux.md #8):** the known failure modes — stale or missing
index (`brain.db` is disposable), missing map data — have deterministic fixes
(`brain ingest`, `brain graph`), so every skill applies the fix itself and
mentions it in one line rather than surfacing an error. `brain doctor` exists
for whatever can't be self-healed; users should never meet a traceback for a
known mode.

**Every write-path skill ends the same way** (/log, /quiz, /review, /debrief,
/ingest, /path): it refreshes the derived views itself (`brain ingest` +
`brain graph` — you never run regeneration), commits a labeled **local
snapshot** ("nothing leaves your machine"; skipped with a note if git is
absent), and closes with the receipt block defined in [ux.md](ux.md) #2 —
what changed, every number's before → after with claimed vs proven labeled,
"map data refreshed — reload the tab", and the one next action.

## /start — guided first-run tour (built)
Offered automatically when the brain is empty, goal-less, or never quizzed
(state-triggered, every step skippable). One conversation: pick a goal
(shipped roadmaps first, free text as the escape), log one sentence, take a
two-question micro-quiz on that same note, then read the map on your own data.
Forks to /ingest if you have old notes; offers `brain demo --install` if you
don't, so the map is never empty. The micro-quiz always targets your own first
note, never demo content. Completing the map step retires the Map coach-mark
(and only that one) — the tour just taught it.

## /log — capture (built)
Say what you studied/built/struggled with, even one sentence. Creates a validated,
goal-linked note via `brain add`. Infers self-confidence from your language and
preserves struggle markers (they're negative evidence for gap analysis).

## /ingest — bulk import + enrichment (built)
Point it at an export folder (Joplin first-class). Runs `brain import`, then the
enrichment pass over imported notes: real topics, goal links, importance, plus two
sanctioned judgments — confidence 1 (awareness) vs 2 (engaged) from the note body,
and a trailing `## Related` wikilinks section (the only body edit). Never touches
ai_confidence or any other body content.

## /query — RAG answers (built)
Ask anything. Searches the knowledge base and answers in two sections:
**From your notes** (cited [[note-ids]], honest about confidence and freshness) and
**Beyond your notes** (new advice, clearly framed as not yet yours).

## /quiz — assessment (built)
Generates questions at the boundary of your evidence (one rubric level above what's
evidenced, targeting thin spots). Classifies answers against `rubrics/depth.yaml`
with quotes and writes ai_confidence via `brain assess` — the only path that sets it.
Every quiz also leaves a session note (`source: quiz` — questions, answers,
classifications, same shape as /debrief's) cited as evidence in the assessment, so
each score has a clickable artifact on the map. No extra step; it just happens.
Missed a question? Any saved mnemonic appears with the correction (only ever after
your answer is classified), and the AI offers to mint a new one (see /mnemonic).

## /review — spaced review (built)
Surfaces weak-but-important topics (plus stale ones), drills them with active recall
using your own notes, and records the event via `brain log-exposure`. Never changes
confidence scores — it routes to /quiz for that. If a topic has a saved mnemonic,
it's the recall aid: offered as the hint when you stall, restated after recall.

## /mnemonic — memory hooks (built)
Short one-liner mnemonics, minted from a personal vocabulary of characters and
places (`mnemonics/vocabulary.yaml` — ships a public-domain starter cast; anything
you add is `pack: personal` and never leaves your machine). Nothing saves without
your accept: on a missed quiz/review answer the AI offers one (accept / edit /
reject), or you dictate your own anytime ("remember it as…"). "Forget that
mnemonic" removes it. Scenes live in `mnemonics/scenes.yaml` only — never in note
bodies — and surface only in /review and in /quiz after an answer is classified
(never before, so evidence stays untainted). Aids, not evidence: mnemonics never
touch confidence, ai_confidence, or events.

## /interview-pack — verbal mock interview brief (built)
Generates a copy-paste block for a Claude voice-mode session: targeted questions at
your evidence boundary, a compressed rubric, interviewer role instructions, and the
mandatory structured `=== DEBRIEF ===` format the interviewer emits at the end.

## /debrief — record verbal assessment results (built)
Paste the debrief block back; it sanity-checks levels against quoted answers, creates
a session note (`source: quiz` — the evidence artifact, so even never-noted topics
have somewhere to land), records assessments via `brain assess`, and reports
divergences and follow-ups.

## /path — pathway compiler (built)
Give it a free-text objective ("FAANG interview prep"); it compiles a route from
your knowledge + roadmaps into `ui/paths/<slug>.json` — ordered nodes with strength
statuses plus a suggestions array — which the UI renders as a highlighted route with
the suggestions tab alongside.

## /frontier — expand the map beyond the known radius (built)
Proposes relevant topics OUTSIDE your current coverage (the unknown unknowns) and,
once you confirm, appends them to a roadmap as dashed nodes via `brain frontier add`.
Two modes: deepen (sub-topics of a node) and broaden (adjacent siblings the map
hasn't touched). Also the engine behind the cockpit's per-node Expand button.

## /context — learning-state export (built)
Wraps `brain context`: a one-screen YAML summary of tracks, readiness, and top
gaps, ready to paste into any AI assistant. Scope with a track or goal
(`/context gcp-cdl`). Topic names and states only — no note contents.

## /tag — curated topic lenses (built)
Creates and maintains the tags in `tags.yaml` — the groupings the map's search
and Tag filter use to connect topics that share a theme but not vocabulary
("tag my AWS stuff", "add kubernetes to the cloud tag"). The AI proposes members
from the real on-map topic ids (judgment for entity/brand relations,
`brain search` for recall), nothing is written without your confirm, and
`brain graph` rebuilds the UI data. Also does check-ups: unmatched topic ids
and new topics that plausibly belong to an existing tag.

