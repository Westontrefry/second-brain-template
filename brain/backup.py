"""Opt-in backup to a private remote — the only place "push" exists (ux.md #6).

Snapshots (the per-skill local commits) never leave the machine on their own.
`brain backup --setup` only inspects state and prints the walk; creating the
remote and pushing are always explicit user actions.
"""
from __future__ import annotations

import shutil
import subprocess

from .config import root


def _git(*args: str, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root()), *args],
                          capture_output=capture, text=True)


def git_ready() -> bool:
    return shutil.which("git") is not None and (root() / ".git").exists()


def remote_url() -> str | None:
    if not git_ready():
        return None
    r = _git("remote", "get-url", "origin")
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def current_branch() -> str | None:
    r = _git("rev-parse", "--abbrev-ref", "HEAD")
    return r.stdout.strip() if r.returncode == 0 else None


def setup_text() -> str:
    lines: list[str] = []
    if shutil.which("git") is None:
        return ("backup needs git, which isn't installed\n"
                "install git first; your notes are still safe on disk either way\n")
    if not (root() / ".git").exists():
        return ("this folder isn't a git repository yet\n"
                "run: git init\n"
                "that only enables local snapshots; nothing is pushed by it\n"
                "then run: brain backup --setup\n")
    url = remote_url()
    if url:
        lines += [
            f"a remote is already wired up: {url}",
            "make sure that repository is PRIVATE, your notes are personal",
            "back up anytime with: brain backup",
            "until you run that, everything stays on this machine",
        ]
    elif shutil.which("gh"):
        lines += [
            "you have the GitHub CLI, so this is two steps:",
            "  1. check you're on the right account: gh auth status",
            "  2. create a private repo wired to this folder:",
            "     gh repo create second-brain --private --source . --remote origin",
            "that creates the remote but pushes nothing",
            "back up anytime with: brain backup",
        ]
    else:
        lines += [
            "create a PRIVATE repository on your git host (github.com -> New -> Private)",
            "then wire it up: git remote add origin <its-url>",
            "that pushes nothing by itself",
            "back up anytime with: brain backup",
        ]
    lines.append("brain backup is the only command that ever sends your notes anywhere")
    return "\n".join(lines) + "\n"


def push() -> tuple[bool, str]:
    """Push the current branch to origin. Returns (ok, message)."""
    if not git_ready():
        return False, "backup needs git and a git repository here (brain backup --setup explains)"
    url = remote_url()
    if not url:
        return False, "no remote wired up yet — run: brain backup --setup"
    branch = current_branch()
    if not branch or branch == "HEAD":
        return False, "not on a branch (detached HEAD) — check out a branch first"
    r = _git("push", "-u", "origin", branch)
    if r.returncode != 0:
        return False, (f"push failed:\n{r.stderr.strip()}\n"
                       "nothing partial happened; your local snapshots are intact")
    return True, (f"backed up: {branch} -> {url}\n"
                  "this is the only command that pushes; everything else stays local")
