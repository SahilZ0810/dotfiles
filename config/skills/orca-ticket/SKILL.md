---
name: orca-ticket
description: Use when working a Linear ticket (PRO-*) through Orca across the Zamp FE (application-platform-frontend) and BE (pantheon) repos on the Coder seats — starting ticket work, picking a seat, choosing a repo selector, freeing or stopping a seat, or when an Orca selector is ambiguous/not found, a closed terminal keeps running, an agent lands in the wrong folder, or someone reaches for `orca worktree create`.
---

# Orca ticket workflow (Zamp FE + BE)

## Overview

**One seat = one ticket.** `zamp dev` can only run the stack from the seat's fixed main checkouts,
`~/zamp/services/application-platform-frontend` and `~/zamp/services/pantheon`, and FE + BE run together on one seat.
So ticket work happens **on those main checkouts, on a ticket branch** — never in an extra folder. Orca already lists
each main checkout as a worktree record; link the ticket to that record. Max 5 tickets in flight (5 seats).

**REQUIRED SUB-SKILL:** `orca-linear` for reading/updating the ticket. `orchestration` only when one big ticket must be
split across many agents — not for normal tickets.

## Fleet facts (verify with `orca host list`, `orca repo list`)

| Seat | `--host` id | FE record id | BE record id |
|---|---|---|---|
| seat-1 | `ssh:ssh-1786444147408-lxdmy7` | `3d4aee9f-9ef7-4dc1-81b7-76c52112b923` | `523d8483-276b-4316-b1df-05ccd1cb8a87` |
| seat-3 | `ssh:ssh-1786444395055-1gnnu4` | `cf609af5-8646-4794-be84-f467f8a374f9` | `405ea508-e39a-4997-ab77-3b38cc8a6757` |
| seat-5 | `ssh:ssh-1786444560779-jdz0ti` | `dd1f3109-475d-47df-a51f-479404dc8d66` | `50bb7958-983f-443f-aad8-640f58fff610` |

Worktree selector for a main checkout = `id:<record id>::/home/coder/zamp/services/<repo>`. Seats 2 and 4 have no repo
records yet (`orca project setup-existing-folder` to add). Coder names `sahil-seat-N`; hq = `sahil-hq` (no TTL).
Never `name:<repo>` — it matches 3 records (`selector_ambiguous`).

Rules: FE branches from `origin/release`, run with `zamp dev application-platform-frontend` (`zamp dev 2`). BE branches
from `origin/main`, run with `zamp dev pantheon` (`zamp dev 1`). Setup scripts live in the Orca app repo settings (no
CLI) — check `orca repo show --repo id:<id> --json` → `hookSettings.scripts.setup`.

## Daily loop

**Before spawning anything on a seat: `orca terminal list --worktree "$FE" --json` (and the BE worktree too) and look
at what's already there.** A seat only has 2 real checkouts (FE, BE) — it should never carry more than a small handful
of live terminals. If old tabs from a finished/abandoned task are still sitting there, `orca terminal stop --terminal
<h>` them (not `terminal close` — that only hides the tab, the process survives) before adding a new one. Reuse an
existing idle terminal on that worktree for the next task instead of defaulting to a fresh `orca terminal create`
every time — one seat has ended up running 5-6 stray `claude` processes at once from always creating new tabs and
never closing old ones. New tabs are only for genuinely new, unrelated work landing on that seat.

```bash
orca linear list --filter assigned
orca worktree ps        # free seat: its FE/BE rows sit on release/main with live:0 (or idle)
FE="id:<FE record id>::/home/coder/zamp/services/application-platform-frontend"
orca terminal list --worktree "$FE" --json   # check first — stop stale terminals, reuse an idle one if possible
orca worktree set --worktree "$FE" --linear-issue PRO-XXXX          # sidebar row now shows the ticket
orca terminal create --worktree "$FE" --command "claude 'First: git fetch origin && git checkout -B sahil/pro-xxxx-slug origin/release. Then read the ticket with orca linear issue --current --full --json and fix it per CLAUDE.md. Push the branch when done; do not open a PR.'"
# BE half (only if the ticket touches pantheon): same three lines with the BE record id, path .../pantheon, base origin/main
orca worktree ps        # unread:yes = agent needs you
orca terminal list --worktree "$FE" --json   # handles (<h>) for terminal read/send/stop
```

Branch slug = ticket number + 2–4 words from the title, kebab-case (`sahil/pro-2764-file-tab-extensions`).

A fresh folder makes Claude ask "trust this folder?" once. Answer in the Orca tab, or
`orca terminal send --terminal <h> --text "$(printf '\x1b[B')"` then `--text "$(printf '\r')"`.

## Free a seat (Orca AND Coder — two layers)

1. `orca terminal read --terminal <h> --limit 30` on each live terminal of that seat: idle. Then prove the push:
   `git status --porcelain` empty and `git log origin/<branch>..HEAD` empty in the checkout (run via a one-shot
   `orca terminal create --worktree "$FE" --command "..."`, or over `coder ssh`). Un-pushed → stop and ask.
2. In each checkout that carries the ticket (FE, and BE only if it was used) put the base branch back
   (`git checkout release` / `git checkout main`) and `orca worktree set --worktree "$FE" --linear-issue null`.
3. `orca terminal list --worktree "$FE" --json` (and BE) and `orca terminal stop --terminal <h>` on **every** handle
   returned, not just the one you were using — a seat can accumulate several stray `claude` processes from past
   sessions that never got stopped. `orca terminal stop --worktree "$FE"` alone may only hit the active one.
4. Seat must be off now → `coder stop sahil-seat-N`, confirm with `coder list`. Otherwise the idle TTL stops it.
   Note: while the seat's host stays registered in Orca, Orca's SSH dial can auto-start a stopped seat.
5. **Agent-session card ("chat") is not removed by any step above.** The CLI has no chat/session command — stopping the
   seat leaves the `sahil/<branch>` chat in the sidebar. Tell the user to right-click it in the Orca app → Archive/Delete
   (does not touch the pushed branch). Only the app can clear it.

## Common mistakes

| Mistake | Reality |
|---|---|
| Creating a fresh `orca terminal create` tab for every new task on a seat, never checking what's already running | Old `claude` processes pile up unstopped — one seat has ended up carrying 5-6 stray agent processes at once. Always `orca terminal list --worktree "$FE" --json` first; stop stale ones and reuse an idle terminal before creating a new tab. |
| `orca worktree create` for a ticket | Makes `…/<repo>-<name>` — a folder `zamp dev` cannot run, with no deps. Only for edit-only work that will never run; default is don't. Remove one with `orca worktree rm --worktree branch:<branch>`. |
| Work in the `zamp-N` folder shell (`~/zamp`) | Root folder, not a repo record; cannot link a ticket. Use the FE/BE checkout records. |
| Sending a command containing `--dangerously-skip-permissions` | Blocked by the harness classifier. Not needed: seat Claude already runs in bypass/auto mode. |
| Editing `~/.claude.json` over SSH to pre-trust folders | Blocked for agents; the user does it if wanted. |
| Terminal opens in the wrong folder / `orca` "not installed" | Old dotfiles `tmux-init.sh` attached every login to tmux `main`. Removed in SahilZ0810/dotfiles `cf1c12d` (2026-09-02). Only tmux sessions started before that still do it — close them. Remote `orca` = `~/.orca-relay/bin/orca`, on PATH only in Orca-spawned shells. |
| `worker-start --terminal <h>` to target another workspace | Only accepts a terminal in the coordinator's own worktree. Use `orchestration dispatch --task … --to <h>`; pass `--from <coordinator-handle>` outside the coordinator terminal. |
| `orchestration reset` to tidy one run | Global (`--all\|--tasks\|--messages`), wipes legacy state too. Use `task-update --status completed\|failed`. |

Long-form background: vault `reports/orca-linear-ticket-workflow.md` and `reports/orca-fleet-setup-design.md`.
