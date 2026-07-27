#!/usr/bin/env python3
"""Render the capped lessons block that install.sh injects into ~/.claude/CLAUDE.md.

The cap is the whole design constraint: this text is loaded into every context
window on every turn, so an uncapped lessons file is a lessons file nobody reads.
Full detail stays in the vault and the agent can open it on demand.
"""

VAULT_HINT = (
    "Full detail: `<vault>/wiki/agent-lessons.md`, `<vault>/wiki/how-sahil-works.md`, "
    "run records in `<vault>/reports/agent-runs/`."
)


def _entries(lessons_md):
    """Split a lessons note into whole `### …` entries, dropping any preamble."""
    entries, current = [], None
    for line in lessons_md.splitlines():
        if line.startswith("### "):
            if current:
                entries.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current:
        entries.append(current)
    return [[l for l in e if l.strip()] for e in entries]


def _profile_lines(profile_md):
    return [l for l in profile_md.splitlines() if l.strip()]


def build_block(lessons_md, profile_md, max_lines=60):
    """Build the block. Profile first (always applies), then whole lessons."""
    profile = _profile_lines(profile_md)
    entries = _entries(lessons_md)
    if not profile and not entries:
        return ""

    out = list(profile)
    footer_cost = 2  # blank line + the hint/truncation line
    dropped = 0
    for entry in entries:
        if len(out) + 1 + len(entry) + footer_cost > max_lines:
            dropped += 1
            continue
        out.append("")
        out.extend(entry)

    out.append("")
    if dropped:
        out.append(f"_{dropped} more lesson(s) truncated._ {VAULT_HINT}")
    else:
        out.append(f"_{VAULT_HINT}_")

    # Guard the cap even if the profile alone overshoots it.
    if len(out) > max_lines:
        out = out[: max_lines - 1] + [f"_truncated._ {VAULT_HINT}"]
    return "\n".join(out).rstrip("\n") + "\n"


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Print the CLAUDE.md lessons block.")
    parser.add_argument("--lessons", default=None)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--max-lines", type=int, default=60)
    args = parser.parse_args(argv)

    def read(path):
        if not path:
            return ""
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                return fh.read()
        except OSError:
            return ""

    block = build_block(read(args.lessons), read(args.profile), args.max_lines)
    if block:
        print(block, end="")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
