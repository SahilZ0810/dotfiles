---
name: pro3417-no-chat-regroup
description: PRO-3417 change groups — regrouping from chat (merge/split/rename/move/reword groups) is intentionally NOT a feature
metadata:
  node_type: memory
  type: project
  originSessionId: 6cd05345-c54b-494c-8d4a-476fcbd043e1
  modified: 2026-09-28T18:52:03.347Z
---

PRO-3417 (Grouped Changes for Branch Review): users can NOT regroup from chat — no merging, splitting or renaming groups, no moving a change between groups, no rewording group summaries by asking the agent. Groups come only from the agent's `record_change_groups` call on content-changing turns plus Jev placement.

**Why:** product decision by the user on 2026-09-28 ("this is not a bug i also don't want this feature from chats a user can't say to merge groups").

**How to apply:** don't report "agent has no tool to regroup" / "main chat doesn't forward regroup requests" as bugs; don't build a regroup-from-chat path. Test cases B1, B4, B5, B6, B7, B10, F6 in the manual suite are out of scope.
