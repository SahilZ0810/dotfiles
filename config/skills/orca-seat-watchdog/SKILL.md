---
name: orca-seat-watchdog
description: >-
  Keep the Zamp Coder seats (zamp-1..zamp-5) alive while they are working. The seats are AWS
  spot workspaces, so a box can be reclaimed and powered off mid-task at any time — killing its
  dev servers and dropping the running agent. Use this WHENEVER the user wants to watch, babysit,
  keep-alive, or auto-recover the seats, says a seat "went down" / "keeps dying" / "is a spot
  instance", or asks to make sure assigned seats stay up. It sweeps every seat, and for each one
  that carries work AND is genuinely powered down (confirmed against coder, not just orca's flaky
  reachability), it wakes the box, restarts the stack with `zamp dev 1` (pantheon) and `zamp dev 2`
  (frontend), and resumes the dropped agent. Best run as a continuous /loop so drops get caught
  automatically. It reuses orca-seats' idea of "which seats carry work" but owns the up-time layer;
  prefer orca-seats for assigning/freeing, this for keeping the working ones alive.
---

# Orca Seat Watchdog — keep working spot seats alive

The five seats are **spot** Coder workspaces. Spot capacity gets reclaimed with little warning, so
a box can power off in the middle of a task. When that happens three things break at once:

1. the workspace goes to `stopped` (its `/home/coder` disk survives, so committed + pushed work and
   the agent's `~/.claude` session history are intact — only the running processes die),
2. the dev servers (`zamp dev`) die, so any preview the user had is gone,
3. the agent's Orca terminal drops.

This skill's job: notice a seat that **was working and is now down**, and put all three back —
without disturbing seats that are fine.

## The one distinction that makes this safe

> **orca "OFFLINE" / `host 'error'` does NOT mean the box is down.**

Orca's SSH dialer loses its tunnel constantly and reports the host as `error`/OFFLINE for a few
seconds while the seat keeps running its agent underneath (you will have watched a seat flip to
OFFLINE and back with its work untouched). If the watchdog treated that as "down" it would
`coder start` an already-running box and run `zamp dev` on top of a live stack — restarting dev
servers under a working agent, for nothing.

So the watchdog **never trusts orca reachability alone**. The ground truth for "is the box on" is
**coder**, not orca. A seat is a real recovery target only when *coder* says it is `stopped`/`failed`
**and** the seat carries work. That cross-check is the whole point of the bundled script; do not
skip it and eyeball orca's OFFLINE instead.

## Resolve the CLI and the sandbox

Resolve the `orca` executable once (see the `orca-cli` stub). On the user's Mac the bash sandbox
blocks the socket the CLI uses to reach the Orca app, so **run every `orca` and `coder` command with
the sandbox disabled** (`dangerouslyDisableSandbox: true`). If `orca` says the app is not running,
`orca open --json` and retry.

## One sweep

Fetch the three live inputs and run the classifier. These three are the only sandbox-off commands a
sweep needs:

```bash
orca host list        --json         > "$TMPDIR/hosts.json"   # seat names zamp-1..zamp-5
orca worktree ps      --json         > "$TMPDIR/wts.json"      # links, comments, terminals, branches
coder list            --output json  > "$TMPDIR/coder.json"    # GROUND TRUTH for power state
python3 <skill>/scripts/watchdog_sweep.py \
    --hosts "$TMPDIR/hosts.json" --worktrees "$TMPDIR/wts.json" --coder "$TMPDIR/coder.json"
```

(`<skill>` is this skill's directory. Add `--json` for machine-readable output.)

Each seat gets a verdict:

| Verdict | Meaning | Watchdog action |
|---|---|---|
| **RECOVER** | coder says `stopped`/`failed` **and** the seat carries work | Wake it — full recovery below. |
| **SETTLING** | coder says `starting` — a wake is already in flight | Wait for the next sweep; do nothing. |
| **TRANSIENT** | coder says `running` but orca can't reach it | **Do NOT touch.** Dial blip, not a real outage. It'll reconnect. |
| **OK** | up and reachable | Nothing. |
| **DOWN_IDLE** | down but no work on it | Leave it off — no reason to burn spot on an empty seat. |
| **UNKNOWN** | no coder row matched (name-map miss) | Report to the user; don't act blind. |

The `RECOVER:` block at the bottom names each seat to wake, its coder workspace, its `zamp` root,
and its service checkouts.

## Recovering one seat (do this per RECOVER seat)

The seat name is `zamp-N`; its coder workspace is `sahil-seat-N` (the shared number is the link).

1. **Wake the box.** `coder start sahil-seat-N` (or a no-op `coder ssh sahil-seat-N true`, which
   auto-starts and blocks until the agent is reachable — often 30–60s). Then confirm it is really up
   before doing anything on it: `coder list --output json` shows it `running`. Don't push commands at
   a box that is still `starting`.

2. **Restart the stack — `zamp dev` must run from the `~/zamp` root**, not a checkout (it looks for
   `zamp_dev_setup/` + `services/` and errits out anywhere else). `1` = pantheon (BE), `2` = frontend.
   Run it in a *managed Orca terminal* so it stays alive after the ssh call returns and the user can
   see it, rather than a bare backgrounded ssh process. Point the terminal at the seat's FE worktree
   selector (from the sweep) and `cd` to root inside the command:
   ```bash
   orca terminal create --worktree "<FE selector for this seat>" --title "zamp dev (recovered)" \
     --command "cd ~/zamp && zamp dev 1 2" --json
   ```
   If `zamp dev 1 2` (space-separated services) is rejected on this version, fall back to two
   terminals, one `zamp dev 1` and one `zamp dev 2`. `zamp dev` is a long-running server; expect the
   terminal to stay busy streaming logs — that is success, not a hang. Only restart the servers the
   task actually needs: a frontend-only task needs `2`; a task that touches pantheon needs `1` too.

3. **Resume the dropped agent — only if its terminal is actually gone.** First look:
   `orca terminal list --worktree "<checkout selector>" --json`. If a live `claude` terminal is
   already back (Orca's own resume can reattach it), leave it — don't stack a second agent. If it is
   gone, resume the prior session in that checkout rather than starting a blank one — the seat's
   `~/.claude` history survived the spot restart, so `claude --continue` picks up exactly where the
   agent was:
   ```bash
   orca terminal create --worktree "<checkout selector>" --title "<task> (resumed)" \
     --command "claude --continue" --json
   ```
   Do this for **each** checkout that carried work (a seat running both an FE and a BE agent needs
   both resumed, one per checkout). Then read the terminal to confirm it came up on the right session
   — and mind the two spawn gotchas from orca-seats: the first-run "trust this folder?" prompt
   (defaults to "No, exit" — arrow down to "Yes" and Enter), and never prefixing the command with a
   local `/skill:name` (seats don't have the user's personal skills).

4. **Re-sweep** to confirm the seat now reads OK (or SETTLING if coder is still bringing it up, which
   is fine — the next tick will confirm).

## Running it as a loop

Spot drops happen whenever, so a single sweep only catches what is down right now. Run it on a
`/loop` so every drop gets caught within one interval:

```
/loop 3m /orca-seat-watchdog
```

Each tick is exactly "one sweep" above, then recover any RECOVER seats. Cadence guidance:

- **3–5 minutes** is a good default — long enough not to thrash, short enough that a reclaimed
  working seat is usually back within a few minutes.
- A tick where every seat is OK/DOWN_IDLE is a **noop** — nothing changed, report it as a quiet hold,
  don't narrate five "still fine" lines.
- A tick that actually woke a seat is worth surfacing: say which seat dropped and that it's back.
- **Stop the loop** when the user says so, or when no seat carries work any more (all FREE/idle — then
  there is nothing to keep alive; offer to stop rather than looping over an idle fleet).

Do not add extra short-interval wakeups to "check faster" — one steady interval is enough, and each
sweep is three sandbox-off CLI calls plus any recovery.

## Common failure modes

- **Recovering a TRANSIENT seat.** The mistake this skill is built to avoid: orca said OFFLINE, but
  coder said running, and a recovery restarted `zamp dev` under a live agent. Always let the coder
  power state decide, never orca reachability.
- **`zamp dev` errors "Could not detect Zamp project structure".** It was run from a checkout, not the
  `~/zamp` root. `cd ~/zamp` first.
- **A second agent piled on a seat that was actually fine.** You resumed without listing terminals
  first. Check `orca terminal list` for a live `claude` before creating one; Orca often reattaches the
  old session itself on restart.
- **`claude --continue` starts a blank session.** The checkout had no prior session (e.g. a fresh
  seat that never ran the agent), or `~/.claude` didn't survive. Rare — the disk persists across spot
  stop — but if so, re-brief the agent from the card's task comment / the linked issue or PR.
- **UNKNOWN verdict for a seat.** The `zamp-N` → `sahil-seat-N` number map missed (a rename). Verify
  with `coder ssh sahil-seat-N hostname` and fix `MAP_WS`/`ws_for` in the script if the convention
  changed. Don't act on an UNKNOWN seat blind.
- **coder shows the seat bouncing `stopped`→`starting` on its own.** Orca's dialer re-wakes registered
  hosts; also expected right after `coder start`. Treat `starting` as SETTLING and let the next tick
  settle it — don't hammer `coder start` in a loop.

## Relationship to orca-seats

`orca-seats` owns *assigning* and *freeing* seats and the FREE/DIRTY/OCCUPIED/OFFLINE state map for
picking one to work on. This skill owns *keeping the working ones powered* — it reuses the same
"does this seat carry work?" signals (linked issue/PR, task comment, live terminal) but adds the
coder power cross-check and the spot-recovery routine. When a seat is freed in orca-seats it stops
carrying work, so this watchdog will read it DOWN_IDLE and stop reviving it — which is the intended
handoff between the two.
