"""brain doctor — PLAN-UX U4: every problem named with its one fixing command."""
from __future__ import annotations

from brain import doctor


def test_broken_sandbox_names_every_problem_with_fix(sandbox):
    # fresh sandbox: notes exist but no index, no graph data, no git repo
    out = doctor.render(doctor.run_checks())
    assert "index not built" in out
    assert "brain ingest" in out
    assert "map data never generated" in out
    assert "brain graph" in out or "brain ui" in out
    assert "git" in out
    assert "thing(s) to fix" in out


def test_invalid_note_fails_notes_check(sandbox):
    bad = sandbox / "knowledge" / "cs" / "2026-07-05-broken.md"
    bad.write_text("---\nid: nope\n---\nbody\n", encoding="utf-8")
    check = doctor.check_notes()
    assert not check.ok
    assert "brain validate" in check.fix


def test_empty_brain_is_healthy(sandbox):
    for f in (sandbox / "knowledge").rglob("*.md"):
        f.unlink()
    assert doctor.check_notes().ok
    assert doctor.check_index().ok


def test_healthy_when_derived_state_fresh(sandbox):
    # build the pieces doctor inspects, without embeddings: fake db rows + graph file
    import hashlib

    from brain import store

    files = sorted((sandbox / "knowledge").rglob("*.md"))
    con = store.connect()
    for f in files:
        con.execute(
            "INSERT INTO notes (id, path, content_hash, domain, source, confidence,"
            " importance, topics, goals, created, last_reviewed, exposure_count)"
            " VALUES (?, ?, ?, 'cs', 'study-session', 2, 3, '[]', '[]',"
            " '2026-07-01', '2026-07-01', 1)",
            (f.stem, str(f), hashlib.sha256(f.read_bytes()).hexdigest()),
        )
    con.commit()
    con.close()
    ui = sandbox / "ui"
    ui.mkdir(exist_ok=True)
    (ui / "graph.data.js").write_text("window.GRAPH = {};\n", encoding="utf-8")
    assert doctor.check_index().ok
    assert doctor.check_graph_data().ok
