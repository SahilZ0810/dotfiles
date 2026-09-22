#!/usr/bin/env python3
"""One health sweep of the Zamp Coder seats: find seats that carry work but are
actually powered down, so a watchdog loop can bring exactly those back.

Why this is its own thing (and not just the orca-seats classifier): the seats are
AWS *spot* workspaces. Spot reclaims power a box off at any time. When that happens
the running dev servers die and the agent's terminal drops — but the seat's card
(linked issue/PR, task comment) stays, so orca still shows it "assigned". A seat that
went down mid-task needs waking; a FREE seat that went down can stay down.

The load-bearing distinction this script exists to get right:

    orca "OFFLINE"/host-error  !=  the workspace is powered down.

Orca's SSH dialer throws a transient `host 'error'` all the time — the box is up and
the agent is running, Orca just lost its tunnel for a moment (you will have seen a seat
flip to OFFLINE and back while its agent kept working). If the watchdog "recovered"
that seat it would `coder start` an already-running box and re-run `zamp dev` on top of
a live stack — disruptive and pointless. So this script never trusts orca's reachability
alone: it cross-checks the *coder* power state, which is the ground truth for "is the box
on". Only a seat that coder says is stopped/failed AND that carries work is a real
recovery target.

Inputs (pre-fetched so the sandbox-off surface stays to three commands):
    orca host list       --json  > hosts.json
    orca worktree ps     --json  > wts.json
    coder list           --output json > coder.json
    python3 watchdog_sweep.py --hosts hosts.json --worktrees wts.json --coder coder.json

Add --json for machine-readable output.

Seat name mapping: the orca ssh host is named `zamp-N`; its coder workspace is
`sahil-seat-N`. The trailing number is the only stable link between the two systems,
so this script maps by that number. If the fleet is ever renamed, fix MAP_WS below.
Verify the mapping any time with: coder ssh sahil-seat-N hostname  (prints ...sahil-seat-N).
"""
import argparse, json, re, sys

# repo -> base branch (both services rest on release in this fleet; see orca-seats).
BASE_BRANCH = {"application-platform-frontend": "release", "pantheon": "release"}
SERVICE_REPOS = set(BASE_BRANCH)


def _load(path):
    with open(path) as f:
        return json.load(f)


def _hosts(blob):
    r = blob.get("result", blob)
    hosts = r.get("hosts") or (r if isinstance(r, list) else [])
    return [h for h in hosts if h.get("kind") == "ssh"]


def _worktrees(blob):
    r = blob.get("result", blob)
    return r.get("worktrees") or blob.get("worktrees") or []


def _coder_power(blob):
    """coder workspace name -> power state (running/stopped/starting/failed/...)."""
    rows = blob if isinstance(blob, list) else (blob.get("workspaces") or [])
    out = {}
    for w in rows:
        name = w.get("name") or ""
        # coder puts the live state under latest_build.status; be defensive.
        status = (
            (w.get("latest_build") or {}).get("status")
            or w.get("status")
            or "unknown"
        )
        if name:
            out[name] = str(status).lower()
    return out


def ws_for(seat_name):
    """orca host 'zamp-N' -> coder workspace 'sahil-seat-N' via the shared number."""
    m = re.search(r"(\d+)\s*$", seat_name or "")
    return f"sahil-seat-{m.group(1)}" if m else None


def _branch(w):
    return (w.get("branch") or "").replace("refs/heads/", "")


def seat_facts(host, wts):
    hid = "ssh:" + host.get("id", "")
    mine = [w for w in wts if w.get("hostId") == hid]

    has_work = False
    work_reasons = []
    fe_sel = zamp_root_path = None
    for w in mine:
        repo, br = w.get("repo"), _branch(w)
        if repo == "application-platform-frontend":
            fe_sel = f"id:{w.get('repoId')}::{w.get('path')}"
            # derive the seat's zamp root from the FE checkout path
            p = w.get("path") or ""
            if "/services/" in p:
                zamp_root_path = p.split("/services/")[0]
        # "assigned work" = an active task signal (not merely a leftover branch).
        if (w.get("liveTerminalCount") or 0) > 0:
            has_work = True; work_reasons.append(f"{repo}: live terminal")
        if w.get("linkedLinearIssue"):
            has_work = True; work_reasons.append(f"{repo}: {w['linkedLinearIssue']}")
        if w.get("linkedPR"):
            has_work = True; work_reasons.append(f"{repo}: linked PR")
        c = (w.get("comment") or "").strip()
        if c and c.lower() != "free":
            has_work = True; work_reasons.append(f"{repo}: '{c}'")

    checkouts = []
    for w in mine:
        if w.get("repo") in SERVICE_REPOS:
            checkouts.append({
                "repo": w.get("repo"),
                "selector": f"id:{w.get('repoId')}::{w.get('path')}",
                "branch": _branch(w),
                "live": w.get("liveTerminalCount") or 0,
            })
    return {
        "reachable": host.get("connectionStatus") == "connected",
        "has_work": has_work,
        "work_reasons": work_reasons,
        "fe_selector": fe_sel,
        "zamp_root": zamp_root_path,
        "checkouts": checkouts,
    }


def verdict(power, reachable, has_work):
    """Decide what the watchdog should do with this seat.

    RECOVER      box is down (coder) and it carries work -> wake + zamp dev + resume
    DOWN_IDLE    box is down but no work -> leave it off
    TRANSIENT    coder says running but orca can't reach it -> NOT down; do not touch,
                 let orca reconnect (recovering here would disrupt a live seat)
    SETTLING     coder says starting -> a recovery is already in flight; wait
    OK           up and reachable
    UNKNOWN      no coder row (mapping miss) -> report, don't act
    """
    if power in ("stopped", "failed", "canceled", "deleted"):
        return "RECOVER" if has_work else "DOWN_IDLE"
    if power in ("starting", "pending", "stopping"):
        return "SETTLING"
    if power == "running":
        return "OK" if reachable else "TRANSIENT"
    return "UNKNOWN"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hosts", required=True)
    ap.add_argument("--worktrees", required=True)
    ap.add_argument("--coder", required=True)
    ap.add_argument("--json", action="store_true", dest="as_json")
    a = ap.parse_args()

    hosts = sorted(_hosts(_load(a.hosts)), key=lambda h: h.get("name", ""))
    wts = _worktrees(_load(a.worktrees))
    power_of = _coder_power(_load(a.coder))

    seats = []
    for h in hosts:
        name = h.get("name")
        ws = ws_for(name)
        power = power_of.get(ws, "unknown")
        f = seat_facts(h, wts)
        v = verdict(power, f["reachable"], f["has_work"])
        seats.append({
            "seat": name, "workspace": ws, "power": power, "verdict": v,
            **f,
        })

    if a.as_json:
        print(json.dumps({"seats": seats}, indent=2))
        return

    print(f"{'SEAT':8} {'WORKSPACE':16} {'POWER':10} {'VERDICT':10} WHY")
    print("-" * 92)
    order = {"RECOVER": 0, "SETTLING": 1, "TRANSIENT": 2, "UNKNOWN": 3, "OK": 4, "DOWN_IDLE": 5}
    for s in sorted(seats, key=lambda s: (order.get(s["verdict"], 9), s["seat"] or "")):
        why = "; ".join(s["work_reasons"]) if s["has_work"] else "no active work"
        if s["verdict"] == "TRANSIENT":
            why = "coder=running but orca can't reach it — dial blip, NOT down"
        print(f"{s['seat'] or '?':8} {s['workspace'] or '?':16} {s['power']:10} {s['verdict']:10} {why}")

    recover = [s for s in seats if s["verdict"] == "RECOVER"]
    print("-" * 92)
    if not recover:
        print("Nothing to recover — no seat is both powered-down and carrying work.")
        return
    print("RECOVER these (down + has work):")
    for s in recover:
        print(f"  {s['seat']} -> {s['workspace']}")
        print(f"     zamp_root: {s['zamp_root'] or '~/zamp'}")
        for c in s["checkouts"]:
            print(f"     checkout: {c['repo']} on {c['branch']}  {c['selector']}")


if __name__ == "__main__":
    main()
