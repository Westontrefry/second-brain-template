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

## Getting started

Three commands, then a conversation (the README has the copy-paste versions):
clone it, install it, open the folder in Claude Code, and say hi.

If your brain is empty, it offers a short guided tour (/start). No setup
quiz, no forms — one conversation:

1. Pick what you're working toward (it suggests the built-in goal roadmaps,
   or takes your own words).
2. Tell it one sentence about anything you studied this week — that becomes
   your first note.
3. Answer two quick questions about that same thing — that becomes your first
   real score.
4. It opens your map and points at what just happened: your dot, its size,
   its color, and the dashed circles your goal still wants filled.

Every step is skippable. If you already have years of notes in Joplin or
Obsidian, say so at the start and it walks you through importing them instead.
If you have nothing to import, it can drop in the demo examples first
(`brain demo --install`) so the map isn't an empty void on day one — they're
clearly marked, never get scored, and `brain demo --remove` deletes them
without a trace.

## The two ways you use it

- **Talk to it** — you open the folder in Claude Code (an AI assistant that
  runs in a window on your computer) and just… tell it things or ask it
  things. You never need to memorize commands: "show my map", "quiz me on
  graphs", and "what should I study?" all just work. The `/` shortcuts below
  are there when you want to be exact.
- **Look at it** — your knowledge map and dashboard, in your web browser.

And if you ever type just `brain` in a terminal, you get a little home screen:
how many notes and topics you have, whether anything needs a re-sync, a
"since last time" recap (what you added, what you proved, what quietly went
stale while you weren't looking), the top three gaps worth your attention,
and three things you could try right now.

One nice touch as you explore: the first time you try a feature — your first
quiz, your first import, your first review — it opens with a short plain-English
explanation of what's about to happen and what the numbers mean. You see it
once, and after that the feature just runs. The visual side works the same way:
your first visit to each view dims the page for a moment and points right at
the thing it's explaining (the color legend, the chart) with a short note.
Click "got it" and it never appears again — and the little `?` next to a
view's title brings it back whenever you want a refresher. No manual required.

---

## The daily loop

The whole habit is three small moves. Everything else is optional.

### Save something you just learned
Studied something? Struggled with something? Tell it in one sentence — it
files a proper note for you.

```
/log spent an hour on binary search trees, insertion finally makes sense
but deleting nodes with two children still confuses me
```

That's it. It records what you learned, how solid it felt, and even keeps the
"still confuses me" part — the struggles are valuable data. Every save ends
with a receipt: what changed, which numbers moved, "map data refreshed —
reload the tab", and a note that a local snapshot was saved (nothing leaves
your machine). No silent writes, ever.

### Get quizzed (this is where scores become real)
It asks you questions right at the edge of what your notes prove — not too
easy, not impossible — then grades your answers against a fixed rubric and
records the result *with receipts*. This is the only way the "tested" score
ever changes, so it can't be gamed and it never drifts.

```
/quiz test me on graphs
```

Every quiz also files its own session note — the questions, your answers, the
grading — and pins it to the score as evidence, so on the map you can click a
tested topic and read exactly why it earned its color.

### Review before you forget
Knowledge fades — the system literally decays scores with time. This picks
the topics that are important-but-getting-stale and runs a quick refresh
session, then records that you reviewed them.

```
/review what's getting rusty?
```

Then glance at the map. The moment a dot turns green is the whole point.

### Let it help you actually remember
Miss a quiz or review question and it offers you a memory hook — one vivid
line built from characters you already know ("Sisyphus is your infinite
loop: no exit condition, boulder forever"). You accept it, reword it, or
wave it off; nothing gets saved without your say-so. You can also just tell
it one anytime: "remember binary search as splitting the phone book." Saved
hooks come back as hints in your reviews, and in quizzes only *after*
you've answered — they help you remember, they never inflate your score.
It ships with a starter cast (Zeus, Sherlock, Dracula, Alice…), and any
characters or places you add from your own head stay private on your
machine, like everything else.

---

## Bring in your old notes

Got years of notes in another app (Joplin, Obsidian, or plain markdown
files)? It imports them in bulk, then reads each one and tags it properly so
it joins the map.

Export your notes from the other app as markdown, then:
```
/ingest import the folder ~/Desktop/my-notes-export
```
Heads-up: the tagging step reads every note with AI, so a big pile of notes
takes a while (and Claude usage). Fine to let it run overnight.

Everything you import starts at **"aware"** — you *have* the material, but having
a file doesn't mean you've learned it. As the AI reads each note to tag it, it
also decides whether the note actually shows you *engaged* with the material
(worked problems, your own explanations) and bumps those up to "know it." If you
already know a folder cold, import it with `--confidence 2` so it doesn't have to
guess. And if it ever calls one wrong, just tell it — "actually, bump red-black
trees to known" — or be exact:
```
brain set-confidence 2024-03-14-red-black-trees --level 2
```
(That only touches your self-rating — the quiz-tested score still rules where a
quiz exists.)

---

## The map and its views

### See your knowledge map
Every topic you've ever taken a note on, drawn as a dot. Bigger dot = more of
your knowledge lives there. The color is the topic's proven depth, one rung
per color: grey = aware (you have the material), yellow = you understand it,
green = you've applied it, blue = fluent, purple = mastery. Dashed outline =
something your goals need that you haven't touched yet. Lines connect topics
whose notes link to each other, plus the prerequisites your goals need in order
(the AI adds those cross-references as it organizes new material). Topics that
merely show up together share a fainter web — hidden by default so the map stays
clean and quick, and drawn back in whenever you tick **co-occurrence**.

**How:** say "show my map" (or run `brain ui`). Your browser opens the map.
Click any dot to zoom into its neighborhood and
see the actual notes behind it (a filter box appears when the list is long) —
and **click any note in that list to read it right there**, nicely formatted —
math equations, flowchart diagrams, and color-highlighted code all render
properly — without leaving the map. Some topics also carry a **Practice**
list — real problems (with links straight to LeetCode) you can go solve right
now to earn that node its next color. **Click any color in the legend** to fade
the rest of the map and light up just the topics at that rung (click it again
to clear). **Type in the search bar** and the map narrows as you type — every
topic still matching stays lit while the rest fades, and the suggestion list
ranks your strongest nodes first; pick one to jump straight into it. Search
covers **tags** too — type "Google" and it surfaces GCP, Gemini, BigQuery and
the rest, even though none of them say "Google" in the name. Use the **Goal**
dropdown to show only what matters for one goal, the **Tag** dropdown to isolate
a theme's whole sub-network (all your Google topics as their own little map),
and tick **show gaps** to light up what's missing. When the map feels crowded,
drag the **spread** slider to push everything further apart or pull it back in;
it opens up the busy core so labels stop overlapping, and touches nothing about
your data. The map also arrives grouped into **labelled regions** — computer
science, cloud, career and so on — so related topics cluster together instead
of piling into one central knot; untick **cluster** if you'd rather see it as
one free-floating field. Tags are a curated lens you
edit in `tags.yaml` — group any topics under a name and they're searchable and
filterable together. You don't have to edit that file yourself: just say "tag
my AWS stuff" or "add Kubernetes to the Google tag" in a session and the AI
proposes the members from your real topics, you approve, and the map picks it
up. Prefer dark mode? Hit the 🌙 button
in the header — it remembers your choice and follows you everywhere.

Want the map to feel like a star chart? Hit the ✦ button next to it and the
whole thing turns into **Constellation** mode: deep-space black, faint distant
stars behind, and every topic drawn as a celestial body that grows grander the
better you know it — a little four-pointed sparkle when you're just aware of
something, a sharper six-point burst once you can apply it, a whole spiral
galaxy at fluency, and a blazing quasar at mastery. (Galaxies and quasars are
rare on purpose — trophies you earn, so most of the sky is sparkles.) Click a
topic and instead of a flat zoom you *fly into* its cluster —
the whole field banks and tilts back into perspective as you go, like turning
to face it through space, then levels out when you zoom back out. The distant
starfield drifts slowly around the centre the whole time, so the sky always
feels alive. It's the same map underneath (same dots, same clicks), just a
night-sky skin —
and like dark mode it's a global setting that sticks and follows you around.
Hit the button again to come back to the flat map.

One small honesty feature: the header always says how old the picture is
("data generated 5 min ago"). If you logged something and don't see it,
that line is the tell — just reload the tab.

### Check the other views
The header has four view buttons — **Map · Readiness ·
Divergence · Real estate** (or just press 1–4). Same page, no reloads, and
your selections follow you: pick a goal on the Readiness view, press 1, and
the map is already showing that goal's corner of your knowledge. Three
pictures:

- **Readiness** — one glance answers *"am I ready for this goal?"* The
  green shape is what you know; the dashed outline is what the goal requires.
  Wherever green fills the outline, you're ready. Dents = study there.
  (No goal picked yet? It offers you the list.)
- **Divergence** — a dot for each topic that's been quiz-tested,
  comparing how confident you *felt* vs how you *performed*. Dots below the
  line = overconfident (feelings ahead of evidence). Above = you're better
  than you think. (Never been quizzed? The view shows a clearly-labeled
  example chart so you can see what's coming — your first real dot lands
  after your first quiz.)
- **Real estate** — every topic as a box; bigger box = more of your
  knowledge lives there, and the color is the topic's *proven* rung — the
  same colors as the map, so one glance shows where your knowledge is big
  but unproven (a big grey box is a to-do list). Hover any box for its
  exact share. **Scroll in** on a crowded corner and it re-tiles into its
  own view — first a whole domain, then a single topic's actual notes
  (click one to read it right there); scroll out to back up. **Click any
  box** (or any dot on the divergence chart) and it jumps you to that
  topic in the map with its full summary open — the notes behind it, its
  scores, what goals need it.

### Drive it from the map (the cockpit)
Most of the time you talk to it in Claude Code. But if you want to run the
whole thing from the map itself, there's an opt-in panel called the cockpit.

You turn it on once. In a terminal, install the little server it needs
(`pip install -e ".[cockpit]"`), then run `brain cockpit` and open the page
it prints. A small "Cockpit" button shows up in the header. Open the plain
map the normal way and that button simply is not there, so nothing about the
everyday map changes.

Click it and a dock slides out with buttons. Log, Quiz, and Review do exactly
what the chat commands do. The system quietly runs the same skill for you in
the background and streams the reply right into the panel, and a little box
lets you answer back for a full quiz or review. It still costs nothing to run.
The other buttons (Ingest, Graph, Gaps, Status, Doctor) are the plumbing
commands, run for you with one click.

Even easier, you rarely have to name a topic at all. Click any dot on the map
and its card grows its own Quiz, Review, Log, and Expand buttons. Hit Quiz there
and it quizzes you on that exact topic right away, with nothing to type. Log
there and it starts the note for you with the topic already filled in. Expand
reaches past what you already have and suggests related topics you have not
covered yet, so your map can grow at its edges. And when you do kick off a quiz
or review from the dock itself, it no longer makes you guess a topic into a
blank box. It suggests your real topics as you type, so you just pick one and go.

One promise holds here too. The panel never writes to your knowledge on its
own. Every score, every note, every event still goes through the same skill it
always did, with the same receipts. The button is just a faster way to press
go.

### Grow the map into what you don't know yet
The map is honest about a hard thing: you only know what you know. The dashed
outlines are topics a goal needs that you haven't touched. But there's a bigger
blind spot — the topics you don't even know you're missing, because they were
never on the map at all.

That's what the frontier feature is for. Point it at any topic ("expand the
frontier on graphs", or click a node's **Expand** button on the map) and it
does the one thing the deterministic system can't: it uses what it knows about
the whole field to name the relevant topics sitting *outside* your current
radius. Ask it to "deepen" and it drills into sub-topics; ask it to "broaden"
and it surfaces the neighbors you skipped. It shows you each one with a reason,
you pick the ones that belong, and they land on your map as new dashed nodes to
go study.

It never writes without your yes, it won't propose something you already have,
and it caps how many it adds at once so your to-do list doesn't drown. Then
those new gaps show up in "what should I study next?" like everything else.

---

## The rest of the network

### Ask what you know
Search your own brain. It answers from YOUR notes first (citing them), and
clearly separates anything beyond your notes.
```
/query what do I actually know about hash tables?
```

### Ask "what should I study next?"
The ranked to-do list. It compares every goal's requirements against your
evidence and sorts by what's most urgent and most missing.

**How:** just ask — "what should I study next?" (or run `brain gaps`, and
`brain gaps --goal gcp-ace` for one goal).

### Practice interviews out loud
It writes a personalized mock-interview script — questions aimed at your weak
spots — that you run with Claude's voice mode on your phone, like a phone
screen. Afterward, the debrief gets recorded as real evidence (answering
under pressure counts for a lot).
```
/interview-pack 30 minutes, data structures focus
```
…do the voice session, then paste the debrief back with `/debrief`.

### Chart a path to a custom goal
For objectives that aren't one of your set goals ("get ready for a FAANG
interview loop"), it compiles a route through the map — which topics, in what
order, with your weak segments highlighted — and draws it as an overlay on
the map.
```
/path get ready for FAANG interviews by spring
```
Then pick the pathway from the **Pathway** dropdown in the map.

### Teach it a course or study plan
Hand it a syllabus (or any outline — a cert exam guide, a book's table of
contents, a study plan) and it learns the *structure*: which topics the
course covers, in what order, and what builds on what. That structure joins
your knowledge model, so the system can later tell you how ready you are for
week 5 before you get there.

**How:** save the syllabus as a markdown file (headings for the weeks, bullet
points for the topics), then say "teach it this syllabus:
~/Downloads/course-syllabus.md" (or run `brain model import <file>`, with
`--dry-run` to preview without saving). Topics it already knows get matched
up (it knows "splay trees" belong to your Trees knowledge); genuinely new
ones get added to its vocabulary automatically.

Curious how the whole model is doing? Ask it — "how's my knowledge model
looking?" (`brain model build`) prints a one-glance health check: how many
concepts it tracks, how many you have real evidence for, and what's mastered
vs still fading.

Imported courses also show up on the knowledge map — the **Goal** dropdown
lists them under their own **Tracks** heading (goals are things you're
working toward; tracks are courses and resources you've taught it), and
picking one gets the same treatment: suggested
next actions, dashed circles for the parts you haven't touched, and each
topic's panel notes how many courses/goals converge on it ("in 2 tracks" =
learn it once, it pays off twice).

### Check if you're ready (and take your brain anywhere)
Two questions everything else builds toward. *"Am I ready?"* — ask exactly
that ("am I ready for gcp-cdl?", or run `brain readiness gcp-cdl`) and get a
line-by-line verdict where every line explains itself (stale since when,
missing what, do what first). And *"can another AI help me?"* — type
`/context` and it hands you a one-screen summary of your entire learning
state, ready to paste into any assistant (ChatGPT, a fresh Claude chat,
whatever) so it instantly knows what you know (add a goal name to scope it,
e.g. `/context gcp-cdl`). The export contains no note contents — just topic
names and states — so it's safe to paste around.

### Keep it healthy, keep it yours
Something feel off? `brain doctor` checks the whole setup — packages, the
search index, the map data, all of it — and every problem it finds comes
with the exact command that fixes it. (Skills also fix the routine stuff
themselves as they run — a stale index heals on the next question.)

Worried about losing your notes? They're all on your machine, saved with
little local snapshots as you work. When you want an off-site copy too,
`brain backup --setup` shows you how to wire up a private online home for
them, and `brain backup` is the one and only command that sends anything
there.

---

## Common questions

**Where's my data?** Plain text files in one folder on your computer. Open
them with any editor. Nothing syncs anywhere.

**What does it cost?** Nothing to run. The AI features use a Claude
subscription you'd already have for Claude Code.

**Can I break it?** Hard to. The map and search index are disposable — tell
it "rebuild the index" (or run `brain rebuild`) and they're rebuilt from your
notes. The notes themselves are versioned with git, so anything can be undone.

**Why does it say I'm weak at something I know well?** Because you haven't
*proven* it yet — self-confidence only counts so far (it caps at level 3 by
design). Run `/quiz` on the topic; if you're right about yourself, the score
catches up and the dot turns green.

**Do I have to use all of this?** No. The minimum loop is: `/log` when you
learn, `/quiz` sometimes, and glance at the map. Everything else is there
when you want it.

**What if something breaks, or a future AI session wants to "improve" things?**
The repo carries its own institutional memory: three maintenance skills
(failure-archaeology, debugging-playbook, confidence-judgment) record every bug
that's been fixed, every approach that's been rejected, and how the judgment
calls work — so a fresh session doesn't re-fight old battles or undo
deliberate decisions.
