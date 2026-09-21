---
name: orca-seats
description: >-
  Safely assign work to the Zamp Coder seats (zamp-1..zamp-5) through the orca CLI, with a
  mandatory live seat-state check first. Use this WHENEVER the user wants to spawn or assign a
  seat, start a Linear ticket or GitHub PR on a seat, asks which seats are free or busy, wants a
  status of all seats / "where is each seat right now", or needs to drive Orca's embedded browser
  on a seat. It never double-books a seat that is already working or is not checked out, it derives
  seat identity and repo ids live every time (never from a hardcoded table, which goes stale and
  causes double-booking), and it applies the workaround for Orca browser bug #21210 (tab create /
  goto silently opening on the wrong SSH host). Prefer this over orca-ticket for anything about
  picking, assigning, or reporting the state of a seat.
---

# Orca Seats — safe seat assignment for the Zamp fleet

This skill wraps the `orca` CLI with three guardrails that plain `orca-ticket` does not enforce:

1. **Know the state of every seat before you touch one** (Rule 1).
2. **Never assign a seat that is already working or is not checked out** (Rule 2).
3. **Drive the browser without hitting Orca bug #21210** (Rule 3).

For the detailed ticket-branch-and-run mechanics (branch naming, `zamp dev`, freeing a seat, the
FE-from-`release` / BE-from-`main` rules) this skill defers to `orca-ticket`, and to `orca-linear`
for reading and updating Linear issues. This skill owns the *seat safety* layer on top.

## The fleet, and the one load-bearing rule

The fleet is five Coder seats. The only stable identifiers are their host names **`zamp-1` ..
`zamp-5`**, from `orca host list`. Everything else — repo ids, the `<repoId>::<path>` worktree
selectors, which branch a checkout is on, which seat is free — **changes constantly and MUST be
read live every time.**

> Load-bearing rule: never hardcode a seat's repo id or a `worktree` selector, and never trust a
> table of them (including any table inside `orca-ticket`). The single incident this skill exists
> to prevent was caused by a stale table whose repo ids were all wrong. Derive ids from
> `orca worktree ps --json` on every task.

## Resolve the CLI and the sandbox

Resolve the `orca` executable once (see the `orca-cli` stub: `ORCA_CLI_COMMAND` env, else
`orca-dev` in a dev checkout, else `orca-ide` on bare Linux, else `orca`). Substitute it for
`orca` below.

On the user's Mac, the bash sandbox blocks the local socket the CLI uses to reach the running
Orca app, so a sandboxed `orca` call fails with `runtime_unavailable` even though the app is up.
**Run every `orca` command with the sandbox disabled** (`dangerouslyDisableSandbox: true`), or from
a shell the user has taken out of the sandbox. `orca skills get ...` is the exception — it reads
bundled content and works sandboxed. If `orca` reports the app is not running, start it with
`orca open --json` and retry.

## Rule 1 — Build the seat-state map before ANY assignment

Do this first, every time, before picking or spawning anything. Fetch the two live inputs and run
the bundled classifier:

```bash
orca host list --json      > "$TMPDIR/hosts.json"     # stable seat names zamp-1..zamp-5
orca worktree ps --json    > "$TMPDIR/wts.json"        # live repo ids, branches, terminals, links
python3 <skill>/scripts/seat_state.py --hosts "$TMPDIR/hosts.json" --worktrees "$TMPDIR/wts.json"
```

(`<skill>` is this skill's directory. Add `--json` for machine-readable output. The script can also
call orca itself with `--orca <cmd>`, but pre-fetching keeps the sandbox-off surface to two
commands.)

It prints one row per seat with a state and the reason, and names the seat to assign:

```
SEAT     STATE     WHY
zamp-2   DIRTY     pantheon on release (base main)
zamp-1   OCCUPIED  application-platform-frontend: linked PRO-2629; zamp: comment 'FE #3144 ...'; ...
...
Assign to: zamp-2  FE=id:27bd04bb-...::/home/coder/zamp/services/application-platform-frontend
```

When the user asks "where is each seat" / "which seats are free" / "status of all seats", this table
**is** the answer — show it.

## Rule 2 — Never assign an occupied or not-checked-out seat

The classifier assigns each seat one of four states. Assign work only to a **FREE** seat. A
**DIRTY** seat is reusable but must be cleaned first. Never assign an **OCCUPIED** or **OFFLINE**
seat.

| State | Meaning | Action |
|---|---|---|
| **FREE** | Checked out, on base branches, no live terminals, no links, no task comment | Assign. |
| **DIRTY** | No active work, but a checkout is left on a feature branch | Reusable — but have the agent `git stash -u` then reset to the base branch before branching. Warn the user it is a reused leftover seat. |
| **OCCUPIED** | A terminal is live, **or** a ticket/PR is linked, **or** any checkout's comment names a task | Do NOT assign. It is already working. |
| **OFFLINE** | Host not `connected`, or missing an FE/pantheon repo record | Not checked out. Do not assign; tell the user (a stopped seat can be started, an unconfigured one needs `orca project setup-existing-folder`). |

**Why "occupied if ANY checkout shows ANY signal", including a sibling checkout.** A seat is one
Coder workspace holding several checkouts (the `zamp` root, the FE checkout, the pantheon checkout).
Work assigned to the seat can leave its mark on any of them. The incident this skill prevents:
seat-1's FE checkout showed `comment: 'free'` and `liveTerminalCount: 0`, so it looked free — but
its `zamp` root card said `FE #3144 (CONFLICTING) + BE #6149`. It was already assigned. **`live=0`
means no terminal is attached right now, not that the work is done.** An agent that finished its
turn, and a session dropped by an Orca reconnect, both read as `live=0`. So the terminal count
alone is never enough — a linked issue/PR or a task comment on *any* of the seat's checkouts marks
the whole seat occupied.

**If no seat is FREE.** Do not fall back to an OCCUPIED seat. If a DIRTY seat exists, offer it as
"reusable after cleanup". If every seat is OCCUPIED/OFFLINE, stop and tell the user the fleet is
full (max 5 concurrent) — do not invent capacity.

Once you pick a seat, take its FE selector from the classifier output (or from
`orca worktree ps --json` directly) — never from memory or a table.

## Rule 3 — Browser ops must name the seat explicitly (#21210)

Orca bug [stablyai/orca#21210](https://github.com/stablyai/orca/issues/21210): with several SSH
hosts each holding the same repo at the **same path** (exactly the Zamp fleet — every seat has
`/home/coder/zamp/services/application-platform-frontend`), `orca tab create` / `orca goto`
**without `--worktree`** silently resolve to a worktree on a *different* host. The browser then
cannot load a URL served only by the intended seat, and fails silently:
`chrome-error://chromewebdata/`, an empty page, sometimes a later
`{"error":{"code":"browser_tab_not_found"}}`. There is no diagnostic — it looks exactly like a
network or auth outage and costs hours.

Mitigation — treat as mandatory for any seat browser work:

1. **Always pass an explicit `--worktree` selector** on `tab create`, `goto`, and any browser
   command. Never rely on cwd/default resolution.
2. Resolve that selector for the *intended* seat first, live:
   ```bash
   orca worktree list --json | ...   # find the FE worktree whose hostId is ssh:<intended-host-id>
   orca tab create --worktree "id:<repoId>::<path>" --url <url> --json
   ```
   The classifier's `feSelector` for the chosen seat is exactly this value.
3. After opening, **confirm the resolved host matches the seat you meant** (read the command's
   echoed worktree/host, or `orca worktree current`).
4. If you still get `chrome-error` or `browser_tab_not_found`, do not retry blind — re-issue the
   command with the explicit `--worktree` selector. That is the one change the issue confirms fixes
   it. Feed served-only-by-that-host URLs (dev servers on the seat) only to that seat's tab.

## Assigning a seat (the workflow)

1. **Rule 1** — build the seat-state map. Pick a FREE seat (or a DIRTY one with cleanup).
2. Confirm the FE checkout has no stray terminals: `orca terminal list --worktree "<FE>" --json`.
   Stop stale ones (`orca terminal stop`) and reuse an idle terminal rather than piling up tabs.
3. Link the ticket/PR and label the card so the state stays legible to the *next* run of Rule 1:
   ```bash
   orca worktree set --worktree "<FE>" --linear-issue <PRO-XXXX> \
     --display-name "<short title>" --comment "spawning: <task>" --json
   ```
   (A task comment is what makes this seat read as OCCUPIED next time — that is the point.)
4. Spawn the agent in the FE checkout (fresh ticket → new branch from `origin/release`; existing PR
   → check out its branch and `reset --hard` to origin, never `-B` from release, which would blow
   the PR away; DIRTY seat → `git stash -u` first). See `orca-ticket` for the exact branch rules.
   ```bash
   orca terminal create --worktree "<FE>" --title "<task>" --command "claude '<brief>'" --json
   ```
5. The seat may be a stopped Coder workspace; `terminal create` auto-starts it (can take ~30-60s).
   Confirm with `orca terminal read`; if the handle later returns `terminal_handle_stale` (Orca
   reconnected and dropped the agent, leaving a bare shell), re-list terminals, take the new handle,
   and relaunch the agent in that shell with `orca terminal send` rather than opening a new tab.
6. **Always read the terminal after launch — don't assume it started.** A checkout that hasn't run
   Claude before shows a one-time "trust this folder?" prompt, with **"No, exit" pre-highlighted**.
   A bare `--enter` there confirms "No" and drops straight back to a shell — the agent never starts,
   silently. If the tail shows this prompt: send `$(printf '\x1b[B')` (down arrow, moves the
   selection to "Yes, I trust this folder") as its own `terminal send`, confirm with a read that the
   selection moved, then send `$(printf '\r')` to confirm — then relaunch the `claude '<brief>'`
   command. Do this as three separate sends with a read in between each; sending them all at once
   can race the prompt render.

## Freeing a seat

Freeing = releasing the seat's current task so Rule 1 reads it FREE again. Order matters, and two
commands in the older `orca-ticket` procedure are wrong for this CLI version — use the steps below,
not that procedure.

1. **Prove the work is saved first — never free unpushed work.** Read the agent terminal; if it is
   mid-turn, wait or ask. Then, on the seat, in each service checkout the task touched, run
   `git status --porcelain` (only an untracked `.orca/` is OK) and `git log --oneline @{u}..HEAD`
   (must be empty). If anything is uncommitted or unpushed, STOP and ask the user — do not free. A
   pushed branch or an open PR for the branch is proof enough (`gh pr list --head <branch>`).

2. **Put every service checkout back on its base branch**, not just the one the task used. In this
   fleet **both** services rest on `release` — FE and pantheon PRs alike target `release`, and this
   is what the user means by **"reset a seat" / "clean a seat": `git checkout release` on every
   service checkout (FE and pantheon).** A seat is FREE only when all its service checkouts are on
   `release`; a checkout left on a feature branch (or pantheon on `main`) makes the seat read DIRTY.
   Run in each: `git checkout release`. (An older orca-ticket note says "BE from main" — that is
   stale for the resting state; go by the live PR `baseRefName`, which is `release`.)

3. **Clear the card state** on each checkout so the next Rule 1 sees it FREE:
   `orca worktree set --worktree "<sel>" --comment free --linear-issue null --json`. Until the link
   and task comment are cleared, this skill keeps the seat OCCUPIED — by design.

4. **Close the terminals with the right command.** `orca terminal stop --terminal <handle>` does NOT
   exist in this CLI — it takes only `--worktree`, is deprecated, and errors `invalid_argument` on
   `--terminal`. Use instead:
   `orca terminal close --worktree "<FE>" --all --json`. This stops the processes and durably
   retires the tabs, layouts, and agent-resume records.
   - It often returns `terminal_stop_unverifiable` ("the owning SSH host did not confirm the PTY
     exit"). Do NOT report the agent as stopped, and do NOT retry against another host — that is the
     documented `unverifiable` case. The surfaces are retired; any lingering PTY is killed by the
     `coder stop` in the next step.

5. **`coder stop sahil-seat-N` is best-effort, not durable.** It powers the workspace down and kills
   lingering PTYs, but Orca's SSH dial auto-restarts a still-registered host — often within seconds,
   and *your own* `orca host list` / `orca worktree ps` verify calls are enough to trigger it. Run
   `coder stop` once to kill orphans, then expect the host to bounce back to "Starting". Do not loop
   trying to keep it down. The task is freed regardless; the workspace idle-TTL, or the next
   assignment, settles the power state.

6. **The agent-session ("chat") card is not removed by any CLI step.** Tell the user to right-click
   it in the Orca app → Archive/Delete. Only the app can clear it; it does not touch the pushed
   branch or PR.

Then re-run Rule 1 to confirm the seat reads FREE — or OFFLINE/reconnecting if `coder stop` is still
settling, which is expected, not a failure.

> **Order is not optional — retire terminals (step 4) BEFORE `coder stop` (step 5), and never
> `coder stop` on its own.** `coder stop` kills the seat's processes but leaves Orca's terminal
> *surfaces* and *agent-resume records* intact. Orca's background SSH dialer restarts a registered
> seat by itself (not only when you run a CLI command), and on restart it reattaches those surfaces
> — the agent comes back to life on a fresh process. The incident that added this note: on a "close
> all the seats" request the processes were `coder stop`ped with no prior `terminal close --all`;
> every seat bounced back to "Started" within a minute with its agent **live again**. So treat
> closing a seat as "retire the Orca surfaces", not "stop the box". `terminal close --all` is the
> durable stop; `coder stop` only settles the power state, which the dialer may undo anyway.

## Closing seats in bulk (shutdown, e.g. "close all the seats")

A bulk shutdown is the free procedure applied to every seat, in this order — not a shortcut to
`coder stop`:

1. Rule 1 map — see which seats have live checkouts and which tasks are foreign (not yours to kill);
   confirm with the user before killing work they did not ask you to start.
2. For every checkout with a live terminal, verify the work is saved (free step 1), then
   **`orca terminal close --worktree <sel> --all --json`** — this is what actually stops the agents
   and retires their resume records so a restart comes up empty. Do all of these before any
   `coder stop`. `terminal_stop_unverifiable` here is expected when a host is mid-reconnect; do not
   loop on it — re-run the close once the host is settled, or let the coder stop and idle-TTL carry
   it. A seat is durably closed once its surfaces are retired, even if it later powers back to idle.
3. **Clear the card labels on every carded checkout — not just the ones that had a terminal.** The
   display-name, comment, and linked issue/PR persist independently of terminals and `coder stop`,
   so a closed seat keeps showing its old task name in the sidebar until you reset the card. Find
   them with `orca worktree ps --json` (any checkout whose `displayName` != repo, or `comment` is
   not empty/`free`, or has `linkedLinearIssue`/`linkedPR`), then for each:
   `orca worktree set --worktree <sel> --display-name <repo> --comment free --linear-issue null --json`.
   Do this across all three checkouts (zamp root, FE, pantheon) of every seat — the label the user
   sees is often on the `zamp` root, not the FE checkout.
4. `coder stop sahil-seat-N` each seat. Verify with `coder list`, never with `orca ...` (an `orca`
   call re-wakes the dialer and restarts the seat you just stopped).
5. Expect seats to still power back to **idle** while the Orca app runs — that is fine once
   terminals are retired and cards cleared; they come up empty, no agents, no task name. To keep
   them powered off, the user quits Orca (stops the dialer) or you deregister the hosts.
6. Agent-session ("chat") cards remain in the sidebar for the user to archive in the app.

## Common failure modes

- **`live=0` read as "free".** The double-booking this skill prevents. Trust the classifier's
  OCCUPIED verdict over a single checkout's terminal count.
- **`runtime_unavailable` while the app is running.** The sandbox is blocking the app socket. Run
  the `orca` command with the sandbox disabled.
- **`terminal_handle_stale`.** Orca reconnected; the old handle is dead and the agent may have been
  replaced by a bare shell. Re-list, take the new handle, relaunch in place.
- **Silent `chrome-error` in the browser.** Bug #21210 — you omitted `--worktree` and hit the wrong
  host. Re-issue with the explicit selector for the intended seat.
- **`terminal stop --terminal <h>` errors `invalid_argument`.** That command is deprecated and takes
  only `--worktree`. Free terminals with `terminal close --worktree <sel> --all` instead.
- **`terminal_stop_unverifiable` on close.** The host could not confirm every PTY exited. Do not
  claim the agent stopped and do not retry on another host; `coder stop` cleans up the orphan.
- **A stopped seat immediately shows "Starting" again.** Orca's SSH dial re-wakes a registered host,
  and your own verify calls trigger it. Expected — the task is still freed; do not loop on it.
- **Stopped seats come back with their agents running again.** You ran `coder stop` without a prior
  `terminal close --worktree <sel> --all`. `coder stop` kills processes but not Orca's terminal
  surfaces/resume records; the dialer restarts the seat and reattaches the agent. Retire the
  terminals first — that is the durable stop; `coder stop` alone is not.
