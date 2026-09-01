# dotfiles

Personal, canonical store for the parts of my Claude Code setup that are
mine alone — not already provided by `Zampfi/zamp_dev_setup` (org-wide
CLAUDE.md, settings, skills, relinked fresh into `~/zamp/.claude/` on every
workspace boot) and not owned by the Coder platform itself
(`~/.claude/CLAUDE.md` is rewritten at workspace start via
`CODER_MCP_CLAUDE_MD_PATH` — do not manage that file here).

## What's tracked here

- `config/settings.json` — user-scope `~/.claude/settings.json`: personal
  permission mode, enabled plugin marketplaces. Distinct from the
  project-scope settings.json that `zamp_dev_setup` links into
  `~/zamp/.claude/settings.json`.
- `config/commands/` — personal slash commands not tied to any one repo.
- `memory/projects/<slug>/` — mirrors `~/.claude/projects/<slug>/memory/`
  for every project, where `<slug>` is Claude Code's dash-encoded absolute
  path (e.g. `-home-coder-zamp-services-application-platform-frontend`).
- `shell/` — interactive shell config for **both bash and zsh**:
  - `init.sh` — the single entry point sourced from `~/.bashrc` and
    `~/.zshrc`; picks the per-shell file and loads the banner.
  - `common.sh` — shared by both shells (PATH, `EDITOR`, aliases).
  - `bash.sh` / `zsh.sh` — per-shell settings. `zsh.sh` carries history,
    completion, plugin loading, and a dependency-free git-aware prompt (no
    oh-my-zsh, so a fresh workspace needs nothing installed).
  - `fastfetch-init.sh`, `fastfetch-config.jsonc` — login banner.
- `config/tmux.conf` — symlinked to `~/.tmux.conf`.
- `config/git/delta.gitconfig` — included into `~/.gitconfig` by `install.sh`.

## CLI tools

`install.sh` installs these into `~/.local/bin` from **pinned** release URLs.
Pinned rather than "latest" because this script runs on every workspace start,
and resolving latest meant a GitHub API round-trip (and rate-limit exposure)
each time.

| Tool | Use |
|------|-----|
| `rg` (ripgrep) | Fast search. Also what `shell/zsh.sh` hands fzf as `FZF_DEFAULT_COMMAND`, making `Ctrl-T` gitignore-aware. |
| `fd` | Fast find. |
| `delta` | Git diff pager. Configured purely via gitconfig, so **zero shell-startup cost**. |
| `bat` | `cat` with highlighting. |
| `lazygit` | Git TUI; good for interactive rebase and hunk staging. |
| `tmux` | Used by `zamp_dev_setup` agent-pool scripts (see below). No auto-attach. |
| `jq` | JSON. |
| `fastfetch` | Banner. linux-amd64 only upstream, so skipped elsewhere. |

Only `linux/x86_64` and `darwin/arm64` are wired up — those are the targets
whose release assets were verified to exist. Other platforms skip with a
message rather than failing. Every download is non-fatal, so an offline or
rate-limited boot yields a workspace missing a tool, never a failed build.

Deliberately **not** included: `eza` (has never published a macOS binary),
`btop` (no macOS build since 2022), `dust` (Rosetta-only on arm64), `duf`
(unmaintained), `starship` (~354ms command lag; the `vcs_info` prompt here is
effectively free), and `atuin` (fights fzf for `Ctrl-R` and hijacks
`ZSH_AUTOSUGGEST_STRATEGY`).

## tmux

The binary and `config/tmux.conf` stay, because the `zamp_dev_setup` agent-pool
scripts (`skills/_shared/start-seat.sh`, `seatctl.py`) start their own named
sessions with it.

There is **no login auto-attach** any more (`shell/tmux-init.sh` was removed,
2026-09-02). It used to `exec tmux new-session -A -s main` on every SSH login.
Orca opens each terminal over SSH with the worktree as `cwd` and injects
`ORCA_*` env (including the remote `orca` CLI on `PATH`); attaching to one
shared tmux session replaced both with the first pane's stale cwd and env, so
agents started in the wrong checkout and could not find `orca`. Orca's relay
handles reconnects itself, so nothing is lost by dropping the wrapper.

## zsh plugins

`install.sh` clones these into `${XDG_DATA_HOME:-~/.local/share}/zsh/plugins`
rather than vendoring them as submodules, to keep the repo lean:

| Plugin | What it gives you |
|--------|-------------------|
| [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions) | Inline suggestion from history as you type |
| [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting) | Colors invalid commands before you run them |
| [zsh-completions](https://github.com/zsh-users/zsh-completions) | Extra completion definitions |
| [fzf](https://github.com/junegunn/fzf) | `Ctrl-R` fuzzy history, `Ctrl-T` files, `Alt-C` dirs |

fzf goes to `~/.fzf` via its own installer, which resolves a prebuilt binary
for the current arch (so unlike the fastfetch step, it works on arm64 too).

**Two ordering constraints in `shell/zsh.sh` that are easy to break:**

1. `zsh-completions` must be added to `fpath` *before* `compinit` runs, or its
   definitions are silently ignored.
2. `zsh-syntax-highlighting` must be sourced *last*, after everything else that
   binds ZLE widgets, because it wraps the widgets it finds at load time.

Every plugin is sourced behind a `[ -f ... ]` guard, so a clone that failed
during workspace build degrades to "that plugin is missing" and never to a
broken interactive shell.

## What's deliberately NOT tracked here

- `~/.claude/CLAUDE.md` — Coder-platform-managed, rewritten on every
  workspace boot.
- `~/zamp/.claude/*` — org-managed, symlinked from `zamp_dev_setup` on
  every boot. Change it there, not here.
- `~/.claude/.credentials.json`, `history.jsonl`, `sessions/`,
  `session-env/`, `shell-snapshots/`, `remote/` — secrets and ephemeral
  session state. Never belongs in git.

## Setting up a Coder workspace (the normal path)

Paste this repo's URL into the workspace's **dotfiles** field. Coder clones
it and runs `install.sh` automatically — nothing to do by hand.

Details worth knowing:

- Coder picks the first match from `install.sh`, `install`, `bootstrap.sh`,
  `bootstrap`, `script/bootstrap`, `setup.sh`, `setup`, `script/setup`. Ours
  is `install.sh`, the first entry.
- Coder clones into its own config dir — `~/.config/coderv2/dotfiles`, *not*
  `~/dotfiles`. Symlinks resolve against wherever it landed, so this is only
  worth knowing when you go looking for the checkout.
- **A non-zero exit fails the workspace build.** Every optional step here
  (fastfetch, memory pull) is therefore non-fatal by design. Keep it that
  way when adding steps.
- `install.sh` runs at workspace **creation**. For something that should run
  on every **start**, use Coder's `~/personalize` hook instead.

## Setting up by hand (your laptop, or an existing workspace)

```bash
git clone <this-repo-url> ~/dotfiles
cd ~/dotfiles
./install.sh   # symlinks config/ into ~/.claude, wires both shells, pulls memory
exec $SHELL -l # pick up the shell changes
```

## Day to day

- `install.sh` already runs `sync-memory.sh pull`, so a fresh workspace
  comes up with your memory in place.
- End of a session: `./sync-memory.sh push` (stages, commits, and pushes
  any memory that changed across all projects).
- **`pull` never overwrites a file that already exists locally.** This is
  load-bearing: because Coder re-runs `install.sh` on every workspace *start*,
  an unconditional copy would silently revert memory you edited but hadn't
  pushed. Use `./sync-memory.sh pull --force` to deliberately overwrite local
  memory from the repo.
- `config/settings.json` is a live symlink after `install.sh` runs, so
  edits there are effective immediately — commit + push when you want
  other environments to pick them up.
- `install.sh` is idempotent and safe to re-run. Shell wiring lives in a
  delimited `# >>> zamp dotfiles >>>` block that gets replaced rather than
  appended, so re-running never duplicates it or leaves a stale path.
