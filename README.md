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

## What's deliberately NOT tracked here

- `~/.claude/CLAUDE.md` — Coder-platform-managed, rewritten on every
  workspace boot.
- `~/zamp/.claude/*` — org-managed, symlinked from `zamp_dev_setup` on
  every boot. Change it there, not here.
- `~/.claude/.credentials.json`, `history.jsonl`, `sessions/`,
  `session-env/`, `shell-snapshots/`, `remote/` — secrets and ephemeral
  session state. Never belongs in git.

## Setting up a new environment (Coder workspace or your laptop)

```bash
git clone <this-repo-url> ~/dotfiles
cd ~/dotfiles
./install.sh          # symlinks config/ into ~/.claude (one-time)
./sync-memory.sh pull # restores personal memory for every project
```

## Day to day

- Start of a session: `./sync-memory.sh pull`
- End of a session: `./sync-memory.sh push` (stages, commits, and pushes
  any memory that changed across all projects)
- `config/settings.json` is a live symlink after `install.sh` runs, so
  edits there are effective immediately — commit + push when you want
  other environments to pick them up.
