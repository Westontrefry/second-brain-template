---
name: start
description: Guided first-run tour — pick a goal, log a first note, take a two-question micro-quiz, read the map on the user's own data. Offer when the brain is empty (no user-authored notes), has no goals, or has never been quizzed; every step is skippable.
---

# /start — the guided A→Z

State-triggered, never time-triggered (ux.md #7): offer it when `knowledge/` has
no user-authored notes (`source: demo` doesn't count), no goals exist, or no quiz
has ever run. Offer, don't launch — run it when the user says yes or asks for it.

Every step is skippable ("skip" moves on, "stop" ends cleanly, nothing nags
later). One user message per step is the budget (ux.md #9). Tour copy follows the
locked Arc A rules: bold lead, one fact per line, readable in two seconds, no
em-dashes.

**Step 0 — orient + the one fork question.**
- **This is your second brain.** Notes go in, an honest map of what you actually
  know comes out.
- Everything stays on this machine.
Then ask the single fork: "Do you have years of notes somewhere already (Joplin,
Obsidian, plain markdown)?"
- Yes → take the **import branch** below.
- No → offer the demo pack so the map has shape by step 4:
  `.venv/bin/brain demo --install`. Say what it is in one line each: synthetic
  examples, clearly marked, removable without trace (`brain demo --remove`).

**Step 1 — goal.** "What are you working toward?"
- Offer the shipped roadmaps as picks first (list `goals/roadmaps/*.yaml` by
  title), free text as the escape hatch (templates-first, locked decision 8).
- Template pick: ensure the goal exists in `goals/goals.yaml` (add the entry if
  this clone doesn't have it) so the roadmap drives gaps immediately.
- Free text: append a goal to `goals/goals.yaml` (slug id, title, priority 3,
  deadline only if they said one). Be honest in the receipt: goal saved, gap
  analysis unlocks once a roadmap exists, and /path can build a route anytime.

**Step 2 — first capture.** "Tell me one sentence about anything you studied this
week." Run the full /log path on it (search for related notes, draft, `brain
add`). Receipt: note id, domain, self-confidence and what that number means
(claimed, not yet proven), and that it just landed on the map.

**Step 3 — first proof.** A two-question micro-quiz on the step-2 note's topic.
The target is the user's own first note, NEVER demo content (locked: demo notes
stay unassessed so removal leaves no trace). Follow the /quiz skill: questions one
level above the evidence, classify answers with quotes against `rubrics/depth.yaml`,
record with `brain assess ... --source quiz`. Receipt must show claimed
(self-confidence) vs proven (ai_confidence) side by side — that contrast is the
product's honesty in one line.

**Step 4 — the map.** Run `.venv/bin/brain ui --toured`. (`--toured` retires the
Map view's coach-mark, because this step teaches the same ground seconds earlier.
Locked supersession rule: the map hint is the ONLY one the tour may retire; every
other view and skill keeps its own first touch.) Explain on THEIR data:
- find the step-2 note's topic: dot size = how much of their knowledge lives there
- its color = the rung they just earned (or didn't) in step 3
- dashed circles = what their goal still needs
Don't walk the other views; their coach-marks cover that ground on first visit.

**Step 5 — the loop card.** Close with the daily rhythm, one line each:
- log when you learn (one sentence is enough)
- quiz sometimes (quizzes turn claimed into proven)
- glance at the map (green is earned, never given)
- your old notes, whenever you're ready: /ingest
- everything saved so far is local; nothing leaves this machine
If demo notes are installed, add: when your own notes fill the map in,
`brain demo --remove` clears the examples without a trace.

**Import branch (from step 0):** hand off to /ingest with its own confirmations
(dry-run first, per-folder domains, park unclear mappings). When the import
lands, rejoin at step 1 — step 4 then shows their real history and the demo pack
is never offered.

Hard rules: never assess demo content; never write into `knowledge/` except via
`brain add`/`brain import`; never re-run the tour unprompted once the brain has
user notes, a goal, and a quiz event.
