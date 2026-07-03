# Second Brain — the friendly tour

*A plain-English guide for showing this to someone new. No tech background
needed. (Maintained as features are added — see the working rules.)*

## What is this thing?

It's a second brain: a private study companion that lives entirely on your
computer. Every time you learn something, you tell it. Over time it builds a
**map of everything you know** — and, more importantly, it's honest about how
*well* you know each thing and what you should study next.

Think of it like a fitness tracker, but for knowledge. A step counter doesn't
just say "you walked" — it says how much, and whether you're hitting your goal.
This does that for learning.

Three things make it different from a notes app:

1. **It knows your goals.** You tell it what you're working toward (a
   certification, interviews, a degree) and it constantly compares what you
   know against what those goals require.
2. **It doesn't take your word for it.** You can *say* you know something
   (self-confidence), but the score that really counts comes from being
   quizzed. The gap between "how confident I feel" and "how I actually
   performed" is one of the most useful things it shows you.
3. **Everything stays on your machine.** Your notes are ordinary files in a
   folder. Nothing is uploaded anywhere. It costs $0 to run.

## The two ways you use it

- **Talk to it** — you open the folder in Claude Code (an AI assistant that
  runs in a window on your computer) and just… tell it things or ask it
  things. The commands below that start with a `/` are typed into that chat.
- **Look at it** — one command opens the visual side: your knowledge map and
  dashboard, in your web browser.

---

## Capability tour

### 1. See your knowledge map
**What it is:** every topic you've ever taken a note on, drawn as a dot.
Bigger dot = more of your knowledge lives there. Green = strong, orange =
weak, dashed outline = something your goals need that you haven't touched yet.
Lines connect topics that show up together.

**How:** in the chat, type:
```
python -m brain ui
```
Your browser opens the map. Click any dot to zoom into its neighborhood and
see the actual notes behind it. Use the **Goal** dropdown to show only what
matters for one goal, and tick **show gaps** to light up what's missing.

### 2. Check the dashboard
**What it is:** click **dashboard →** in the map's header. Two pictures:

- **Readiness radar** — one glance answers *"am I ready for this goal?"* The
  green shape is what you know; the dashed outline is what the goal requires.
  Wherever green fills the outline, you're ready. Dents = study there.
- **Confidence divergence** — a dot for each topic that's been quiz-tested,
  comparing how confident you *felt* vs how you *performed*. Dots below the
  line = overconfident (feelings ahead of evidence). Above = you're better
  than you think.

### 3. Save something you just learned
**What it is:** the daily habit. Studied something? Struggled with something?
Tell it in one sentence — it files a proper note for you.

**How:** in the chat:
```
/log spent an hour on binary search trees, insertion finally makes sense
but deleting nodes with two children still confuses me
```
That's it. It records what you learned, how solid it felt, and even keeps the
"still confuses me" part — the struggles are valuable data.

### 4. Ask what you know
**What it is:** search your own brain. It answers from YOUR notes first
(citing them), and clearly separates anything beyond your notes.

**How:**
```
/query what do I actually know about hash tables?
```

### 5. Bring in your old notes
**What it is:** got years of notes in another app (Joplin, Obsidian, or plain
markdown files)? It imports them in bulk, then reads each one and tags it
properly so it joins the map.

**How:** export your notes from the other app as markdown, then:
```
/ingest import the folder ~/Desktop/my-notes-export
```
Heads-up: the tagging step reads every note with AI, so a big pile of notes
takes a while (and Claude usage). Fine to let it run overnight.

### 6. Get quizzed (this is where scores become real)
**What it is:** it asks you questions right at the edge of what your notes
prove — not too easy, not impossible — then grades your answers against a
fixed rubric and records the result *with receipts*. This is the only way the
"tested" score ever changes, so it can't be gamed and it never drifts.

**How:**
```
/quiz test me on graphs
```

### 7. Review before you forget
**What it is:** knowledge fades — the system literally decays scores with
time. This picks the topics that are important-but-getting-stale and runs a
quick refresh session, then records that you reviewed them.

**How:**
```
/review what's getting rusty?
```

### 8. Practice interviews out loud
**What it is:** it writes a personalized mock-interview script — questions
aimed at your weak spots — that you run with Claude's voice mode on your
phone, like a phone screen. Afterward, the debrief gets recorded as real
evidence (answering under pressure counts for a lot).

**How:**
```
/interview-pack 30 minutes, data structures focus
```
…do the voice session, then paste the debrief back with `/debrief`.

### 9. Ask "what should I study next?"
**What it is:** the ranked to-do list. It compares every goal's requirements
against your evidence and sorts by what's most urgent and most missing.

**How:**
```
python -m brain gaps
```
Or for one goal: `python -m brain gaps --goal <goal-id>` (goal ids live in
`goals/goals.yaml`)

### 10. Chart a path to a custom goal
**What it is:** for objectives that aren't one of your set goals ("get ready
for a FAANG interview loop"), it compiles a route through the map — which
topics, in what order, with your weak segments highlighted — and draws it as
an overlay on the map.

**How:**
```
/path get ready for FAANG interviews by spring
```
Then pick the pathway from the **Pathway** dropdown in the map.

---

## Common questions

**Where's my data?** Plain text files in one folder on your computer. Open
them with any editor. Nothing syncs anywhere.

**What does it cost?** Nothing to run. The AI features use a Claude
subscription you'd already have for Claude Code.

**Can I break it?** Hard to. The map and search index are disposable — one
command (`python -m brain rebuild`) rebuilds them from your notes. The notes
themselves are versioned with git, so anything can be undone.

**Why does it say I'm weak at something I know well?** Because you haven't
*proven* it yet — self-confidence only counts so far (it caps at level 3 by
design). Run `/quiz` on the topic; if you're right about yourself, the score
catches up and the dot turns green.

**Do I have to use all of this?** No. The minimum loop is: `/log` when you
learn, `/quiz` sometimes, and glance at the map. Everything else is there
when you want it.
