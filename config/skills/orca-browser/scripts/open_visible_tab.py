#!/usr/bin/env python3
"""Open a URL as a visible tab on THIS Mac's own Orca worktree — never a zamp-N seat.

Why this exists: Orca bug stablyai/orca#21210 — when several SSH hosts hold the same
repo at the same path (the whole zamp-1..5 fleet does), `tab create` / `goto` without an
explicit --worktree can silently resolve to the WRONG host. The page then fails with a
bare chrome-error and no diagnostic. The fix that issue confirms works is always passing
an explicit --worktree selector.

This skill sidesteps the failure mode entirely by construction: it only ever targets the
"local" host (this Mac, where the Orca desktop app itself runs). That worktree is never
shared with another host, so there is no ambiguous resolution to fall into. But the
--worktree selector is still passed explicitly on every call, both as cheap insurance and
so a future change to the fleet (e.g. a second local worktree) fails loudly instead of
silently picking the wrong one.

It also does the three-step "make it actually visible" sequence in one shot, so a caller
can't accidentally skip the focus step and end up with a tab that opened successfully but
is not the one on screen:
  1. resolve the local worktree selector live (never hardcoded — see orca-seats' rule
     against hardcoded ids for why)
  2. orca tab create --worktree <local> --url <url>
  3. orca tab switch --page <id> --worktree <local> --focus

Usage:
    python3 open_visible_tab.py --url https://example.com
    python3 open_visible_tab.py --url https://example.com --orca orca-dev --json
"""
import argparse, json, subprocess, sys


def run(orca, *args):
    p = subprocess.run([orca, *args, "--json"], capture_output=True, text=True)
    if p.returncode != 0 and not p.stdout.strip():
        print(f"orca {' '.join(args)} failed:\n{p.stderr}", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        print(f"orca {' '.join(args)} returned non-JSON:\n{p.stdout}\n{p.stderr}", file=sys.stderr)
        sys.exit(1)


def local_worktree_selector(orca):
    d = run(orca, "worktree", "ps")
    rows = d.get("result", {}).get("worktrees") or d.get("worktrees") or []
    locals_ = [w for w in rows if w.get("hostId") == "local"]
    if not locals_:
        print("No local-host worktree found. Is Orca's desktop app running and does it "
              "have a repo checked out on this Mac? Run `orca worktree ps --json` to check.",
              file=sys.stderr)
        sys.exit(1)
    if len(locals_) > 1:
        print("More than one local-host worktree found — this skill's assumption (exactly "
              "one, unambiguous local worktree) no longer holds. Pick one explicitly instead "
              "of using this script:\n" +
              "\n".join(f"  {w.get('repo')} -> id:{w.get('repoId')}::{w.get('path')}"
                        for w in locals_), file=sys.stderr)
        sys.exit(1)
    w = locals_[0]
    return f"id:{w.get('repoId')}::{w.get('path')}", w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--orca", default="orca")
    ap.add_argument("--profile", help="browser profile id, if a non-default profile is needed")
    ap.add_argument("--json", action="store_true", dest="as_json")
    a = ap.parse_args()

    sel, w = local_worktree_selector(a.orca)

    create_args = ["tab", "create", "--worktree", sel, "--url", a.url]
    if a.profile:
        create_args += ["--profile", a.profile]
    created = run(a.orca, *create_args)
    if not created.get("ok", True):
        print("tab create failed:", json.dumps(created.get("error")), file=sys.stderr)
        sys.exit(1)
    result = created.get("result", created)
    tab = result.get("tab", result)
    page_id = tab.get("browserPageId") or tab.get("pageId") or tab.get("id")

    focused = None
    if page_id:
        focused = run(a.orca, "tab", "switch", "--page", str(page_id), "--worktree", sel, "--focus")

    out = {
        "worktreeSelector": sel,
        "repo": w.get("repo"),
        "path": w.get("path"),
        "url": a.url,
        "pageId": page_id,
        "created": created,
        "focused": focused,
    }
    if a.as_json:
        print(json.dumps(out, indent=2))
    else:
        print(f"Opened on local worktree ({w.get('repo')} @ {w.get('path')})")
        print(f"  url:     {a.url}")
        print(f"  pageId:  {page_id}")
        print(f"  focused: {'yes' if focused and focused.get('ok', True) else 'UNCONFIRMED — check the Orca window'}")


if __name__ == "__main__":
    main()
