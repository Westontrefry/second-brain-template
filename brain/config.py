"""Load config.yaml and goals.yaml from the repo root.

The root is normally the repo containing this package; tests (and any tooling)
can point at a sandbox by setting the BRAIN_ROOT environment variable.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


def root() -> Path:
    return Path(os.environ.get("BRAIN_ROOT") or Path(__file__).resolve().parent.parent)


@lru_cache(maxsize=4)
def _load_config_cached(root_dir: str) -> dict:
    import yaml

    with open(Path(root_dir) / "config.yaml") as f:
        return yaml.safe_load(f)


def load_config() -> dict:
    return _load_config_cached(str(root()))


@lru_cache(maxsize=4)
def _goal_ids_cached(root_dir: str) -> frozenset[str]:
    import yaml

    cfg = _load_config_cached(root_dir)
    with open(Path(root_dir) / cfg["paths"]["goals_file"]) as f:
        goals = yaml.safe_load(f)["goals"]
    return frozenset(g["id"] for g in goals)


def goal_ids() -> frozenset[str]:
    return _goal_ids_cached(str(root()))


def knowledge_dir() -> Path:
    return root() / load_config()["paths"]["knowledge_dir"]
