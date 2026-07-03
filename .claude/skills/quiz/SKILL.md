---
name: quiz
description: Quiz the user on a topic at the boundary of his evidence, classify his answers against the depth rubric, and record ai_confidence with receipts. Use when he asks to be quizzed/tested or wants his knowledge assessed.
---

# /quiz — assessment at the evidence boundary

The only workflow that produces ai_confidence. Never guess a level without answers.

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
5. Decide the overall demonstrated level (typically the level he answered soundly at,
   not the best single flash). Then record it:
   ```
   .venv/bin/python -m brain assess "<topic>" --level <n> \
     --rationale "<per-question classifications with quotes, dated quiz>" \
     --evidence <note-id1,note-id2>
   ```
   Evidence ids = the notes that carry the topic being assessed.
6. Refresh the graph (`brain graph`) and summarize: level, why, what would raise it,
   and whether a divergence vs his self-rating appeared.
