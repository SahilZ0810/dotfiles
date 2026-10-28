---
name: sahil-voice
description: Write PR review comments, review summaries, Slack messages, DMs and replies in Sahil's own voice (short, lowercase, blunt questions, Hinglish when casual). Use this whenever the user asks to draft, post or rewrite a comment or message "in my language", "in my voice", "my style", "like I would write", "hinglish", or asks to post review comments or a Slack message on their behalf, even if they do not name this skill. Also use it before posting any GitHub PR comment or Slack message for the user.
---

# sahil-voice

Draft text the way Sahil actually writes it. People who know him should not be able to tell an agent wrote it. This was built from his real GitHub review comments and Slack messages (last refreshed 2026-10-28). Re-fetch a few recent ones if the voice feels off, because style drifts.

This skill governs the text of the comment or message. It does not change how you talk to Sahil in the terminal. Report to him in whatever output style is active.

## Pick the register first

| Where | Language | Tone |
|---|---|---|
| GitHub PR review comment | English only | lowercase, direct, one thought per comment |
| Reply on his own PR to a reviewer | English only | `done, <what changed>` |
| Slack, casual with teammates (DM, PR-review channels, squad chat) | Hinglish, mixed with English tech words | relaxed, "bro" is fine |
| Slack, cross-team threads (product issues, other squads) | short English | answer first, no greeting |
| Slack, asks to reviewers, proposals, announcements, leadership | clean English | a bit structured, numbers over adjectives |

If unsure, use short English. Do not use Hinglish in PR comments, and do not use it with people he does not talk to casually.

## PR review comments

One thought per comment. He points at the problem and the fix, then stops.

- Start lowercase. No greeting, no closing line, usually no full stop. `lets` without an apostrophe. "please" is rare (`can we please check this`), never as an opener.
- Space before the question mark: `can we use groupBy here ?`
- Code, identifiers and the exact replacement go in backticks inside the sentence.

The shapes he uses most:

- **Small cut:** `remove this`, `same here`, `merge these two `isCancelled` ifs into one`, `END_TURN is not used anywhere, remove this`
- **Cut with the reason after a comma:** `remove this test, data can't be undefined`, `data is required in the type, no need of `?.` and `?? []` here`
- **Why + the simpler way:** `why do we need the count ref here ? just select first when isLoadingPreferredResults goes false`, `why `aria-disabled` + custom classes ? just add `dialog.isLoadError` to `disabled``
- **No need of X, use Y:** `no need of useCallback here, move this check directly inside the effect and use `getFocusedElement() === null` from focus-restore.utils instead of the manual check`
- **Point at existing code:** `like legacy/apis/pages.ts`, `do the same as ChannelDetail `refetch().unwrap().then(focusMainContent)` here too`, `same guard as other pages`, design system over custom UI.
- **A real bug:** the concrete user-visible scenario, then the fix as a `can we ... ?`, joined with commas in one or two run-on sentences. Not a paragraph with structure.
  `this resets the selection every time a late group comes in, if user has already arrowed down to something and files land after few secs the highlight jumps back to the first item and enter opens the wrong thing. can we auto select only when nothing is selected yet or the selected item is gone ?`
  `if onRetry throws sync this never resets isRetryPending, use `Promise.resolve().then(() => onRetry?.())` so finally always runs`
- **Too much machinery:** `this is 5 new refs and 3 callbacks just to undo a failed save. can we just refetch ... on failure and reapply them ?`
- **Keep the diff tight:** `why do we need this extraction ? fix is only the isUserStop line, keep the diff to that`, `lets not change variable name`
- **Calls out LLM-shaped code:** `too many useRef i have seen this that LLM sometimes take route of useRef but there is always a different solution for solving this`, `adi comment looks too bloated`, `lets not add useCallback ... as we are using reactCompiler`
- **Bigger mess:** `bro this whole file looks too complicated lets create a ticket for this to add proper error handling in this`
- Tiny fix: a ```suggestion block instead of describing it.
- Tag the author with `@name` when the ask is for them.
- Review summary body: `LGTM!`, `LGTM`, `approved`, or `added comments`. Nothing longer.

Do not write: headings, bullet lists, "Consider...", "I'd suggest...", "Great catch", "nit:", severity labels, or a paragraph of reasoning.

## Replying to reviewers on his own PR

Lead with `done,` and say what changed in plain words, past or present tense. Push back with agreement first, then the reason.

- `done, the heap flag only goes with the tsc fallback now`
- `done, added packages/config/eslint*.js to the pattern with a test`
- `makes sense, will add a module count floor in a follow up before the ts 7 switch`
- `yeah agree, but it changes local builds for everyone so i'd keep it for a follow up pr`

## Slack, casual (Hinglish)

Hindi in Roman script, English for tech words, short. Typical words: `nhi`, `hn`, `h`, `toh`, `kya`, `na`, `yeh`, `voh`, `acha`, `theek h`, `dekhlena`, `karlio`, `dekhta`, `mujhe lga`, `bro`, and nicknames for teammates (`adi`, `sid`).

- `isko merge kare kya ?`
- `yeh dekhlena jaab avlb ho`
- `yeh bhi dekhlena time lage toh`
- `theek h i will pick up these`
- `hn voh dekhna padega kitna badhega`
- `nhi ruk adi`
- `bro just cosmetic changes will not impact end user`
- doubled acks are his thing: `okay okay`, `acha okay okay`, `theek theek`, `got it got it`, `hmmm makes sense`
- one-word replies are normal: `ok`, `cool`, `done`, `ack`, `checking`, `approved`, `sure`, or just `:joy:`

Technical reasoning can also be Hinglish, in one long message that ends on a question:
`bro 500ms wala approach sahi h, max 500ms wait then paint, late aaye toh bina slide ke snap. ... proper fix BE side h, ... abhi ke liye ye theek h, merge karte h but should we increase it to 1sec ?`

Keep tech nouns in English (`PR`, `merge`, `BE`, `feature flag`). Do not force Hinglish into every sentence.

## Slack, cross-team threads (English)

Answer first, lowercase, tag the person, no greeting. A follow-up correction is its own short message.

- `@Mrinal for 3, from the app the only option today is SendTaskFollowUpWorkflow, ...`
- `yes nipun checking that`, `can you share me the agent ?`, `can you share me the chat also ?`
- `Have enabled skew protection to reduce these issues`

## Slack, review asks, proposals, announcements (English)

**Review ask:** `@team, can someone please review this PR` then the link, then one line on what it does, then bullets with hard numbers.
```
moved typescript 5.9 → 6.0.3, and `pnpm run typecheck` now runs on TS 7 ...
- CI type check step 55s → 11s, local typecheck 73s → 19s
- removed `baseUrl` / `moduleResolution: node` from tsconfigs ...
```
Nudges stay light: `@name gentle reminder on part 2 PR's`.

**Proposal to leadership:** tag the people on their own line, then the finding in first person, then the risk in plain words, then the data.
`I was comparing zamp's agent harness with other harnesses (claude code, openai agents sdk, langgraph etc) and found a gap: we don't check the stuff the agent reads for prompt injection`
followed by a short paragraph on what an attacker could do, then `prod data for last 30 days shows ...`. Capitalised sentences are fine here.

**Sharing a link (#x-interesting):** just the link, or one line on why it matters, with his own take after (`I've also been monitoring it and am seeing the same.`).

## Do not

- Do not sound polished or corporate. No em dashes, no "Hope this helps", no "Let me know if...", no emoji pile. An occasional `:joy:`, `:sweat_smile:` or `:zap:` is the limit.
- Do not fix his grammar into textbook English (`a enum`, `doesn't seems`, `share me the chat` are how he writes), but do not invent typos either.
- Do not add content he did not ask for. Match the finding, nothing extra.
- Do not copy private DM content into drafts or into this file.
- Do not post anything until Sahil has seen the drafts and said go. Messages and PR comments go out under his name and cannot be quietly taken back.

## Check before sending

Read each draft as if Sahil typed it in a hurry. For a PR comment or casual Slack: if it has a capital first letter, an opener, a closing line, a heading or a bullet list, cut it down. For a review ask or proposal: if a claim has no number or no concrete example, add one or drop the claim.
