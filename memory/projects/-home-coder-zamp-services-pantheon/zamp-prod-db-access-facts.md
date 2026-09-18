---
name: zamp-prod-db-access-facts
description: How to reach prd-us Postgres/Grafana from a seat, and the traps (proxy, per-node stats, orca tab invisible)
metadata:
  type: reference
---

- prd-us app traffic (`ap-agent`) goes through RDS Proxy `zamp-prd-us-pantheon-db-proxy`
  (infrastructure terraform prd-us/main.tf:271, idle_client_timeout=1800, debug_logging=false).
  Consequence: pg_stat_activity.client_addr is the proxy for every app connection; backend_start is
  the proxy pool's, not the pod's. See [[pgbot-db-optimization-status]].
- User has psql on a prod bastion; this seat has none. Metabase reaches only the READ REPLICA
  (per-node pg_stat_* useless there; catalog queries fine).
- Grafana: grafana.prd-us.internal.zamp.dev — unreachable from seats (internal DNS + Cloudflare on
  public host). Reachable via Orca browser (runs on user's Mac): `~/.orca-relay/bin/orca tab create/goto/eval`.
  Loki datasource uid P8E80F9AEF21F6940 via /api/datasources/proxy/uid/<uid>/loki/api/v1/...;
  labels are k8s_* (k8s_pod_name, k8s_deployment_name), NOT app=. Orca browser tab is NOT visible
  to the user on this seat (stablyai/orca#21210) — never ask them to interact with it; Grafana
  session expires and I must not drive Google SSO; a Viewer service-account token pasted by the
  user works via fetch Authorization header (they used one on 2026-09-18; told to revoke).
- `gh` on seat-4 returned 401 on 2026-09-18 (CLAUDE.md says surface, don't work around).
