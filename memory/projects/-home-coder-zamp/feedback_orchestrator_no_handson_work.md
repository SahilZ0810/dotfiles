---
name: feedback-orchestrator-no-handson-work
description: "In the chief-of-staff orchestrator chat, never run hands-on commands yourself — dispatch to a separate worker Claude session on a seat instead"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 80ce98cd-34a3-40db-b753-81baaabc3418
  modified: 2026-07-27T17:30:57.369Z
---

When acting as the chief-of-staff orchestrator (L1, runs `/chief-of-staff tick` etc.), never drive hands-on work — checking out branches, running builds, restarting dev servers, debugging failures — directly via `coder_workspace_bash`/SSH in the orchestrator's own chat, even for quick ad-hoc asks that aren't a Linear ticket.

**Why:** The user corrected this directly: "we are assigning a worker that worker should work in another chat not in this chat as this chat's work is to just orchestrate." The orchestrator's job is to decide *what* and *when* and dispatch (per [[chief-of-staff-design]] / the skill's own framing: "You do not write code — the per-seat `agent-loop` conductor does that"). That separation should hold even for non-ticket, exploratory tasks (e.g. "check out branch X on a seat and run it end to end") — not just formal `/agent-loop <TICKET>` assignments.

**How to apply:** When a hands-on task needs to happen on a seat (including ad-hoc/manual verification with no Linear ticket), use the "Launching a seat" recipe to start an actual Claude Code session there (tmux + `cc-launch.sh`, `CC_ROLE`/`CC_TICKET`/`CC_SESSION_ID` env vars for RC card naming) and hand it the task via `tmux send-keys` — then step back and only poll/report status from the orchestrator chat. Reserve direct `coder_workspace_bash` command execution in the orchestrator chat for: seat mechanics (`seatctl` calls), bootstrap, and the minimal setup needed to hand off (e.g. checking out the branch so the prompt can reference it) — not the actual verification/debugging work itself.

**Gotcha noticed while fixing this:** a `tmux send-keys` with a long/multi-clause string can get swallowed into Claude Code's bracketed-paste mode ("[Pasted text #1 +1 lines]") instead of submitting — the trailing `Enter` lands inside the paste rather than submitting it. A second bare `tmux send-keys -t <session> Enter` after a short sleep submits it. The existing `kick-agentloop.sh` avoids this by sending a short fixed string (`/agent-loop <ticket>`); a custom ad-hoc prompt needs this extra submit step or the same poll-and-verify pattern.
