---
name: interview-pack
description: Generate a mock-interview session brief to run in Claude voice mode (or with any AI interviewer) — targeted questions, grading rubric, and a structured debrief format the interviewer must emit. Use when the user wants to practice interviewing verbally.
---

# /interview-pack — brief for a verbal mock interview

Produces a self-contained prompt the user pastes into a Claude app voice conversation.
The voice AI does the interviewing; the debrief comes back via /debrief.

1. Target selection: `.venv/bin/python -m brain gaps --goal dsa-interviews -n 10`
   (or the goal/objective he names; check ui/paths/ overlays for an active route).
   Pick 2–3 technical topics at the evidence boundary + 1–2 behavioral prompts
   (search his notes for logged STAR stories to probe).
2. Read `rubrics/depth.yaml` and the relevant notes so questions target thin spots
   (probe struggle markers verbatim).
3. Output ONE copy-paste block containing:
   - Role instructions: act as a rigorous but fair interviewer; one question at a
     time; push with follow-ups ("why", "what breaks", "tradeoff vs X"); time-box
     answers; no teaching mid-session.
   - The question set with intended rubric level per question.
   - A compressed rubric (level names + one-line indicators, from depth.yaml).
   - The MANDATORY debrief format to emit at session end, exactly:
     ```
     === DEBRIEF ===
     session: <one-line description>
     date: <today>
     topics:
       - topic: <lowercase topic>
         demonstrated_level: <0-5>
         justification: "<what he said, quoted, and which rubric indicator it met>"
         weak_spots: "<specific misses>"
     overall: "<2-3 sentence summary>"
     === END DEBRIEF ===
     ```
   - Instruction: be strict — recited definitions are level 2; only applied/justified
     answers under pressure earn 4.
4. Tell the user: run the session in voice mode, then bring the debrief block back and
   run /debrief.
