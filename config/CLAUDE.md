# Personal Memory — Obsidian Vault

I (the user) maintain a durable knowledge base as an Obsidian vault. Treat it as
my long-term knowledge layer across Claude Code sessions and machines.

**Vault location — use whichever path exists:**
- macOS (local): `~/Documents/Obsidian Vault`
- Coder workspace (or other Linux): `~/obsidian-vault`

**Index note:** `<vault>/AI Memory System.md` — read this first.

## When to consult it
When a task relates to my saved knowledge, past decisions, projects, research, or
"what did I think/decide about X" — **read the vault before answering from scratch.**
Start with the index note, then `Grep`/`Glob` across the folders below. Retrieve only
what's relevant; don't load the whole vault.

## Structure
| Folder | Holds |
|--------|-------|
| `raw/` | unprocessed capture: articles, transcripts, links, pasted text, meeting dumps |
| `wiki/` | processed knowledge: one concept/person/project/tool per note, wikilinked |
| `reports/` | my best synthesized outputs: briefs, reviews, plans, drafts |
| `templates/` | repeatable note formats |

## When to write to it
Follow the loop **Capture → Process → Synthesize → Save → Reuse**. When I produce
something durable and ask to keep it (or it clearly belongs in the knowledge base):
- a synthesized answer/brief/plan → `reports/`
- a reusable explanation of a concept → `wiki/` (link back to its `raw/` source)
- a decision worth remembering → a decision-log note in `wiki/`

Ask before creating vault files unless I've told you to save something.

## Sync (important for Coder workspaces)
The vault is a private git repo (`SahilZ0810/obsidian-vault`). `install.sh` clones it
to `~/obsidian-vault` at workspace start (full clone, so it can be committed to).
- **Auth:** the workspace's default git credential is org-scoped (Zampfi) and cannot
  read this personal repo. A fine-grained PAT in `~/.config/obsidian-vault-token`
  (persistent home) is used via a repo-local credential helper. If `~/obsidian-vault`
  is missing, the token is probably absent — create it, then re-run `install.sh`.
- **Before relying on it in a workspace:** `git -C ~/obsidian-vault pull --ff-only`.
- **After saving notes in a workspace:** `git -C ~/obsidian-vault add -A && commit && push`.
- On the Mac, Obsidian's own Git plugin (or manual commits) keeps it current.
If both sides edit the same note between syncs, expect a merge conflict — resolve normally.

## Scope / caveats
- This file is delivered to every environment via the dotfiles repo (linked to
  `~/.claude/CLAUDE.md` by `install.sh`), so it loads in every Claude Code instance —
  local Mac and Coder workspaces alike.
- It does **not** cover Claude Desktop or claude.ai (separate surfaces).
- Separate from Claude Code's native per-project `memory/` store (which the dotfiles
  `sync-memory.sh` already syncs) — this vault is the richer, human-curated layer.
