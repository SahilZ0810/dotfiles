---
name: feedback-no-commit-superpowers-specs
description: "Spec/plan documents written by superpowers-style skills (e.g. brainstorming) must never be committed, regardless of what else is being committed"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 80ce98cd-34a3-40db-b753-81baaabc3418
  modified: 2026-07-28T07:48:32.554Z
---

When a `superpowers` skill (brainstorming, spec-writing, etc.) produces a spec or plan
document as part of its process, that file must never be committed to git — not even as
part of a broader commit that includes real code changes.

**Why:** the user said explicitly they don't want these specs committed, full stop —
they're working/process artifacts for the current session, not deliverables meant to
live in the repo's history.

**How to apply:** when a superpowers-style skill writes a spec/plan file (wherever it
lands — scratch dir, repo root, a `specs/`-type folder), treat it as excluded from any
`git add`/`git commit` by default. If asked to commit other changes in the same
session, stage and commit everything *except* that spec file — don't ask, just exclude
it (and mention it was excluded if it's not obvious why). If the user explicitly asks to
commit the spec itself, that overrides this default — but never include it by default or
by inference from a broad `git add`.
