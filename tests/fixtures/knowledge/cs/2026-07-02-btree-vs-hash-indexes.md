---
id: 2026-07-02-btree-vs-hash-indexes
domain: cs
topics: [databases, indexing, b-trees]
source: study-session
confidence: 3
ai_confidence: null
ai_confidence_rationale: null
last_assessed: null
importance: 4
goals: [dsa-interviews, uf-cs-degree]
created: 2026-07-02
last_reviewed: 2026-07-02
exposure_count: 1
---

B-tree indexes keep keys sorted, so they serve range queries (`WHERE age > 30`) and
ordered scans, not just point lookups. Hash indexes are O(1) for equality but useless
for ranges. Postgres defaults to B-tree for this reason — most real queries mix
equality and range predicates.

Still shaky on: when the planner chooses a sequential scan over an index even when an
index exists (selectivity thresholds). Need to revisit with EXPLAIN examples.
