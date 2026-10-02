---
name: primary-source-check
description: Before a technical claim is published, checks every number, name, version, date and quote in the draft against the primary source (vendor docs, release notes, papers, filings, official repos) and flags anything that is not in the source, is in it with a different meaning, or comes only from a secondary source. Use when the user asks to fact-check, verify or source a draft, post, article, release note, slide or README before publishing, or asks "is this accurate?" about a technical statement.
license: Apache-2.0
compatibility: Helper script needs Python 3.9+ (stdlib only). Fetching sources needs network access.
metadata:
  author: The Tech Gazette
  homepage: https://techgazette.com.br
  version: "1.0"
---

# Primary source check

Verify a draft claim by claim against the primary source, and report what holds,
what does not, and what cannot be verified.

## When to use

- The user shares a draft (article, post, changelog entry, slide, README section) and
  asks to check it, source it or make sure it is accurate before publishing.
- The user asks whether a specific technical statement is true and has, or can name,
  the source.

## What counts as a primary source

The organization or people who did the thing: the vendor's docs, changelog, blog,
pricing page, status page or official repository; the paper's authors; the standard
body's text; a regulator's filing. News articles, aggregators, social posts and AI
answers are secondary. They can lead you to the primary source; they cannot confirm a
claim on their own.

## Steps

1. Collect sources. Use the links in the draft and any the user gives. For each claim
   without a link, find the primary source; if you cannot, the claim is "unsourced".
   Save or note the exact URL you read and the date you read it.
2. Extract and match:

   ```bash
   python3 scripts/claims.py check draft.md <source URL or file> [...] --format md
   ```

   It pulls numbers, percentages, currency, versions, dates, quoted phrases and
   multi-word or mixed-case names from the draft, then searches each source for the
   exact text and for simple variants (1,024 vs 1024, 40% vs 40 percent, 2026-03-05 vs
   March 5, 2026). Exit code 1 means at least one item was not found. Use
   `claims.py extract draft.md` to list items without sources.
3. Read every match in context. A number that appears in the source can describe
   something else (see the example). For each item decide:
   - **Confirmed**: the source states the same value about the same thing.
   - **Mismatch**: the source states a different value; give the source's value.
   - **Context differs**: the value appears but refers to something else, or the source
     qualifies it ("up to", "in preview", "recommended", "in the US only").
   - **Not in source**: nothing in the primary source supports it.
   - **Secondary only**: supported only by a secondary source.
4. Check what the script cannot extract: single-word names (a company, product or person
   at the start of a sentence), relative time ("last week", "now available"), superlatives
   ("first", "fastest", "only"), and causal claims. Each needs a source sentence too.
5. Report (format below). Suggest a corrected sentence only when the source gives the
   right value; otherwise suggest cutting or attributing the claim.

## Output format

```markdown
## Source check: <draft title>, <YYYY-MM-DD>
Sources read: <URL> (<date read>), ...

| # | Claim in draft | Verdict | Source says | Source |
| - | --- | --- | --- | --- |
| 1 | "<draft wording>" | Confirmed / Mismatch / Context differs / Not in source / Secondary only | "<exact quote>" | <URL#anchor> |

### Fixes
- Line <n>: replace "<draft>" with "<corrected text>" (source: <URL>)
- Line <n>: cut or attribute; no primary source found.
```

## Guardrails

- Quote the source exactly. If you shorten a quote, mark the cut with "..." and keep
  the meaning.
- Never mark a claim confirmed from memory or because it "is well known". No source
  sentence, no confirmation.
- Never fill a gap with a plausible value. "Not in source" is a valid, useful result.
- When sources conflict (docs vs blog post, old vs new page), show both with dates and
  let the user decide.
- Note qualifiers the draft dropped: "up to", "beta", "for paid plans", region limits.
- If a page could not be fetched or was behind a login, say so and list the claims that
  remain unchecked because of it.

## Files

- `scripts/claims.py`: extractor and matcher (stdlib only, `--help` for options).
- `scripts/test_claims.py`: tests, run with `python3 -m unittest` from `scripts/`.
- `examples/draft.md` and `examples/walkthrough.md`: a real check of a short paragraph
  about the Agent Skills format against agentskills.io and the Claude Code docs.
