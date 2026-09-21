#!/usr/bin/env python3
"""Derive the live state of every Zamp Coder seat from Orca data.

Why this exists: the seat identity (zamp-1..zamp-5) is stable, but repo ids,
branches, and which seat is busy change constantly. A hardcoded table goes
stale and causes double-booking (assigning a seat that is already working).
This script computes the truth every time from `orca host list` and
`orca worktree ps`, so callers never guess.

Usage (preferred — you already fetch these with the sandbox off):
    orca host list --json          > hosts.json
    orca worktree ps --json        > wts.json
    python3 seat_state.py --hosts hosts.json --worktrees wts.json

Or let it call orca itself (needs the orca runtime reachable; on this Mac
that means running the orca calls with the sandbox disabled):
    python3 seat_state.py --orca orca

Add --json for machine-readable output.

State meanings:
  FREE      checked out, on base branches, nothing running or assigned -> safe to assign
  DIRTY     no active work, but a checkout is left on a feature branch -> reusable, but
            stash/reset first (leftover from a previous task that was not cleaned up)
  OCCUPIED  a terminal is live, or a ticket/PR is linked, or a checkout comment names a
            task -> DO NOT assign; the seat is already working
  OFFLINE   host not connected, or missing an FE/pantheon repo record -> not checked out
"""
import argparse, json, subprocess, sys

# repo name -> its base branch. A checkout sitting on any other branch is "dirty".
BASE_BRANCH = {
    "application-platform-frontend": "release",
    "pantheon": "main",
}
# The seat is "checked out" only if it carries at least one real service repo.
SERVICE_REPOS = set(BASE_BRANCH)


def _load(path):
    with open(path) as f:
        return json.load(f)


def _run_orca(orca, *args):
    out = subprocess.run([orca, *args, "--json"], capture_output=True, text=True)
    # orca prints a codesign warning to stderr on macOS; ignore it, parse stdout.
    return json.loads(out.stdout)


def _hosts(blob):
    r = blob.get("result", blob)
    hosts = r.get("hosts") or (r if isinstance(r, list) else [])
    return [h for h in hosts if h.get("kind") == "ssh"]


def _worktrees(blob):
    r = blob.get("result", blob)
    return r.get("worktrees") or blob.get("worktrees") or []


def _branch(w):
    return (w.get("branch") or "").replace("refs/heads/", "")


def classify(host, wts):
    """Return (state, reasons, checkouts) for one seat."""
    hid = "ssh:" + host.get("id", "")
    mine = [w for w in wts if w.get("hostId") == hid]
    repos = {w.get("repo") for w in mine}

    if host.get("connectionStatus") != "connected":
        return "OFFLINE", [f"host {host.get('connectionStatus')!r}"], mine
    if not (SERVICE_REPOS & repos):
        return "OFFLINE", ["no FE/pantheon repo record (not checked out)"], mine

    occupied, dirty = [], []
    for w in mine:
        repo, br = w.get("repo"), _branch(w)
        # OCCUPIED signals — any one means the seat is actively spoken for.
        if (w.get("liveTerminalCount") or 0) > 0:
            occupied.append(f"{repo}: {w['liveTerminalCount']} live terminal(s)")
        if w.get("linkedLinearIssue"):
            occupied.append(f"{repo}: linked {w['linkedLinearIssue']}")
        if w.get("linkedPR"):
            occupied.append(f"{repo}: linked PR")
        c = (w.get("comment") or "").strip()
        if c and c.lower() != "free":
            # A comment on ANY checkout (including the zamp root) marks the whole
            # seat. This is the seat-1 lesson: FE said 'free' with live=0 while the
            # root said 'FE #3144 ...'. live=0 means no terminal attached now, not
            # that the work is done.
            occupied.append(f"{repo}: comment {c!r}")
        # DIRTY signal — feature branch left behind, but nobody is on it.
        base = BASE_BRANCH.get(repo)
        if base and br and br != base:
            dirty.append(f"{repo} on {br} (base {base})")

    if occupied:
        return "OCCUPIED", occupied, mine
    if dirty:
        return "DIRTY", dirty, mine
    return "FREE", ["clean: on base branches, no live terminals, no links"], mine


def fe_selector(checkouts):
    for w in checkouts:
        if w.get("repo") == "application-platform-frontend":
            return f"id:{w.get('repoId')}::{w.get('path')}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hosts")
    ap.add_argument("--worktrees")
    ap.add_argument("--orca", default="orca", help="orca executable if fetching live")
    ap.add_argument("--json", action="store_true", dest="as_json")
    a = ap.parse_args()

    hosts_blob = _load(a.hosts) if a.hosts else _run_orca(a.orca, "host", "list")
    wts_blob = _load(a.worktrees) if a.worktrees else _run_orca(a.orca, "worktree", "ps")

    hosts = sorted(_hosts(hosts_blob), key=lambda h: h.get("name", ""))
    wts = _worktrees(wts_blob)

    seats = []
    for h in hosts:
        state, reasons, checkouts = classify(h, wts)
        seats.append({
            "seat": h.get("name"),
            "hostId": h.get("id"),
            "state": state,
            "reasons": reasons,
            "feSelector": fe_selector(checkouts),
        })

    if a.as_json:
        print(json.dumps({"seats": seats}, indent=2))
        return

    order = {"FREE": 0, "DIRTY": 1, "OCCUPIED": 2, "OFFLINE": 3}
    seats.sort(key=lambda s: (order.get(s["state"], 9), s["seat"] or ""))
    print(f"{'SEAT':8} {'STATE':9} WHY")
    print("-" * 78)
    for s in seats:
        print(f"{s['seat'] or '?':8} {s['state']:9} {'; '.join(s['reasons'])}")
    free = [s for s in seats if s["state"] == "FREE"]
    dirty = [s for s in seats if s["state"] == "DIRTY"]
    print("-" * 78)
    if free:
        print(f"Assign to: {free[0]['seat']}  FE={free[0]['feSelector']}")
    elif dirty:
        print(f"No clean seat. Reusable (stash/reset first): {dirty[0]['seat']}  "
              f"FE={dirty[0]['feSelector']}")
    else:
        print("No FREE or DIRTY seat — every seat is OCCUPIED or OFFLINE. Do not assign; "
              "tell the user.")


if __name__ == "__main__":
    main()
