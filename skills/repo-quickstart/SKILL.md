---
name: repo-quickstart
description: Extracts, verbatim, the exact install command and the first working commands or smallest runnable example from a repository's README, with line references, and refuses to shorten, merge or invent code. Use when the user asks how to install or start using a library, CLI or repo, wants a "use it today" or quickstart box for an article, or pastes a GitHub link and asks how to try it.
license: Apache-2.0
compatibility: Helper script needs Python 3.9+ (stdlib only). Reading a remote README needs network access.
metadata:
  author: The Tech Gazette
  homepage: https://techgazette.com.br
  version: "1.0"
---

# Repo quickstart

Produce a "use it today" box: the install line and the smallest working example,
copied exactly from the project's own README.

## When to use

- "How do I install X?", "How do I try this repo?", "Give me the quickstart for <link>".
- Writing an article or post that needs a short, correct "try it" section.

## Steps

1. Locate the README. For a GitHub repository use the raw file of the default branch,
   for example `https://raw.githubusercontent.com/OWNER/REPO/HEAD/README.md`. If the
   README links to a separate "Getting started" or "Installation" page and has no code of
   its own, read that page instead and say so in the output.
2. List the code blocks:

   ```bash
   python3 scripts/readme_blocks.py <README path or raw URL> --format md
   ```

   Each block is printed verbatim with its line range, language tag, the heading it sits
   under, and hints (`install`, `shell`, `prompts`). Use `--block N` to print one block
   raw when you need to copy it exactly.
3. Choose the install line. Prefer, in order: the block under an "Install" or
   "Installation" heading, the first block tagged `install`, an install command written
   inline in prose. When the README offers several package managers, keep the first one
   it lists and mention that alternatives exist; do not translate between them.
4. Choose the first working example: the first block after the install line that
   runs on its own (a CLI invocation, a short script, a REPL session). Skip blocks that
   are configuration fragments, output only, or depend on code shown elsewhere, unless
   the README presents them as the quick start.
5. Write the box (format below). Record the commit, tag or date you read so the reader
   knows what version the commands come from.

## Output format

```markdown
### Use it today: <project>
Install (README line <n>):
<exact block, fenced, with the README's language tag>

First run (README lines <a>-<b>, under "<heading>"):
<exact block, fenced>

Requires: <only what the README states, for example "Python 3.10+">
Source: <README URL>, read on <YYYY-MM-DD> (<commit or tag if known>)
```

## Guardrails

- Copy code byte for byte: same prompts (`$`, `>>>`), same quotes, same placeholders,
  same comments, same line breaks. Do not remove prompts or output lines even if they
  make copy-paste awkward; note it in one line instead.
- Never shorten, merge, reorder or "simplify" a block. If the smallest example is long,
  use it whole or pick a different block that is complete on its own.
- Never write code the README does not contain. No added imports, no filled-in API
  keys, no guessed flags, no version pins the README does not show.
- If the README has no install line or no example, say exactly that ("The README does
  not include an install command") and link to where the project points instead.
- Do not run install commands on the user's machine unless asked. If the user asks you
  to verify the quickstart, run it in a throwaway directory or container and report
  the real output.
- Prefer the README of the version the user will install (default branch vs latest
  release tag). If they differ in the install line, show both and say which is which.

## Files

- `scripts/readme_blocks.py`: verbatim code-block lister (stdlib only, `--help` for options).
- `scripts/test_readme_blocks.py`: tests, run with `python3 -m unittest` from `scripts/`.
- `examples/requests.md`: a real run on the README of psf/requests.
