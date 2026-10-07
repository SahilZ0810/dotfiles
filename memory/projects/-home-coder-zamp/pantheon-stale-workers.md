---
name: pantheon-stale-workers
description: "zamp pantheon-dev restart leaves old combined_workers alive (SIGTERM ignored), so live tests can run on stale code"
metadata:
  node_type: memory
  type: project
  originSessionId: e69c4286-8a47-4a82-bbaf-6ec9d1a7e04e
  modified: 2026-10-07T06:28:42.383Z
---

On Coder seats, `zamp pantheon-dev restart` (make target missing, exits 2) and the Makefile stop step send SIGTERM and drop pid files, but `combined_workers` processes often survive (likely each manager's `loop.add_signal_handler(SIGTERM)` overwrites the previous one in base_worker). Survivors keep polling the same Temporal task queue, so a workflow can run on hours-old code. All write to the same `.logs/combined_workers.log` (out-of-order timestamps are the tell).

**Why:** PRO-3724 (2026-10-07) lost an hour debugging a "marker never fires" bug that was just a stale worker from 00:24 serving the run.

**How to apply:** after any pantheon restart before a live test, run `pgrep -af combined_workers` and SIGKILL any worker older than the restart; confirm which pid ran a workflow via the Temporal history (worker identity) when behaviour contradicts the code.
