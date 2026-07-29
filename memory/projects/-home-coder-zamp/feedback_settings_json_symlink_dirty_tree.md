---
name: feedback-settings-json-symlink-dirty-tree
description: ~/.claude/settings.json is a symlink into the dotfiles repo — any JSON merge write leaves that repo locally dirty and silently blocks the NEXT git pull on it
metadata:
  node_type: memory
  type: feedback
  originSessionId: 80ce98cd-34a3-40db-b753-81baaabc3418
  modified: 2026-07-29T08:11:37.575Z
---

`~/.claude/settings.json` is a symlink to `~/.config/coderv2/dotfiles/config/settings.json` (both on
HQ and every seat). Any script that merges JSON into it (the ECC install block, the memory-hooks
install block, `install-impl-gate.py`, or ad-hoc drift like Claude Code itself setting
`agentPushNotifEnabled`) writes straight through the symlink into a **tracked file inside the dotfiles
git working tree** — leaving that repo locally dirty. The next `git -C
~/.config/coderv2/dotfiles pull --ff-only` then fails with "Your local changes to
config/settings.json would be overwritten by merge" and aborts — silently, if the caller wraps it in
`|| true` (as `seatctl.py`'s `BOOTSTRAP` does for robustness), so a bootstrap can report full success
(`gh: token wired`, `auth: ok`) while the new file it was supposed to pull down (e.g.
`memory-hooks.sh`) simply never lands.

**Why:** discovered rolling out `memory-hooks.sh` to all 5 seats — `seatctl bootstrap` reported clean
success on every seat, but `memory-hooks.sh` was only actually present on seat-5. Seats 1–4 had
pre-existing drift in their tracked `config/settings.json` (the same `agentPushNotifEnabled` drift
found on HQ), which blocked the newly-added `git pull` line before it ever reached the file.

**How to apply:** any `BOOTSTRAP`/setup script that both (a) pulls the dotfiles repo and (b) writes to
`~/.claude/settings.json` must discard local drift on that one tracked file *before* pulling —
`git -C ~/.config/coderv2/dotfiles checkout -- config/settings.json 2>/dev/null || true` — since the
JSON-merge step that follows rewrites it fully anyway. Never assume `|| true`-guarded git commands in
a bootstrap script actually succeeded just because the overall script exit code was clean; when a
bootstrap is supposed to have delivered a new file, verify the file is actually present on at least
one representative seat before declaring the rollout done, don't just read the script's stdout.
Related: [[feedback_memory_sync_is_manual_twostep]].
