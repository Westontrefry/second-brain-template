---
name: debrief
description: Ingest a mock-interview debrief (from /interview-pack voice sessions or any assessed practice) into the knowledge base — session note + ai_confidence assessments with receipts. Use when the user pastes a debrief block or reports how an interview/practice session went.
---

# /debrief — record verbal assessment results

Input: the interviewer's `=== DEBRIEF ===` block (preferred) or the user's own account.

**First-touch (run this first):** `.venv/bin/python -m brain first-touch debrief`. If it
prints a paragraph, this is the user's first debrief — open your reply with that text
verbatim, then continue. If it prints nothing, skip it and proceed.

1. Sanity-check before trusting it: levels must be plausible against the rubric and
   the justifications must contain actual quoted answers. If a claimed level has no
   supporting quote, downgrade to what the quote supports and say so. Map topic names
   onto the existing vocabulary (check current topics; don't mint near-duplicates).
2. Create the session note — this is the evidence artifact:
   ```
   .venv/bin/python -m brain add --domain career --title "Mock interview <date> <focus>" \
     --topics "<all covered topics>" --goals "dsa-interviews,job-readiness" \
     --source quiz --confidence <his own feel, ask if unclear> --importance 4 \
     --body "<overall summary + per-topic justifications with quotes + weak spots>"
   ```
3. For each debriefed topic, record the assessment against the session note plus any
   existing notes carrying that topic:
   ```
   .venv/bin/python -m brain assess "<topic>" --level <demonstrated_level> \
     --rationale "verbal mock interview <date>: <quoted justification>" \
     --evidence <session-note-id>[,<existing-note-ids>] --source debrief
   ```
   (`--source debrief` keeps this distinct from a /quiz event, so each keeps its own
   first-touch. The session note's own `--source quiz` above is unrelated to this tag.)
4. Verbal-under-pressure is prime level-4 evidence — but never exceed what the
   quotes support.

**Finish every run (ux.md #2/#3/#6 — one command per tool call):**
1. `.venv/bin/python -m brain ingest`, then `.venv/bin/python -m brain graph`.
2. Snapshot: `git add` the session note + touched notes + `events.jsonl`, then
   `git commit -m "snapshot: debrief: <focus> <date>"`. No git? One line:
   snapshot skipped, results still saved.
3. End with the receipt block (docs/ux.md #2): session note id; per-topic
   levels recorded (claimed vs proven, divergences called out); weak spots
   worth a /log or /review, and whether the pathway overlay needs a /path
   rerun; "map data refreshed — reload the tab"; "saved a local snapshot —
   nothing leaves your machine"; next action.
