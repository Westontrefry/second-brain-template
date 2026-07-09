"""Ingest/ drop-folder sweep: routing, dedup layers, and the GUI surfaces.

The embedding sync is mocked out (same pattern as test_pdfextract) — the sweep
delegates to the separately-tested import pipeline; what's under test here is
the folder protocol: domain routing, move-to-processed, the collision guards,
and that files are never silently guessed into a domain.
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def no_sync(monkeypatch):
    import brain.ingest

    monkeypatch.setattr(brain.ingest, "sync", lambda *a, **k: None)


def _drop_md(sandbox: Path, domain: str, name: str, body: str) -> Path:
    target = sandbox / "Ingest" / domain / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


MD_BODY = "# Load Balancing\n\nRound-robin vs least-connections tradeoffs.\n"


def test_ensure_layout_creates_domain_folders(sandbox, no_sync):
    from brain.config import load_config
    from brain.inbox import sweep

    sweep()
    for domain in load_config()["domains"]:
        assert (sandbox / "Ingest" / domain).is_dir()


def test_waiting_files_excludes_processed_and_dotfiles(sandbox):
    from brain.inbox import waiting_files

    _drop_md(sandbox, "cs", "a.md", MD_BODY)
    _drop_md(sandbox, "processed", "old.md", MD_BODY)
    _drop_md(sandbox, "cs", ".DS_Store", "")
    assert [p.name for p in waiting_files()] == ["a.md"]


def test_root_file_reported_never_guessed(sandbox, no_sync):
    from brain.inbox import sweep

    stray = sandbox / "Ingest"
    stray.mkdir(exist_ok=True)
    stray = stray / "stray.md"
    stray.write_text(MD_BODY, encoding="utf-8")

    result = sweep()
    assert not result.created
    assert stray.exists()  # left in place, not moved
    reasons = {p.name: r for p, r in result.skipped}
    assert "Ingest/<domain>/" in reasons["stray.md"]


def test_unknown_subfolder_skipped(sandbox, no_sync):
    from brain.inbox import sweep

    _drop_md(sandbox, "notadomain", "x.md", MD_BODY)
    result = sweep()
    assert not result.created
    reasons = {p.name: r for p, r in result.skipped}
    assert "not a domain" in reasons["notadomain"]


def test_markdown_swept_into_domain_and_moved(sandbox, no_sync):
    from brain.inbox import sweep
    from brain.schema import parse_note

    _drop_md(sandbox, "cs", "lb.md", MD_BODY)
    result = sweep()

    assert len(result.created) == 1
    note, errors = parse_note(result.created[0])
    assert not errors and note is not None
    assert note.meta["domain"] == "cs"
    assert note.meta["source"] == "import"
    assert note.meta["confidence"] == 1
    # original moved out of the scan set
    assert not (sandbox / "Ingest" / "cs" / "lb.md").exists()
    assert (sandbox / "Ingest" / "processed" / "cs" / "lb.md").exists()


def test_redrop_is_dedup_noop_but_still_cleared(sandbox, no_sync):
    from brain.inbox import sweep, waiting_files

    _drop_md(sandbox, "cs", "lb.md", MD_BODY)
    sweep()
    _drop_md(sandbox, "cs", "lb.md", MD_BODY)  # same content again
    result = sweep()

    assert not result.created  # content-hash dedup
    assert not waiting_files()  # but the drop folder is cleared
    assert (sandbox / "Ingest" / "processed" / "cs" / "lb-2.md").exists()


def test_dry_run_imports_and_moves_nothing(sandbox, no_sync):
    from brain.inbox import sweep

    dropped = _drop_md(sandbox, "cs", "lb.md", MD_BODY)
    result = sweep(dry_run=True)
    assert len(result.created) == 1  # previewed
    assert not result.moved
    assert dropped.exists()
    assert not list((sandbox / "knowledge" / "cs").glob("*load-balancing*"))


def test_export_folder_swept_as_one_entry(sandbox, no_sync):
    from brain.inbox import sweep

    _drop_md(sandbox, "cs", "export/one.md", "# One\n\nbody one\n")
    _drop_md(sandbox, "cs", "export/two.md", "# Two\n\nbody two\n")
    result = sweep()
    assert len(result.created) == 2
    assert (sandbox / "Ingest" / "processed" / "cs" / "export").is_dir()
    assert not (sandbox / "Ingest" / "cs" / "export").exists()


def test_pdf_collision_guard_and_force(sandbox, no_sync):
    pytest.importorskip("pypdf")
    from test_pdfextract import _make_pdf

    from brain.inbox import sweep

    buf = _make_pdf(
        ["cover page",
         "Chapter One body text about caching",
         "Chapter Two body text about sharding"],
        [("Chapter One", 1), ("Chapter Two", 2)],
    )
    pdf = sandbox / "Ingest" / "cs" / "Design Book.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.write_bytes(buf.getvalue())
    first = sweep()
    assert len(first.created) == 2

    # same book dropped again: slug guard refuses before extraction
    pdf.write_bytes(buf.getvalue())
    second = sweep()
    assert not second.created
    assert pdf.exists()  # left in place for the user to decide
    reasons = {p.name: r for p, r in second.skipped}
    assert "--force" in reasons["Design Book.pdf"]

    # --force re-runs the import (content-hash still dedups the chapters)
    third = sweep(force=True)
    assert not pdf.exists()
    assert not third.created  # identical content skipped downstream


def _enrich_and_retag(note_path: Path, new_tag: str) -> None:
    """Simulate the /ingest enrichment pass: append a ``## Related`` block (the
    one sanctioned body edit) and retag the note (as the ACE chapter-split /
    manual enrichment did). Both changes are what defeated the two dedup guards.
    """
    import yaml

    from brain.schema import parse_note

    note, errors = parse_note(note_path)
    assert not errors and note is not None
    note.meta["topics"] = [new_tag]
    body = note.body.strip() + "\n\n## Related\n\n- [[some-other-note]] — related.\n"
    note_path.write_text(
        "---\n"
        + yaml.safe_dump(note.meta, sort_keys=False, allow_unicode=True)
        + "---\n\n"
        + body
        + "\n",
        encoding="utf-8",
    )


def test_enriched_retagged_book_reswept_imports_zero_duplicates(sandbox, no_sync):
    pytest.importorskip("pypdf")
    from test_pdfextract import _make_pdf

    from brain.inbox import sweep

    buf = _make_pdf(
        ["cover page",
         "Chapter One body text about caching",
         "Chapter Two body text about sharding"],
        [("Chapter One", 1), ("Chapter Two", 2)],
    )
    pdf = sandbox / "Ingest" / "cs" / "PacktACEGuide.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.write_bytes(buf.getvalue())
    first = sweep()
    assert len(first.created) == 2

    # enrich + retag the imported chapters, exactly as the ACE guide was:
    # topics renamed away from the book slug, a ## Related block appended.
    for note_path in first.created:
        _enrich_and_retag(note_path, "google-cloud-associate-cloud-engineer-guide")

    # re-drop the identical book. The filename guard (Gap 1) refuses it despite
    # the retag defeating the book-slug tag guard, so nothing is re-imported.
    pdf.write_bytes(buf.getvalue())
    second = sweep()
    assert not second.created
    reasons = {p.name: r for p, r in second.skipped}
    assert "already imported" in reasons["PacktACEGuide.pdf"]
    assert "--force" in reasons["PacktACEGuide.pdf"]

    # even forcing past the filename/tag guards, content-hash dedup (Gap 2) now
    # strips the ## Related section before hashing, so the enriched chapters
    # still hash identically and import zero duplicates.
    pdf.write_bytes(buf.getvalue())
    third = sweep(force=True)
    assert not third.created
    # exactly the two original chapters remain — no -2.md duplicates landed
    chapter_notes = [p.name for p in (sandbox / "knowledge" / "cs").glob("*chapter-*.md")]
    assert len(chapter_notes) == 2
    assert not any(n.endswith("-2.md") for n in chapter_notes)


def test_dedup_still_distinguishes_different_content(sandbox, no_sync):
    """Stripping ## Related for the hash must not collapse genuinely different
    notes that happen to share an identical Related block."""
    from brain.importer import import_dir

    _drop_md(sandbox, "cs", "a.md",
             "# A\n\nAlpha core body.\n\n## Related\n\n- [[x]] — r.\n")
    _drop_md(sandbox, "cs", "b.md",
             "# B\n\nBeta core body.\n\n## Related\n\n- [[x]] — r.\n")
    result = import_dir(sandbox / "Ingest" / "cs", domain="cs")
    assert len(result.created) == 2  # different cores, identical Related


def test_home_screen_shows_waiting_nudge(sandbox):
    from brain.home import render_home

    _drop_md(sandbox, "cs", "waiting.md", MD_BODY)
    out = render_home()
    assert "inbox: 1 file(s) waiting in Ingest/" in out

    (sandbox / "Ingest" / "cs" / "waiting.md").unlink()
    assert "inbox:" not in render_home()


def test_cockpit_exposes_inbox_op(sandbox, no_sync):
    from brain.cockpit import MECHANICAL_OPS, run_mechanical

    assert "inbox" in MECHANICAL_OPS
    _drop_md(sandbox, "cs", "lb.md", MD_BODY)
    out = run_mechanical("inbox")
    assert out["ok"]
    assert "imported 1 note(s)" in out["output"]
