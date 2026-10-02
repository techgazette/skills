---
name: weekly-tech-brief
description: Assembles a short weekly brief from RSS and Atom feeds the user chooses, with no algorithmic ranking - items are grouped by source in the user's order and listed chronologically, each linked to the original post, with feed failures and coverage gaps stated plainly. Use when the user asks for a weekly roundup, digest, newsletter draft or "what happened this week" from a list of feeds, blogs or changelogs they follow.
license: Apache-2.0
compatibility: Helper script needs Python 3.9+ (stdlib only) and network access to fetch feeds. Local feed files work offline.
metadata:
  author: The Tech Gazette
  homepage: https://techgazette.com.br
  version: "1.0"
---

# Weekly tech brief

A brief built only from the feeds the user picked: chronological, grouped by source,
every item linked. The reader decides what matters; the brief does not.

## When to use

- "Make me a weekly digest from these feeds", "What did these blogs publish this week?",
  "Draft this week's newsletter from my sources."

If the user has no feed list, ask for one or offer to find the official feed URLs for
sources they name. Do not pick sources for them.

## Steps

1. Get the feed list into a file, one per line, `Name | URL` or just `URL`, in the order
   the user wants sources to appear. If the user gives a site instead of a feed, look for
   its feed (a `<link rel="alternate" type="application/rss+xml">` in the page head, or
   `/feed`, `/rss`, `/atom.xml`, `/index.xml`) and confirm it is the site's own feed.
2. Pick the period. Default: the last 7 full days ending yesterday, in UTC. State it.
3. Run:

   ```bash
   python3 scripts/brief.py feeds.txt --since YYYY-MM-DD --until YYYY-MM-DD
   ```

   Options: `--days N` instead of `--since`, `--newest-first`, `--with-summary` to include
   the feed's own summary text (trimmed, marked with `[...]` when cut), `--format json`.
4. Review the output before handing it over:
   - Feeds that failed are listed at the end. Report them; do not fill them in from
     another source.
   - A "Partial coverage" note means the feed only holds recent items and does not reach
     the start of the period. Tell the user, and if they want, check the source's own
     archive page and add missing items with their real links and dates.
   - Items without a date were skipped and counted. Mention the count.
5. Optional one-line notes. Only if the user asks for more than titles: add one neutral
   line per item, written from that item's own text (open the link and read it). Do not
   add opinions, importance labels or "top stories".

## Output format

The script's Markdown is the format:

```markdown
# Weekly brief: <start> to <end>

Chronological (oldest first), grouped by source in the order given. No ranking.

## <Source name>
- <YYYY-MM-DD>: [<item title as published>](<item link>)

## Feeds that could not be read
- <source> (<url>): <error>
```

## Guardrails

- No ranking, scoring, filtering by "importance" or merging stories across sources. Keep
  the user's source order and chronological order inside each source.
- Titles exactly as the feed publishes them. Do not rewrite headlines.
- Every item links to the URL the feed gives. Never construct or guess a link.
- Do not summarize an item you have not opened. Feed summaries are labeled as such.
- Do not drop items because they look minor, and do not add items that are not in the
  feeds (or in the source's archive, when covering a partial-coverage gap).
- Say what is missing: failed feeds, partial coverage, skipped undated items.

## Files

- `scripts/brief.py`: fetches and formats feeds (RSS 2.0, RSS 1.0/RDF, Atom; stdlib only).
- `scripts/test_brief.py`: tests with inline fixture feeds, run with `python3 -m unittest` from `scripts/`.
- `examples/feeds.txt` and `examples/walkthrough.md`: a real run over four public feeds.
