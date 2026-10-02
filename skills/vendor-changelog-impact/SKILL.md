---
name: vendor-changelog-impact
description: Reads a vendor changelog or release notes (URL or pasted text) and reports which deprecations, breaking changes, removals and deadlines actually affect the user's repository, with exact quotes from the vendor and file:line evidence from the code. Use when the user asks "does this changelog affect us", shares release notes for an API, SDK or platform they depend on, or wants to know what to change before a vendor deadline.
license: Apache-2.0
compatibility: Helper script needs Python 3.9+ (stdlib only). Fetching a URL needs network access; pasted text works offline.
metadata:
  author: The Tech Gazette
  homepage: https://techgazette.com.br
  version: "1.0"
---

# Vendor changelog impact

Turn a vendor changelog into a short list of things that affect this repository,
each backed by a verbatim quote from the vendor and a location in the code.

## When to use

- The user pastes or links release notes, a changelog, an "upcoming changes" page or a
  deprecation notice for something the repository depends on.
- The user asks whether a vendor change breaks them, or what to do before a vendor date.

Do not use it to summarize a changelog in general. The output is only what affects
this repository.

## Inputs

1. The changelog: a URL, a local file, or text pasted into the conversation (save pasted
   text to a temporary file so the script can read it).
2. The repository: the current working directory unless the user names another path.

## Steps

1. Get the text. If you were given a URL, fetch it. If the page is empty or only a
   JavaScript shell, say so and ask for the text instead of guessing its contents.
   Record the URL and, when available, the anchor or heading of each entry.
2. Run the helper to collect candidates:

   ```bash
   python3 scripts/changelog_signals.py --changelog <url-or-file> --repo <repo> --format md
   ```

   It lists every changelog line that mentions a deprecation, removal, breaking change,
   end of life or required action, the dates on that line, the identifiers it names
   (code spans, endpoints, dotted names, constants) and where those identifiers occur in
   the repository. Add `--only-hits` to drop lines with no repository match.
3. Read the candidates in context. The script matches text, not meaning. For each one:
   - Open the repository hits and confirm the code actually uses the affected thing
     (the same SDK, endpoint, parameter or header, not a same-named local variable).
   - Check the changelog lines around the candidate: the deadline or the replacement is
     often on the next line or in the section heading.
   - Check versions: a change in SDK v8 does not affect a repo pinned to v7 unless the
     vendor says so. Look at the manifest and lockfile.
4. Look for what the script cannot see: runtime requirements (for example "no longer
   supports Node.js 18" against `engines`, `.nvmrc`, Dockerfiles and CI images),
   configuration keys, and dashboard settings the code does not contain. Report these
   as "check manually" when the repository gives no answer.
5. Write the report in the format below.

## Output format

```markdown
## <Vendor> changelog impact for <repo>
Source: <url or "pasted text">, read on <YYYY-MM-DD>

### Affects this repository
1. <one-line summary>
   - Vendor says: "<exact quote>" (<link to entry or heading>)
   - Deadline: <date exactly as written by the vendor, or "none stated">
   - Where: `path/file.ext:line` (and others)
   - Change: <the replacement the vendor names, or "vendor names no replacement">

### Check manually
- <item>: <why the repository alone cannot answer it>

### Does not affect this repository
- <short list of signal lines ruled out, with the reason in a few words>
```

Order "Affects this repository" by deadline, earliest first; items with no date go last.

## Guardrails

- Quote the vendor verbatim. Do not paraphrase inside quotation marks, do not merge two
  entries into one quote, and do not "fix" the vendor's wording.
- Never invent a deadline, version number, replacement API or link. If the changelog
  does not state it, write "none stated" or "vendor names no replacement".
- Do not convert or normalize dates inside quotes. You may add an ISO date next to the
  quote when the vendor's date is unambiguous.
- Every "Affects" item needs both a vendor quote and repository evidence. Without the
  evidence it belongs in "Check manually".
- If the page could not be fetched, or only part of it loaded, say exactly that. Do not
  fill gaps from memory of what the vendor "usually" announces.
- Do not edit code unless the user asks. When they do, change one item at a time and
  keep the quote in the commit or PR description.

## Files

- `scripts/changelog_signals.py`: candidate finder (stdlib only, `--help` for options).
- `scripts/test_changelog_signals.py`: tests, run with `python3 -m unittest` from `scripts/`.
- `examples/walkthrough.md`: a full run against the fixture in `examples/`.
