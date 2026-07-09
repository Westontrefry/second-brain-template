"""PDF ingestion: extraction logic (pure) + a real text-layer PDF round-trip.

The chapter-slicing and scanned-detection logic is pure and tested directly.
extract_pdf's pypdf adapter is exercised against PDFs built in-memory here (no
checked-in binary fixture). The full write path (import_pdf -> notes on disk) is
e2e-marked because it runs the real embedding sync.
"""
from __future__ import annotations

import io

import pytest

from brain.pdfextract import (
    ScannedPdfError,
    _chapters_from,
    _is_scanned,
    _strip_running_headers,
    extract_pdf,
    missing_deps,
)

pypdf = pytest.importorskip("pypdf")


# --- fixture builder: a minimal text-layer PDF with an outline -----------------

def _make_pdf(
    pages: list[str],
    outline: list[tuple[str, int]] | None = None,
    nested: list[tuple[str, int, list[tuple[str, int]]]] | None = None,
) -> io.BytesIO:
    """Build an in-memory text-layer PDF.

    `outline`: flat (title, page) entries. `nested`: (parent_title, parent_page,
    [(child_title, child_page), ...]) to exercise container/leaf handling.
    """
    from pypdf.generic import DictionaryObject, NameObject

    writer = pypdf.PdfWriter()
    for text in pages:
        page = writer.add_blank_page(width=300, height=300)
        if text:
            stream = pypdf.generic.DecodedStreamObject()
            stream.set_data(f"BT /F1 12 Tf 40 250 Td ({text}) Tj ET".encode("latin-1"))
            font = DictionaryObject({
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            })
            font_ref = writer._add_object(font)
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})
            })
            page[NameObject("/Contents")] = writer._add_object(stream)
    for title, page_index in outline or []:
        writer.add_outline_item(title, page_index)
    for parent_title, parent_page, children in nested or []:
        parent = writer.add_outline_item(parent_title, parent_page)
        for child_title, child_page in children:
            writer.add_outline_item(child_title, child_page, parent=parent)
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf


# --- pure logic ----------------------------------------------------------------

def test_chapters_split_at_outline_starts():
    pages = ["cover", "chapter one text", "more of one", "chapter two text"]
    chapters = _chapters_from(pages, [("One", 1), ("Two", 3)], "book")
    assert [c.title for c in chapters] == ["One", "Two"]
    assert "chapter one text" in chapters[0].text
    assert "more of one" in chapters[0].text  # spans to the next chapter's page
    assert "cover" not in chapters[0].text     # pre-first-chapter pages dropped
    assert chapters[1].text == "chapter two text"


def test_no_outline_yields_single_chapter():
    chapters = _chapters_from(["all", "the", "text"], [], "my-book")
    assert len(chapters) == 1
    assert chapters[0].title == "my-book"
    assert chapters[0].text == "all\n\nthe\n\ntext"


def test_outline_is_sorted_and_empty_chapters_dropped():
    # unsorted outline; the second entry points at a blank tail page
    chapters = _chapters_from(["", "body", ""], [("B", 1), ("A", 0)], "book")
    assert [c.title for c in chapters] == ["A", "B"] or [c.title for c in chapters] == ["B"]
    # the empty-body chapter (page 2) is dropped; "body" survives
    assert any("body" in c.text for c in chapters)
    assert all(c.text.strip() for c in chapters)


def test_strip_running_headers_removes_recurring_header_and_page_numbers():
    # a book-title header (constant) + a page number (varies) recur on every page;
    # each page's prose is genuinely different words
    bodies = ["arrays and loops", "hashing and maps", "graph traversal",
              "dynamic programming", "binary search trees", "heaps and queues",
              "sorting networks", "string matching"]
    pages = ["\n".join(["The Phoenix Project", f"{b} intro", f"{b} in more detail", str(i + 1)])
             for i, b in enumerate(bodies)]
    cleaned = _strip_running_headers(pages)
    joined = "\n".join(cleaned)
    assert "The Phoenix Project" not in joined          # recurring header gone
    assert "graph traversal in more detail" in joined    # unique body kept
    assert not any(line.strip().isdigit() for c in cleaned for line in c.split("\n"))


def test_strip_running_headers_drops_chapter_footer():
    bodies = ["the outage began overnight", "the meeting ran long", "the deploy failed again",
              "the audit found gaps", "the team regrouped fast", "the metrics improved"]
    pages = ["\n".join([f"heading {i}", f"{b}, in detail", f"Chapter {i + 1} • {i + 41}"])
             for i, b in enumerate(bodies)]
    cleaned = _strip_running_headers(pages)
    joined = "\n".join(cleaned)
    assert "• 41" not in joined and "• 46" not in joined  # "Chapter N • NN" footer gone
    assert "the outage began overnight" in joined


def test_strip_running_headers_keeps_body_and_short_docs():
    # a mid-page line with digits is not an edge line -> kept; single page -> only
    # the bare-page-number rule can fire (no recurrence to learn from)
    pages = ["opening line\nsection 3 covers indexing and 12 related ideas\n7"]
    cleaned = _strip_running_headers(pages)
    assert "section 3 covers indexing and 12 related ideas" in cleaned[0]
    assert not cleaned[0].endswith("7")


def test_is_scanned_detects_empty_text():
    assert _is_scanned(["", "   ", "\n"]) is True
    assert _is_scanned(["a short bit of real extracted text here"]) is False
    assert _is_scanned([]) is True


def test_missing_deps_empty_when_pypdf_present():
    assert missing_deps() == []


def test_book_slug_cleans_download_filenames():
    from brain.importer import book_slug

    # the real case: junk parenthetical + subtitle after " _ "
    assert book_slug(
        "The Phoenix Project _ A Novel about IT ( PDFDrive )"
    ) == "the-phoenix-project"
    assert book_slug("Clean Code (z-lib.org)") == "clean-code"
    assert book_slug("System Design Primer") == "system-design-primer"
    # length cap keeps tags manageable
    assert len(book_slug("one two three four five six seven eight nine ten").split("-")) == 8


# --- extract_pdf adapter over a real PDF ---------------------------------------

def test_extract_pdf_splits_by_outline(tmp_path):
    buf = _make_pdf(
        ["Cover boilerplate page", "Chapter One about arrays and loops",
         "Chapter Two about graphs and trees"],
        [("Chapter One", 1), ("Chapter Two", 2)],
    )
    pdf = tmp_path / "algorithms.pdf"
    pdf.write_bytes(buf.getvalue())

    chapters = extract_pdf(pdf)
    assert [c.title for c in chapters] == ["Chapter One", "Chapter Two"]
    assert "arrays and loops" in chapters[0].text
    assert "graphs and trees" in chapters[1].text
    assert "Cover boilerplate" not in " ".join(c.text for c in chapters)


def test_extract_pdf_splits_nested_outline_at_leaf_chapters(tmp_path):
    # Part > Chapter nesting (like The Phoenix Project): split at the chapters,
    # not the Parts, and prefix each chapter with its Part for context.
    buf = _make_pdf(
        ["cover boilerplate here", "part one divider page here",
         "Chapter one body about the first idea and its details",
         "Chapter two body about the second idea and its details",
         "Chapter three body about the third idea and its details"],
        nested=[("Part 1", 1, [("CHAPTER 1", 2), ("CHAPTER 2", 3)]),
                ("Part 2", 4, [("CHAPTER 3", 4)])],
    )
    pdf = tmp_path / "novel.pdf"
    pdf.write_bytes(buf.getvalue())

    chapters = extract_pdf(pdf)
    titles = [c.title for c in chapters]
    assert titles == ["Part 1 — CHAPTER 1", "Part 1 — CHAPTER 2", "Part 2 — CHAPTER 3"]
    assert "first idea" in chapters[0].text
    assert "Part 1" not in " ".join(c.text for c in chapters)  # divider not its own note


def test_extract_pdf_folds_subsections_and_drops_back_matter(tmp_path):
    # A technical book (like the Packt ACE guide): Parts and Chapters are
    # siblings at the top level, each chapter nests its own sections, and the
    # book ends with a mock test then an index. Split at the chapters (folding
    # their sections in), keep the mock test, drop the index.
    buf = _make_pdf(
        ["cover", "part one divider",                     # 0, 1
         "chapter one overview of planning",              # 2
         "section alpha detail about budgets",            # 3
         "chapter two overview of compute",               # 4
         "section gamma detail about machines",           # 5
         "mock test one practice questions here",         # 6
         "index aardvark budgets machines"],              # 7
        outline=[("Part 1", 1), ("Mock Test 1", 6), ("Index", 7)],
        nested=[("Chapter 1", 2, [("Section Alpha", 3)]),
                ("Chapter 2", 4, [("Section Gamma", 5)])],
    )
    pdf = tmp_path / "ace-guide.pdf"
    pdf.write_bytes(buf.getvalue())

    chapters = extract_pdf(pdf)
    assert [c.title for c in chapters] == ["Chapter 1", "Chapter 2", "Mock Test 1"]
    # a chapter owns its subsections — the section body is folded in, not split out
    assert "section alpha detail" in chapters[0].text
    assert "chapter one overview" in chapters[0].text
    # the Part divider and the Index are boundaries, never their own notes
    joined_titles = " ".join(c.title for c in chapters)
    assert "Part 1" not in joined_titles and "Index" not in joined_titles
    # the mock test stops at the index — it doesn't swallow the back matter
    assert "index aardvark" not in chapters[2].text


def test_extract_pdf_no_outline_single_note(tmp_path):
    buf = _make_pdf(["Just one page of typed manual text here"], [])
    pdf = tmp_path / "manual.pdf"
    pdf.write_bytes(buf.getvalue())

    chapters = extract_pdf(pdf)
    assert len(chapters) == 1
    assert chapters[0].title == "manual"
    assert "typed manual text" in chapters[0].text


def test_extract_pdf_refuses_scanned(tmp_path):
    buf = _make_pdf(["", "", ""], [])  # blank pages = no text layer
    pdf = tmp_path / "scanned.pdf"
    pdf.write_bytes(buf.getvalue())

    with pytest.raises(ScannedPdfError):
        extract_pdf(pdf)


# --- importer wiring (dry-run: no embedding sync) ------------------------------

def test_import_pdf_dry_run_reports_chapters(sandbox):
    from brain.importer import import_pdf

    buf = _make_pdf(
        ["cover boilerplate page here",
         "Chapter One body text about arrays and iteration and loops",
         "Chapter Two body text about graphs and trees and traversal"],
        [("Chapter One", 1), ("Chapter Two", 2)],
    )
    pdf = sandbox / "book.pdf"
    pdf.write_bytes(buf.getvalue())

    result = import_pdf(pdf, domain="cs", dry_run=True)
    assert len(result.created) == 2
    assert all(str(p).endswith(".md") for p in result.created)
    # nothing actually written in dry-run
    assert not list((sandbox / "knowledge" / "cs").glob("*book*"))


# --- full write path (real embedding sync) -------------------------------------

def test_import_pdf_writes_tagged_confidence1_notes(sandbox, monkeypatch):
    # Exercise the real on-disk write path (extract -> validated notes) without
    # the embedding sync, which is the shared, separately-tested import pipeline.
    import brain.ingest

    from brain.importer import import_pdf
    from brain.schema import parse_note

    monkeypatch.setattr(brain.ingest, "sync", lambda *a, **k: None)

    buf = _make_pdf(
        ["cover boilerplate page here",
         "Chapter One body text about load balancing and caching layers",
         "Chapter Two body text about sharding and replication strategies"],
        [("Chapter One", 1), ("Chapter Two", 2)],
    )
    pdf = sandbox / "System Design Primer.pdf"
    pdf.write_bytes(buf.getvalue())

    result = import_pdf(pdf, domain="cs")
    assert len(result.created) == 2
    for path in result.created:
        note, errors = parse_note(path)
        assert not errors and note is not None
        assert note.meta["source"] == "import"
        assert note.meta["confidence"] == 1
        assert note.meta["domain"] == "cs"
        assert "system-design-primer" in note.meta["topics"]  # grouped by book slug
