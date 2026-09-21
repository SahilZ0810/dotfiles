#!/usr/bin/env python3
"""Open a URL as a visible tab on the worktree the calling session is running in.

Why this exists: Orca bug stablyai/orca#21210 — when several SSH hosts hold the same
repo at the same path (the whole zamp-1..5 fleet does), `tab create` / `goto` without an
explicit --worktree can silently resolve to the WRONG host. The page then fails with a
bare chrome-error and no diagnostic. The fix that issue confirms works is always passing
an explicit --worktree selector.

The guardrail is the explicit selector, not any particular host. $ORCA_WORKTREE_ID names
one exact worktree (`<repoId>::<path>`), so pinning it is unambiguous by construction even
when five seats share a path — there is nothing left for Orca to resolve.

Targeting the session's own worktree is also the only way the tab is actually visible. The
Orca window shows one worktree at a time, so a tab opened on a different one is the active
tab in a pane nobody is looking at: it reports active:true and no loadError while the user
sees nothing. An earlier version of this script always targeted the "local" Mac worktree
and hit exactly that.

Resolution order:
  1. --worktree, if the caller passed one
  2. $ORCA_WORKTREE_ID — the worktree this session runs in (the normal case)
  3. the single "local"-host worktree, for a bare shell with no Orca session context

It also does the three-step "make it actually visible" sequence in one shot, so a caller
can't accidentally skip the focus step and end up with a tab that opened successfully but
is not the one on screen:
  1. resolve the worktree selector live (never hardcoded — see orca-seats' rule against
     hardcoded ids for why)
  2. orca tab create --worktree <sel> --url <url>
  3. orca tab switch --page <id> --worktree <sel> --focus

Note: a server listening on the seat's localhost is not reachable from the Orca browser,
which runs on the desktop. Use the forwarded Coder URL instead — the pattern is in
$VSCODE_PROXY_URI, e.g. https://3000--main--<workspace>--<user>.coder.<domain>.

Usage:
    python3 open_visible_tab.py --url https://example.com
    python3 open_visible_tab.py --url https://example.com --orca orca-dev --json
    python3 open_visible_tab.py --url https://example.com --worktree "id:<repoId>::<path>"
"""
import argparse, json, os, subprocess, sys


def run(orca, *args):
    p = subprocess.run([orca, *args, "--json"], capture_output=True, text=True)
    if p.returncode != 0 and not p.stdout.strip():
        print(f"orca {' '.join(args)} failed:\n{p.stderr}", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        start = p.stdout.find("{")
        if start != -1:
            try:
                return json.loads(p.stdout[start:])
            except json.JSONDecodeError:
                pass
        print(f"orca {' '.join(args)} returned non-JSON:\n{p.stdout}\n{p.stderr}", file=sys.stderr)
        sys.exit(1)


def worktree_rows(orca):
    d = run(orca, "worktree", "ps")
    return d.get("result", {}).get("worktrees") or d.get("worktrees") or []


def session_worktree(rows):
    wid = os.environ.get("ORCA_WORKTREE_ID", "").strip()
    if not wid:
        return None
    match = next((w for w in rows if f"{w.get('repoId')}::{w.get('path')}" == wid), None)
    return f"id:{wid}", match or {"repo": "(not in worktree ps)", "path": wid.split("::", 1)[-1]}


def local_worktree(rows):
    locals_ = [w for w in rows if w.get("hostId") == "local"]
    if not locals_:
        print("No worktree to target: $ORCA_WORKTREE_ID is unset and there is no local-host "
              "worktree. Pass --worktree explicitly, or run `orca worktree ps --json` to see "
              "what is available.", file=sys.stderr)
        sys.exit(1)
    if len(locals_) > 1:
        print("$ORCA_WORKTREE_ID is unset and more than one local-host worktree exists, so "
              "there is no unambiguous fallback. Pass --worktree explicitly:\n" +
              "\n".join(f"  {w.get('repo')} -> id:{w.get('repoId')}::{w.get('path')}"
                        for w in locals_), file=sys.stderr)
        sys.exit(1)
    w = locals_[0]
    return f"id:{w.get('repoId')}::{w.get('path')}", w


def resolve_worktree(orca, override):
    if override:
        sel = override if override.startswith("id:") else f"id:{override}"
        rows = worktree_rows(orca)
        match = next((w for w in rows if f"id:{w.get('repoId')}::{w.get('path')}" == sel), None)
        return sel, match or {"repo": "(not in worktree ps)", "path": sel}, "--worktree"
    rows = worktree_rows(orca)
    picked = session_worktree(rows)
    if picked:
        return picked[0], picked[1], "$ORCA_WORKTREE_ID"
    sel, w = local_worktree(rows)
    return sel, w, "local fallback"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--orca", default=os.environ.get("ORCA_CLI_COMMAND") or "orca")
    ap.add_argument("--worktree", help="worktree selector to target, overriding $ORCA_WORKTREE_ID")
    ap.add_argument("--profile", help="browser profile id, if a non-default profile is needed")
    ap.add_argument("--json", action="store_true", dest="as_json")
    a = ap.parse_args()

    sel, w, source = resolve_worktree(a.orca, a.worktree)

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

    current = run(a.orca, "tab", "current", "--worktree", sel)
    ctab = current.get("result", {}).get("tab", {})

    out = {
        "worktreeSelector": sel,
        "worktreeSource": source,
        "repo": w.get("repo"),
        "path": w.get("path"),
        "url": a.url,
        "pageId": page_id,
        "active": ctab.get("active"),
        "loadError": ctab.get("loadError"),
        "certificateFailure": ctab.get("certificateFailure"),
        "created": created,
        "focused": focused,
    }
    if a.as_json:
        print(json.dumps(out, indent=2))
    else:
        print(f"Opened on {w.get('repo')} @ {w.get('path')} (via {source})")
        print(f"  url:     {a.url}")
        print(f"  pageId:  {page_id}")
        print(f"  focused: {'yes' if focused and focused.get('ok', True) else 'UNCONFIRMED — check the Orca window'}")
        if ctab.get("loadError"):
            print(f"  LOAD ERROR: {ctab.get('loadError')}")


if __name__ == "__main__":
    main()
