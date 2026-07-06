---
name: quiz
description: Quiz the user on a topic at the boundary of his evidence, classify his answers against the depth rubric, and record ai_confidence with receipts. Use when he asks to be quizzed/tested or wants his knowledge assessed.
---

# /quiz — assessment at the evidence boundary

The only workflow that produces ai_confidence. Never guess a level without answers.

**First-touch (run this first):** `.venv/bin/python -m brain first-touch quiz`. If it
prints a paragraph, this is the user's first quiz — open your reply with that text
verbatim, then continue. If it prints nothing, skip it and proceed.

1. Pick the target: his choice, or the highest-value candidate from
   `.venv/bin/python -m brain gaps` (weak-but-important beats unknown-and-optional).
2. Read the evidence: `brain search "<topic>" -k 5`, then the full matching notes.
   Read `rubrics/depth.yaml`. Establish the currently evidenced level and what's thin.
3. Generate 3–5 questions targeting ONE level above evidenced, aimed at the thin
   spots (e.g. evidenced 2 from definitions → ask application questions; struggle
   markers in notes → probe exactly those). Ask one at a time; no reference material.
4. Classify each answer against the rubric, quoting the part of his answer that
   justifies the classification. Be strict: a correct-but-recited answer is level 2,
   not 3; applying it to a novel scenario is 3+.
   Mnemonic timing (locked): if `mnemonics/scenes.yaml` holds a scene for
   the topic, it may be shown only AFTER the answer is classified — never with or
   before a question, or it taints the evidence. On a missed question, showing the
   existing scene alongside the correction is the right moment.
5. Decide the overall demonstrated level (typically the level he answered soundly at,
   not the best single flash).
   Then, if any questions were missed: offer a mnemonic per the /mnemonic skill's
   MINT procedure — one compact offer covering the missed facts, not one per miss.
   Accept / edit / reject before anything is saved; save-on-accept writes
   `mnemonics/scenes.yaml` only (never the session note, never evidence fields).
   A rejection costs one line and the quiz moves on.
6. Create the session note — the clickable evidence artifact, same shape as
   /debrief's (U3 quiz-artifact parity; no extra user step):
   ```
   .venv/bin/python -m brain add --domain <the topic's domain> \
     --title "Quiz <date>: <topic>" --topics "<topic + subtopics touched>" \
     --goals "<goals the topic serves>" --source quiz \
     --confidence <demonstrated level, capped at 3> --importance 3 \
     --body "<each question, his answer, its classification with the quote,
             then the overall call>"
   ```
   Never quiz or assess demo content (`source: demo` notes stay unassessed).
7. Record the assessment citing the session note first, then the existing notes
   that carry the topic:
   ```
   .venv/bin/python -m brain assess "<topic>" --level <n> \
     --rationale "<per-question classifications with quotes, dated quiz>" \
     --evidence <session-note-id>,<existing-note-ids> --source quiz
   ```
   (`--source quiz` tags the event so the first-touch explainer retires after this run.)
**Finish every run (ux.md #2/#3/#6 — one command per tool call):**
1. `.venv/bin/python -m brain ingest`, then `.venv/bin/python -m brain graph`.
2. Snapshot: `git add` the touched notes + `events.jsonl` (+ `mnemonics/` if a
   scene was accepted), then
   `git commit -m "snapshot: quiz session on <topic>"`. No git? One line:
   snapshot skipped, results still saved.
3. End with the receipt block (docs/ux.md #2): session note id + topic +
   evidence note ids; claimed (self-confidence) vs proven (ai_confidence)
   before → after, and whether a divergence appeared; what would raise the
   level; "map data refreshed — reload the tab"; "saved a local snapshot —
   nothing leaves your machine"; next action.
