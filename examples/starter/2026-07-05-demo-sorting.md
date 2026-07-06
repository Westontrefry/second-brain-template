---
id: 2026-07-05-demo-sorting
title: Merge sort vs quicksort, first pass
domain: cs
topics: [sorting, big o, algorithms]
source: demo
confidence: 2
ai_confidence: null
ai_confidence_rationale: null
last_assessed: null
importance: 3
goals: [dsa-interviews]
created: 2026-07-05
last_reviewed: 2026-07-05
exposure_count: 1
---

Read the chapter on divide-and-conquer sorts. Merge sort is a guaranteed
O(n log n) but needs extra space; quicksort is usually faster in practice but
can degrade to O(n²) on sorted input with a bad pivot. Still shaky on why the
partition step works — need to trace it by hand.
