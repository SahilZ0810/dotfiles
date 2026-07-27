#!/usr/bin/env python3
"""Build an agent-run record from one seat's local artifacts.

Deterministic and stdlib-only, so it can be golden-file tested with no network.
Interpretation (turning records into lessons) is deliberately NOT here — that is
the distiller's job on HQ. This module only archives facts faithfully.
"""

import json
import re

# approve-gate.sh's own output strings. The rejection message embeds the human's
# verbatim reply, which is the single most valuable learning signal in the pool and
# is stored nowhere else — the gate script only touches a marker file on approval.
GATE_REJECT = re.compile(r'not-approval:\s*"(.*?)"\s+is not an explicit', re.S)
GATE_APPROVE = re.compile(r"unlocked: implementation gate opened for (\S+)")

# Ordered least → most advanced. derive_outcome reports the furthest one reached.
STAGE_LABELS = [
    "agent:queued",
    "agent:planning",
    "agent:plan-review",
    "agent:implementing",
    "agent:pr-open",
    "agent:ready-to-verify",
    "agent:approved",
]


def _blocks(obj):
    """Yield content blocks from one transcript line.

    Tolerates both `message.content` (current shape) and a top-level `content`
    (older lines), and both a bare string and a list of blocks. We control neither
    the transcript schema nor its version, so this stays permissive on purpose.
    """
    for src in ((obj.get("message") or {}), obj):
        content = src.get("content")
        if content is None:
            continue
        if isinstance(content, str):
            yield {"type": "text", "text": content}
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    yield block
                elif isinstance(block, str):
                    yield {"type": "text", "text": block}
        return


def _result_text(block):
    """Flatten a tool_result block's content to plain text."""
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text") or "")
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return ""


def parse_transcript(lines, session_id=None):
    """Extract human corrections from a Claude Code transcript.

    Returns a list of {"timestamp", "kind", "text"} where kind is one of
    "reply", "plan-rejected", "plan-approved". Consecutive exact duplicates are
    collapsed (a resumed session can replay the tail of its own transcript).
    """
    out = []
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except (ValueError, TypeError):
            continue  # a partially-flushed or non-JSON line must never raise
        if not isinstance(obj, dict):
            continue
        if session_id is not None and obj.get("sessionId") != session_id:
            continue
        timestamp = obj.get("timestamp") or ""
        is_user = obj.get("type") == "user"
        for block in _blocks(obj):
            btype = block.get("type")
            if btype == "tool_result":
                text = _result_text(block)
                match = GATE_REJECT.search(text)
                if match:
                    out.append(
                        {
                            "timestamp": timestamp,
                            "kind": "plan-rejected",
                            "text": match.group(1).strip(),
                        }
                    )
                match = GATE_APPROVE.search(text)
                if match:
                    out.append(
                        {
                            "timestamp": timestamp,
                            "kind": "plan-approved",
                            "text": match.group(1),
                        }
                    )
            elif btype == "text" and is_user:
                text = (block.get("text") or "").strip()
                if not text:
                    continue
                if text.startswith("/"):
                    continue  # slash command, not a correction
                if text.startswith("<"):
                    continue  # system-reminder / attachment envelope
                out.append({"timestamp": timestamp, "kind": "reply", "text": text})

    deduped = []
    for entry in out:
        if deduped and (deduped[-1]["kind"], deduped[-1]["text"]) == (
            entry["kind"],
            entry["text"],
        ):
            continue
        deduped.append(entry)
    return deduped


def derive_outcome(labels):
    """Map a ticket's current labels to a single run outcome."""
    if "agent:blocked" in labels:
        return "blocked"
    for label in reversed(STAGE_LABELS):
        if label in labels:
            return label.split(":", 1)[1]
    return "unknown"


def existing_started(path):
    """Read `started:` out of an existing record so re-syncs don't reset it.

    Only the frontmatter block is scanned. The fence is located with a line
    counter rather than fh.tell(): mixing tell() with `for line in fh` raises
    OSError ("telling position disabled by next() call") in Python 3.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            for index, line in enumerate(fh):
                if line.startswith("started:"):
                    return line.split(":", 1)[1].strip()
                if index > 0 and line.startswith("---"):
                    break
    except OSError:
        return None
    return None


def _labels_of(issue):
    return [n["name"] for n in ((issue.get("labels") or {}).get("nodes") or [])]


def build_record(meta, evidence, issue, corrections):
    """Render one run record. Deterministic: same inputs → identical bytes."""
    labels = _labels_of(issue)
    rejections = [c for c in corrections if c["kind"] == "plan-rejected"]
    comments = (issue.get("comments") or {}).get("nodes") or []

    lines = [
        "---",
        f"ticket: {meta['ticket']}",
        f"seat: {meta['seat']}",
        f"repo: {meta['repo']}",
        f"branch: {meta['branch']}",
        f"started: {meta['started']}",
        f"ended: {meta['ended']}",
        f"outcome: {derive_outcome(labels)}",
        f"preemptions: {meta['preemptions']}",
        f"plan_rounds: {1 + len(rejections)}",
        f"pr: {meta.get('pr') or ''}",
        "---",
        "",
        f"# {meta['ticket']} — {issue.get('title') or '(no title)'}",
        "",
        f"{issue.get('url') or ''}",
        "",
        "## Timeline",
        "",
        f"- state: {((issue.get('state') or {}).get('name')) or '-'}",
        f"- labels: {', '.join(labels) or '-'}",
    ]
    for comment in comments:
        who = (comment.get("user") or {}).get("name") or "?"
        lines.append(f"- {comment.get('createdAt', '')} — comment by {who}")
    lines += ["", "## What I tested", ""]
    lines.append(evidence.strip() if evidence.strip() else "(no evidence recorded)")
    lines += ["", "## Human corrections", ""]
    if corrections:
        for c in corrections:
            lines.append(f"- **{c['kind']}** · {c['timestamp']}")
            lines.append(f"  > {c['text']}")
    else:
        lines.append("(none)")
    lines += ["", "## Failures", ""]
    failures = []
    if int(meta["preemptions"]) > 0:
        failures.append(f"- preempted {meta['preemptions']} time(s)")
    for c in rejections:
        failures.append(f"- plan rejected: {c['text']}")
    if derive_outcome(labels) == "blocked":
        failures.append(f"- ended blocked (labels: {', '.join(labels)})")
    lines += failures or ["(none)"]
    lines += ["", "## Linear comments", ""]
    if comments:
        for comment in comments:
            who = (comment.get("user") or {}).get("name") or "?"
            lines.append(f"### {who} · {comment.get('createdAt', '')}")
            lines.append("")
            lines.append(comment.get("body") or "")
            lines.append("")
    else:
        lines.append("(none)")
    return "\n".join(lines).rstrip("\n") + "\n"


def _without_ended(record):
    return "\n".join(
        line for line in record.splitlines() if not line.startswith("ended:")
    )


def unchanged_except_ended(new_record, path):
    """True when `path` already holds this record apart from its `ended:` stamp.

    The harvester re-runs every few minutes for the whole life of a run, and
    `ended` is wall-clock. Without this check each cycle would rewrite the file,
    commit, and push — filling the vault's history with no-op churn. Skipping the
    write makes `ended` mean "when this run last actually changed", which is the
    more useful reading anyway.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            old = fh.read()
    except OSError:
        return False
    return _without_ended(old) == _without_ended(new_record)


def main(argv=None):
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Write one agent-run record.")
    parser.add_argument("--current", required=True, help="path to current.json")
    parser.add_argument("--issue", required=True, help="path to linear.py get --json output")
    parser.add_argument("--out", required=True, help="record path to write")
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--transcript", default=None)
    parser.add_argument("--seat", default=os.environ.get("CODER_WORKSPACE_NAME", "unknown"))
    parser.add_argument("--branch", default="-")
    parser.add_argument("--preemptions", type=int, default=0)
    parser.add_argument("--pr", default="")
    parser.add_argument("--ended", default="")
    args = parser.parse_args(argv)

    def read(path):
        if not path:
            return ""
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                return fh.read()
        except OSError:
            return ""

    try:
        current = json.loads(read(args.current) or "{}")
        issue = json.loads(read(args.issue) or "{}")
    except ValueError:
        return 2
    ticket = current.get("ticket") or issue.get("identifier")
    if not ticket:
        return 2

    corrections = []
    if args.transcript:
        try:
            with open(args.transcript, encoding="utf-8", errors="replace") as fh:
                corrections = parse_transcript(fh.readlines(), current.get("session_id"))
        except OSError:
            corrections = []

    ended = args.ended or _now()
    meta = {
        "ticket": ticket,
        "seat": args.seat,
        "repo": current.get("repo") or "-",
        "branch": args.branch,
        "started": existing_started(args.out) or ended,
        "ended": ended,
        "preemptions": args.preemptions,
        "pr": args.pr,
    }
    record = build_record(meta, read(args.evidence), issue, corrections)
    if unchanged_except_ended(record, args.out):
        return 0
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(record)
    return 0


def _now():
    import datetime

    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    import sys

    sys.exit(main())
