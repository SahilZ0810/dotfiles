---
name: bugpatrol-start-fe-stale-server
description: "bugpatrol start-fe.sh can silently keep serving the main checkout on :3000, so fix retests test old code"
metadata:
  node_type: memory
  type: project
  originSessionId: 1e4de09e-4dec-4bc5-8d2d-f1a21835eb6d
  modified: 2026-11-01T14:57:38.513Z
---

`.bugpatrol/start-fe.sh` frees :3000 with `fuser`, which is not installed on the Coder workspace (`|| true` hides it). The fix worktree's `next start` then dies with EADDRINUSE, yet the script prints `BP_READY` because the old server (often `application-platform-frontend`'s own) still answers `/login`.

**Why:** a bugpatrol retest of the dataset-create fix (2026-11-01) "had no effect" because the served chunk was the main checkout's build, not the fix.

**How to apply:** before trusting a retest, check `ss -ltnp | grep :3000` and `/proc/<pid>/cwd`, or grep the served `_next/static/chunks/*.js` for the changed code.
