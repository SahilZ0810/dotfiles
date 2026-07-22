---
name: global-skills-setup
description: "Global Claude skills in this Coder workspace are symlinks into the zamp_dev_setup repo's central skills directory"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8b34d40c-301d-484b-aeb6-15e13dd71a3f
---

`~/.claude/skills/` contains symlinks (created 2026-07-14) to `~/zamp/zamp_dev_setup/skills/` — the team's central skills directory, git-tracked in the zamp_dev_setup repo. Skills: branching-migration, feature-qa, onprem, pr-cleanup, skill-creator. Repos under `~/zamp/services/` also symlink their `.claude/skills/` entries to the same central dir.

**How to apply:** When a new shared skill is added to zamp_dev_setup/skills/, symlink it into ~/.claude/skills/ to make it global. Personal skills go directly in ~/.claude/skills/. Don't copy skill files — symlink, so `git pull` keeps them fresh.
