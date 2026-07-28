---
name: feedback-seat-launch-conventions
description: "When dispatching seats for ad-hoc PR/feature verification: honor an explicit single-seat instruction literally, and default worker dev servers to hot-reload mode"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 80ce98cd-34a3-40db-b753-81baaabc3418
  modified: 2026-07-28T07:15:10.149Z
---

Two corrections from dispatching a full-fledged feature (a paired FE + BE PR) to a worker seat.

**1. A single-seat instruction means exactly one seat, full stop.**
When the user says something like "assign 1 workspace for both FE and BE" (or otherwise
signals one seat should own a multi-repo/multi-PR feature), launch exactly **one** seat —
do not default to "one seat per repo" reasoning, even though PRs usually map 1:1 to seats.
**Why:** corrected directly — "you are assigning 2 different seats to frontend and backend
i am saying assign 1 same workspace for both." I had bootstrapped two seats (one per repo)
before the user caught it. **How to apply:** when a task spans multiple repos/PRs but the
user's wording implies one unit of work, pin one seat, note both repos in `current.json`
(e.g. `"repo":"both"`), and give the worker a single prompt describing both PRs so it
checks out and runs both from that one seat. See [[agent-pool-orchestrator-worker-separation]]
for the broader dispatch-not-drive rule this sits inside.

**2. Worker seats verifying a PR/feature should start dev servers in hot-reload mode, not normal mode.**
I told the worker to run `zamp dev 1,2` (normal mode) to check out and verify the two PRs.
**Why:** corrected directly — "you have started the coder with zamp-dev workspaces should
always start with zamp-hot to support hot reload." A worker actively verifying/debugging a
branch needs the fast iterate loop — normal mode forces a manual restart after every code
tweak, which slows down exactly the kind of investigative work these seats do.
**How to apply:** this is scoped to **seat/worker dispatch** (agent-pool conductor sessions
doing PR/feature verification), not a blanket override of the general
`zamp dev 1,2` vs `1,2h` guidance in `~/zamp/.claude/CLAUDE.md` (which is written for
interactive engineering sessions where hot reload is explicitly opt-in). When writing the
task prompt for a worker seat, tell it to start with hot reload (the `h` suffix) by default.
