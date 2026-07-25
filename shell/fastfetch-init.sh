# Sourced from shell/init.sh, which has already confirmed an interactive shell
# and provided ZAMP_DOTFILES_DIR. Must not use BASH_SOURCE (unset in zsh).

if command -v fastfetch >/dev/null 2>&1; then
  fastfetch -c "$ZAMP_DOTFILES_DIR/shell/fastfetch-config.jsonc"
fi
