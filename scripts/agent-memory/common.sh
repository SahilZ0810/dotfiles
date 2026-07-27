#!/usr/bin/env bash
# Shared helpers for the agent-memory layer. SOURCE this file; do not execute it.
# No `set -e` anywhere in this layer: a memory problem must never fail a Coder
# workspace build (Coder's dotfiles module treats a non-zero exit as build failure).

# vault_root — print the Obsidian vault path, exit 1 if there isn't one.
# Requires .git: install.sh clones the vault, and a bare directory without .git
# means the clone failed (usually a missing PAT) — treating that as "found" would
# make the harvester write records that can never be pushed.
vault_root() {
  local d
  for d in "$HOME/obsidian-vault" "$HOME/Documents/Obsidian Vault"; do
    if [ -d "$d/.git" ]; then
      printf '%s' "$d"
      return 0
    fi
  done
  return 1
}
