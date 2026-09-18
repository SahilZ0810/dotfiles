---
name: pgbot-db-optimization-status
description: State of the Sep-2026 Postgres optimization workstream — branch pushed, TRDs in Notion, what is applied vs pending
metadata:
  type: project
---

Branch `sahil/pgbot-db-optimizations` pushed 2026-09-18 (commit 1aaa5385a), no PR per request.
Repo carries: docs/db/{README, prod-evidence-pack.sql (22 queries), metabase-replica-queries.sql,
incident-2026-09-17-orphaned-transactions.md} + 3 migrations.

**Why:** follow-up to 2026-08-19 pgbot audit; everything re-verified on dev + prd-us.

**How to apply:**
- Applied on DEV only: super/20260917110000 pg_monitor grant (redaction 90%→0%).
- NOT applied anywhere: 20260917120000 (FK partial index, trigger_event_streams.connection_id, ~1 MB
  replaces 513 MB index walk) and 20260917140000 (HNSW partial rebuild, 141 GB→~21 GB, needs staging
  build timing + by-hand CONCURRENTLY on prd-us first — see file headers).
- TRDs in Notion under "Pantheon Postgres health — 2026-09 follow-up"
  https://app.notion.com/p/3deedc94e67f81d28ac9e3cbf9a77f1d (TRD-001 ready, 002 deferred by user,
  003 drop list ready ~203 MB, 004 decided, 005 proposed ~120 GB, 006 blocked on prod pg_monitor).
- Open follow-ups (incident doc §Follow-ups): worker_bootstrap shutdown must dispose DB pool;
  batch etl_service.py:102; Grafana alert on xact age; prod pg_monitor grant (also `metabase` role).
