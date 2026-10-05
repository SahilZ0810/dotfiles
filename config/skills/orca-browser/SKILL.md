---
name: orca-browser
description: >-
  Open and drive Orca's embedded browser for ad hoc browsing, research, screenshots, or web
  automation — always on the worktree the calling session is running in, so the tab is visible
  in the pane the user is actually looking at. Use this WHENEVER the user wants to open a page
  in Orca's browser, look something up and see it, take a screenshot, fill a form, log into a
  site, or otherwise drive a browser tab through Orca. It always makes the tab visible (focused
  in the worktree the session belongs to, not a hidden background tab on another host) and
  applies the fix for Orca browser bug #21210 (tab create / goto silently opening on the wrong
  SSH host) by pinning an explicit --worktree selector on every call. Prefer this over ad hoc
  `orca goto`/`tab create` calls for anything that is really "open a browser and look at
  something"; use orca-seats to assign ticket work to a seat.
---

# Orca Browser — always-visible browser tabs, pinned to the calling worktree

Two failure modes, one rule that prevents both.

**The bug.** Orca bug ([stablyai/orca#21210](https://github.com/stablyai/orca/issues/21210)):
with several SSH hosts holding the same repo at the same path — exactly the `zamp-1`..`zamp-5`
fleet — `tab create` / `goto` **without an explicit `--worktree`** can silently resolve to the
wrong host. The page fails with a bare `chrome-error://chromewebdata/` and no diagnostic; it
looks exactly like a network outage and can cost hours to diagnose.

**The invisible tab.** The Orca window shows **one worktree at a time**. A tab opened on a
different worktree is the active tab in a pane nobody is looking at. It reports `active: true`,
`loadError: null`, and a correct URL, while the user sees nothing at all. This is worse than an
error, because every check you can run says the tab is fine.

**The rule that prevents both: always pin `--worktree` to the worktree this session is running
in,** which `$ORCA_WORKTREE_ID` names exactly (`<repoId>::<path>`).

- It defeats #21210 by construction. The bug is ambiguous *resolution*; an exact id leaves
  nothing to resolve. Five seats sharing a path cannot be confused when you name one of them.
- It puts the tab in the pane the user is already looking at, which is what "visible" has to
  mean in practice.

Never hardcode the selector, and never reuse a cached one — read it from the environment each
time. (Same discipline as `orca-seats`' rule against hardcoded seat tables: a stale id is
exactly how #21210-style failures happen even when you meant to target the right host.)

> Earlier versions of this skill always targeted this Mac's `local` worktree instead. That did
> avoid the bug, but it put every tab on a worktree the user was usually not viewing, so tabs
> opened "successfully" and stayed invisible. Targeting the session's own worktree keeps the
> guardrail and fixes the visibility.

## The one command that does it right

```bash
python3 <skill>/scripts/open_visible_tab.py --url <url> --json
```

(`<skill>` is this skill's directory.) It does all the required steps in one shot, so none can
be silently skipped:

1. **Resolves the worktree selector live** — `--worktree` if given, else `$ORCA_WORKTREE_ID`,
   else the single `local`-host worktree for a bare shell with no Orca session context. It
   refuses to guess when the fallback is ambiguous.
2. **Creates the tab** with that selector explicit: `orca tab create --worktree <sel> --url <url>`.
3. **Focuses it**: `orca tab switch --page <id> --worktree <sel> --focus`, which is what actually
   guarantees visibility — a created tab that isn't the active one can sit unseen behind others.
4. **Reads the tab back** and reports `active`, `loadError`, and `certificateFailure`, so a
   silent #21210 failure shows up immediately instead of being assumed fine.

It prints the resolved worktree, which source it came from, the page id, and whether focus was
confirmed. For a non-default browser session (e.g. a separate login), pass `--profile <id>`;
see `orca tab profile list --json`.

Doing it by hand — always in this order, always with explicit `--worktree` on every call,
including follow-up `goto`/`snapshot`/`click` in the same session:

```bash
SEAT="id:${ORCA_WORKTREE_ID}"
orca tab create --worktree "$SEAT" --url <url> --json
orca tab switch --page <pageId> --worktree "$SEAT" --focus --json
orca tab current --worktree "$SEAT" --json      # confirm active + no loadError
```

## Reaching a server that runs on the seat

The browser runs on the desktop, not on the seat, so **`localhost:<port>` will not resolve**.
Use the forwarded Coder URL. The pattern is in `$VSCODE_PROXY_URI`:

```bash
echo "$VSCODE_PROXY_URI"    # https://{{port}}--main--<workspace>--<user>.coder.<domain>
```

so a dev server on `:3000` is `https://3000--main--<workspace>--<user>.coder.<domain>`.

## Resolve the CLI and the sandbox

Resolve the `orca` executable once (`ORCA_CLI_COMMAND` env, else `orca-dev` in a dev checkout,
else `orca-ide` on bare Linux, else `orca`). The bash sandbox blocks the socket the CLI needs to
reach the running Orca app, so a sandboxed call fails with `runtime_unavailable` even though the
app is up — run every `orca` call, and the script above, with the sandbox disabled. If `orca`
reports the app isn't running, `orca open --json` starts it, then retry.

## Driving the page

Once the tab is open and focused, use the standard snapshot-interact-re-snapshot loop, keeping
`--worktree "$SEAT"` explicit on every call:

```bash
orca snapshot --worktree "$SEAT" --json
orca click --element @e3 --worktree "$SEAT" --json
orca snapshot --worktree "$SEAT" --json      # re-snapshot: refs invalidate on navigation/click
orca fill --element @e1 --value "text" --worktree "$SEAT" --json
orca screenshot --worktree "$SEAT" --json
orca wait --text "Loaded" --worktree "$SEAT" --json   # prefer wait over a bare timeout
```

Refs like `@e3` are scoped to one tab and invalidated by navigation, tab switches, or any click
that changes the page — re-`snapshot` after each. The full command list (fill, type, select,
check, scroll, hover, keypress, upload, cookie, console, network, pdf, full-screenshot, exec, …)
is in `orca-cli`'s bundled browser reference
(`orca skills get orca-cli --reference references/browser.md`) — load it if a command isn't
covered here.

## Taking screenshots

`orca screenshot` captures the visible viewport of the tab and returns it as base64 inside the
JSON result (`result.data`, with `result.format`). It does not write a file, so decode it
yourself. Save captures in the session scratchpad, never in the repo:

```bash
OUT="<session scratchpad>/shots"; mkdir -p "$OUT"   # the scratchpad dir from the system prompt
shot() {
  orca screenshot --worktree "$SEAT" --json 2>/dev/null | python3 -c "
import json, sys, base64
d = json.load(sys.stdin)['result']
open(sys.argv[1], 'wb').write(base64.b64decode(d['data'].split(',')[-1]))" "$OUT/$1.png"
}
shot 1-default-view
```

Get the page into the state you want before each shot:

- **Set up state with `orca eval`.** Clicking, expanding, and switching views through
  `orca eval --expression '<js>'` is more reliable than `orca click` refs, which sometimes miss
  and leave the page unchanged. Read the result back with another `eval` (the URL, a selected
  element) before shooting.
- **Radix tabs, menus and toggles ignore a bare `.click()`.** They open on pointer events, so
  dispatch them first:
  `el.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, button: 0, pointerType: 'mouse'}));`
  then `mousedown`, then `el.click()`. React's `onPointerEnter` listens for `pointerover`, so a
  synthetic `pointerenter` does nothing. Dispatch a bubbling `pointerover` to test hover.
- **Scroll the subject into view** with `el.scrollIntoView({block: 'center'})`. Only the visible
  viewport is captured. Use `full-screenshot` for the whole page.
- **Wait longer than you think.** The embedded tab throttles `requestAnimationFrame` to about once
  a second, so fades, springs and editors such as Monaco can take several seconds to settle. A
  shot taken too early shows blank or half-faded content. Sleep 5 to 15 seconds after a view
  change.
- **Look at every capture before you use it** by reading the PNG. Retake any that caught a
  loading or fading state.
- **The tab uses the user's own session**, so it is already logged in to whichever org they
  picked. Do not sign in a test account in it.

To put captures in a PR, reference each one in the body as `![Caption](./name.png)` and run
`gh pr edit <n> --body-file body.md --attach ./name.png …` from the capture directory. That needs
gh 2.99 or newer. gh uploads each file and rewrites the path to a
`github.com/user-attachments` URL. Read the body back to confirm every path was rewritten. If
`GITHUB_TOKEN` is an app token or has expired, prefix the command with `env -u GITHUB_TOKEN` to
use the saved `gh` login.

## Common recoveries

- **User says they can't see the tab, but every check says it's fine** — it is on a worktree
  they are not viewing. Check `worktreeId` from `orca tab current` against `$ORCA_WORKTREE_ID`;
  if they differ, close it and re-open with the selector pinned to `$ORCA_WORKTREE_ID`.
- **`chrome-error` / blank page / silent failure** — this is #21210. It should not happen when
  every call pins `--worktree`; if it does, re-resolve the selector from the environment rather
  than reusing a cached one.
- **`browser_no_tab`** — open one: `orca tab create --worktree "$SEAT" --url <url> --json`.
- **`browser_stale_ref`** — run `orca snapshot --worktree "$SEAT" --json` and retry with fresh refs.
- **`browser_tab_not_found`** — run `orca tab list --worktree "$SEAT" --json` before switching or
  closing; the page id may have changed.
- **`browser_host_unavailable`** — the desktop hosting the page is offline, so Orca itself isn't
  running. `orca open --json`, then retry.
- **Tab opened but the focus call's `ok` wasn't confirmed** — verify directly:
  `orca tab current --worktree "$SEAT" --json` and check `result.tab.active` and `result.tab.url`
  match what you expected before assuming it's visible. Note `"switched": 0` is normal when the
  tab is already the active one; it is not a failure.

## Relationship to orca-seats

`orca-seats` governs assigning ticket/PR work to the `zamp-1`..`zamp-5` seats — picking a free
seat, spawning an agent on it, reporting seat state. This skill is about browsing, and it does
not pick or consume a seat: it uses whichever worktree the calling session already occupies. A
ticket agent driving a browser on its own seat is the normal case here, not an exception.
