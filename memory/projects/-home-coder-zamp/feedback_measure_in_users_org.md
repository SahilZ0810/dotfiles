---
name: feedback-measure-in-users-org
description: "Perf claims must be verified on the org/data the user actually uses, not only the QA profile's org"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3378a880-887d-487d-a25b-950dcd4cb53f
  modified: 2026-10-20T13:00:32.128Z
---

When verifying a performance change, also measure on the org/sandbox the user actually browses (check API logs for their org_id), not only the feature-qa `user-1` org.

**Why:** Files search was "done" with numbers from `dev_org_001`; the user tried it in `dev_org_006` and it was no faster (a hidden `.worktrees` tree made plocate's per-match visibility check slow there). Data shape differs a lot between dev orgs.

**How to apply:** Before reporting a perf win, grep the API logs for the user's own recent requests and A/B old vs new path in that org too. Related: [[feedback-seat-launch-conventions]]
