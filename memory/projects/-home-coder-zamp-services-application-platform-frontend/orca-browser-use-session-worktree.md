---
name: orca-browser-use-session-worktree
description: "Open Orca browser tabs on the worktree the current chat is running in, not the Mac's local worktree"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a564845b-191c-4c1d-8461-b693d697e9f0
  modified: 2026-09-21T12:33:48.396Z
---

Always open Orca browser tabs on the worktree this session is running in — the one in
`$ORCA_WORKTREE_ID` — passing `--worktree "id:$ORCA_WORKTREE_ID"` explicitly on every
`tab create` / `tab switch --focus` / `snapshot` / `click` call.

**Why:** the `orca-browser` skill always targets the Mac's `local` worktree
(`/Users/lscypher/Workspace/zamp`). A tab opened there is the active tab *in that
worktree*, but the Orca window is showing whichever worktree the chat is in, so the user
sees nothing and the tab looks broken. Stated on 2026-09-21 after exactly that happened.

**How to apply:** `SEAT="id:${ORCA_WORKTREE_ID}"`, then `orca tab create --worktree "$SEAT"
--url <url>`, then `orca tab switch --page <id> --worktree "$SEAT" --focus`. Pinning
`--worktree` on every call is what avoids Orca bug #21210 (ambiguous host resolution across
the identical `zamp-N` seat paths, which fails with a bare `chrome-error://chromewebdata/`),
so the skill's real guardrail is kept even though its "always local" rule is not. Run the
calls with the bash sandbox disabled. To reach a server running on the seat, use the Coder
URL, not `localhost`: `https://<port>--main--<workspace>--<user>.coder.dev-mum.internal.zamp.dev`
(pattern is in `$VSCODE_PROXY_URI`). See [[orca-browser-skill-conflict]].
