---
name: feedback-brainstorm-before-changes
description: Never start code changes on a ticket; first run /superpowers:brainstorming to walk the user through the issue and the removal plan
metadata:
  node_type: memory
  type: feedback
  originSessionId: ea7b3e70-f383-41d5-8c75-a6fa84acbaf6
  modified: 2026-11-24T07:27:23.118Z
---

Never start making code changes for a ticket/bug straight away, even when the task prompt lays out a fix direction. First invoke `/superpowers:brainstorming` to explain to the user what the issue is and how we plan to remove it, and get their agreement.

**Why:** On PRO-3974 (2026-11-24) I went straight to patching `cmd_home_folder_init_git` + tests; the user had me revert everything and said "never start working on the changes always use /superpowers:brainstorming to first help me what is the issue and how are we planning to remove it".

**How to apply:** Reading code to understand the issue is fine; editing files, branching for a fix, or running fix-related commands waits until the brainstorming pass is done and the user approves the plan. Related: [[feedback_orchestrator_no_handson_work]].
