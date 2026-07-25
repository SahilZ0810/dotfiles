# Settings shared by bash and zsh. POSIX syntax only.

# install.sh drops binaries into these (fastfetch, fzf). On Debian-family
# images ~/.local/bin is added to PATH by ~/.profile, which only login shells
# read, and zsh never reads it at all -- so without this the banner and the
# fzf key bindings both silently no-op.
for _dir in "$HOME/.local/bin" "$HOME/.fzf/bin"; do
  case ":$PATH:" in
    *":$_dir:"*) ;;
    *) [ -d "$_dir" ] && PATH="$_dir:$PATH" ;;
  esac
done
unset _dir
export PATH

export EDITOR="${EDITOR:-vim}"
export VISUAL="$EDITOR"

# macOS ships a `less` too old for bat's pager integration, which shows up as
# garbled output rather than a clean error. $OSTYPE is set by both bash and zsh,
# so this costs no fork (unlike calling uname on every shell start).
case "${OSTYPE:-}" in
  darwin*) export BAT_PAGER="builtin" ;;
esac

# Personal aliases and exports go here -- they apply to both shells.
