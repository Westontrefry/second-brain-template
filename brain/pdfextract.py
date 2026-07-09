"""Extract a text-layer PDF into per-chapter markdown, ready for import.

Text-layer PDFs only (books, manuals, typed notes). Scanned or handwritten PDFs
carry no extractable text — they are detected and refused, not silently imported
as empty notes. OCR/vision for handwriting is a separate path: drop a photo into
a /log or /ingest session and Claude transcribes it via vision ($0).

The chapter split follows the PDF's embedded outline (bookmarks/table of
contents), one note per top-level entry. A PDF with no outline becomes a single
note. The extraction logic (_chapters_from / _is_scanned) is pure and unit-
tested; pypdf is a thin adapter behind extract_pdf.

pypdf is an optional dependency: install with `pip install -e ".[pdf]"`.
"""
from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def missing_deps() -> list[str]:
    """PDF deps that aren't importable (empty = good to extract)."""
    return [m for m in ("pypdf",) if importlib.util.find_spec(m) is None]


class ScannedPdfError(Exception):
    """Raised when a PDF has no extractable text layer (scanned/handwritten)."""


@dataclass
class Chapter:
    title: str
    text: str


def _clean(text: str) -> str:
    """Tidy pypdf's raw page text: normalize newlines, drop runs of blanks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_scanned(pages: list[str]) -> bool:
    """A text-layer doc yields real text; scanned pages extract ~nothing."""
    return not any(len(p.strip()) > 20 for p in pages)


_PAGE_NUMBER = re.compile(r"^\s*\d{1,4}\s*$")
_CHAPTER_FOOTER = re.compile(r"^\s*(chapter|part)\b.*\d+\s*$", re.IGNORECASE)


def _chrome_key(line: str) -> str:
    """Normalize an edge line for recurrence counting: drop digits (page numbers
    change page to page) and punctuation, leaving the stable header/footer text."""
    return re.sub(r"[^a-z]", "", line.lower())


def _strip_running_headers(pages: list[str]) -> list[str]:
    """Remove running headers/footers and page numbers, deterministically.

    A header/footer is a line that recurs at the top or bottom edge of many pages
    (its page number varies, so we count on digit-stripped text). Only the first
    and last two lines of each page are ever touched, so body prose is safe. Bare
    page numbers and "Chapter 3 • 41"-style footers are dropped at the edges too.
    Single-page docs can't establish recurrence, so only the pattern rules apply.
    """
    page_lines = [p.split("\n") for p in pages]
    counts: dict[str, int] = {}
    for lines in page_lines:
        edges = lines[:2] + lines[-2:]
        for key in {_chrome_key(ln) for ln in edges if len(_chrome_key(ln)) >= 4}:
            counts[key] = counts.get(key, 0) + 1
    threshold = max(3, int(len(pages) * 0.4))
    chrome = {key for key, count in counts.items() if count >= threshold}

    cleaned: list[str] = []
    for lines in page_lines:
        last = len(lines) - 1
        kept = []
        for i, ln in enumerate(lines):
            at_edge = i < 2 or i > last - 2
            if at_edge and (
                _PAGE_NUMBER.match(ln)
                or _CHAPTER_FOOTER.match(ln)
                or (_chrome_key(ln) in chrome and len(_chrome_key(ln)) >= 4)
            ):
                continue
            kept.append(ln)
        cleaned.append("\n".join(kept).strip())
    return cleaned


def _chapters_from(
    pages: list[str], outline: list[tuple[str, int]], fallback_title: str
) -> list[Chapter]:
    """Slice page text into chapters at the outline's start pages.

    `outline` is (title, start_page_index) pairs. With no outline the whole
    document becomes one chapter. Pages before the first outline entry (cover,
    copyright, table of contents) are not their own chapter — low-value boiler-
    plate — so extraction starts at the first real entry.
    """
    if not outline:
        body = "\n\n".join(p for p in pages if p.strip()).strip()
        return [Chapter(fallback_title, body)] if body else []

    marks = sorted(outline, key=lambda t: t[1])
    chapters: list[Chapter] = []
    for i, (title, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(pages)
        body = "\n\n".join(p for p in pages[start:end] if p.strip()).strip()
        if body:
            chapters.append(Chapter(title.strip() or f"section-{i + 1}", body))
    return chapters


# A chapter (or mock test / appendix) is real content that gets its own note.
# A technical book nests sections *under* each chapter; splitting at those
# leaves would shatter one chapter into dozens of fragments, so we split at the
# chapter titles and let each chapter own its whole page range, subsections and
# all. Mock tests and appendices are content too (great quiz fodder).
_CONTENT_TITLE = re.compile(
    r"^\s*(chapter|appendix|mock\s+test|mock\s+exam|practice\s+(?:test|exam))\b",
    re.IGNORECASE,
)
# Back matter is not content, but its start page is a useful boundary: it stops
# the final chapter from swallowing the index/ads. We split at it, then drop it.
_BACKMATTER_TITLE = re.compile(
    r"^\s*(index|about\s|other\s+books|bibliography|references)\b",
    re.IGNORECASE,
)


def _flat_title(node: Any) -> str:
    """A node's title with embedded newlines/runs of spaces collapsed."""
    return " ".join(str(getattr(node, "title", "") or "").split())


def _leaf_outline(reader: object) -> list[tuple[str, int]]:
    """Flatten pypdf's nested outline to leaf (title, start_page) entries.

    The fallback for books whose entries aren't labelled "Chapter". pypdf yields
    Destination objects with a node's children following it as a sublist, e.g.
    [Part1, [Ch1, Ch2, ...], Part2, [...]]. We split at the LEAF entries because
    a container like "Part 1" holds no content of its own; each leaf's title is
    prefixed with its ancestors so context survives ("Part 1 — CHAPTER 1").
    """
    items: list[tuple[str, int]] = []

    def walk(nodes: Any, prefix: list[str]) -> None:
        seq = list(nodes)
        for idx, node in enumerate(seq):
            if isinstance(node, list):
                continue  # handled when we reach its parent, below
            title = _flat_title(node)
            following = seq[idx + 1] if idx + 1 < len(seq) else None
            if isinstance(following, list):
                # container: recurse into its children, don't emit it as a note
                walk(following, prefix + [title] if title else prefix)
                continue
            try:
                page = reader.get_destination_page_number(node)  # type: ignore[attr-defined]
            except Exception:
                continue
            if page is not None:
                full = " — ".join([*prefix, title]) if title else " — ".join(prefix)
                items.append((full, int(page)))

    try:
        walk(reader.outline, [])  # type: ignore[attr-defined]
    except Exception:
        return []
    return items


def _read_outline(reader: object) -> list[tuple[str, int]]:
    """Split points for the outline: one per chapter, subsections folded in.

    Walks the outline collecting chapter-level content marks (titles matching
    _CONTENT_TITLE) at any depth, prefixed by any container ancestor so a
    Part>Chapter nesting reads "Part 1 — CHAPTER 1". A chapter owns its whole
    span, so we do not descend into its subsections. Back-matter starts
    (index/ads) are kept only as trailing boundaries — they bound the last
    chapter, then extract_pdf drops them. Books with no chapter labels fall back
    to _leaf_outline (every leaf becomes a note, as before).
    """
    content: list[tuple[str, int]] = []
    backmatter: list[tuple[str, int]] = []

    def page_of(node: Any) -> int | None:
        try:
            page = reader.get_destination_page_number(node)  # type: ignore[attr-defined]
        except Exception:
            return None
        return int(page) if page is not None else None

    def walk(nodes: Any, prefix: list[str]) -> None:
        seq = list(nodes)
        for idx, node in enumerate(seq):
            if isinstance(node, list):
                continue
            title = _flat_title(node)
            following = seq[idx + 1] if idx + 1 < len(seq) else None
            if _CONTENT_TITLE.match(title):
                page = page_of(node)
                if page is not None:
                    full = " — ".join([*prefix, title]) if prefix else title
                    content.append((full, page))
                continue  # a chapter owns its subsections; don't descend
            if _BACKMATTER_TITLE.match(title):
                page = page_of(node)
                if page is not None:
                    backmatter.append((title, page))
                continue
            if isinstance(following, list):
                walk(following, prefix + [title] if title else prefix)

    try:
        walk(reader.outline, [])  # type: ignore[attr-defined]
    except Exception:
        return []
    if not content:
        return _leaf_outline(reader)
    first = min(page for _, page in content)
    # keep only back matter that trails the content (a glitchy page-0 dest for an
    # ads page must not become the first mark and eat the whole book)
    trailing = [(t, p) for t, p in backmatter if p > first]
    return sorted(content + trailing, key=lambda m: m[1])


def extract_pdf(path: Path) -> list[Chapter]:
    """Extract a text-layer PDF into chapters. Raises ScannedPdfError on no text."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [_clean(page.extract_text() or "") for page in reader.pages]
    if _is_scanned(pages):
        raise ScannedPdfError(
            "no extractable text — the PDF looks scanned or handwritten"
        )
    pages = _strip_running_headers(pages)
    outline = _read_outline(reader)
    chapters = _chapters_from(pages, outline, fallback_title=Path(path).stem)
    # back-matter marks bounded the final chapter; they aren't notes themselves
    return [c for c in chapters if not _BACKMATTER_TITLE.match(c.title)]
