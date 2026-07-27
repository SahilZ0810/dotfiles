---
ticket: PRO-2374
seat: sahil-seat-2
repo: frontend
branch: sahil/pro-2374-update-share-dataset-copy
started: 2026-07-27T11:40:00Z
ended: 2026-07-27T11:40:00Z
outcome: ready-to-verify
preemptions: 2
plan_rounds: 2
pr: https://github.com/Zampfi/application-platform-frontend/pull/1234
---

# PRO-2374 — Update share dataset copy and add agent and user icons

https://linear.app/zamp/issue/PRO-2374/update-share-dataset-copy-and-add-agent-and-user-icons

## Timeline

- state: In Review
- labels: agent:ready-to-verify
- 2026-07-27T09:13:00Z — comment by Sahil Sharma
- 2026-07-27T09:20:00Z — comment by Sahil Sharma

## What I tested

- `npm run test` → 412 passed, 0 failed
- pre-commit → clean
- browser check: picker renders agent + user icons in dark mode

## Human corrections

- **reply** · 2026-07-27T09:31:00Z
  > don't add a new util file, put the icon map next to the picker
- **plan-rejected** · 2026-07-27T09:31:30Z
  > don't add a new util file, put the icon map next to the picker
- **reply** · 2026-07-27T09:55:00Z
  > approved
- **plan-approved** · 2026-07-27T09:55:10Z
  > PRO-2374
- **reply** · 2026-07-27T10:06:00Z
  > legacy top-level content shape

## Failures

- preempted 2 time(s)
- plan rejected: don't add a new util file, put the icon map next to the picker

## Linear comments

### Sahil Sharma · 2026-07-27T09:13:00Z

picked up on seat sahil-seat-2

### Sahil Sharma · 2026-07-27T09:20:00Z

**Plan**
1. Add icon map
2. Update copy
