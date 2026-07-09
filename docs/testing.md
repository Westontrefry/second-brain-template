# Testing

The suite grows with the code: every iteration that adds or changes behavior adds or
updates tests (PLAN.md working rules). Verification for a milestone = the suite
passing, not ad-hoc runs.

## How to run

```bash
.venv/bin/python -m pytest              # everything (~10s; includes e2e)
.venv/bin/python -m pytest -m "not e2e" # fast layers only (<1s)
```

## Layers

**L1 — unit (fast, no embeddings).** Schema validation (valid, malformed, misplaced
notes), chunking behavior. Files: `test_schema.py`, `test_chunking.py`.

**L2 — integration (fast, no embeddings).** The scoring brain on synthetic corpora:
decay halves at half-life, self-confidence caps at level 3, ai_confidence overrides,
one note strengthens many topics, project evidence outweighs reading, alias matching,
prereq blocking, satisfied topics disappear. Files: `test_weights.py`, `test_gaps.py`.
The knowledge model (KME) lives here too: registry alias resolution + dup detection,
roadmap-track blocking parity with gaps.py, outline parsing + idempotent import,
state thresholds + convergence, self-explaining readiness lines, context export
shape, and the graph track layer. Files: `test_model_registry.py`,
`test_model_tracks.py`, `test_model_outline.py`, `test_model_compile.py`,
`test_model_readiness.py`, `test_model_context.py`, `test_graph_tracks.py`.

**L3 — end-to-end (marked `e2e`, real embeddings).** Drives the actual CLI as
subprocesses through the full lifecycle: validate → ingest → search → add → rebuild →
delete → sync → gaps → status. File: `test_e2e_cli.py`. Runs offline
(`HF_HUB_OFFLINE=1`; the model is cached after first ingest).

**L4 — skill flows (manual checklist).** Skills are conversational, so they're
verified by executing their documented steps in a session (as done at build time):
/log creates a valid note; /ingest imports + enriches and re-validates; /query
separates "from your notes" from "beyond your notes". Re-check after editing a
SKILL.md.

## Sandboxing

Every test runs against a sandbox in a tmp dir, selected via the `BRAIN_ROOT`
env var (`tests/conftest.py::sandbox`): live config/goals/rubrics/model plus a frozen
knowledge set (`tests/fixtures/knowledge/` — the four original seed notes; the
live `knowledge/` tree grows with use and would make assertions data-dependent).
Tests never touch the real knowledge base or index. `write_note()` in conftest
builds synthetic notes.

## Adding tests for a new feature

1. Name behaviors in glossary terms; put fast logic tests in L1/L2.
2. If the feature adds a CLI command or changes the lifecycle, extend
   `test_full_lifecycle` (or add a new e2e test) rather than testing only in-process.
3. UI (Phase 5) verification: `brain graph` output shape gets L2 tests; rendering is
   checked manually in the browser (documented per-milestone in PROGRESS.md).
