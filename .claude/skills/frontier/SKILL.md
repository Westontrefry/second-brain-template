---
name: frontier
description: Expand the knowledge map beyond what the user already knows — propose relevant topics OUTSIDE their current coverage (unknown unknowns) and add the confirmed ones as dashed roadmap nodes. Use when they want to grow the map around a topic or goal ("what don't I know about X", "expand the frontier on graphs", "grow my map around system design"), or when the cockpit's per-node Expand button fires.
---

# /frontier — expand the map beyond the known radius

A node renders **dashed** ("you don't know this yet") when a roadmap names a
topic that matches zero notes. So expanding the frontier = proposing genuinely
relevant topics the user has no evidence for and appending them to a roadmap.
The reasoning (what a *complete* version of a domain contains) is world
knowledge — that's this skill's job; the guarded write is `brain frontier add`.

Two modes, ask which unless the request implies one:
- **deepen** — sub-topics *inside* the selected node (system design → caching,
  sharding, queues).
- **broaden** — adjacent siblings at the same altitude the user hasn't touched
  (graphs → union-find, network flow, A*).

## Procedure

1. **Fix the target and its home.** Identify the node/topic or goal, and the
   mode. A frontier node must attach to an existing roadmap, so pick the goal
   whose roadmap it extends (a topic may serve several — pick the best fit; the
   graph shows convergence anyway). Frontier expansion *extends* a path; it does
   not create one from nothing (that's `/path`). If the goal has no roadmap yet,
   say so and offer to draft one first.

2. **Load what already exists — never propose a duplicate.** Read the target
   `goals/roadmaps/<goal>.yaml`, the current nodes via
   `.venv/bin/python -m brain graph` + `ui/graph.json`, and the concept
   vocabulary in `model/concepts.yaml`. The frontier is the *complement*: the
   complete domain minus everything already covered (roadmap topic ids, concept
   ids/aliases, note topics).

3. **Enumerate, then subtract.** From world knowledge, list what a thorough
   version of the target contains. Drop anything already covered. What remains is
   the candidate frontier — the unknown unknowns.

4. **Shape each candidate:**
   - `id`: kebab-case slug. `name`: display label. `required_level`: per
     `rubrics/depth.yaml` and the goal's norms (interview canon → 4; breadth or
     conceptual → 2–3).
   - `prereqs`: attach to existing node ids so the branch structure holds.
   - `aliases`: **specific** vocabulary only. Never generic words that would
     collide with unrelated evidence — e.g. bare `networking` resolves onto
     cloud/OS networking notes and silently un-dashes a real blind spot. Prefer
     `recruiter outreach`, `informational interview` over `networking`.
   - one-line **rationale**: why it belongs on this path.

5. **Confirm — never auto-write.** Show the candidates with rationale and let the
   user pick. Keep it a route, not an inventory: ≤ 8 per run (the command caps
   too). Proposals are training-time world knowledge, so for fast-moving areas
   (cloud product names) flag lower confidence and lean on their confirmation.

6. **Write via the guarded command.** Put the confirmed topics in a JSON spec —
   a list of `{id, name, required_level, prereqs, aliases}` — and run:
   `.venv/bin/python -m brain frontier add --goal <goal> --spec <file.json>`
   It dedups against the roadmap, drops any alias that belongs to an existing
   concept, re-syncs `model/concepts.yaml`, and rebuilds the graph. Report its
   `added` / `skipped` / `dropped alias` lines faithfully — a dropped alias or
   skip is signal, not an error to hide.

**Finish every run (docs/ux.md #2 — one command per tool call):**
1. The command already rebuilt the graph; no notes were written, so no ingest.
2. Snapshot: `git add` the changed `goals/roadmaps/<goal>.yaml` +
   `model/concepts.yaml`, then
   `git commit -m "frontier: expand <goal> around <target>"`. No git? One line:
   snapshot skipped, nodes still saved.
3. Receipt: what was added (with the new dashed-node count from the command),
   what was skipped and why, "map data refreshed — open brain ui to see the new
   dashed nodes"; next action = study the highest-leverage new gap (it now shows
   in `brain gaps`).
