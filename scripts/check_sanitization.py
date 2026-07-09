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
    (re.compile(r"[A-Za-z0-9._%+-]+@(?:gmail|outlook|yahoo|icloud|hotmail|proton(?:mail)?)\.[A-Za-z]{2,}", re.I),
     "personal-provider email address"),
    (re.compile(r"\beb\.app\b", re.I), "personal project (eb.app)"),
    (re.compile(r"\bebapp\b", re.I), "personal project goal/topic (ebapp)"),
    (re.compile(r"\bsecond-brain-hq\b", re.I), "private business repo"),
    (re.compile(r"\bmidi-maker\b", re.I), "unrelated personal repo"),
    (re.compile(r"\bprocesswizard\b", re.I), "unrelated business identifier"),
    (re.compile(r"\bclaude-config\b", re.I), "private config repo"),
    (re.compile(r"University of Florida|\bGainesville\b", re.I), "institution identifier"),
    (re.compile(r"\buf-cs\b", re.I), "UF-tied slug (goal names use cs-degree here)"),
    # COP9999 is the deliberately fictional course code in the example syllabus.
    (re.compile(r"\b(?:cop|cda|cen|cis|cot|cap|cnt)(?!9999)[0-9]{4}\b", re.I),
     "university course code"),
    (re.compile(r"/Users/[A-Za-z]"), "absolute macOS home path"),
    (re.compile(r"^\s*(pack|source):\s*personal\b", re.I | re.M), "personal-only content marker"),
    # Prose MENTIONS of upstream doc names are tolerated; a markdown LINK to one
    # is a dangling reference for template users, so links are the leak class.
    (re.compile(r"\]\([^)]*(?:PLAN(?:-UX|-KME)?\.md|HANDOFF[\w-]*\.md|PROGRESS\.md|"
                r"graph-scaling\.md|overnight-runbook\.md|ci-and-branch-protection\.md|"
                r"template-sync\.md)"),
     "markdown link to an upstream-only doc"),
]

# Upstream-only artifacts that must not exist in the public template.
FORBIDDEN_PATHS = [
    "launcher",
    "PLAN.md",
    "PLAN-UX.md",
    "PLAN-KME.md",
    "PROGRESS.md",
    ".templateignore",
    "docs/graph-scaling.md",
    "docs/overnight-runbook.md",
    "docs/ci-and-branch-protection.md",
    "docs/template-sync.md",
    "goals/roadmaps/uf-cs-degree.yaml",
    "goals/roadmaps/job-readiness.yaml",
    ".claude/skills/failure-archaeology",
    ".claude/skills/debugging-playbook",
    "joplin-export",
    "brain.db",
    "events.jsonl",
    "ui/graph.json",
    "ui/graph.data.js",
    "ui/notes.data.js",
]

# Glob classes of upstream-only artifacts (e.g. HANDOFF-map-rendering.md).
FORBIDDEN_PATH_GLOBS = [
    "HANDOFF*.md",
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

    for pattern in FORBIDDEN_PATH_GLOBS:
        for hit in sorted(ROOT.glob(pattern)):
            violations.append(
                f"{hit.relative_to(ROOT)}: upstream-only artifact present in public template")

    for rel in tracked_files():
        # vendored minified JS is noise for word-boundary patterns, not content
        if rel in SKIP_FILES or rel.endswith(".min.js") \
                or Path(rel).suffix.lower() in SKIP_SUFFIXES:
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
