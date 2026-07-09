"""Web cockpit — Arc B rung 2 (PLAN-UX).

The AI actions shell out to a headless `claude` process; these tests swap in a
stub binary via BRAIN_CLAUDE_BIN so no real model runs. Mechanical ops run
in-process against the sandbox. Requires the cockpit extra (fastapi) — skipped
cleanly if it isn't installed.
"""
from __future__ import annotations

import json

import pytest

from brain import cockpit

pytest.importorskip("fastapi", reason="cockpit extra not installed")
from fastapi.testclient import TestClient  # noqa: E402

# A fake `claude`: ignores its flags, emits the stream-json event sequence the
# server parses — init (session id), two text deltas, the authoritative
# assistant message (must dedup to nothing extra), then the result.
STUB = '''#!/usr/bin/env python3
import json, sys
sid = "stub-session-1"
def emit(o): sys.stdout.write(json.dumps(o) + "\\n"); sys.stdout.flush()
emit({"type": "system", "subtype": "init", "session_id": sid, "tools": []})
emit({"type": "stream_event", "event": {"type": "message_start"}})
emit({"type": "stream_event", "event": {"type": "content_block_delta",
      "delta": {"type": "text_delta", "text": "Hello "}}})
emit({"type": "stream_event", "event": {"type": "content_block_delta",
      "delta": {"type": "text_delta", "text": "world"}}})
emit({"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello world"}]}})
emit({"type": "result", "subtype": "success", "result": "Hello world", "session_id": sid})
'''


@pytest.fixture()
def client(sandbox):
    # The app serves ui/ statics; the sandbox has no real ui/, so stub one.
    (sandbox / "ui").mkdir()
    (sandbox / "ui" / "index.html").write_text("<html><body>ok</body></html>")
    return TestClient(cockpit.create_app())


@pytest.fixture()
def stub_claude(tmp_path, monkeypatch):
    p = tmp_path / "claude_stub.py"
    p.write_text(STUB)
    p.chmod(0o755)
    monkeypatch.setenv(cockpit.CLAUDE_BIN_ENV, str(p))
    return p


def parse_sse(text: str) -> list[tuple[str, dict]]:
    events = []
    for block in text.split("\n\n"):
        ev, data = "message", ""
        for ln in block.splitlines():
            if ln.startswith("event:"):
                ev = ln[6:].strip()
            elif ln.startswith("data:"):
                data += ln[5:].strip()
        if data:
            events.append((ev, json.loads(data)))
    return events


# ---- health + mechanical (no AI) ----

def test_health_reports_state(client):
    h = client.get("/api/health").json()
    assert h["ok"] is True
    assert set(cockpit.MECHANICAL_OPS) == set(h["mechanical"])


def test_mechanical_status_runs_in_process(client):
    d = client.post("/api/mechanical/status").json()
    assert d["exit_code"] == 0
    assert "notes on disk" in d["output"]


def test_mechanical_unknown_op_is_404(client):
    assert client.post("/api/mechanical/launch-rockets").status_code == 404


def test_run_cli_turns_a_blowup_into_a_payload():
    # A crash inside an op becomes a friendly result, not a traceback (ux.md #8).
    def boom(_ns):
        raise RuntimeError("kaboom")
    out = cockpit._run_cli(boom, None)
    assert out["ok"] is False
    assert "kaboom" in out["output"]


# ---- AI actions (stubbed claude) ----

def test_action_streams_session_text_and_done(client, stub_claude):
    r = client.post("/api/action", json={"action": "log", "text": "studied trees"})
    assert r.status_code == 200
    events = parse_sse(r.text)
    kinds = [e for e, _ in events]
    assert "session" in kinds and "done" in kinds
    text = "".join(d["text"] for e, d in events if e == "text")
    assert text == "Hello world"   # deltas streamed once, assistant msg deduped
    sid = next(d["session_id"] for e, d in events if e == "session")
    assert sid == "stub-session-1"


def test_reply_resumes_a_known_session(client, stub_claude):
    client.post("/api/action", json={"action": "quiz", "text": "graphs"})
    r = client.post("/api/action/reply",
                    json={"session_id": "stub-session-1", "text": "my answer"})
    events = parse_sse(r.text)
    assert any(e == "done" for e, _ in events)


def test_reply_rejects_an_unissued_session(client, stub_claude):
    r = client.post("/api/action/reply",
                    json={"session_id": "never-issued", "text": "hi"})
    events = parse_sse(r.text)
    assert any(e == "error" and "unknown session" in d["message"]
               for e, d in events)


def test_action_without_claude_streams_an_error(client, monkeypatch):
    monkeypatch.setenv(cockpit.CLAUDE_BIN_ENV, "/no/such/claude")
    r = client.post("/api/action", json={"action": "quiz", "text": "x"})
    events = parse_sse(r.text)
    assert any(e == "error" for e, _ in events)
    assert not any(e == "done" for e, _ in events)


# ---- unit-level guards ----

def test_action_prompt_shapes():
    assert "studied trees" in cockpit._action_prompt("log", "studied trees")
    assert cockpit._action_prompt("quiz", "").startswith("Quiz me")
    # the node "Expand" button invokes the /frontier skill on the topic
    expand = cockpit._action_prompt("expand", "graphs")
    assert "/frontier" in expand and "graphs" in expand
    with pytest.raises(ValueError):
        cockpit._action_prompt("delete-everything", "")


def test_missing_deps_lists_uninstalled(monkeypatch):
    import importlib.util
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec",
                        lambda n: None if n == "fastapi" else real(n))
    assert "fastapi" in cockpit.missing_deps()
