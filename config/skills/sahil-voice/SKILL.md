---
name: sahil-voice
description: Write PR review comments, review summaries, Slack messages, DMs and replies in Sahil's own voice (short, lowercase, blunt questions, Hinglish when casual). Use this whenever the user asks to draft, post or rewrite a comment or message "in my language", "in my voice", "my style", "like I would write", "hinglish", or asks to post review comments or a Slack message on their behalf, even if they do not name this skill. Also use it before posting any GitHub PR comment or Slack message for the user.
---

# sahil-voice

Draft text the way Sahil actually writes it. People who know him should not be able to tell an agent wrote it. This was built from his real GitHub review comments and Slack messages (Oct 2026). Re-fetch a few recent ones if the voice feels off, because style drifts.

This skill governs the text of the comment or message. It does not change how you talk to Sahil in the terminal. Report to him in whatever output style is active.

## Pick the register first

| Where | Language | Tone |
|---|---|---|
| GitHub PR review comment | English only | terse, lowercase, direct |
| Slack, casual with teammates (DM, PR-review channels, squad chat) | Hinglish, mixed with English tech words | relaxed, "bro" is fine |
| Slack, asks to reviewers, announcements, cross-team or leadership | clean English | polite, a bit structured |

If unsure, use short English. Do not use Hinglish in PR comments, and do not use it with people he does not talk to casually.

## PR review comments

The pattern: one thought per comment, usually a question or a short order. He points at the problem and lets the author fix it. He does not explain at length.

- Start lowercase. No greeting, no "please", no closing line. Often no full stop.
- Put a space before the question mark: `can we use groupBy here ?`
- Questions are his main tool: `can we use ...`, `why do we need ...`, `what if label is null this will break in that case`, `are these changes required ?`, `isn't input already have a support of label ?`
- Short orders for obvious things: `remove this`, `same here`, `simplify comments`, `create a enum for this`, `no need of this directly use icon`, `we can remove this component`
- Tag the author with `@name` when the ask is for them: `@kuntal-zamp can you take a pull from release`
- Point at the design system or existing code instead of arguing: `are these radio button can we check if we can use them from design system`, `please don't use magic numbers ... use the from design system`
- For a tiny fix, use a ```suggestion block instead of describing it.
- Same issue elsewhere: `same here` or `same with this`. Do not repeat the explanation.
- Review summary body: `LGTM!`, `LGTM`, `approved`, or `added comments`. Nothing longer.

Do not write: headings, bullet lists, "Consider...", "I'd suggest...", "Great catch", severity labels, or a paragraph of reasoning. If the reason matters, give it in the same short line: `any 4xx shows "add a working key", use 422 only`.

## Slack, casual (Hinglish)

Hindi in Roman script, English for tech words, short. Typical words: `nhi`, `hn`, `h`, `toh`, `kya`, `na`, `karlio`, `dekhta`, `mujhe lga`, `bro`, and nicknames for teammates (`adi`, `sid`).

- `isko merge kare kya ?`
- `aur koi PR pending toh nhi na`
- `hn done mein dekhta isko`
- `chill h jab time lage toh karlio`
- `nhi nhi mujhe lga ki kaal ka din h merge karke test karte h`
- one-word replies are normal: `ok`, `ok ok`, `cool`, `done`, `ack`, `checking`, `approved`

Keep tech nouns in English (`PR`, `merge`, `feature flag`, `network console`). Do not force Hinglish into every sentence. Mix only when it is natural.

## Slack, to reviewers or the wider team (English)

Opening is `Hey @name` or the ask directly: `@name can you please review these PR's`. Then one or two lines on what the PR does, then the link. For stacked PRs, list them in order and say so. Test steps go in short bullets.

For an announcement (a fix, an optimisation, a release note), a short structured post is fine: what changed, why it mattered, why it is safe. Still no filler.

## Do not

- Do not sound polished or corporate. No em dashes, no "Hope this helps", no "Let me know if...", no emoji pile. An occasional `:sweat_smile:` or `:zap:` is the limit.
- Do not add content he did not ask for. Match the finding, nothing extra.
- Do not copy private DM content into drafts or into this file.
- Do not post anything until Sahil has seen the drafts and said go. Messages and PR comments go out under his name and cannot be quietly taken back.

## Check before sending

Read each draft as if Sahil typed it in a hurry. If it has a capital first letter, a "please", a closing line or a paragraph, cut it down.
