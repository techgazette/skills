# Walkthrough: one week from four official engineering feeds

A real run on 2026-10-01 over the feeds in `feeds.txt` (in this folder), for the week of
2026-09-21 to 2026-09-27.

## Request

> Give me last week's brief from my feeds (feeds.txt). Titles and links are enough.

## Step 3: command

```bash
python3 ../scripts/brief.py feeds.txt --since 2026-09-21 --until 2026-09-27
```

## Step 4: review

The GitHub Changelog feed returned only its 10 most recent items, all dated 2026-10-01,
so it cannot show the week asked for. The script says so instead of reporting "no
news". The fix is to read https://github.blog/changelog/ for that week and add the
items with their own links, or to tell the user the section is incomplete.

## Output, as delivered

```markdown
# Weekly brief: 2026-09-21 to 2026-09-27

Chronological (oldest first), grouped by source in the order given. No ranking.

## GitHub Changelog
No items found; see the coverage note below.
(Partial coverage: this feed only goes back to 2026-10-01. Earlier items in the period may be missing; check the source page.)

## Node.js Blog
- 2026-09-22: [Node.js 26.10.0 (Current)](https://nodejs.org/en/blog/release/v26.10.0)
- 2026-09-23: [Node.js 22.23.3 (LTS)](https://nodejs.org/en/blog/release/v22.23.3)

## Python Insider
- 2026-09-23: [The Python documentation is now available in Persian](https://blog.python.org/2026/09/the-python-documentation-is-now-available-in-persian/)
- 2026-09-26: [The Python documentation is now available in German](https://blog.python.org/2026/09/python-docs-in-german/)

## Kubernetes Blog
- 2026-09-21: [Kubernetes v1.37: Tracking When a PersistentVolumeClaim Was Last Used (Beta)](https://kubernetes.io/blog/2026/09/21/kubernetes-v1-37-pvc-last-used-time/)
- 2026-09-22: [Spotlight on SIG Apps](https://kubernetes.io/blog/2026/09/22/sig-apps-spotlight/)
```

Note to the user, sent with the brief: "GitHub Changelog: the feed only keeps its latest
items, so this week is not covered. I can add the week from the changelog page if you
want."
