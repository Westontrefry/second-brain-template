---
name: review
description: Run a spaced review session over weak-but-important or stale topics and record the exposure. Use when the user asks what to review, wants a study session, or wants to refresh fading knowledge.
---

# /review — deliberate review of what matters

1. Build the queue: `.venv/bin/python -m brain gaps -n 15` for weak-but-important,
   plus stale topics (evidenced but last_reviewed > 120 days — check `brain graph`
   output or note frontmatter). Rank: goal-critical weak topics first, then stale
   strong ones (they decay silently).
2. For each topic reviewed (2–4 per session is plenty):
   - Active recall first: ask him to explain it before showing anything.
   - Then fill gaps from his own notes (cite [[note-ids]]) — his words beat generic
     explanations. Add anything genuinely new only after.
   - Record the event: `.venv/bin/python -m brain log-exposure "<topic>"`
     (bumps exposure_count + last_reviewed → refreshes decay).
3. Review does NOT change confidence or ai_confidence. If his recall was notably
   strong or shaky, suggest `/quiz <topic>` for a formal assessment.
4. If the session surfaced new understanding, offer a `/log` to capture it.
