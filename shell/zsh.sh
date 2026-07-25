# zsh-only settings. Sourced from shell/init.sh for interactive shells.
#
# Load order in this file is deliberate and fragile in two places:
#   1. zsh-completions must land in fpath BEFORE compinit runs, or its
#      definitions are never picked up.
#   2. zsh-syntax-highlighting must be sourced LAST, after every other plugin
#      that binds ZLE widgets, because it wraps the widgets it finds.
# install.sh clones these; every source is guarded so a missing plugin
# degrades to "absent" rather than a broken shell.

ZSH_PLUGIN_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/plugins"

# --- history ---------------------------------------------------------------
HISTFILE="$HOME/.zsh_history"
HISTSIZE=50000
SAVEHIST=50000
setopt SHARE_HISTORY        # one history across concurrent shells
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_SPACE    # leading space keeps a command out of history
setopt HIST_REDUCE_BLANKS
setopt INC_APPEND_HISTORY   # write as you go, so a killed workspace keeps it

# --- completion ------------------------------------------------------------
# fpath first (see note 1 above), then compinit.
if [ -d "$ZSH_PLUGIN_DIR/zsh-completions/src" ]; then
  fpath=("$ZSH_PLUGIN_DIR/zsh-completions/src" $fpath)
fi

ZSH_COMPDUMP="${XDG_CACHE_HOME:-$HOME/.cache}/zsh/zcompdump"
mkdir -p "${ZSH_COMPDUMP:h}"
autoload -Uz compinit && compinit -d "$ZSH_COMPDUMP"

zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'  # case-insensitive
zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path "${XDG_CACHE_HOME:-$HOME/.cache}/zsh"

# --- navigation ------------------------------------------------------------
setopt AUTO_CD              # bare directory name means cd
setopt AUTO_PUSHD
setopt PUSHD_IGNORE_DUPS

# --- autosuggestions -------------------------------------------------------
if [ -f "$ZSH_PLUGIN_DIR/zsh-autosuggestions/zsh-autosuggestions.zsh" ]; then
  # Fall back to completion when history has no match.
  ZSH_AUTOSUGGEST_STRATEGY=(history completion)
  # Suggesting against a pasted multi-line blob is slow and never useful.
  ZSH_AUTOSUGGEST_BUFFER_MAX_SIZE=40
  . "$ZSH_PLUGIN_DIR/zsh-autosuggestions/zsh-autosuggestions.zsh"
fi

# --- fzf -------------------------------------------------------------------
# Ctrl-R fuzzy history, Ctrl-T file picker, Alt-C directory jump.
if command -v fzf >/dev/null 2>&1; then
  export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border --info=inline'
  # Respect .gitignore when ripgrep is around; plain find otherwise.
  if command -v rg >/dev/null 2>&1; then
    export FZF_DEFAULT_COMMAND='rg --files --hidden --glob "!.git/*"'
    export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
  fi

  # fzf >= 0.48 ships its own integration; older git checkouts use shell/.
  if fzf --zsh >/dev/null 2>&1; then
    eval "$(fzf --zsh)"
  else
    [ -f "$HOME/.fzf/shell/key-bindings.zsh" ] && . "$HOME/.fzf/shell/key-bindings.zsh"
    [ -f "$HOME/.fzf/shell/completion.zsh" ] && . "$HOME/.fzf/shell/completion.zsh"
  fi
fi

# --- prompt ----------------------------------------------------------------
# Deliberately dependency-free: no oh-my-zsh, no external prompt binary, so a
# fresh workspace needs nothing installed. Shows cwd, git branch, and a red
# arrow when the last command failed. Override by redefining PROMPT after this.
setopt PROMPT_SUBST
autoload -Uz vcs_info
zstyle ':vcs_info:*' enable git
zstyle ':vcs_info:git:*' formats ' %F{yellow}%b%f'
zstyle ':vcs_info:git:*' actionformats ' %F{yellow}%b%f %F{red}(%a)%f'
precmd_functions+=(vcs_info)
PROMPT='%F{cyan}%~%f${vcs_info_msg_0_} %(?.%F{green}❯.%F{red}❯)%f '

# --- syntax highlighting (must stay last, see note 2 above) ----------------
if [ -f "$ZSH_PLUGIN_DIR/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]; then
  ZSH_HIGHLIGHT_HIGHLIGHTERS=(main brackets)
  . "$ZSH_PLUGIN_DIR/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
fi
