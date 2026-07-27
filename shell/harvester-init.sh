# Seat self-heal for the agent-memory harvester.
#
# install.sh starts the harvester at boot, but on a box's FIRST provisioning the
# dotfiles can run BEFORE provision-box.sh writes ~/.agent-pool-seat -- and then the
# boot-time start is skipped entirely. Observed live: the harvester came up on 3 of 5
# freshly-provisioned seats. Any interactive login now repairs it, so a seat can't sit
# there silently recording nothing until its next restart.
#
# Cost when it's already healthy: one `tmux has-session` (a few ms). No `set -e` here;
# this is sourced into the user's interactive shell and must never abort it.

[ -f "$HOME/.agent-pool-seat" ] || return 0
command -v tmux >/dev/null 2>&1 || return 0
tmux has-session -t agent-memory 2>/dev/null && return 0

_am_harvest="$ZAMP_DOTFILES_DIR/scripts/agent-memory/harvest.sh"
if [ -f "$_am_harvest" ]; then
  setsid tmux new-session -d -s agent-memory \
    "bash -lc 'bash $_am_harvest --daemon'" >/dev/null 2>&1 \
    && echo "dotfiles: started agent-memory harvester"
fi
unset _am_harvest
