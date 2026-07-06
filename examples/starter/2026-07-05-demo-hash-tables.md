---
id: 2026-07-05-demo-hash-tables
title: Hash tables — buckets and collisions
domain: cs
topics: [hash tables, algorithms]
source: demo
confidence: 2
ai_confidence: null
ai_confidence_rationale: null
last_assessed: null
importance: 4
goals: [dsa-interviews]
created: 2026-07-05
last_reviewed: 2026-07-05
exposure_count: 1
---

A hash function maps a key to a bucket index; collisions land in the same
bucket and chain into a list. Average O(1) lookup, worst case O(n) if
everything collides. This is what made the fix in
[[2026-07-05-demo-big-o-basics]] work — the set was a hash table underneath.
