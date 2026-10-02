---
name: deprecation-deadlines
description: Scans a repository's manifests (package.json, requirements.txt, pyproject.toml, go.mod, Gemfile, Cargo.toml, composer.json, runtime version files, Dockerfiles and GitHub Actions workflows) and produces a dated checklist of dependencies, runtimes, images and CI actions that have an announced end of life, deprecation or API shutdown, each citing the vendor's own page. Use when the user asks what is going end-of-life, what deadlines are coming for their stack, or wants a deprecation audit before planning work.
license: Apache-2.0
compatibility: Helper script needs Python 3.9+ (3.11+ to read TOML files), stdlib only. Looking up vendor pages and the optional npm check need network access.
metadata:
  author: The Tech Gazette
  homepage: https://techgazette.com.br
  version: "1.0"
---

# Deprecation deadlines

Build a dated checklist of what in this repository has an announced end of life,
with each date taken from the vendor's own page.

## When to use

- "What in our stack is going end-of-life?", "Any deadlines coming for our dependencies?"
- Planning a quarter, taking over a repository, or preparing an upgrade.

For one specific changelog the user already has, use `vendor-changelog-impact` instead.

## Steps

1. Inventory. From the repository root run:

   ```bash
   python3 scripts/list_deps.py . --format md --npm-deprecated
   ```

   This lists packages, runtimes (`engines`, `.nvmrc`, `requires-python`, `go`, `ruby`,
   `.tool-versions`), container base images, GitHub Actions and runners, each with its
   `file:line`. `--npm-deprecated` asks the npm registry whether the locked version is
   marked deprecated by its publisher; drop it when offline. Use `--format json` if you
   want to process the list further.
2. Pick what to look up. Prioritize, in this order: runtimes and base images, CI actions
   and runners, platform SDKs and cloud APIs, then major frameworks. Small utility
   libraries rarely announce end-of-life dates; do not spend lookups on them unless the
   registry flags them.
3. Find the vendor's own statement for each candidate. Acceptable sources, in order:
   - The project's official release or support policy page (for example the runtime's
     release schedule, the framework's "supported versions" page).
   - The vendor's changelog, blog or deprecation notice.
   - The package registry's deprecation flag set by the publisher.
   - The repository's own README or SECURITY.md support table.
   Aggregators and community trackers (endoflife.date, blog posts, forum answers) may
   point you to the right page, but never cite them as the source. Open the vendor page
   and quote it.
4. Match the version the repository actually runs. Use the lockfile or the pinned
   version, not the newest release. A range like `>=20` means the lowest allowed version
   is what to check, and say so.
5. Write the checklist (format below). Use today's date as the "as of" date and split
   items into: already past, within 90 days, later, and no announced date.

## Output format

```markdown
## Deprecation deadlines for <repo>, as of <YYYY-MM-DD>

### Already past
- [ ] <name> <version in use> (`file:line`): <what ended> on <date>.
      Source: "<exact quote or table row>" <vendor URL>
      Next step: <the vendor's named replacement or upgrade path, or "vendor names none">

### Within 90 days
- [ ] ...

### Later
- [ ] ...

### Checked, no announced date
- <name> <version>: <page checked>

### Not checked
- <name>: <why, for example "no official support policy found">
```

## Guardrails

- Every date needs a vendor URL and a verbatim quote or table row. No source, no date:
  move the item to "Checked, no announced date" or "Not checked".
- Do not infer end-of-life from age, from a newer major existing, or from popularity.
- Quote dates exactly as the vendor writes them. If a page gives only a month or quarter,
  keep that precision; do not invent a day.
- Distinguish kinds of deadline: end of security support, end of all support, API
  shutdown, registry deprecation flag. Say which one the vendor announced.
- If a vendor page has changed or contradicts another vendor page, show both quotes and
  flag the conflict instead of picking one.
- State the "as of" date. These facts expire.

## Files

- `scripts/list_deps.py`: inventory of manifests (stdlib only, `--help` for options).
- `scripts/test_list_deps.py`: tests, run with `python3 -m unittest` from `scripts/`.
- `examples/walkthrough.md`: a full run against `examples/sample-repo/` with real vendor sources.
