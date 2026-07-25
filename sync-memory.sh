#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MEMORY_STORE="$REPO_DIR/memory/projects"
CLAUDE_PROJECTS="$HOME/.claude/projects"

# Default is NO-CLOBBER: a file already present in the workspace wins over the
# committed copy. This matters because install.sh runs pull on every workspace
# START, not just at creation -- Coder's dotfiles module sets run_on_start=true
# -- so an unconditional copy would silently revert memory that was edited in
# the workspace but not yet pushed. Fresh workspaces still get everything,
# since nothing is there to protect.
#
# Use `pull --force` to deliberately overwrite local memory from the repo.
# Copies only files absent from the destination. Written as an explicit per-file
# test rather than `cp -n` because the two cp implementations disagree on exit
# status: BSD cp (macOS) exits non-zero when it skips a file, GNU cp (Linux)
# exits 0. Depending on that made the script report a false "pull failed".
copy_absent_only() {
  local src_dir="$1" dst_dir="$2" rel
  while IFS= read -r -d '' rel; do
    rel="${rel#./}"
    [ -e "$dst_dir/$rel" ] && continue
    mkdir -p "$dst_dir/$(dirname "$rel")"
    cp -a "$src_dir/$rel" "$dst_dir/$rel"
  done < <(cd "$src_dir" && find . -type f -print0)
}

pull() {
  local force=0 mode="no-clobber; local edits win"
  if [ "${1:-}" = "--force" ]; then
    force=1
    mode="FORCE; repo overwrites local"
  fi

  [ -d "$MEMORY_STORE" ] || { echo "no memory store yet"; return 0; }
  echo "pulling memory [$mode]"
  for slug_dir in "$MEMORY_STORE"/*/; do
    [ -d "$slug_dir" ] || continue
    slug="$(basename "$slug_dir")"
    target="$CLAUDE_PROJECTS/$slug/memory"
    mkdir -p "$target"
    if [ "$force" -eq 1 ]; then
      cp -a "$slug_dir." "$target/"
    else
      copy_absent_only "${slug_dir%/}" "$target"
    fi
    echo "  pulled memory for $slug"
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
  pull)
    shift
    pull "$@"
    ;;
  push) push ;;
  *)
    echo "usage: $0 pull [--force] | push"
    echo "  pull            restore memory, never overwriting local files (default)"
    echo "  pull --force    restore memory, overwriting local files from the repo"
    echo "  push            stage, commit and push memory that changed locally"
    exit 1
    ;;
esac
