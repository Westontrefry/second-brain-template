---
name: mnemonic
description: Save, mint, edit, or forget a memory hook (mnemonic) for a topic, and grow the mnemonic vocabulary. Use when the user says "remember it as X", asks for a mnemonic or memory trick, wants one changed or forgotten, or offers a character/place/media for the vocabulary. /quiz and /review call these procedures on a missed answer.
---

# /mnemonic — memory hooks, minted from a personal vocabulary

Mnemonics are aids, not evidence. They live in `mnemonics/` only — NEVER in
note bodies, and nothing here ever touches `confidence`, `ai_confidence`, or
`events.jsonl`. Storage: `mnemonics/scenes.yaml` (the saved one-liners) and
`mnemonics/vocabulary.yaml` (the symbol cast + usage ledger); record shapes
are documented in each file's header. Nothing is ever saved without the
user's explicit accept (or his own dictation) — the AI never saves one
unilaterally.

## Surface discipline (locked — do not widen)

- Scenes surface in **/review and /quiz only**. Not on the map, not in
  /query, not in receipts for other skills.
- In /quiz a scene may appear only AFTER the answer is classified — shown
  before, it taints the evidence the assessment is based on.
- Locked form: short text one-liners (acronym, rhyme, absurd-image
  sentence). No markdown bodies, no typed kinds.

## MINT — propose a scene (the offer-on-miss path)

1. Read `mnemonics/vocabulary.yaml`. Pick 1–2 symbols whose flavors fit the
   fact being encoded; prefer symbols with the shortest `used_for` ledger
   (fresh associations stick better than worn ones).
2. Write ONE vivid line that binds the symbol's global association to the
   specific fact (the `hook`). Absurd beats sensible; concrete beats
   abstract. An acronym or rhyme is fine when it is genuinely tighter.
3. If the vocabulary has no symbol that fits, say so and ask for one
   character, place, or piece of media he knows cold that feels right —
   save his answer per VOCABULARY below (`pack: personal`), then mint with
   it. One question at most; skip the ask mid-quiz and mint symbol-free.
4. Offer it plainly: **accept**, **edit** (his wording wins, verbatim), or
   **reject** (drop it, save nothing, don't re-offer the same fact this
   session).
5. On accept: append the record to `scenes.yaml` (topic, line, hook,
   symbols, origin, created) and add the topic to each used symbol's
   `used_for` ledger in `vocabulary.yaml`.

## DICTATE — "remember it as X"

He states the mnemonic himself, any session, any wording. Identify the
topic (ask only if genuinely ambiguous), save the line verbatim with
`origin: dictated`, and update the ledger for any vocabulary symbols his
line happens to use. No quality gate: his hook, his brain.

## SHOW — during /review and /quiz

When those skills reach their mnemonic step, look the topic up in
`scenes.yaml`. Present a scene as one line, marked as the memory hook, with
its `hook` named when the topic holds several. Never present a scene as
evidence of knowledge.

## FORGET / EDIT — "forget that mnemonic", "change it to…"

1. Find the scene by topic (plus line or hook when the topic holds
   several). If more than one matches, list them and ask which.
2. Forget: delete the record and remove the topic from each symbol's
   `used_for` (only if no other scene for that topic uses the symbol).
   Edit: replace `line` (and `hook` if it changed), verbatim.

## VOCABULARY — growing the cast

When he names a character/place/media plus what it means to him, append to
`vocabulary.yaml`: name, `pack: personal`, his associations as `flavors`,
empty `used_for`. Personal entries are private by definition — never shared
anywhere, never displayed outside his own sessions. (The shipped `starter`
pack stays public-domain-only; never add to it.)

**Finish every run that wrote anything (one command per tool call):**
1. No map data changed, so no `brain ingest`/`brain graph` — say nothing
   about refreshing.
2. Snapshot: `git add mnemonics/`, then
   `git commit -m "snapshot: mnemonic for <topic>"` (or "vocabulary: <name>" /
   "forgot mnemonic for <topic>"). No git? One line: snapshot skipped,
   mnemonic still saved.
3. Receipt (ux.md #2, copy rules: one fact per line, no em-dashes): what
   was saved/changed/forgotten, quoted; where it will surface ("you'll see
   it in your next review of <topic>"); "saved a local snapshot — nothing
   leaves your machine"; next action.
