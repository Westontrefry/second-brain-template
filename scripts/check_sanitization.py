#!/usr/bin/env python3
"""Sanitization gate for this PUBLIC template repo.

Fails (exit 1) if personal data or upstream-only artifacts appear in tracked
content. Runs locally (`python scripts/check_sanitization.py`) and in CI on
every push/PR, so "did I strip the personal stuff?" is a gate, not a habit.

Targeted, not paranoid: it knows the difference between a real leak (the
author's email, a private repo name, a personal goal file) and a benign
product term ("Joplin" is a supported import format, not personal data). Extend
FORBIDDEN / FORBIDDEN_PATHS as new leak classes are discovered — that's the
point of having it in code instead of in someone's memory.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The author's real name is allowed ONLY where it's intentional (copyright).
NAME_RE = re.compile(r"\b(Weston|Trefry)\b")
NAME_ALLOWED_FILES = {"LICENSE"}

# Identifiers that must never appear in tracked content, anywhere.
FORBIDDEN = [
    (re.compile(r"weston\.trefry@\S+|\btrefry\S*@", re.I), "personal email"),
    (re.compile(r"\beb\.app\b", re.I), "personal project (eb.app)"),
    (re.compile(r"\bsecond-brain-hq\b", re.I), "private business repo"),
    (re.compile(r"\bmidi-maker\b", re.I), "unrelated personal repo"),
    (re.compile(r"\bclaude-config\b", re.I), "private config repo"),
    (re.compile(r"University of Florida|\bGainesville\b", re.I), "institution identifier"),
    (re.compile(r"^\s*(pack|source):\s*personal\b", re.I | re.M), "personal-only content marker"),
]

# Upstream-only artifacts that must not exist in the public template.
FORBIDDEN_PATHS = [
    "launcher",
    "PLAN.md",
    "HANDOFF.md",
    "PROGRESS.md",
    "goals/roadmaps/uf-cs-degree.yaml",
    "goals/roadmaps/job-readiness.yaml",
    ".claude/skills/failure-archaeology",
    ".claude/skills/debugging-playbook",
]

# Never scan these (self-reference or binary/noise).
SKIP_FILES = {"scripts/check_sanitization.py"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".pdf"}


def tracked_files() -> list[str]:
    """Tracked + untracked-but-not-ignored, so an in-progress sync is scanned too."""
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard"],
        capture_output=True, text=True, check=True,
    )
    return [f for f in out.stdout.splitlines() if f]


def main() -> int:
    violations: list[str] = []

    for rel in FORBIDDEN_PATHS:
        if (ROOT / rel).exists():
            violations.append(f"{rel}: upstream-only artifact present in public template")

    for rel in tracked_files():
        if rel in SKIP_FILES or Path(rel).suffix.lower() in SKIP_SUFFIXES:
            continue
        p = ROOT / rel
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        for pat, why in FORBIDDEN:
            for m in pat.finditer(text):
                ln = text.count("\n", 0, m.start()) + 1
                violations.append(f"{rel}:{ln}: {why} — {lines[ln-1].strip()[:80]!r}")
        if rel not in NAME_ALLOWED_FILES:
            for i, line in enumerate(lines, 1):
                if NAME_RE.search(line):
                    violations.append(f"{rel}:{i}: author name outside LICENSE — {line.strip()[:80]!r}")

    if violations:
        print(f"SANITIZATION FAILED — {len(violations)} issue(s):\n")
        for v in sorted(violations):
            print(f"  {v}")
        print("\nStrip the personal data (or, if a pattern is a false positive, "
              "refine scripts/check_sanitization.py).")
        return 1
    print("sanitization OK — no personal data or upstream-only artifacts found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
