---
id: 2026-07-02-gcp-iam-basics
domain: cloud
topics: [gcp, iam, security]
source: course
confidence: 2
ai_confidence: null
ai_confidence_rationale: null
last_assessed: null
importance: 5
goals: [gcp-ace, gcp-cdl]
created: 2026-07-02
last_reviewed: 2026-07-02
exposure_count: 1
---

GCP IAM binds members (users, groups, service accounts) to roles on resources. Roles
are bundles of permissions; prefer predefined roles over primitive ones (owner/editor/
viewer) because primitives are far too broad. Policies inherit down the resource
hierarchy: organization -> folder -> project -> resource.

Haven't practiced this hands-on yet — only read the docs. [[gcp-service-accounts]]
