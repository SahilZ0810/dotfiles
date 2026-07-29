#!/usr/bin/env bash
# Claude Code SessionStart/Stop hooks that keep the two memory layers (the
# Claude Code auto-memory dotfiles sync, and the obsidian vault) in sync
# without turning into a hard gate. Always exits 0 -- a memory-sync hiccup
# must never block a session from starting or a turn from finishing.
set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_DIR="$HOME/obsidian-vault"

log() { printf '[memory-hooks] %s\n' "$1"; }

pre() {
  git -C "$REPO_DIR" pull --ff-only --quiet 2>/dev/null \
    && log "dotfiles pulled" \
    || log "dotfiles pull skipped/failed (non-fatal)"
  bash "$REPO_DIR/sync-memory.sh" pull 2>&1 | sed 's/^/[memory-hooks] /'
  if [ -d "$VAULT_DIR/.git" ]; then
    git -C "$VAULT_DIR" pull --ff-only --quiet 2>/dev/null \
      && log "obsidian vault pulled" \
      || log "obsidian vault pull skipped/failed (non-fatal)"
  fi
  exit 0
}

post() {
  bash "$REPO_DIR/sync-memory.sh" push 2>&1 | sed 's/^/[memory-hooks] /'
  exit 0
}

case "${1:-}" in
  pre) pre ;;
  post) post ;;
  *) log "usage: $0 pre|post" ;;
esac
exit 0
