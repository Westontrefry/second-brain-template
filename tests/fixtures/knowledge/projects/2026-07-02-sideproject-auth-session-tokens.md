---
id: 2026-07-02-sideproject-auth-session-tokens
domain: projects
topics: [authentication, sessions, security, sideproject]
source: project
confidence: 4
ai_confidence: null
ai_confidence_rationale: null
last_assessed: null
importance: 4
goals: [sideproject, job-readiness]
created: 2026-07-02
last_reviewed: 2026-07-02
exposure_count: 2
---

Chose short-lived access tokens + httpOnly refresh cookie for the side project
instead of long-lived JWTs in localStorage: XSS can't exfiltrate an httpOnly cookie,
and short expiry bounds the blast radius of a leaked access token. Implemented
rotation on refresh; hit and fixed a race where two tabs refreshing simultaneously
invalidated each other — solved with a small grace window for the previous refresh
token.

Applied knowledge of [[2026-07-02-btree-vs-hash-indexes]] indirectly: session lookup
table is keyed for equality only, so a hash-style unique index is enough there.
