"""First-touch guidance: is this the user's first time using a given skill?

Read-only by design. Each skill's "first time" is derived from state the skill
itself changes on its first successful run, so there is no separate "mark seen"
step and nothing here writes:

    quiz     no `assess` event tagged source=quiz
    debrief  no `assess` event tagged source=debrief
    review   no `exposure` event tagged source=review
    ingest   no note carries source: import
    path     no overlay file under ui/paths/

`is_first_touch(skill)` returns True when it IS the first touch. `explainer(skill)`
returns the one-time copy on the first touch and "" afterwards. The copy lives
here so its tone is edited in one place (warm, plain, honest; see docs/ux.md #5,
#7 and the Arc A grill, 2026-07-05).
"""
from __future__ import annotations

import json

from .config import knowledge_dir, root
from .events import events_path


def _events() -> list[dict]:
    path = events_path()
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _no_event(kind: str, source: str) -> bool:
    """True when no event of this kind carries this source tag. Legacy sourceless
    events never match a source, so a user with only pre-tag history sees the new
    explainer once, then their next sourced run silences it (self-healing)."""
    return not any(e.get("kind") == kind and e.get("source") == source
                   for e in _events())


def _first_quiz() -> bool:
    return _no_event("assess", "quiz")


def _first_debrief() -> bool:
    return _no_event("assess", "debrief")


def _first_review() -> bool:
    return _no_event("exposure", "review")


def _first_ingest() -> bool:
    """First import = no note yet carries source: import. Short-circuits on the
    first import note found, so it is O(1) for anyone who has imported before."""
    from .schema import parse_note

    for path in knowledge_dir().rglob("*.md"):
        note, _ = parse_note(path)
        if note is not None and note.meta.get("source") == "import":
            return False
    return True


def _first_path() -> bool:
    paths_dir = root() / "ui" / "paths"
    if not paths_dir.is_dir():
        return True
    return not any(paths_dir.glob("*.json"))


DETECTORS = {
    "quiz": _first_quiz,
    "debrief": _first_debrief,
    "review": _first_review,
    "ingest": _first_ingest,
    "path": _first_path,
}

# Warm, plain, honest, no em-dashes. One paragraph each; the skill prepends it
# once and then proceeds normally in the same turn (never a separate question).
EXPLAINERS = {
    "quiz": (
        "First quiz, so here's how it works. I'll ask a few questions at the edge "
        "of what your notes show, then grade your answers against a depth rubric and "
        "quote your own words back as the receipts. That updates your proven "
        "confidence, which is tracked separately from the confidence you claimed "
        "when you logged a note. It takes a few messages to work through, and that's "
        "just the format, not friction."
    ),
    "review": (
        "First review session, so a quick word on what it does. I'll pull up topics "
        "that are weak or going stale and walk you through active recall on them. "
        "This records that you revisited them, which slows their decay on the map. It "
        "doesn't grade you or move your proven confidence. For that, ask me to quiz "
        "you."
    ),
    "ingest": (
        "First import, so here's what happens. I'll bring your existing notes in, "
        "then enrich each one with topics, goal links, and an importance rating, "
        "without touching the note bodies. The very first run also downloads a small "
        "embedding model, around 90MB, one time, and it stays on your machine. "
        "Nothing leaves your computer."
    ),
    "path": (
        "First pathway, so here's the idea. You give me a free-text goal, like "
        "preparing for system design interviews, and I compile it into an ordered "
        "route through your topics, marking which ones you're strong on and which "
        "need work. It shows up as an overlay you can toggle on the map. It doesn't "
        "change any of your scores, it just plans a way through them."
    ),
    "debrief": (
        "First debrief, so here's the shape of it. Paste the summary block from a "
        "practice session or mock interview, and I'll turn it into a session note and "
        "record proven-confidence assessments for the topics it covered, each with "
        "quoted receipts. I only read what you paste, I won't invent a score you "
        "didn't earn."
    ),
}


def is_first_touch(skill: str) -> bool:
    detector = DETECTORS.get(skill)
    if detector is None:
        raise ValueError(
            f"unknown skill for first-touch: {skill!r} "
            f"(known: {', '.join(sorted(DETECTORS))})"
        )
    return detector()


def explainer(skill: str) -> str:
    """The one-time explainer if this is the first touch, else ''."""
    return EXPLAINERS[skill] if is_first_touch(skill) else ""
