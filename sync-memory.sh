#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MEMORY_STORE="$REPO_DIR/memory/projects"
CLAUDE_PROJECTS="$HOME/.claude/projects"

pull() {
  [ -d "$MEMORY_STORE" ] || { echo "no memory store yet"; return 0; }
  for slug_dir in "$MEMORY_STORE"/*/; do
    [ -d "$slug_dir" ] || continue
    slug="$(basename "$slug_dir")"
    target="$CLAUDE_PROJECTS/$slug/memory"
    mkdir -p "$target"
    cp -a "$slug_dir." "$target/"
    echo "pulled memory for $slug"
  done
}

push() {
  mkdir -p "$MEMORY_STORE"
  shopt -s nullglob
  for mem_dir in "$CLAUDE_PROJECTS"/*/memory; do
    [ -d "$mem_dir" ] || continue
    slug="$(basename "$(dirname "$mem_dir")")"
    mkdir -p "$MEMORY_STORE/$slug"
    cp -a "$mem_dir/." "$MEMORY_STORE/$slug/"
    echo "staged memory for $slug"
  done
  cd "$REPO_DIR"
  git add memory
  if git diff --cached --quiet; then
    echo "nothing new to commit"
  else
    git commit -m "sync memory from $(hostname 2>/dev/null || echo unknown)"
    git push
  fi
}

case "${1:-}" in
  pull) pull ;;
  push) push ;;
  *) echo "usage: $0 [pull|push]"; exit 1 ;;
esac
