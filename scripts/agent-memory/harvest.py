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
