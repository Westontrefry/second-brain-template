"""End-to-end: drive the real CLI as subprocesses against a sandbox, including
real local embeddings. Marked e2e — skip with `pytest -m "not e2e"` for fast runs."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
# The running interpreter, so the suite works regardless of venv location.
PYTHON = Path(sys.executable)

pytestmark = pytest.mark.e2e


def brain(sandbox: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, BRAIN_ROOT=str(sandbox), HF_HUB_OFFLINE="1")
    return subprocess.run(
        [str(PYTHON), "-m", "brain", *args],
        capture_output=True, text=True, env=env, cwd=REPO, timeout=300,
    )


def test_full_lifecycle(sandbox: Path):
    r = brain(sandbox, "validate")
    assert r.returncode == 0, r.stdout + r.stderr

    r = brain(sandbox, "ingest")
    assert r.returncode == 0 and "indexed 4" in r.stdout

    r = brain(sandbox, "search", "database indexes for range queries", "-k", "1")
    assert r.returncode == 0 and "btree-vs-hash-indexes" in r.stdout

    r = brain(sandbox, "add", "--domain", "cs", "--title", "E2E test note",
              "--topics", "testing", "--goals", "cs-degree",
              "--body", "Content created by the e2e suite to prove add works.")
    assert r.returncode == 0 and "added and indexed" in r.stdout

    r = brain(sandbox, "rebuild")
    assert r.returncode == 0 and "indexed 5" in r.stdout

    note = next((sandbox / "knowledge" / "cs").glob("*e2e-test-note.md"))
    note.unlink()
    r = brain(sandbox, "ingest")
    assert r.returncode == 0 and "removed 1" in r.stdout

    r = brain(sandbox, "gaps", "--goal", "gcp-ace", "-n", "20")
    assert r.returncode == 0 and "IAM" in r.stdout

    r = brain(sandbox, "status")
    assert r.returncode == 0 and "up to date" in r.stdout
