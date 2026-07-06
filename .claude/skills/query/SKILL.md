---
name: query
description: Answer a question using the user's second-brain knowledge base, separating what he already knows (his notes, cited) from new advice. Use for questions about his studies, skills, projects, or when he asks "what do I know about X".
---

# /query — RAG answer over the knowledge base

**Fail soft (ux.md #8):** if search errors, returns nothing on a topic that
clearly has notes, or `brain status` would show pending changes, run
`.venv/bin/python -m brain ingest` yourself and retry once — then mention it
in one line ("synced the index first"). A deleted/stale index is a known
mode with a deterministic fix, never an error to show the user.

1. Search, more than once if the phrasing allows: run
   `.venv/bin/python -m brain search "<query>" -k 5` and, when useful, a second
   reformulation or `--domain`/`--goal` filtered pass.
2. Read the full top notes (not just snippets) — frontmatter matters: confidence,
   goals, dates tell you how solid and how fresh his knowledge is.
3. Answer in TWO clearly separated parts:

   **From your notes** — what he already knows, cited as [[note-id]], honest about
   its state ("noted at confidence 2 in September and not reviewed since" is signal,
   not filler). Include struggle markers his notes recorded.

   **Beyond your notes** — new information/advice from model knowledge, explicitly
   framed as not yet in his knowledge base.

4. If the answer surfaced something worth keeping, offer a one-line `/log` follow-up
   (don't auto-create notes from queries).
5. If search returns nothing relevant, say so plainly — never present model knowledge
   as if it came from his notes.
