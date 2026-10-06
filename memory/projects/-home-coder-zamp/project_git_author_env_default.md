---
name: git-author-env-default
description: "Coder workspace exports GIT_AUTHOR_NAME/GIT_COMMITTER_NAME=default, which overrides git config and -c user.name"
metadata:
  node_type: memory
  type: project
  originSessionId: 47fcc85d-9980-46de-b45c-93e3ac54f7b4
  modified: 2026-10-06T18:41:00.700Z
---

The Coder workspace env sets `GIT_AUTHOR_NAME=default` and `GIT_COMMITTER_NAME=default` (emails are correct). Env vars beat `git config user.name` and `git -c user.name=...`, so commits come out authored by "default".

**Why:** user requires commits as `SahilZ0810 <sahil@zamp.ai>`; a merge commit on 2026-10-06 (PRO-3417) landed as "default" and had to be amended.

**How to apply:** when committing, prefix with `GIT_AUTHOR_NAME=SahilZ0810 GIT_COMMITTER_NAME=SahilZ0810` (or `--author=` plus `GIT_COMMITTER_NAME=`), then check with `git log -1 --format='%an | %cn'`. See [[no-claude-commit-attribution]].
