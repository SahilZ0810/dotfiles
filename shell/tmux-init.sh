# Auto-attach to tmux, for real interactive SSH logins only.
# Sourced last from shell/init.sh. POSIX syntax: runs under bash and zsh.
#
# Why this exists: `coder ssh` has no reconnecting PTY, so a dropped connection
# kills the foreground process -- including a long-running Claude Code session.
# tmux is what makes that survivable. Coder's *web* terminal already reconnects
# server-side and is not SSH, so it is deliberately left alone.
#
# The guards matter more than the feature. Wrapping an IDE terminal, a CI step,
# an agent session, or the dotfiles install itself would range from merely
# irritating to failing the workspace build.

_dotfiles_should_tmux() {
  command -v tmux >/dev/null 2>&1            || return 1
  [ -z "${TMUX:-}" ]                         || return 1  # already inside tmux
  [ -t 0 ]                                   || return 1  # no tty: pipe, script, build
  [ -z "${CI:-}" ]                           || return 1
  [ -z "${CLAUDECODE:-}" ]                   || return 1  # never wrap an agent session
  [ -z "${INSIDE_EMACS:-}" ]                 || return 1
  [ -z "${VSCODE_SHELL_INTEGRATION:-}" ]     || return 1
  [ -z "${ZED_TERM:-}" ]                     || return 1
  [ "${TERM_PROGRAM:-}" != "vscode" ]        || return 1
  [ "${TERMINAL_EMULATOR:-}" != "JetBrains-JediTerm" ] || return 1
  [ "${TERM:-}" != "dumb" ]                  || return 1

  # Only real SSH logins get wrapped.
  [ -n "${SSH_TTY:-}${SSH_CONNECTION:-}" ]   || return 1
  return 0
}

if _dotfiles_should_tmux; then
  unset -f _dotfiles_should_tmux
  # -A is create-or-attach, so reconnecting after a drop rejoins the same
  # session instead of stacking up a new one each time.
  exec tmux new-session -A -s main
fi

unset -f _dotfiles_should_tmux
