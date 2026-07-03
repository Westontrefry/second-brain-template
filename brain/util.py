"""Small shared helpers."""
from __future__ import annotations

import re
from typing import Iterable


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def slug_keys(entry_id: str, aliases: Iterable[str] = ()) -> set[str]:
    """Slugified join keys for a concept/roadmap topic: its id plus all aliases.

    This is THE join rule between structured vocabularies (roadmaps, the concept
    registry) and note topics: two terms refer to the same thing iff their slugs
    match. Note topics are never renamed to fit — aliases absorb the difference.
    """
    return {slugify(entry_id)} | {slugify(a) for a in aliases}
