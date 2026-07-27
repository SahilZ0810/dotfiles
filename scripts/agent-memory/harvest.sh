#!/usr/bin/env bash
# One harvest cycle (or a daemon loop) for an agent-pool seat.
#
# Syncs this seat's live run into the Obsidian vault every few minutes, so the
# record already exists by the time `seatctl reset` runs its
# `rm -f ~/agent-pool/evidence-*.md`. That inversion is the whole point: we never
# have to patch the shared zamp_dev_setup repo to get durable memory.
#
# NO `set -e`: every failure path exits 0. Coder treats a non-zero dotfiles
# script as a failed workspace build.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/common.sh"

POOL_DIR="${AGENT_MEMORY_POOL_DIR:-$HOME/agent-pool}"
LINEAR="${AGENT_MEMORY_LINEAR:-$HOME/zamp/zamp_dev_setup/skills/_shared/linear.py}"
INTERVAL="${AGENT_MEMORY_INTERVAL:-180}"

now_utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }

cycle() {
  local vault current ticket session record repo_dir branch preemptions pr issue_json rc

  vault="${AGENT_MEMORY_VAULT:-$(vault_root)}" || vault=""
  if [ -z "$vault" ] || [ ! -d "$vault/.git" ]; then
    echo "harvest: no vault (missing PAT at ~/.config/obsidian-vault-token?) — skipping"
    return 0
  fi

  current="$POOL_DIR/current.json"
  if [ ! -f "$current" ]; then
    echo "harvest: no current.json — seat is idle, nothing to record"
    return 0
  fi

  ticket="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("ticket") or "")' "$current" 2>/dev/null)"
  if [ -z "$ticket" ]; then
    echo "harvest: current.json has no ticket — skipping"
    return 0
  fi

  issue_json="$(mktemp)"
  if ! python3 "$LINEAR" get "$ticket" --json >"$issue_json" 2>/dev/null; then
    echo "harvest: linear.py get $ticket failed — skipping this cycle"
    rm -f "$issue_json"
    return 0
  fi

  pr="$(python3 "$LINEAR" pr "$ticket" 2>/dev/null | head -1)"

  case "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("repo") or "")' "$current" 2>/dev/null)" in
    frontend) repo_dir="$HOME/zamp/services/application-platform-frontend" ;;
    pantheon) repo_dir="$HOME/zamp/services/pantheon" ;;
    *)        repo_dir="" ;;
  esac
  branch="-"
  if [ -n "$repo_dir" ] && [ -d "$repo_dir/.git" ]; then
    branch="$(git -C "$repo_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo -)"
  fi

  preemptions=0
  [ -f "$POOL_DIR/preemptions-$ticket" ] && \
    preemptions="$(tr -dc '0-9' <"$POOL_DIR/preemptions-$ticket" 2>/dev/null || echo 0)"
  [ -z "$preemptions" ] && preemptions=0

  # Newest transcript for the seat's project dir; harvest.py filters by session_id.
  session="$(ls -t "$HOME/.claude/projects"/*/*.jsonl 2>/dev/null | head -1)"

  record="$vault/reports/agent-runs/$ticket.md"
  python3 "$HERE/harvest.py" \
    --current "$current" \
    --issue "$issue_json" \
    --evidence "$POOL_DIR/evidence-$ticket.md" \
    ${session:+--transcript "$session"} \
    --seat "${CODER_WORKSPACE_NAME:-unknown}" \
    --branch "$branch" \
    --preemptions "$preemptions" \
    --pr "$pr" \
    --out "$record"
  rc=$?
  rm -f "$issue_json"
  if [ "$rc" -ne 0 ]; then
    echo "harvest: harvest.py exited $rc — skipping push"
    return 0
  fi

  push_record "$vault" "$ticket" && printf '%s\n' "$(now_utc)" >"$POOL_DIR/memory-heartbeat"
  return 0
}

# push_record — commit + push just this ticket's record. Retries with rebase; never
# forces. One writer per file, so a rebase can't clobber another seat's work.
push_record() {
  local vault="$1" ticket="$2" rel="reports/agent-runs/$2.md" attempt
  git -C "$vault" add "$rel" 2>/dev/null || return 1
  if git -C "$vault" diff --cached --quiet -- "$rel"; then
    return 0   # nothing changed this cycle — idempotent, still healthy
  fi
  git -C "$vault" commit -q -m "agent-memory: $ticket run record" -- "$rel" || return 1
  for attempt in 1 2 3; do
    git -C "$vault" pull --rebase -q 2>/dev/null
    if git -C "$vault" push -q 2>/dev/null; then
      return 0
    fi
    sleep 2
  done
  echo "harvest: push failed after 3 attempts — record kept locally, will retry next cycle"
  return 1
}

case "${1:---once}" in
  --once)
    cycle
    ;;
  --daemon)
    echo "harvest: daemon up, interval ${INTERVAL}s"
    while true; do
      cycle
      sleep "$INTERVAL"
    done
    ;;
  *)
    echo "usage: harvest.sh [--once|--daemon]"
    exit 0
    ;;
esac
exit 0
