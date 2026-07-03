---
name: debrief
description: Ingest a mock-interview debrief (from /interview-pack voice sessions or any assessed practice) into the knowledge base — session note + ai_confidence assessments with receipts. Use when the user pastes a debrief block or reports how an interview/practice session went.
---

# /debrief — record verbal assessment results

Input: the interviewer's `=== DEBRIEF ===` block (preferred) or the user's own account.

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
     --evidence <session-note-id>[,<existing-note-ids>]
   ```
4. `brain graph`, then summarize: levels recorded, divergences vs his self-ratings,
   weak spots worth a /log or targeted /review, and whether the active pathway
   overlay should be regenerated (/path) to reflect new statuses.
5. Verbal-under-pressure is prime level-4 evidence — but never exceed what the
   quotes support.
