#!/usr/bin/env python3
"""Build a chronological, per-source brief from RSS and Atom feeds.

Stdlib only. No ranking, no scoring, no cross-source merging: items are grouped
by source in the order the feeds were given, and sorted by date inside each
group. Every item keeps the link the feed published.

Feeds file: one feed per line, "URL" or "Name | URL". Local paths work too.
Lines starting with # are ignored.

Usage:
  python3 brief.py feeds.txt                      # last 7 days, Markdown
  python3 brief.py feeds.txt --since 2026-09-21 --until 2026-09-27
  python3 brief.py feeds.txt --days 14 --newest-first --format json
  python3 brief.py feeds.txt --with-summary       # include the feed's own summary text

Exit code 0 even when some feeds fail; failures are listed in the output.
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

ATOM = "{http://www.w3.org/2005/Atom}"
DC = "{http://purl.org/dc/elements/1.1/}"
RSS1 = "{http://purl.org/rss/1.0/}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}"
UA = "weekly-tech-brief/1.0 (+https://techgazette.com.br)"


def read_feeds_file(path: str) -> list[tuple[str | None, str]]:
    feeds = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                name, url = (x.strip() for x in line.split("|", 1))
                feeds.append((name or None, url))
            else:
                feeds.append((None, line))
    return feeds


def fetch(url: str, timeout: int = 20) -> bytes:
    if not re.match(r"^https?://", url):
        with open(url, "rb") as fh:
            return fh.read()
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/atom+xml, application/rss+xml, application/xml;q=0.9, */*;q=0.5"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_date(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        d = email.utils.parsedate_to_datetime(value)  # RFC 822, used by RSS 2.0
    except (TypeError, ValueError, IndexError):
        d = None
    if d is None:
        v = value.replace("Z", "+00:00")
        v = re.sub(r"(\.\d{6})\d+", r"\1", v)
        try:
            d = dt.datetime.fromisoformat(v)  # RFC 3339, used by Atom
        except ValueError:
            try:
                d = dt.datetime.strptime(value[:10], "%Y-%m-%d")
            except ValueError:
                return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def text_of(el) -> str:
    if el is None:
        return ""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def clean_summary(raw: str, limit: int = 280) -> str:
    raw = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<(br|/?p|/?div|/?li|/?ul|/?ol|/?h[1-6]|/?tr|/?td)\b[^>]*>", " ", raw)
    txt = html.unescape(re.sub(r"<[^>]+>", "", raw))
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(txt) > limit:
        cut = txt[:limit].rsplit(" ", 1)[0]
        txt = cut + " [...]"
    return txt


def parse_feed(data: bytes) -> tuple[str, str, list[dict]]:
    """Return (feed title, feed home link, items)."""
    root = ET.fromstring(data)
    items = []
    if root.tag == ATOM + "feed":
        title = text_of(root.find(ATOM + "title"))
        home = ""
        for link in root.findall(ATOM + "link"):
            if link.get("rel", "alternate") == "alternate":
                home = link.get("href", "")
                break
        for e in root.findall(ATOM + "entry"):
            link = ""
            for l in e.findall(ATOM + "link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
                    break
            date_raw = text_of(e.find(ATOM + "published")) or text_of(e.find(ATOM + "updated"))
            summary = e.find(ATOM + "summary")
            if summary is None:
                summary = e.find(ATOM + "content")
            items.append({"title": text_of(e.find(ATOM + "title")), "link": link,
                          "date_raw": date_raw, "summary_raw": text_of(summary)})
        return title, home, items

    channel = root.find("channel")
    if channel is not None:  # RSS 0.9x / 2.0
        title = text_of(channel.find("title"))
        home = text_of(channel.find("link"))
        for it in channel.findall("item"):
            link = text_of(it.find("link"))
            guid = it.find("guid")
            if not link and guid is not None and guid.get("isPermaLink", "true") == "true":
                link = text_of(guid)
            date_raw = text_of(it.find("pubDate")) or text_of(it.find(DC + "date"))
            summary = it.find("description")
            if summary is None:
                summary = it.find(CONTENT + "encoded")
            items.append({"title": text_of(it.find("title")), "link": link,
                          "date_raw": date_raw, "summary_raw": "" if summary is None else (summary.text or "")})
        return title, home, items

    if root.tag.endswith("RDF"):  # RSS 1.0
        ch = root.find(RSS1 + "channel")
        title = text_of(ch.find(RSS1 + "title")) if ch is not None else ""
        home = text_of(ch.find(RSS1 + "link")) if ch is not None else ""
        for it in root.findall(RSS1 + "item"):
            items.append({"title": text_of(it.find(RSS1 + "title")), "link": text_of(it.find(RSS1 + "link")),
                          "date_raw": text_of(it.find(DC + "date")),
                          "summary_raw": text_of(it.find(RSS1 + "description"))})
        return title, home, items

    raise ValueError(f"not an RSS or Atom document (root element {root.tag})")


def build(feeds, since: dt.datetime, until: dt.datetime, newest_first=False, with_summary=False, fetcher=fetch):
    sections, failures = [], []
    for name, url in feeds:
        try:
            ftitle, home, items = parse_feed(fetcher(url))
        except Exception as exc:  # noqa: BLE001 - one bad feed must not stop the brief
            failures.append({"source": name or url, "url": url, "error": str(exc)})
            continue
        kept, undated, seen, oldest = [], 0, set(), None
        for it in items:
            d = parse_date(it["date_raw"])
            if d is None:
                undated += 1
                continue
            oldest = d if oldest is None or d < oldest else oldest
            if not (since <= d < until):
                continue
            key = it["link"] or it["title"]
            if key in seen:
                continue
            seen.add(key)
            entry = {"title": it["title"] or "(untitled)", "link": it["link"], "date": d.isoformat()}
            if with_summary and it["summary_raw"]:
                entry["summary"] = clean_summary(it["summary_raw"])
            kept.append(entry)
        kept.sort(key=lambda x: x["date"], reverse=newest_first)
        sections.append({"source": name or ftitle or url, "feed": url, "home": home,
                         "items": kept, "undated_skipped": undated,
                         # The feed's oldest item is newer than the window start, so the
                         # feed may not reach back far enough and items may be missing.
                         # Only flagged for feeds with 5+ dated items, since small feeds
                         # usually contain their whole history.
                         "covers_from": oldest.isoformat() if oldest and oldest > since
                         and len(items) - undated >= 5 else None})
    return {"since": since.date().isoformat(), "until": (until - dt.timedelta(days=1)).date().isoformat(),
            "order": "newest first" if newest_first else "oldest first",
            "sections": sections, "failures": failures}


def render_md(brief: dict) -> str:
    out = [f"# Weekly brief: {brief['since']} to {brief['until']}", "",
           f"Chronological ({brief['order']}), grouped by source in the order given. No ranking.", ""]
    for s in brief["sections"]:
        out.append(f"## {s['source']}")
        if not s["items"]:
            out.append("No items found; see the coverage note below." if s["covers_from"]
                       else "No new items in this period.")
        for it in s["items"]:
            day = it["date"][:10]
            link = f"[{it['title']}]({it['link']})" if it["link"] else f"{it['title']} (no link in feed)"
            out.append(f"- {day}: {link}")
            if it.get("summary"):
                out.append(f"  Feed summary: {it['summary']}")
        if s["covers_from"]:
            out.append(f"(Partial coverage: this feed only goes back to {s['covers_from'][:10]}. "
                       "Earlier items in the period may be missing; check the source page.)")
        if s["undated_skipped"]:
            out.append(f"({s['undated_skipped']} item(s) without a date were skipped.)")
        out.append("")
    if brief["failures"]:
        out.append("## Feeds that could not be read")
        for f in brief["failures"]:
            out.append(f"- {f['source']} ({f['url']}): {f['error']}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Chronological, per-source brief from RSS/Atom feeds.")
    ap.add_argument("feeds_file")
    ap.add_argument("--since", help="YYYY-MM-DD, inclusive (UTC)")
    ap.add_argument("--until", help="YYYY-MM-DD, inclusive (UTC); default today")
    ap.add_argument("--days", type=int, default=7, help="window length when --since is not given")
    ap.add_argument("--newest-first", action="store_true")
    ap.add_argument("--with-summary", action="store_true", help="include the feed's own summary, trimmed")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    args = ap.parse_args(argv)

    utc = dt.timezone.utc
    until_day = dt.date.fromisoformat(args.until) if args.until else dt.datetime.now(utc).date()
    until = dt.datetime.combine(until_day + dt.timedelta(days=1), dt.time(), utc)
    since = (dt.datetime.combine(dt.date.fromisoformat(args.since), dt.time(), utc) if args.since
             else until - dt.timedelta(days=args.days))

    brief = build(read_feeds_file(args.feeds_file), since, until, args.newest_first, args.with_summary)
    if args.format == "json":
        json.dump(brief, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_md(brief))
    return 0


if __name__ == "__main__":
    sys.exit(main())
