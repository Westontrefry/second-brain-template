---
name: tag
description: Create, extend, trim, or delete a tag — a curated lens grouping map topics that share a theme but not vocabulary (e.g. one vendor's products). Use when the user wants to group topics ("tag my AWS stuff", "group these under interview prep", "add X to the Y tag", "delete the exam tag"), asks what tags exist, or wants a tag check-up after new topics land.
---

# /tag — curate the thematic lenses over the map

A tag is a saved grouping of existing topic ids (`tags.yaml`, repo root). The
map's search matches tag labels (searching a vendor name surfaces its products
even when no topic name contains it) and the Tag dropdown filters to a tag's
sub-network. Tags connect what vocabulary can't: the judgment of WHICH topics
belong to a theme (brand, exam, project, tech family) is world knowledge —
that's this skill's job; the write is a plain `tags.yaml` edit, rebuilt into
the UI by `brain graph`.

**Curation bar:** a tag earns its place only when it groups topics whose names
share no words — search already finds shared vocabulary, so a `cloud` tag over
`cloud sql`/`cloud storage` adds nothing. Few, sharp lenses beat many broad
ones; if a proposed tag would cover more than ~15 topics, it's probably a
domain in disguise — say so instead of writing it.

## Procedure

1. **Fix the intent.** Create a new tag, extend/trim an existing one, rename,
   delete, list what exists, or a maintenance check-up. For create: pin the
   label (display name) and a kebab-case id.

2. **Load the real ids — never guess a topic name.** Tag topics must match
   on-map node ids exactly (the lowercase topic labels). Refresh and read them:
   `.venv/bin/python -m brain graph`, then the `id` fields in `ui/graph.json`,
   plus the current `tags.yaml` (may not exist yet — that's fine, the feature
   is optional-additive).

3. **Build the candidate membership.** From the theme, sweep the node ids for
   everything that plausibly belongs — judgment first (entity/brand/theme
   relations the names don't show), `.venv/bin/python -m brain search <theme>`
   for recall on anything notes mention that ids don't. Bias to precision:
   a wrong member pollutes the lens every time it's used.

4. **Confirm — never auto-write.** Show the proposed members with a one-line
   reason each and let the user trim or extend. Deleting or renaming a tag, or
   removing members, also gets shown before it's done.

5. **Write `tags.yaml`** with the Edit tool, keeping the comment header
   intact. Format per tag: `<id>:` with `label:` and `topics:` (a YAML list of
   on-map topic ids, lowercase). Then rebuild: `.venv/bin/python -m brain
   graph` — and report any unmatched-topic lines it prints faithfully (an
   unmatched id means a typo or a renamed topic, not a cosmetic detail).

6. **Maintenance mode** ("check my tags", or when /ingest's batch summary
   flags candidates): diff each tag's topics against `ui/graph.json` node ids
   — report unmatched leftovers — then scan topics added since the tags were
   last touched for plausible members of existing tags. Propose; the user
   confirms; write as above.

**Finish every run (docs/ux.md #2 — one command per tool call):**
1. `brain graph` already ran (step 5); no notes were written, so no ingest.
2. Snapshot: `git add tags.yaml`, then
   `git commit -m "tags: <what changed>"`. No git? One line: snapshot
   skipped, tag still saved.
3. Receipt: the tag and its member count (as matched by the rebuild), anything
   skipped or unmatched and why, "map data refreshed — reload the UI tab and
   type the tag name in search to see it light up".
