"""Markdown outline/syllabus parser: headings become units, list items become
concept terms. Deliberately dumb and deterministic — no AI ($0 house style);
the structure IS the signal (a syllabus's week order is its prereq claim).

Rules: the first heading (any level) is the title; every later heading starts
a unit; -, *, + and numbered list items under a unit are terms. Items before
the first unit (instructor, office hours, ...) are ignored — they describe the
course, not its concepts. A term is the text left of the first ':' or ' — '
separator, with links/bold/code markers stripped.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+?)\s*$")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")


@dataclass
class OutlineUnit:
    name: str
    terms: list[str] = field(default_factory=list)


def _strip_markup(text: str) -> str:
    text = LINK_RE.sub(r"\1", text)
    for marker in ("**", "__", "`"):
        text = text.replace(marker, "")
    return text.strip().strip("*_").strip()


def clean_term(text: str) -> str:
    """A list item reduced to its concept term: markup stripped, description
    after ':' / ' — ' / ' – ' dropped ('IPC: pipes, signals' -> 'IPC')."""
    text = _strip_markup(text)
    for sep in (":", " — ", " – "):
        if sep in text:
            text = text.split(sep, 1)[0]
    return text.strip()


def parse_outline(text: str) -> tuple[str, list[OutlineUnit]]:
    """(title, ordered units). Title is "" if the file has no headings."""
    title = ""
    seen_title = False
    units: list[OutlineUnit] = []
    for line in text.splitlines():
        h = HEADING_RE.match(line)
        if h:
            if not seen_title:
                title, seen_title = _strip_markup(h.group(2)), True
            else:
                units.append(OutlineUnit(_strip_markup(h.group(2))))
            continue
        item = ITEM_RE.match(line)
        if item and units:
            term = clean_term(item.group(1))
            if term:
                units[-1].terms.append(term)
    return title, units
