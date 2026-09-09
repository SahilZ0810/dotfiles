---
name: reuse-before-building
description: "Sahil's standing rule — audit the codebase and installed deps for existing coverage before writing any new utility"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8f4da816-9c99-4e9d-815a-1cb7143952a0
  modified: 2026-09-09T11:25:21.478Z
---

Before building any new utility, first search the codebase and the installed dependencies for
something that already covers it. Stated as a standing rule on 2026-09-09: "we should never build
a wheel again, we should first look if anywhere in the codebase we can reuse as much as possible."

**Why:** the `page_load_performance` PR (branch `sahil/page-load-metrics`) hand-rolled 13 page-load
metrics, and 8 of them were already captured by three tools mounted in the same app —
`@vercel/speed-insights` (`app/layout.tsx`), `@sentry/nextjs` `browserTracingIntegration()`
(`instrumentation-client.ts`), and `posthog-js` web vitals. Only the service-worker overhead fields
(`workerStart` → `responseStart`) were genuinely new. Nobody checked first.

**How to apply:** when a task calls for a new util, grep the app's `package.json` files and
`src/` for prior art *before* writing, and report the overlap as part of the plan — not after the
code exists. When something is already covered N times, say so and cut the redundant part rather
than shipping a fourth copy. Note the sampling caveat that can justify a duplicate: Sentry runs at
`tracesSampleRate: 0.1`, so tail-latency questions may still warrant a 100% custom event — but that
argues for keeping only the uncovered fields.

Reinforces the repo's own "Reuse before building new" non-negotiable in CLAUDE.md and the
[[ponytail-ladder]] habit of checking rung 2 (already in this codebase) before writing anything.
