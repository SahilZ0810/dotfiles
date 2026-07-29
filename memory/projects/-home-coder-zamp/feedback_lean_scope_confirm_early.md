---
name: feedback_lean_scope_confirm_early
description: "Confirm the true core need up front and default to the leanest viable build; don't run the full heavyweight pipeline before the requirement is settled"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bacf7c1c-c797-47ce-8b67-a6c88d4e3cb9
  modified: 2026-07-29T06:51:57.187Z
---

On FRO-266 (jam.dev feedback flow), the user said "you are overcomplicating it" and scrapped the delivered PR to restart. The build ran the full agent-loop pipeline (deep-reasoner plan → architect review → 3 implementer chunks → pr-cleanup 5 lanes → Greptile drive-to-green) on a text→Slack fallback flow, but the user's actual need was much simpler and different (extension-free Jam recording via a recording URL / custom recording domain — they didn't want the text/Slack flow at all).

**Why:** heavy upfront machinery is wasted — and feels like overcomplication — when the core requirement isn't nailed down yet or turns out to be small. Requirements shifted a lot mid-flight (text fallback → extension-free → custom-recording-domain), so front-loading a rigorous plan+review+CI pipeline on the first interpretation burned effort on the wrong thing.

**How to apply:** early, cheaply confirm the *one core outcome* the user wants (here: "users record a Jam so we can debug" — not a text fallback) before committing to a full plan/architect/implementer/pr-cleanup pipeline. Prefer the leanest viable slice first; scale up ceremony only once scope is settled and the user confirms it's worth it. When a ticket is multi-phase or the ask is ambiguous, ask which slice they actually want before building. Related: [[feedback_orchestrator_no_handson_work]].
