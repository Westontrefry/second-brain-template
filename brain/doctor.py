"""brain doctor: the debugging-playbook basics, automated (PLAN-UX U4).

Read-only. Every check yields pass/fail plus the ONE command that fixes it,
in product language. Deliberately avoids importing sentence_transformers
(seconds of import time) — the model check looks at the cache on disk.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from . import store
from .config import knowledge_dir, load_config, root
from .schema import validate_file


@dataclass
class Check:
    ok: bool
    detail: str
    fix: str | None = None  # the one command/action that repairs a failure


def check_python() -> Check:
    ver = ".".join(str(v) for v in sys.version_info[:3])
    if sys.version_info < (3, 10):
        return Check(False, f"python {ver} is too old",
                     "recreate the venv with python 3.10+")
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    note = "virtualenv active" if in_venv else "no virtualenv (works, but venv keeps deps tidy)"
    return Check(True, f"python {ver}, {note}")


def check_deps() -> Check:
    missing = [name for name, mod in
               (("pyyaml", "yaml"), ("numpy", "numpy"),
                ("sentence-transformers", "sentence_transformers"))
               if importlib.util.find_spec(mod) is None]
    if missing:
        return Check(False, f"missing package(s): {', '.join(missing)}",
                     "pip install -e .")
    return Check(True, "dependencies installed (pyyaml, numpy, sentence-transformers)")


def _hf_hub_dir() -> Path:
    if os.environ.get("HF_HUB_CACHE"):
        return Path(os.environ["HF_HUB_CACHE"])
    if os.environ.get("HF_HOME"):
        return Path(os.environ["HF_HOME"]) / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


def check_model() -> Check:
    model = load_config()["embedding"]["model"]
    cached = _hf_hub_dir() / ("models--" + model.replace("/", "--"))
    if cached.is_dir():
        return Check(True, "embedding model cached (search runs offline)")
    return Check(False, "embedding model not downloaded yet",
                 "brain ingest (downloads it once, ~90MB, stays on your machine)")


def check_notes() -> Check:
    files = sorted(knowledge_dir().rglob("*.md"))
    if not files:
        return Check(True, "no notes yet (an empty brain is healthy — try /start)")
    bad = sum(1 for f in files if validate_file(f))
    if bad:
        return Check(False, f"{bad} of {len(files)} note(s) fail validation",
                     "brain validate (lists every error per file)")
    return Check(True, f"{len(files)} notes on disk, all valid")


def check_index() -> Check:
    files = sorted(knowledge_dir().rglob("*.md"))
    if not store.db_path().exists():
        if not files:
            return Check(True, "index not built (nothing to index yet)")
        return Check(False, "index not built", "brain ingest")
    con = store.connect()
    hashes = dict(con.execute("SELECT id, content_hash FROM notes").fetchall())
    con.close()
    stale = sum(1 for f in files
                if hashes.get(f.stem) != hashlib.sha256(f.read_bytes()).hexdigest())
    ghosts = len(hashes) - sum(1 for f in files if f.stem in hashes)
    behind = stale + max(ghosts, 0)
    if behind:
        return Check(False, f"index is {behind} note change(s) behind", "brain ingest")
    return Check(True, "index up to date with your notes")


def check_graph_data() -> Check:
    data_js = root() / "ui" / "graph.data.js"
    if not data_js.exists():
        return Check(False, "map data never generated", "brain ui (or brain graph)")
    files = sorted(knowledge_dir().rglob("*.md"))
    newest = max((f.stat().st_mtime for f in files), default=0.0)
    if newest > data_js.stat().st_mtime:
        return Check(False, "map data older than your latest note change",
                     "brain graph (any skill run also refreshes it)")
    return Check(True, "map data fresh")


def check_git() -> Check:
    if shutil.which("git") is None:
        return Check(False, "git not found (local snapshots are skipped without it)",
                     "install git — snapshots stay on your machine either way")
    if not (root() / ".git").exists():
        return Check(False, "this folder isn't a git repository yet",
                     "git init (snapshots stay local; nothing is pushed)")
    return Check(True, "git ready (local snapshots on)")


ALL_CHECKS = [check_python, check_deps, check_model, check_notes,
              check_index, check_graph_data, check_git]


def run_checks() -> list[Check]:
    return [c() for c in ALL_CHECKS]


def render(checks: list[Check]) -> str:
    lines = []
    for c in checks:
        mark = "ok " if c.ok else "FIX"
        lines.append(f"  {mark}  {c.detail}")
        if not c.ok and c.fix:
            lines.append(f"       -> {c.fix}")
    broken = sum(1 for c in checks if not c.ok)
    if broken:
        lines.append(f"\n{broken} thing(s) to fix. Each line above names its command.")
    else:
        lines.append("\nall checks pass. You're healthy.")
    return "\n".join(lines) + "\n"
