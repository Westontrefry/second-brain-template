# UX principles — how interacting with the brain should feel

The measure of this system's UX is simple: **the daily loop (log → quiz →
look at the map) should cost one message each, and every action should
visibly pay off.** These principles are specific to this repo — its two
interaction planes (Claude Code chat + CLI), its file://-served UI, and
its local-first invariants. Feature work that touches the user surface
should check itself against this list the same way write-path code checks
itself against `docs/architecture.md`.

## 1. The conversation is the front door

The Claude Code session is the primary interface. The CLI is plumbing;
the graph UI is the reward surface. Every capability must be reachable by
*saying what you want* ("quiz me on graphs", "show my map", "what should
I study?") — the user should never need to memorize `python -m brain ...`
to use a feature. CLI commands exist for precision and scripting, not as
the required path. Corollary: when a doc or skill tells the user to do
something, it gives the conversational form first and the command as the
alternative.

## 2. Every action ends with a receipt

After any state change — a note added, an assessment recorded, an import
finished — the user is told **what changed, in product language**:

> Logged: *binary search trees* → note created, self-confidence 3.
> Your map updated — BST's dot is bigger. (Reload the map tab to see it.)

No silent writes, ever. This is the UX mirror of the `events.jsonl`
invariant: the system already never changes a score silently at the data
layer; the conversation layer must meet the same bar. A receipt names the
note/topic touched, the before → after of any number that moved, and the
one action available next.

**The receipt block (the standard every write-path skill ends with):**

- **Changed:** the notes/topics touched, by id.
- **Numbers:** every score that moved, before → after, with claimed
  (self-rated) and proven (assessed) labeled as exactly that.
- **Fresh:** "map data refreshed — reload the tab" (the skill already ran
  the regeneration itself; see #3).
- **Saved:** "saved a local snapshot — nothing leaves your machine" (see
  #6; if git is unavailable, one line saying the snapshot was skipped).
- **Next:** the single most useful next action, stated conversationally.

Terse is fine — five short lines beat a paragraph. What's not fine is
omitting a line whose event happened, or padding with lines whose event
didn't.

## 3. The reward loop closes in one step

Evidence lands → the map reflects it, without the user knowing that
`brain graph` exists. Any skill that writes also refreshes the derived
views it affects, and its receipt says so. The moment a dot turns green
is the entire emotional payoff of this product; it must never be gated
behind "run this regeneration command you've never heard of."
(Constraint honored: the UI is a file:// page and cannot poll — the
refresh is data-regeneration + "reload the tab," not live push.)

## 4. Zero-decision capture

Capturing knowledge must never interrogate the user. `/log` takes one
sentence and infers the rest (domain, topics, confidence, goal links) —
defaults + AI judgment, correctable later in one line (`brain
set-confidence ...`). If a skill needs a decision mid-capture, the
default is chosen and *stated in the receipt*, not asked. Asking is
reserved for destructive or irreversible calls. A capture that costs
three questions stops happening by week two.

## 5. Explain at the point of confusion, not in the docs

Empty states, first runs, and errors are the UI. Each such surface says
what's going on and offers the single next step:

- Empty map → "No notes yet. Say `/log` + one sentence about anything
  you studied this week, then come back."
- Stale index after edits → the skill runs `brain ingest` itself and
  mentions it did (fail-soft, see #8).
- First `ingest` → "Downloading the embedding model (~90MB, one time,
  stays on your machine)…"

Docs are for depth. If a new user *needs* a doc to survive the first
session, the surface that stranded them is the bug.

## 6. Local-first must be legible, not just true

The system's strongest promise — everything on your machine — is
currently invisible, which reads as uncertainty ("wait, does this push
to GitHub?"). Make the boundary explicit wherever data moves:

- git commits are described as **local snapshots** ("saved a snapshot —
  nothing leaves your machine").
- GitHub/remotes are an opt-in *backup* story with their own explicit
  step, never an implied requirement. The word "push" appears only in
  backup contexts.
- Anything that ever *would* leave the machine states it before doing it.

## 7. Guided when new, invisible when practiced

A first session gets a tour: pick a goal, log one thing, take a
two-question quiz, watch the map. A hundredth session gets zero
ceremony — the loop runs on muscle memory and receipts stay terse.
Guidance is triggered by *state* (empty brain, no goals, never quizzed),
not by time, and every guided step is skippable. Never make the
practiced user pay for the new user's onboarding.

## 8. Fail soft, self-heal, then explain

The known failure modes (stale index, missing model, unbuilt graph data,
malformed note) each have a deterministic fix — so skills apply the fix
and report it, rather than surfacing an error the user must triage.
What can't be auto-fixed is explained in product language with the one
command that fixes it. The debugging-playbook is for maintainers; users
should never need it.

## 9. Friction budget: count messages-to-outcome

The unit of friction is one user message (or one command). Budget for
every core outcome, enforced when reviewing UX changes:

| Outcome | Budget |
|---|---|
| Capture a study session | 1 message |
| Start a quiz | 1 message |
| See the map / dashboard | 1 message or 1 click |
| Ask what to study next | 1 message |
| Import old notes | 1 message + confirmations only for destructive calls |
| First-ever session to first green-able dot | one guided conversation |

A change that adds a step to any of these needs a reason recorded in the
docs. (Deliberate exception: /quiz *answers* take as many messages as
there are questions — that's the product, not friction.)

## 10. Convenience never bends the trust invariants

Auto-actions stay inside the sanctioned write paths: nothing auto-sets
`ai_confidence` outside `brain assess`; enrichment's frontmatter+Related
exception stays the only body-adjacent edit; receipts distinguish
*claimed* (self-rated) from *proven* (assessed) exactly like the data
model does. Frictionless and honest are both requirements; when they
conflict, honest wins and the friction gets redesigned, not the honesty.

---

*Terminology per [glossary.md](glossary.md); user-facing capability changes
update [demo-guide.md](demo-guide.md) in the same commit, per the working
rules.*
