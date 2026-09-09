---
name: browser-qa-coder-proxy-auth
description: "Browser QA must go through the Coder proxy URL, not localhost:3000 — and needs a coder_session_token cookie plus chromium system deps"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3a598d4b-6702-4f2a-b477-e5f73a96c3f7
  modified: 2026-09-09T21:25:43.624Z
---

Browser QA against the dev frontend has two gates that are not in the `browser-qa` skill:

1. **`http://localhost:3000` cannot log in.** The client-side API base is
   `NEXT_PUBLIC_BASE_API_URL=https://pantheon-api--…coder.dev-mum.internal.zamp.dev`
   (`apps/application-dashboard/.env.local`), and that API sends no
   `Access-Control-Allow-Origin` for a `localhost` origin — the login flow dies on a
   CORS preflight. QA must use the `https://3000--…` Coder URL so the origin matches.
2. **The Coder proxy needs its own session.** It redirects to the Coder login before the
   app is ever reached. Inject the workspace's own token as a cookie rather than logging
   in through the UI: read `~/.config/coderv2/session` and add
   `coder_session_token` for domain `.coder.dev-mum.internal.zamp.dev`. Driving Playwright
   from a Bash script (not the MCP server) keeps the token out of the transcript.

Also: the Playwright MCP server fails with *"Missing system dependencies required to run
browser chrome-for-testing"* on a fresh workspace. Fix once with
`sudo npx playwright install-deps chromium` (passwordless sudo works here).

App login is two steps: type the email → click the **second** button (`button:has-text("Continue")`
also matches "Continue with Google", so use `nth(1)`) → **Sign in with Password** → email +
password → **Sign in**.

**Why:** each of these looks like a broken app or a broken change, and costs a long detour
to re-diagnose.

**How to apply:** for any browser QA in this repo, start from the Coder URL with the
session cookie, not localhost. See [[dev-stack-startup-gotchas]].
