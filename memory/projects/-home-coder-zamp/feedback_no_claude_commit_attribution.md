---
name: feedback-no-claude-commit-attribution
description: "When actually committing (only when explicitly asked), never attribute the commit to Claude — no Co-Authored-By trailer, no Claude-Session link"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 80ce98cd-34a3-40db-b753-81baaabc3418
  modified: 2026-07-28T07:48:40.512Z
---

Commits still only happen when the user explicitly asks (that global default is
unchanged) — but when a commit does happen, it must never carry Claude's name or any
Claude attribution.

**Why:** the user explicitly said Claude should never commit changes in its name — asked
directly whether this meant "never commit unprompted" vs. "never attribute an actual
commit to Claude," they chose the attribution reading: commits should happen when
requested, just without Claude's name on them.

**How to apply:** when writing a commit message (via `git commit -m "$(cat <<'EOF' ... EOF)"`
or otherwise), omit the trailing `Co-Authored-By: Claude ... <noreply@anthropic.com>` line
and the `Claude-Session: https://claude.ai/code/session_...` line that the default
commit workflow appends. The commit message should read as if written by the user alone —
just the summary/why, no Claude signature of any kind. This applies to every repo, not
just one project.
