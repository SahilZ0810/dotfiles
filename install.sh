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

# Deliver the Obsidian-vault memory pointer to ~/.claude/CLAUDE.md. Deliberately
# NOT a symlink: in a Coder workspace the agent PREPENDS its own prompt to this
# file, and a symlink would push that write back into this repo -- dirtying it
# and aborting every dotfiles `git pull` (Coder re-runs install on each start).
# Instead we keep our pointer in a marked block inside a REAL file, so our
# content and Coder's prompt coexist and the repo stays clean. Idempotent:
# re-running strips the old block and re-appends the current one.
CM_BEGIN="# >>> obsidian vault pointer >>>"
CM_END="# <<< obsidian vault pointer <<<"
claude_md="$CLAUDE_DIR/CLAUDE.md"
[ -L "$claude_md" ] && rm -f "$claude_md"   # migrate away from the old symlink
[ -e "$claude_md" ] || : >"$claude_md"
cm_tmp="$(mktemp)"
sed "/^${CM_BEGIN}\$/,/^${CM_END}\$/d" "$claude_md" >"$cm_tmp"
{ cat "$cm_tmp"; echo "$CM_BEGIN"; cat "$REPO_DIR/config/CLAUDE.md"; echo "$CM_END"; } >"$claude_md"
rm -f "$cm_tmp"
echo "wired obsidian vault pointer into $claude_md"

if [ -n "$(ls -A "$REPO_DIR/config/commands" 2>/dev/null | grep -v .gitkeep)" ]; then
  link "$REPO_DIR/config/commands" "$CLAUDE_DIR/commands"
fi

# ~/.tmux.conf rather than ~/.config/tmux/tmux.conf: the legacy path is honoured
# by every tmux version, including whatever an older base image ships.
link "$REPO_DIR/config/tmux.conf" "$HOME/.tmux.conf"

BIN_DIR="$HOME/.local/bin"

# Every version below is pinned on purpose. The previous fastfetch step resolved
# "latest" through the GitHub releases API on each run, which is a network
# round-trip and an unauthenticated rate-limit surface on EVERY workspace start
# -- Coder's dotfiles module sets run_on_start = true, so this script is not a
# create-time-only hook. Pinned URLs also make the install reproducible.
RIPGREP_VERSION=15.2.0
FD_VERSION=10.4.2
DELTA_VERSION=0.19.2
JQ_VERSION=1.8.2
LAZYGIT_VERSION=0.63.1
BAT_VERSION=0.26.1
TMUX_VERSION=3.7b
FASTFETCH_VERSION=2.66.0

# fetch_tool <binary-name> <url> [bare]
#   Downloads and installs a single binary into $BIN_DIR. Without `bare` the URL
#   is treated as a .tar.gz and the binary is located inside it by name, which
#   covers both flat archives (lazygit, tmux) and wrapper-dir ones (ripgrep, fd,
#   delta, bat, fastfetch) without a per-tool path.
#   Every failure path returns 0: a missing CLI tool must never fail the build.
fetch_tool() {
  local name="$1" url="$2" bare="${3:-}" tmp found

  # Test the file, not PATH: $BIN_DIR is not on PATH inside this script, so a
  # PATH-only check would re-download every tool on every workspace start.
  if [ -x "$BIN_DIR/$name" ]; then
    echo "  $name already installed"
    return 0
  fi

  tmp="$(mktemp -d)"
  if ! curl -fsSL --max-time 120 "$url" -o "$tmp/dl"; then
    echo "  could not download $name, skipping"
    rm -rf "$tmp"
    return 0
  fi

  if [ "$bare" = "bare" ]; then
    mv "$tmp/dl" "$BIN_DIR/$name"
  else
    if ! tar -xzf "$tmp/dl" -C "$tmp" 2>/dev/null; then
      echo "  could not extract $name, skipping"
      rm -rf "$tmp"
      return 0
    fi
    found="$(find "$tmp" -type f -name "$name" 2>/dev/null | head -1)"
    if [ -z "$found" ]; then
      echo "  $name not found inside archive, skipping"
      rm -rf "$tmp"
      return 0
    fi
    mv "$found" "$BIN_DIR/$name"
  fi

  chmod +x "$BIN_DIR/$name"
  rm -rf "$tmp"
  echo "  installed $name"
}

install_cli_tools() {
  local gh=https://github.com
  # Only the two targets whose release assets I actually verified. Anything else
  # skips rather than 404-ing its way through seven downloads.
  local musl gnu jq_arch lg_arch tmux_arch
  case "$(uname -s)/$(uname -m)" in
    Linux/x86_64)
      musl=x86_64-unknown-linux-musl; gnu=x86_64-unknown-linux-gnu
      jq_arch=linux-amd64; lg_arch=linux_x86_64; tmux_arch=linux-x86_64
      ;;
    Darwin/arm64)
      # Darwin has a single triple; the musl/gnu split only exists on Linux,
      # where ripgrep and bat publish musl-only and fd and delta publish gnu.
      musl=aarch64-apple-darwin; gnu=aarch64-apple-darwin
      jq_arch=macos-arm64; lg_arch=darwin_arm64; tmux_arch=macos-arm64
      ;;
    *)
      echo "skipping CLI tools: no verified assets for $(uname -s)/$(uname -m)"
      return 0
      ;;
  esac

  mkdir -p "$BIN_DIR"
  echo "cli tools:"
  fetch_tool rg "$gh/BurntSushi/ripgrep/releases/download/${RIPGREP_VERSION}/ripgrep-${RIPGREP_VERSION}-${musl}.tar.gz"
  fetch_tool fd "$gh/sharkdp/fd/releases/download/v${FD_VERSION}/fd-v${FD_VERSION}-${gnu}.tar.gz"
  fetch_tool delta "$gh/dandavison/delta/releases/download/${DELTA_VERSION}/delta-${DELTA_VERSION}-${gnu}.tar.gz"
  fetch_tool bat "$gh/sharkdp/bat/releases/download/v${BAT_VERSION}/bat-v${BAT_VERSION}-${musl}.tar.gz"
  fetch_tool lazygit "$gh/jesseduffield/lazygit/releases/download/v${LAZYGIT_VERSION}/lazygit_${LAZYGIT_VERSION}_${lg_arch}.tar.gz"
  fetch_tool tmux "$gh/tmux/tmux-builds/releases/download/v${TMUX_VERSION}/tmux-${TMUX_VERSION}-${tmux_arch}.tar.gz"
  fetch_tool jq "$gh/jqlang/jq/releases/download/jq-${JQ_VERSION}/jq-${jq_arch}" bare

  # fastfetch publishes a linux-amd64 tarball only.
  if [ "$(uname -s)/$(uname -m)" = "Linux/x86_64" ]; then
    fetch_tool fastfetch \
      "$gh/fastfetch-cli/fastfetch/releases/download/${FASTFETCH_VERSION}/fastfetch-linux-amd64.tar.gz"
  else
    echo "  skipping fastfetch: published for linux-amd64 only"
  fi
}

# Called with `|| echo` so bash disables -e inside the function body: any single
# failed download falls through to its guard and skips that tool instead of
# aborting the script. Coder treats a non-zero dotfiles script as a failed
# workspace build, and a missing CLI tool must never do that.
install_cli_tools || echo "cli tool setup failed, continuing"

# delta is configured entirely through gitconfig, which costs nothing at shell
# startup. Wired as an include.path rather than by writing keys directly, so it
# can never clobber or duplicate settings in your own ~/.gitconfig.
configure_delta() {
  local inc="$REPO_DIR/config/git/delta.gitconfig"
  command -v git >/dev/null 2>&1 || return 0
  [ -f "$inc" ] || return 0
  [ -x "$BIN_DIR/delta" ] || command -v delta >/dev/null 2>&1 || return 0

  if git config --global --get-all include.path 2>/dev/null | grep -qxF "$inc"; then
    echo "delta gitconfig already included"
  else
    git config --global --add include.path "$inc"
    echo "wired delta into ~/.gitconfig via include.path"
  fi
}

configure_delta || echo "delta gitconfig setup failed, continuing"

# Plugins are cloned at install time rather than vendored as submodules, to
# keep the repo lean. shell/zsh.sh guards every source with a -f test, so a
# clone that fails here degrades to "that plugin is absent" and never to a
# broken interactive shell.
ZSH_PLUGIN_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/plugins"

clone_or_update() {
  local url="$1" dest="$2" name
  name="$(basename "$dest")"

  if [ -d "$dest/.git" ]; then
    if git -C "$dest" pull --quiet --ff-only 2>/dev/null; then
      echo "  updated $name"
    else
      echo "  could not update $name, keeping existing checkout"
    fi
    return 0
  fi

  rm -rf "$dest"
  if git clone --depth 1 --quiet "$url" "$dest" 2>/dev/null; then
    echo "  installed $name"
  else
    echo "  could not clone $name, skipping"
  fi
}

install_zsh_plugins() {
  mkdir -p "$ZSH_PLUGIN_DIR"
  echo "zsh plugins:"
  clone_or_update https://github.com/zsh-users/zsh-autosuggestions \
    "$ZSH_PLUGIN_DIR/zsh-autosuggestions"
  clone_or_update https://github.com/zsh-users/zsh-syntax-highlighting \
    "$ZSH_PLUGIN_DIR/zsh-syntax-highlighting"
  clone_or_update https://github.com/zsh-users/zsh-completions \
    "$ZSH_PLUGIN_DIR/zsh-completions"
}

install_zsh_plugins || echo "zsh plugin setup failed, continuing"

install_fzf() {
  local dest="$HOME/.fzf"

  # Check the binary path directly as well as PATH: ~/.fzf/bin is only added to
  # PATH by shell/common.sh for interactive shells, so a PATH-only test would
  # miss an existing install here and re-download the binary on every run.
  if command -v fzf >/dev/null 2>&1 || [ -x "$dest/bin/fzf" ]; then
    echo "fzf already installed"
    return 0
  fi

  if [ ! -d "$dest/.git" ]; then
    rm -rf "$dest"
    git clone --depth 1 --quiet https://github.com/junegunn/fzf "$dest" 2>/dev/null \
      || { echo "could not clone fzf, skipping"; return 0; }
  fi

  # --bin only fetches the prebuilt binary for this arch: no rc file edits, no
  # interactive prompts. shell/zsh.sh wires up the key bindings itself.
  if "$dest/install" --bin >/dev/null 2>&1; then
    echo "installed fzf to $dest/bin"
  else
    echo "fzf binary download failed, skipping"
  fi
}

install_fzf || echo "skipping fzf install: setup failed"

MARK_BEGIN="# >>> zamp dotfiles >>>"
MARK_END="# <<< zamp dotfiles <<<"

# Injects a replaceable block that sets ZAMP_DOTFILES_DIR and sources
# shell/init.sh. The path is written in rather than derived at source time
# because zsh does not define BASH_SOURCE, so a sourced file cannot locate
# itself the way the bash-only version used to.
wire_rc() {
  local rc="$1" tmp
  if [ ! -e "$rc" ]; then
    touch "$rc"
    echo "created $rc"
  fi

  tmp="$(mktemp)"
  # Strip our block, plus the legacy pre-block two-liner, so re-running after
  # the repo moves cannot leave a stale path or a duplicate behind.
  sed -e "/^${MARK_BEGIN}\$/,/^${MARK_END}\$/d" \
      -e '/^# dotfiles: fastfetch banner$/d' \
      -e '\|shell/fastfetch-init\.sh|d' \
      "$rc" >"$tmp"

  {
    echo "$MARK_BEGIN"
    echo "ZAMP_DOTFILES_DIR=\"$REPO_DIR\""
    echo "[ -f \"\$ZAMP_DOTFILES_DIR/shell/init.sh\" ] && . \"\$ZAMP_DOTFILES_DIR/shell/init.sh\""
    echo "$MARK_END"
  } >>"$tmp"

  # Copy contents rather than mv, to preserve the rc file's inode and mode.
  cat "$tmp" >"$rc"
  rm -f "$tmp"
  echo "wired dotfiles into $rc"
}

wire_rc "$HOME/.bashrc"
wire_rc "$HOME/.zshrc"

if ! command -v zsh >/dev/null 2>&1; then
  echo "note: zsh is not installed here; ~/.zshrc is wired and ready for when it is"
fi

# Clone (or fast-forward) the Obsidian vault that is the knowledge-base layer of
# Claude's memory; the pointer in config/CLAUDE.md sends Claude here. A full clone
# (not --depth 1) so notes edited in the workspace can be committed and pushed back.
#
# Auth: in a Coder workspace the default git credential is org-scoped (Zampfi) and
# CANNOT read this personal repo. So we use a fine-grained PAT via a dedicated
# helper, wired ONLY into this repo. The `-c credential.helper=` empty value first
# RESETS the inherited (org) helper list, so only our token helper is consulted
# here — Zampfi repos are untouched. Non-fatal throughout: a missing token or auth
# failure must never fail the workspace build.
sync_obsidian_vault() {
  local repo="https://github.com/SahilZ0810/obsidian-vault.git"
  local dest="$HOME/obsidian-vault"
  local cred="$REPO_DIR/config/obsidian-vault-credential.sh"
  local token="${OBSIDIAN_VAULT_TOKEN_FILE:-$HOME/.config/obsidian-vault-token}"
  command -v git >/dev/null 2>&1 || { echo "obsidian vault: git absent, skipping"; return 0; }
  chmod +x "$cred" 2>/dev/null || true

  if [ -d "$dest/.git" ]; then
    git -C "$dest" pull --quiet --ff-only 2>/dev/null \
      && echo "obsidian vault: updated" \
      || echo "obsidian vault: could not fast-forward, keeping local checkout"
    return 0
  fi

  if [ ! -r "$token" ]; then
    echo "obsidian vault: no token at $token — create a fine-grained PAT and save it there to enable sync; skipping"
    return 0
  fi

  if git -c credential.helper= -c "credential.helper=$cred" clone --quiet "$repo" "$dest" 2>/dev/null; then
    # Persist the token helper (reset inherited helpers first) so future
    # pull/push from inside the workspace keep using the PAT, not the org token.
    git -C "$dest" config --add credential.helper ""
    git -C "$dest" config --add credential.helper "$cred"
    echo "obsidian vault: cloned to $dest"
  else
    echo "obsidian vault: clone failed even with token (check the PAT's repo scope), continuing"
  fi
}

sync_obsidian_vault || echo "obsidian vault sync failed, continuing"

# Coder only runs this script, so nothing else would restore memory in a fresh
# workspace. Non-fatal: a memory problem must not fail the workspace build.
if [ -x "$REPO_DIR/sync-memory.sh" ]; then
  "$REPO_DIR/sync-memory.sh" pull || echo "memory pull failed, continuing"
fi

echo
echo "Done."
