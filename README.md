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

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m brain validate    # 2 sample notes pass
.venv/bin/python -m brain ingest      # first run downloads a ~90MB embedding model
.venv/bin/python -m brain ui          # opens the graph in your browser (file://, no server)
```

## Make it yours

The fastest path: open this repo in Claude Code and say
**"Read AI-SETUP.md and set this system up for me."**
Your assistant will interview you for goals and domains, configure the YAML,
import your existing notes, and enrich them. [AI-SETUP.md](AI-SETUP.md) is the
full machine-readable runbook; the short version:

1. `goals/goals.yaml` — replace the example goals with yours.
2. `goals/roadmaps/<goal-id>.yaml` — one per goal you want gap analysis for.
   **Aliases are the join key** between your note vocabulary and roadmap topics.
3. `config.yaml` — rename the seed domains to whatever clusters fit your life.
4. Import notes: `brain import <folder> --dry-run` first (Joplin "MD + Front
   Matter" exports are first-class; plain markdown/Obsidian work too).
5. Delete the two sample notes under `knowledge/`.

## Daily use

| You want to… | Use |
|---|---|
| Capture a study session | `/log` skill (or `brain add`) |
| Bulk-import + tag notes | `/ingest` skill (or `brain import`) |
| Ask what you know | `/query` skill (or `brain search`) |
| Find what to learn next | `brain gaps --goal <id>` |
| Get tested, build evidence | `/quiz`, `/review`, `/interview-pack` skills |
| See the graph | `brain ui` |

## Docs

`docs/` has the architecture, CLI reference, glossary, skill guide, and testing
notes. `rubrics/depth.yaml` is the universal 0–5 knowledge-depth rubric — the
only place "how well do I know this" is defined.
