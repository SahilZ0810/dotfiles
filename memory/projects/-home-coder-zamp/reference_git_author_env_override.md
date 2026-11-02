---
name: git-author-env-override
description: "Coder workspace sets GIT_AUTHOR_NAME/GIT_COMMITTER_NAME=default, which beats `git -c user.name=...`"
metadata:
  node_type: memory
  type: reference
  originSessionId: 1f534277-4176-424a-b3db-a61a1e51ec06
  modified: 2026-11-02T11:35:33.452Z
---

The Coder workspace exports GIT_AUTHOR_NAME=default and GIT_COMMITTER_NAME=default (email is sahil@zamp.ai). Env vars take precedence over `git -c user.name=...`, so commits come out as `default <sahil@zamp.ai>`.

**How to apply:** when committing as SahilZ0810, prefix the command: `GIT_AUTHOR_NAME=SahilZ0810 GIT_COMMITTER_NAME=SahilZ0810 git commit ...`. Check with `git log -1 --format='%an <%ae>'` before pushing. See [[feedback_no_claude_commit_attribution]].
