# Portable entry point for interactive shells. Sourced from both ~/.bashrc and
# ~/.zshrc by the managed block install.sh writes, which is also what sets
# ZAMP_DOTFILES_DIR. Nothing here may use BASH_SOURCE: zsh does not define it,
# so deriving the repo path from the script's own location silently resolves to
# the wrong directory under zsh.

# Interactive shells only. $- carries the `i` flag in both bash and zsh; PS1 is
# not reliable across shells for this.
case $- in
  *i*) ;;
  *) return 0 ;;
esac

if [ -z "${ZAMP_DOTFILES_DIR:-}" ]; then
  echo "dotfiles: ZAMP_DOTFILES_DIR unset, skipping shell init" >&2
  return 0
fi

[ -f "$ZAMP_DOTFILES_DIR/shell/common.sh" ] && . "$ZAMP_DOTFILES_DIR/shell/common.sh"

if [ -n "${ZSH_VERSION:-}" ]; then
  [ -f "$ZAMP_DOTFILES_DIR/shell/zsh.sh" ] && . "$ZAMP_DOTFILES_DIR/shell/zsh.sh"
elif [ -n "${BASH_VERSION:-}" ]; then
  [ -f "$ZAMP_DOTFILES_DIR/shell/bash.sh" ] && . "$ZAMP_DOTFILES_DIR/shell/bash.sh"
fi

# Banner last, so it prints below any output from the sourcing above.
[ -f "$ZAMP_DOTFILES_DIR/shell/fastfetch-init.sh" ] && . "$ZAMP_DOTFILES_DIR/shell/fastfetch-init.sh"

# Genuinely last: on a real SSH login this execs tmux and replaces the shell,
# so nothing after it would run. Everything above is still applied, because the
# shell tmux starts sources this file again from scratch.
[ -f "$ZAMP_DOTFILES_DIR/shell/tmux-init.sh" ] && . "$ZAMP_DOTFILES_DIR/shell/tmux-init.sh"
