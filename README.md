# Second Brain (template)

A local-first personal knowledge system that models **what you know, weighted by
evidence**, finds goal-relevant knowledge gaps, and renders it all as an
interactive graph. Markdown files are the source of truth; SQLite + local
embeddings are a disposable, rebuildable index. No server, no accounts, no API
keys — **$0 to operate**.

The AI layer (capture, enrichment, quizzing, review) runs as [Claude Code](https://claude.com/claude-code)
skills, so the smart parts need a Claude subscription. Everything else — import,
semantic search, gap analysis, the graph UI — is a plain Python CLI that works
without it.

## Quickstart

Three commands from clone to a working brain:

```bash
git clone <your copy of this template> && cd <it>
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

Then open the folder in Claude Code and say hi — the brain is empty, so it
offers the guided tour (/start): pick a goal, log one sentence, take a
two-question quiz, and see your map. Or type `brain` in the terminal for the
home screen: your counts, your top gaps, and what to try next.

One heads-up: the first note sync downloads the embedding model (~90MB, one
time). It lives on your machine after that — nothing you write ever leaves it.

Want something to look at before you have notes? `brain demo --install` drops
in eight synthetic example notes (clearly marked, never scored);
`brain demo --remove` deletes them without a trace.

## Make it yours

The fastest path: open this repo in Claude Code and say
**"Read AI-SETUP.md and set this system up for me."** — or just take the
/start tour. Your assistant will interview you for goals and domains,
configure the YAML, import your existing notes, and enrich them.
[AI-SETUP.md](AI-SETUP.md) is the full machine-readable runbook; the short
version:

1. `goals/goals.yaml` — replace the example goals with yours (shipped
   roadmaps: dsa-interviews, gcp-cdl, gcp-ace — the tour offers them as picks).
2. `goals/roadmaps/<goal-id>.yaml` — one per goal you want gap analysis for.
   **Aliases are the join key** between your note vocabulary and roadmap topics.
3. `config.yaml` — rename the seed domains to whatever clusters fit your life.
4. Import notes: `brain import <folder> --dry-run` first (Joplin "MD + Front
   Matter" exports are first-class; plain markdown/Obsidian work too).
5. Delete the two sample notes under `knowledge/`.

## Daily use

The conversation is the front door — in Claude Code, just say what you want
("quiz me on graphs", "show my map", "what should I study next?"). The exact
forms, when you want them:

| You want to… | Use |
|---|---|
| Capture a study session | `/log` skill (or `brain add`) |
| Bulk-import + tag notes | `/ingest` skill (or `brain import`) |
| Ask what you know | `/query` skill (or `brain search`) |
| Find what to learn next | `brain gaps --goal <id>` (or just ask) |
| Get tested, build evidence | `/quiz`, `/review`, `/interview-pack` skills |
| See the graph | `brain ui` (or "show my map") |
| Health-check the setup | `brain doctor` |

Every skill that writes ends with a receipt (what changed, which numbers
moved), refreshes the map data itself, and saves a labeled local snapshot.

## Backing up

Everything lives on your machine; skills save local snapshots as you work.
Want an off-machine copy? `brain backup --setup` walks you through wiring a
**private** remote, and `brain backup` pushes to it — that is the only command
that ever sends your notes anywhere. Until you run it, nothing leaves the box.

## Docs

`docs/` has the architecture, CLI reference, glossary, skill guide, UX
principles, and testing notes — [docs/demo-guide.md](docs/demo-guide.md) is
the friendly walkthrough. `rubrics/depth.yaml` is the universal 0–5
knowledge-depth rubric — the only place "how well do I know this" is defined.
