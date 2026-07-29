---
name: feedback-seat-free-archive-chat
description: Freeing a seat (reset) must also archive its Remote Control chat — seatctl reset alone is incomplete
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 80ce98cd-34a3-40db-b753-81baaabc3418
  modified: 2026-07-29T07:27:12.532Z
---

Freeing up a seat means two things, not one: `seatctl reset --stop` (kill tmux, clean git, mark
the registry seat free) **and** archiving the seat's Remote Control chat/session. I only did the
first when asked to "free up seat 4" — the user corrected this as a mistake.

**Why:** the user's mental model of "free up a seat" includes leaving no orphaned chat card behind
in the Remote Control app; `seatctl reset` was written for registry/git-state cleanup only and was
never extended to also archive the session on the Claude Code side.

**How to apply:** whenever releasing a seat — via a direct "free up seat N" request, or via
`seatctl reap` at the end of a ticket — archive that seat's Remote Control chat (pinned
`session_id` from the registry / `current.json`) as part of the same action, not as an afterthought.

**Open gap (unresolved as of 2026-07-29):** I looked for a scriptable way to archive a Remote
Control chat from this environment and found none — `coder_list_tasks`/`coder_delete_task` cover a
different Coder "Task" API that returns empty for these tmux+`cc-launch.sh` sessions, and `claude
--help`/`claude agents --help` expose no archive subcommand for Remote Control sessions. Asked the
user for the actual mechanism (Remote Control API endpoint? app-side action only?) — once known,
wire it into `seatctl reset` (and `reap`'s release path) so this stops being a manual step.
See [[agent-pool-seat-launch-conventions]] and [[agent-pool-orchestrator-worker-separation]] for
the sibling decisions this extends (both about getting seat lifecycle actions fully right, not
half-done).
