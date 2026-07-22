#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

link() {
  local src="$1" dest="$2"
  if [ -e "$dest" ] && [ ! -L "$dest" ]; then
    mv "$dest" "${dest}.bak.$(date +%s)"
    echo "backed up existing $dest"
  fi
  ln -sfn "$src" "$dest"
  echo "linked $dest -> $src"
}

mkdir -p "$CLAUDE_DIR"
link "$REPO_DIR/config/settings.json" "$CLAUDE_DIR/settings.json"

if [ -n "$(ls -A "$REPO_DIR/config/commands" 2>/dev/null | grep -v .gitkeep)" ]; then
  link "$REPO_DIR/config/commands" "$CLAUDE_DIR/commands"
fi

install_fastfetch() {
  if command -v fastfetch >/dev/null 2>&1; then
    echo "fastfetch already installed"
    return
  fi

  local arch tarball_url tmp_dir
  arch="$(uname -m)"
  if [ "$arch" != "x86_64" ]; then
    echo "skipping fastfetch install: unsupported arch $arch"
    return
  fi

  tarball_url=$(curl -sSL --max-time 10 https://api.github.com/repos/fastfetch-cli/fastfetch/releases/latest \
    | grep -oE '"browser_download_url": *"[^"]*linux-amd64\.tar\.gz"' | head -1 | grep -oE 'https://[^"]*')
  [ -n "$tarball_url" ] || { echo "could not resolve fastfetch download url, skipping"; return; }

  tmp_dir="$(mktemp -d)"
  curl -sSL "$tarball_url" -o "$tmp_dir/fastfetch.tar.gz"
  tar -xzf "$tmp_dir/fastfetch.tar.gz" -C "$tmp_dir"
  mkdir -p "$HOME/.local/bin"
  cp "$tmp_dir"/fastfetch-linux-amd64/usr/bin/fastfetch "$HOME/.local/bin/fastfetch"
  chmod +x "$HOME/.local/bin/fastfetch"
  rm -rf "$tmp_dir"
  echo "installed fastfetch to $HOME/.local/bin/fastfetch"
}

install_fastfetch

BASHRC="$HOME/.bashrc"
if [ -f "$BASHRC" ] && ! grep -qF "$REPO_DIR/shell/fastfetch-init.sh" "$BASHRC"; then
  {
    echo ""
    echo "# dotfiles: fastfetch banner"
    echo "[ -f \"$REPO_DIR/shell/fastfetch-init.sh\" ] && source \"$REPO_DIR/shell/fastfetch-init.sh\""
  } >> "$BASHRC"
  echo "wired fastfetch banner into $BASHRC"
fi

echo
echo "Done. Run ./sync-memory.sh pull to restore personal memory."
