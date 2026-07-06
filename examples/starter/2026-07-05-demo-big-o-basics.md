---
id: 2026-07-05-demo-big-o-basics
title: Big-O and why my loop was slow
domain: cs
topics: [big o, algorithms]
source: demo
confidence: 3
ai_confidence: null
ai_confidence_rationale: null
last_assessed: null
importance: 4
goals: [dsa-interviews]
created: 2026-07-05
last_reviewed: 2026-07-05
exposure_count: 2
---

Worked through why my duplicate-finder was O(n²): nested loops over the same
list. Rewrote it with a set for seen values and it dropped to O(n). The rule I
keep now: every time I write a loop inside a loop, ask what the inner loop is
actually searching for and whether a [[2026-07-05-demo-hash-tables]] lookup can
replace it.
