---
name: review
description: Run a spaced review session over weak-but-important or stale topics and record the exposure. Use when the user asks what to review, wants a study session, or wants to refresh fading knowledge.
---

# /review — deliberate review of what matters

**First-touch (run this first):** `.venv/bin/python -m brain first-touch review`. If it
prints a paragraph, this is the user's first review — open your reply with that text
verbatim, then continue. If it prints nothing, skip it and proceed.

1. Build the queue: `.venv/bin/python -m brain gaps -n 15` for weak-but-important,
   plus stale topics (evidenced but last_reviewed > 120 days — check `brain graph`
   output or note frontmatter). Rank: goal-critical weak topics first, then stale
   strong ones (they decay silently).
2. For each topic reviewed (2–4 per session is plenty):
   - Active recall first: ask him to explain it before showing anything.
   - Then fill gaps from his own notes (cite [[note-ids]]) — his words beat generic
     explanations. Add anything genuinely new only after.
   - Record the event: `.venv/bin/python -m brain log-exposure "<topic>" --source review`
     (bumps exposure_count + last_reviewed → refreshes decay; `--source review` retires
     the first-touch explainer after this run).
3. Review does NOT change confidence or ai_confidence. If his recall was notably
   strong or shaky, suggest `/quiz <topic>` for a formal assessment.
4. If the session surfaced new understanding, offer a `/log` to capture it.

**Finish every run (ux.md #2/#3/#6 — one command per tool call):**
1. `.venv/bin/python -m brain ingest`, then `.venv/bin/python -m brain graph`.
2. Snapshot: `git add` the touched notes + `events.jsonl`, then
   `git commit -m "snapshot: review: <topics>"`. No git? One line: snapshot
   skipped, review still recorded.
3. End with the receipt block (docs/ux.md #2): topics reviewed with exposure
   counts bumped (no confidence numbers moved — say so); "map data refreshed —
   reload the tab"; "saved a local snapshot — nothing leaves your machine";
   next action (a /quiz or /log when the session earned one).
