---
name: feedback-memory-sync-is-manual-twostep
description: Memory sync between HQ and seats is not automatic beyond first boot — requires explicit git pull + sync-memory.sh pull/push on both ends
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 80ce98cd-34a3-40db-b753-81baaabc3418
  modified: 2026-07-29T07:35:47.156Z
---

`sync-memory.sh pull` does NOT run `git pull` on the dotfiles repo itself — it only copies
from that repo's *already-checked-out* local files. A long-running seat's dotfiles clone goes
stale the moment HQ pushes a new memory entry, and re-running `sync-memory.sh pull` on that seat
silently no-ops (reports "pulled memory" but copies nothing new) unless `git -C
~/.config/coderv2/dotfiles pull --ff-only` runs first. `install.sh` only does that `git pull` +
`sync-memory.sh pull` combo once, at workspace **start** — never again while the workspace stays
up.

The sync is also two-directional and neither leg is automatic: a seat's own `agent-loop`
conductor can write a genuinely useful feedback memory locally (confirmed on seat-4: a real
lesson from FRO-266 — "you are overcomplicating it" — sat local-only, invisible to HQ and every
other seat, until `sync-memory.sh push` ran on that seat).

**Why:** discovered when the user asked "can you confirm whether each seat is able to access the
memory we have defined" — checking found seats 1/2/3/5 running on a memory snapshot from their
last boot (missing an entry added hours earlier), and seat-4 holding an unpushed local-only entry
nobody else could see.

**How to apply:** don't assume a seat has current memory just because it's running. Whenever it
actually matters (a tick where you're relying on a memory-derived rule, or an explicit ask to
verify), on the seat: `git -C ~/.config/coderv2/dotfiles pull --ff-only && bash
~/.config/coderv2/dotfiles/sync-memory.sh pull`. Periodically (e.g. once during a tick after a
seat's ticket wraps up, before `reset`) also run `sync-memory.sh push` on busy seats so anything
their own conductor learned reaches HQ and the rest of the pool before the seat is recycled —
`reset` does not do this and a seat's local-only memory is otherwise lost when it's reused for a
new ticket. Related: [[feedback_seat_free_archive_chat]] — another case of a seat-release action
being incomplete without an explicit sync step.
