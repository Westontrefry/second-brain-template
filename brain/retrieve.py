"""Semantic search over the index with metadata filters."""
from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np

from . import store


@dataclass
class Hit:
    note_id: str
    path: str
    domain: str
    topics: list[str]
    goals: list[str]
    confidence: int
    score: float
    snippet: str


def search(
    query: str,
    k: int = 5,
    domain: str | None = None,
    goal: str | None = None,
    min_confidence: int | None = None,
) -> list[Hit]:
    from .embeddings import embed_texts

    con = store.connect()
    sql = (
        "SELECT c.text, c.embedding, n.id, n.path, n.domain, n.topics, n.goals,"
        " n.confidence FROM chunks c JOIN notes n ON n.id = c.note_id"
    )
    conds, params = [], []
    if domain:
        conds.append("n.domain = ?")
        params.append(domain)
    if min_confidence is not None:
        conds.append("n.confidence >= ?")
        params.append(min_confidence)
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    rows = con.execute(sql, params).fetchall()
    con.close()

    if goal:
        rows = [r for r in rows if goal in json.loads(r[6])]
    if not rows:
        return []

    matrix = np.vstack([np.frombuffer(r[1], dtype=np.float32) for r in rows])
    scores = matrix @ np.asarray(embed_texts([query])[0], dtype=np.float32)

    best: dict[str, tuple[float, int]] = {}
    for i, s in enumerate(scores):
        note_id = rows[i][2]
        if note_id not in best or s > best[note_id][0]:
            best[note_id] = (float(s), i)

    ranked = sorted(best.values(), key=lambda t: t[0], reverse=True)[:k]
    return [
        Hit(
            note_id=rows[i][2], path=rows[i][3], domain=rows[i][4],
            topics=json.loads(rows[i][5]), goals=json.loads(rows[i][6]),
            confidence=rows[i][7], score=score, snippet=rows[i][0],
        )
        for score, i in ranked
    ]
