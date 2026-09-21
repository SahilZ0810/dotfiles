---
name: browser-qa-use-orca-browser
description: Browser QA should use the Orca browser (~/.orca-relay/bin/orca) — it already holds a logged-in Zamp session; Playwright from the seat does not
metadata: 
  node_type: memory
  type: project
  originSessionId: fed752ae-7da0-4232-b0a6-5b05d5abe609
  modified: 2026-09-21T07:44:45.989Z
---

For browser QA of the dashboard, drive the **Orca browser**, not a fresh Playwright
launch from the seat.

`~/.orca-relay/bin/orca` has a full browser surface (`tab create/list/switch`, `goto`,
`snapshot`, `click`, `eval`, `upload`, `screenshot`). Its browser **already has a
logged-in Zamp session**, which is the whole problem a seat-launched Playwright cannot
solve: there is no `tests/session-secrets/session-state.json` and no `ADMIN_EMAIL` /
`GOOGLE_SSO_*` env vars on a seat, and the two auth cookies (`ory_kratos_session`,
`zamp_user_session_v2`) are httpOnly so they cannot be scraped or reconstructed.
Injecting `coder_session_token` only clears the Coder proxy — the app still lands on
`/login`. See [[browser-qa-coder-proxy-auth]], which is still right about the proxy but
does not solve app login.

Gotchas that cost real time:

- **Always pass `--page <id>`.** The Orca browser is shared with other seats' agents; the
  active tab silently drifts to another workspace mid-run. Pin every command to the page
  id returned by `orca tab create`, and re-check with `orca tab list`.
- **`orca screenshot` needs the tab foregrounded.** It fails with "Screenshot timed out —
  the browser tab may not be visible" whenever another seat's tab takes focus, and the
  helper writes a 0-byte file. `orca tab switch --page <id>` first, and expect it to keep
  failing if another agent is active. DOM assertions via `eval` are the reliable evidence.
- **`eval` must be async for anything React renders.** State updates are not visible in
  the same tick — wrap in `(async()=>{ ...; await new Promise(r=>setTimeout(r,900)); ... })()`
  or toasts and re-renders read as absent.
- **Element refs from `snapshot` (`@e5`) go stale on re-render.** Clicking by ref
  silently targets the wrong node. Prefer `eval` with a DOM query on a stable attribute
  (`button[aria-label="Share feedback"]`).
- **Sentry's transport cannot be observed by patching `window.fetch`** — the SDK caches a
  native fetch reference at init. Hook the real transport instead:
  `__SENTRY__['<version>'].defaultCurrentScope.getClient().getTransport().send`
  (note `defaultCurrentScope` is an object, not a function).

**Why:** without this, browser QA looks impossible on a seat and gets skipped or blocked
on asking the user for credentials.

**How to apply:** `orca tab create --url <coder FE url>`, capture the page id, then drive
everything with `orca eval --page <id>` and async expressions.
