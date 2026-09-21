---
name: orca-browser
description: >-
  Open and drive Orca's embedded browser for ad hoc browsing, research, screenshots, or web
  automation — always on this Mac's own local Orca worktree, never on a zamp-N Coder ticket seat.
  Use this WHENEVER the user wants to open a page in Orca's browser, look something up and see it,
  take a screenshot, fill a form, log into a site, or otherwise drive a browser tab through Orca,
  and the task is standalone browsing rather than part of a ticket/PR agent's work. It always makes
  the tab visible (focused in the Orca window, not a hidden background tab) and applies the fix for
  Orca browser bug #21210 (tab create / goto silently opening on the wrong SSH host) by construction
  — it never targets a host that could be ambiguous. Prefer this over ad hoc `orca goto`/`tab create`
  calls, and over orca-seats, for anything that is really "open a browser and look at something"
  rather than "assign ticket work to a seat".
---

# Orca Browser — always-local, always-visible browser tabs

Two guardrails, both born from the same Orca bug
([stablyai/orca#21210](https://github.com/stablyai/orca/issues/21210)): with several SSH hosts
holding the same repo at the same path — exactly the `zamp-1`..`zamp-5` fleet — `tab create` /
`goto` **without an explicit `--worktree`** can silently resolve to the wrong host. The page then
fails with a bare `chrome-error://chromewebdata/` and no diagnostic; it looks exactly like a
network outage and can cost hours to diagnose.

1. **Never use a fleet seat for standalone browsing.** The 5 `zamp-N` seats all share the identical
   repo path, which is precisely the condition that triggers #21210. Ticket/PR seats belong to
   `orca-seats`; this skill deliberately never touches them.
2. **Always target this Mac's own `local` Orca worktree instead.** It is the one host that can
   never collide with another, so the ambiguous-resolution failure mode this bug describes cannot
   happen here by construction — there is nothing else at that path to be confused with. It also
   means the page renders in the Orca desktop app on this machine, which is what "visible" means in
   practice: it's the window in front of the user, not a tab running headless on a remote seat.

## The one command that does it right

```bash
python3 <skill>/scripts/open_visible_tab.py --url <url> --json
```

(`<skill>` is this skill's directory.) This does all three required steps in one shot, so none of
them can be silently skipped:

1. **Resolves the local worktree selector live** — reads `orca worktree ps --json`, filters to
   `hostId == "local"`. Never hardcode this id; it is a repo record and can be re-added with a new
   id. (Same discipline as `orca-seats`' rule against hardcoded seat tables — a stale id is exactly
   how #21210-style failures happen even when you meant to target the right host.)
2. **Creates the tab** with that selector explicit: `orca tab create --worktree <sel> --url <url>`.
3. **Focuses it**: `orca tab switch --page <id> --worktree <sel> --focus`, which is what actually
   guarantees "visible" — a created tab that isn't the active one can sit unseen behind others.

It prints the resolved worktree, the page id, and whether the focus call was confirmed. If your
task needs a non-default browser session (e.g. a separate login), pass `--profile <id>` — see
`orca tab profile list --json` for what's available.

If the script isn't available or you need finer control, do the three steps by hand — but always
in this order and always with the explicit `--worktree` on every call, including follow-up
`goto`/`snapshot`/`click` calls in the same session:

```bash
orca worktree ps --json                                   # find hostId == "local"
LOCAL="id:<repoId>::<path>"                                # from that record, live
orca tab create --worktree "$LOCAL" --url <url> --json
orca tab switch --page <pageId> --worktree "$LOCAL" --focus --json
```

## Resolve the CLI and the sandbox

Resolve the `orca` executable once (`ORCA_CLI_COMMAND` env, else `orca-dev` in a dev checkout, else
`orca-ide` on bare Linux, else `orca`). On this Mac, the bash sandbox blocks the socket the CLI
needs to reach the running Orca app, so a sandboxed call fails with `runtime_unavailable` even
though the app is up — run every `orca` call, and the script above, with the sandbox disabled. If
`orca` reports the app isn't running, `orca open --json` starts it, then retry.

## Driving the page

Once the tab is open and focused, use the standard snapshot-interact-re-snapshot loop, keeping
`--worktree "$LOCAL"` explicit on every call (cheap insurance, and it makes any future drift from
"always local" fail loudly instead of silently targeting the wrong page):

```bash
orca snapshot --worktree "$LOCAL" --json
orca click --element @e3 --worktree "$LOCAL" --json
orca snapshot --worktree "$LOCAL" --json      # re-snapshot: refs invalidate on navigation/click
orca fill --element @e1 --value "text" --worktree "$LOCAL" --json
orca screenshot --worktree "$LOCAL" --json
orca wait --text "Loaded" --worktree "$LOCAL" --json   # prefer wait over a bare timeout
```

Refs like `@e3` are scoped to one tab and invalidated by navigation, tab switches, or any click
that changes the page — re-`snapshot` after each. The full command list (fill, type, select, check,
scroll, hover, keypress, upload, cookie, console, network, pdf, full-screenshot, exec, …) is in
`orca-cli`'s bundled browser reference (`orca skills get orca-cli --reference references/browser.md`)
— load it if a command isn't covered here.

## Common recoveries

- **`chrome-error` / blank page / silent failure** — this is exactly #21210. It should not happen
  here since every call above pins `--worktree` to the resolved local selector, but if it does,
  re-run `open_visible_tab.py` to re-resolve the selector live rather than reusing a cached one —
  the local worktree's id can change if the repo record was re-added.
- **`browser_no_tab`** — open one: `orca tab create --worktree "$LOCAL" --url <url> --json`.
- **`browser_stale_ref`** — run `orca snapshot --worktree "$LOCAL" --json` and retry with fresh refs.
- **`browser_tab_not_found`** — run `orca tab list --worktree "$LOCAL" --json` before switching or
  closing; the page id may have changed.
- **`browser_host_unavailable`** — the desktop hosting the page is offline. Since this skill always
  targets `local`, that desktop is the same machine you're running on — it means Orca itself isn't
  running. `orca open --json`, then retry.
- **Tab opened but the focus call's `ok` wasn't confirmed** — verify directly:
  `orca tab current --worktree "$LOCAL" --json` and check `result.tab.active` and `result.tab.url`
  match what you expected before assuming it's visible.

## Relationship to orca-seats

`orca-seats` governs the `zamp-1`..`zamp-5` ticket/PR seats, including its own Rule 3 for the rare
case a *ticket* agent needs a browser on its own seat. This skill is the default for everything
else — any task that is really "open a page and look at it" rather than "do ticket work" — and it
never consumes one of the 5-seat ticket pool to do it.
