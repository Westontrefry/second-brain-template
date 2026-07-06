---
name: log
description: Capture a study session, project work, or learning moment as a structured note in the second-brain knowledge base. Use when the user describes something he studied, built, struggled with, or learned — even one sentence.
---

# /log — capture a study session

Turn the user's freeform account into a validated note. The CLI is the only write path.

1. Read `config.yaml` (domains, sources) and `goals/goals.yaml` (goal ids).
2. Check for related notes: `.venv/bin/python -m brain search "<key phrases>" -k 3`.
   Sessions are events, so still create a new dated note — but reference related
   existing notes in the body as `[[note-id]]` so the graph gets the edge.
3. Draft the note:
   - **domain**: best fit from config domains.
   - **topics**: 2–5 lowercase tags. Reuse the existing vocabulary where possible
     (`grep -rh "^topics:" knowledge/ | sort -u` or check recent notes) — topic
     consistency is what makes the graph connect.
   - **goals**: only goals the content genuinely advances (empty is fine).
   - **confidence** (SELF-assessed, 1–5): infer from his language — "struggled",
     "confused", "kept getting it wrong" → 2; "got it working", "makes sense" → 3;
     "comfortable", "explained it to someone" → 4. Unsure → pick the lower value.
   - **importance** (1–5): how much this matters to the goals it touches.
   - **body**: his account in his voice. Preserve struggle markers verbatim (negative
     evidence drives gap analysis) and concrete application details (they are the
     evidence for ai_confidence later). Do not polish away specifics.
4. Create it (title becomes the id slug):
   ```
   .venv/bin/python -m brain add --domain <d> --title "<title>" \
     --topics "<a,b,c>" --goals "<g1,g2>" --source study-session \
     --confidence <n> --importance <n> --body "<body>"
   ```
5. If `brain add` rejects the note, fix the draft and retry — never write files
   into `knowledge/` directly.

**Finish every run (ux.md #2/#3/#6 — one command per tool call):**
1. `.venv/bin/python -m brain ingest`, then `.venv/bin/python -m brain graph` —
   the user never learns regeneration exists.
2. Snapshot: `git add` the new note, then
   `git commit -m "snapshot: log: <note title>"`. No git? One line: snapshot
   skipped, notes still saved.
3. End with the receipt block (docs/ux.md #2): the note id + topics it landed
   with; self-confidence stated as claimed, not proven; "map data refreshed —
   reload the tab"; "saved a local snapshot — nothing leaves your machine";
   next action (usually: quiz this topic when you're ready to prove it).
