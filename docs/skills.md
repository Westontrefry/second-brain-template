# Skills — the conversational layer

Skills live in `.claude/skills/` and run inside Claude Code sessions opened in this
repo. They are the reasoning layer ($0 — covered by subscription); the CLI is the
mechanical layer. Skills never write to `knowledge/` directly except the sanctioned
enrichment edit (see [architecture.md](architecture.md) invariant 2).

## /log — capture (built)
Say what you studied/built/struggled with, even one sentence. Creates a validated,
goal-linked note via `brain add`. Infers self-confidence from your language and
preserves struggle markers (they're negative evidence for gap analysis).

## /ingest — bulk import + enrichment (built)
Point it at an export folder (Joplin first-class). Runs `brain import`, then the
enrichment pass over imported notes: real topics, goal links, importance. Never
touches confidence, ai_confidence, or note bodies.

## /query — RAG answers (built)
Ask anything. Searches the knowledge base and answers in two sections:
**From your notes** (cited [[note-ids]], honest about confidence and freshness) and
**Beyond your notes** (new advice, clearly framed as not yet yours).

## /quiz — assessment (built)
Generates questions at the boundary of your evidence (one rubric level above what's
evidenced, targeting thin spots). Classifies answers against `rubrics/depth.yaml`
with quotes and writes ai_confidence via `brain assess` — the only path that sets it.

## /review — spaced review (built)
Surfaces weak-but-important topics (plus stale ones), drills them with active recall
using your own notes, and records the event via `brain log-exposure`. Never changes
confidence scores — it routes to /quiz for that.

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
