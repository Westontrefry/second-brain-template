---
name: context
description: Export the user's compact learning-state summary (brain context) for pasting into any AI assistant, optionally scoped to one track or goal. Use when he asks for his "context", wants to brief another AI/chat on what he knows, or asks "where do I stand" across goals.
---

# /context — portable learning-state export

1. Run the export (scope it if he named a track or goal):
   - `.venv/bin/python -m brain context`
   - `.venv/bin/python -m brain context --track <slug>` / `--goal <goal-id>`
   Unknown slug? The error lists what's available — show him the list.
2. Present the output VERBATIM in one yaml code block (it's designed to be
   copy-pasted whole — never trim the header comments; they make it
   self-explaining to whatever assistant receives it).
3. Below the block, add at most 2-3 sentences of orientation: the single most
   urgent gap and why (the `because` already says it — repeat, don't invent).
4. If he asks what to do about a gap, that's /review or /quiz territory —
   point there instead of improvising a study plan here.
5. Never edit the YAML by hand and never add note contents to it — topic names
   and states only is the privacy contract that makes it safe to paste around.
