---
name: project_coder_seat_tmp_is_ephemeral
description: On Coder seats /tmp is wiped on workspace restart; long-running background work must be setsid-detached with results written under $HOME
metadata: 
  node_type: memory
  type: project
  originSessionId: b5dd5df5-e515-4fde-a7ea-5db1f69a9b6f
  modified: 2026-08-06T09:54:41.567Z
---

On these Coder seats, `/tmp` lives on the ephemeral container overlay (`/`, ~193G) and is
**wiped on every workspace restart**, while `/home/coder` is persistent EBS (~49G). Restarts
also kill background shells started with plain `nohup` from a Claude session, and running
`zamp dev` services.

**Why:** during the Next 16.3.0 upgrade (Aug 2026) two full A/B build benchmarks were lost
mid-run — worktrees, scripts, and results all vanished from `/tmp` across three restarts in
one session, costing ~25 min of rebuilds each time.

**How to apply:** for any long-running background work (builds, benchmarks, multi-minute
scripts): launch with `setsid nohup … & disown` so it survives the session dying, and write
**results/artifacts under `$HOME`**, not `/tmp`. Bulky throwaway inputs (git worktrees, build
output) can still live in `/tmp` to exploit its space — just never the output you need to keep.
Have the script append each measurement as soon as it's taken, so a restart mid-run still
leaves partial results. After any restart, re-check `zamp dev-status` — services will be down.

Related: [[feedback_seat_launch_conventions]]
