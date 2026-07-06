"""The web cockpit — Arc B rung 2 (PLAN-UX). An OPTIONAL local surface that
turns the map into a control panel: click Quiz/Log/Review and the same skills
a chat session would run fire in a headless Claude Code process, streamed back
live; mechanical ops (ingest/graph/status/doctor/gaps) run in-process with no AI.

Trust model (locked, PLAN-UX Arc B rung 2):
- $0 marginal cost: the AI bridge is `claude -p` (subscription-covered), not an
  API provider. No keys, no llm/ layer.
- The server NEVER writes knowledge/, events, or scores itself. Every write goes
  through a skill inside the headless session, exactly as in chat — the same
  sanctioned paths, the same evidence discipline.
- Headless sessions are per-action; `--resume` only continues the same action's
  follow-up turns (quiz/review answers). No long-lived session.
- localhost only, single user. The headless action runs with
  `--permission-mode bypassPermissions` because it must run the skills' own
  `brain` write commands unattended; this is the user driving their own tools on
  their own machine, and the skills still enforce their invariants in their text.

Requires the optional extra: `pip install -e ".[cockpit]"`. Without it,
`brain cockpit` prints the install hint (see cli.cmd_cockpit), never a traceback.

(No `from __future__ import annotations` here on purpose: FastAPI resolves the
endpoints' Pydantic-model annotations at runtime, and stringized annotations
from that future-import can't be resolved for classes defined in this closure.)
"""
import asyncio
import io
import json
import os
import shutil
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path

from .config import root

# The natural-language prompt each AI button sends into the headless session.
# Phrased so the matching skill auto-triggers (ux.md #1 — the conversation is
# the front door); the skill, not the server, does every write.
CLAUDE_BIN_ENV = "BRAIN_CLAUDE_BIN"  # override the `claude` binary (tests use a stub)


def missing_deps() -> list[str]:
    """Optional server deps that aren't importable (empty = good to serve)."""
    import importlib.util

    return [m for m in ("fastapi", "uvicorn") if importlib.util.find_spec(m) is None]


def claude_bin() -> str | None:
    """Path to the headless Claude Code binary, or None if unavailable."""
    override = os.environ.get(CLAUDE_BIN_ENV)
    if override:
        return override if Path(override).exists() else None
    return shutil.which("claude")


def _action_prompt(action: str, text: str) -> str:
    text = (text or "").strip()
    if action == "log":
        return f"Log this study note: {text}" if text else "Log a study note."
    if action == "quiz":
        return f"Quiz me on {text}." if text else "Quiz me at the edge of my evidence."
    if action == "review":
        return f"Run a review session on {text}." if text else "Run a review session."
    raise ValueError(f"unknown AI action: {action!r}")


# ---- mechanical ops: run the CLI's own command functions, capture stdout ----
# No AI, no subprocess — import the library, run it, hand back the text. These
# touch only disposable derived state (the index, graph.data.js).

def _run_cli(func, ns: Namespace) -> dict:
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = func(ns)
    except Exception as e:  # never leak a traceback to the panel (ux.md #8)
        return {"ok": False, "exit_code": 1, "output": f"{type(e).__name__}: {e}"}
    return {"ok": code == 0, "exit_code": int(code or 0), "output": buf.getvalue()}


def run_mechanical(op: str) -> dict:
    """Run one no-AI op by name. Raises KeyError for an unknown op."""
    from . import cli

    ops = {
        "ingest": (cli.cmd_ingest, Namespace(full=False)),
        "graph": (cli.cmd_graph, Namespace()),
        "status": (cli.cmd_status, Namespace()),
        "doctor": (cli.cmd_doctor, Namespace()),
        "gaps": (cli.cmd_gaps, Namespace(goal=None, n=10)),
    }
    func, ns = ops[op]  # KeyError → 404 at the route
    return _run_cli(func, ns)


MECHANICAL_OPS = ("ingest", "graph", "status", "doctor", "gaps")


# ---- SSE helpers ----

def _sse(event: str, data: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode("utf-8")


async def _stream_claude(prompt: str, resume: str | None, issued: set[str]):
    """Spawn a headless Claude turn and yield SSE bytes.

    Emits: `session` (once, with the session id), `text` deltas, `tool`
    breadcrumbs, then exactly one terminal `done` or `error`.
    """
    binary = claude_bin()
    if not binary:
        yield _sse("error", {"message": "Claude Code CLI not found on PATH — "
                                        "the cockpit needs it for AI actions."})
        return

    cmd = [binary, "-p", prompt,
           "--output-format", "stream-json", "--verbose",
           "--include-partial-messages",
           "--permission-mode", "bypassPermissions"]
    if resume:
        if resume not in issued:
            yield _sse("error", {"message": "unknown session"})
            return
        cmd += ["--resume", resume]

    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=str(root()),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        limit=8 * 1024 * 1024,
    )

    session_id: str | None = None
    streamed = ""   # what we've already sent for the current assistant message
    result_text = ""
    try:
        async for raw in proc.stdout:
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = evt.get("type")

            if etype == "system" and evt.get("subtype") == "init":
                session_id = evt.get("session_id")
                if session_id:
                    issued.add(session_id)
                    yield _sse("session", {"session_id": session_id})

            elif etype == "stream_event":
                inner = evt.get("event", {})
                if inner.get("type") == "content_block_delta":
                    delta = inner.get("delta", {})
                    if delta.get("type") == "text_delta":
                        piece = delta.get("text", "")
                        if piece:
                            streamed += piece
                            yield _sse("text", {"text": piece})
                elif inner.get("type") == "message_start":
                    streamed = ""

            elif etype == "assistant":
                # Authoritative text for the turn; send only what deltas missed
                # (dedup-by-prefix works whether or not partials were emitted).
                content = evt.get("message", {}).get("content", [])
                full = "".join(b.get("text", "") for b in content
                               if b.get("type") == "text")
                if full:
                    tail = full[len(streamed):] if full.startswith(streamed) else full
                    if tail:
                        yield _sse("text", {"text": tail})
                    streamed = ""
                for b in content:
                    if b.get("type") == "tool_use":
                        yield _sse("tool", {"name": b.get("name", "")})

            elif etype == "result":
                result_text = evt.get("result", "") or ""

        await proc.wait()
    finally:
        if proc.returncode is None:
            proc.kill()

    if proc.returncode not in (0, None):
        err = (await proc.stderr.read()).decode("utf-8", "replace").strip()
        yield _sse("error", {"message": err or f"claude exited {proc.returncode}"})
        return
    yield _sse("done", {"session_id": session_id, "result": result_text})


def create_app():
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse, StreamingResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel

    class ActionBody(BaseModel):
        action: str
        text: str = ""

    class ReplyBody(BaseModel):
        session_id: str
        text: str

    app = FastAPI(title="Second Brain cockpit")
    app.state.issued_sessions = set()
    ui_dir = root() / "ui"

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True, "root": str(root()), "claude": claude_bin() is not None,
                "mechanical": list(MECHANICAL_OPS)}

    @app.post("/api/mechanical/{op}")
    def mechanical(op: str) -> dict:
        if op not in MECHANICAL_OPS:
            raise HTTPException(status_code=404, detail=f"unknown op: {op}")
        return run_mechanical(op)

    @app.post("/api/action")
    def action(body: ActionBody):
        try:
            prompt = _action_prompt(body.action, body.text)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        gen = _stream_claude(prompt, None, app.state.issued_sessions)
        return StreamingResponse(gen, media_type="text/event-stream")

    @app.post("/api/action/reply")
    def reply(body: ReplyBody):
        gen = _stream_claude(body.text, body.session_id, app.state.issued_sessions)
        return StreamingResponse(gen, media_type="text/event-stream")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(ui_dir / "index.html")

    # Everything else (graph.data.js, d3, etc.) served straight from ui/.
    app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")
    return app


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    import uvicorn

    from .graph import export

    export()  # fresh data before the tab opens, same courtesy as `brain ui`
    print(f"cockpit on http://{host}:{port}  (Ctrl-C to stop)")
    if not claude_bin():
        print("note: Claude Code CLI not found — mechanical buttons work, "
              "AI actions (quiz/log/review) need it on PATH")
    uvicorn.run(create_app(), host=host, port=port, log_level="warning")
