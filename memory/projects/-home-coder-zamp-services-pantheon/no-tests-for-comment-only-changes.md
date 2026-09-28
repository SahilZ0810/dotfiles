---
name: no-tests-for-comment-only-changes
description: "Don't run pytest for comment/docstring-only edits the user requests on a PR"
metadata:
  node_type: memory
  type: feedback
  originSessionId: adfdc365-4286-4b0d-b81f-91fc197e88b7
  modified: 2026-09-28T13:10:55.951Z
---

For comment/docstring-only edits (e.g. "remove this comment" on a PR line), don't run tests — just edit, commit, push.

**Why:** User said "no need of running tests" after I ran the suite for a comment removal on PR #6149 (2026-09-28).

**How to apply:** Skip pytest when the diff touches only comments/docstrings; still run tests when any code changes.
