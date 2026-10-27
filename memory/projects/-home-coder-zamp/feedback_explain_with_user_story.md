---
name: explain-with-user-story
description: "Sahil understands technical issues best as a concrete numbered user story (who does what, what breaks, what they see)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 209832c0-3128-48ef-91e9-df19d4229ac0
  modified: 2026-10-27T19:10:16.579Z
---

When explaining a technical issue or design risk, tell it as a short numbered user story: a named user does X → system does Y → what goes wrong → what the user sees → the fix in plain words → a one-line summary.

**Why:** On PRO-4007 Sahil could not follow an abstract explanation of a FRAP/permissions pitfall ("runs through FRAP, returns empty set"). The same point told as "Priya deletes branch B1, sub-task still running, sweep asks 'any tasks?', can't see them, deletes folder" landed immediately, and Sahil said "this is great way to explain things".

**How to apply:** Default to this shape for design docs and review answers, especially for access-control, race, or failure-mode issues. Keep code references to a minimum inside the story and put them after it.
