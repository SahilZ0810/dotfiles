---
description: Distil agent-pool run records into durable lessons (HQ, daily)
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# retro — turn run records into lessons

You run on HQ, once a day. You read the pool's run records and maintain two curated
notes in the Obsidian vault. You are the **only** writer of those two files.

## Inputs

- Resolve the vault first, and use `$VAULT` everywhere below:
  ```bash
  DOTFILES="$(ls -d ~/dotfiles ~/Workspace/dotfiles 2>/dev/null | head -1)"
  . "$DOTFILES/scripts/agent-memory/common.sh"
  VAULT="$(vault_root)" || { echo "no vault — check ~/.config/obsidian-vault-token"; exit 0; }
  ```
- Run records: `$VAULT/reports/agent-runs/*.md`
- Watermark: `~/agent-pool/retro-watermark` (ISO-8601). Process records modified after it.
  If absent, process everything.
- PR review findings: for each record with a non-empty `pr:` field, read the review threads:
  `export GH_TOKEN="$(bash ~/zamp/zamp_dev_setup/skills/_shared/gh-token.sh)"; export GITHUB_TOKEN="$GH_TOKEN"`
  then `gh pr view <url> --json reviews,comments` and `gh api repos/<owner>/<repo>/pulls/<N>/comments`.
  Mint the token first — a stale ambient `GH_TOKEN` shadows gh's stored creds and 401s.

## What to produce

### `$VAULT/wiki/agent-lessons.md`

Actionable rules about the **code and the repos**. One `### ` entry each, in exactly this
shape — `lessons_block.py` parses it, and a different shape silently empties the block that
reaches every seat:

```
### pantheon: new endpoint DTOs go in `api/dto/`, not `schemas/`
- scope: pantheon
- evidence: PRO-2277, PRO-2340 (2 hits) · last 2026-07-23
- cost: 1 review cycle each
```

Rules:
- **Promote only at ≥2 independent tickets.** One occurrence is an anecdote. Promoting
  anecdotes is how a wrong rule enters every future run's context.
- Each entry must cite its evidence tickets. No citation, no entry.
- Be specific and actionable. "Follow conventions" is not a lesson; "new endpoint DTOs go in
  `api/dto/`" is.
- Merge duplicates and bump the hit count rather than appending a near-identical entry.
- Order by hit count descending, then most-recent first.

### `$VAULT/wiki/how-sahil-works.md`

The human's patterns, mined from `## Human corrections` in the records — especially
`plan-rejected` entries, which contain his verbatim words about plans he refused. Cover:
what he rejects in plans, what he always asks for, how he wants scope cut. Short bullets.

## Escalation — do not just add another lesson

If a lesson's hit count reaches **≥3**, injecting it a fourth time is not working. Move it
to an `## Escalations` section at the top of `agent-lessons.md` with a concrete proposal —
a lint rule, a repo `CLAUDE.md` change, or a codebase fix — and say why the reminder failed.
Escalated items still count as lessons but must carry the proposal.

## Finish

1. Write both notes.
2. Update the watermark: `date -u +%Y-%m-%dT%H:%M:%SZ > ~/agent-pool/retro-watermark`
3. Commit and push the vault:
   `git -C "$VAULT" add wiki && git -C "$VAULT" commit -m "retro: distil lessons" && git -C "$VAULT" pull --rebase && git -C "$VAULT" push`
4. Post a one-paragraph digest of what changed: new lessons, escalations, and any seat that
   reported **memory: OFF**.

## Never

- Never invent a lesson that no record supports.
- Never exceed the promotion threshold rules to make the note look fuller.
- Never write to `reports/agent-runs/` — those are the seats' files.
