import datetime as dt
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import brief  # noqa: E402

RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel><title>Example RSS</title><link>https://rss.example.com/</link>
<item><title>Later post</title><link>https://rss.example.com/2</link><pubDate>Thu, 24 Sep 2026 10:00:00 +0000</pubDate>
<description>&lt;p&gt;Second &lt;b&gt;post&lt;/b&gt;.&lt;/p&gt;</description></item>
<item><title>Earlier post</title><link>https://rss.example.com/1</link><pubDate>Mon, 21 Sep 2026 08:00:00 -0300</pubDate></item>
<item><title>Too old</title><link>https://rss.example.com/0</link><pubDate>Mon, 14 Sep 2026 08:00:00 +0000</pubDate></item>
<item><title>Undated</title><link>https://rss.example.com/x</link></item>
<item><title>Later post</title><link>https://rss.example.com/2</link><pubDate>Thu, 24 Sep 2026 10:00:00 +0000</pubDate></item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Example Atom</title>
<link rel="self" href="https://atom.example.com/feed"/><link href="https://atom.example.com/"/>
<entry><title>Atom entry</title><link rel="alternate" href="https://atom.example.com/a"/>
<published>2026-09-25T12:00:00Z</published><updated>2026-09-26T12:00:00Z</updated><summary>Short.</summary></entry>
</feed>"""

RDF = b"""<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel><title>Example RDF</title><link>https://rdf.example.com/</link></channel>
<item><title>RDF item</title><link>https://rdf.example.com/1</link><dc:date>2026-09-22T00:00:00+00:00</dc:date></item>
</rdf:RDF>"""

UTC = dt.timezone.utc
SINCE = dt.datetime(2026, 9, 21, tzinfo=UTC)
UNTIL = dt.datetime(2026, 9, 28, tzinfo=UTC)


def fake_fetch(url):
    return {"rss": RSS, "atom": ATOM, "rdf": RDF, "bad": b"<html>not a feed</html>"}[url]


class ParseTests(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(brief.parse_feed(RSS)[0], "Example RSS")
        t, home, items = brief.parse_feed(ATOM)
        self.assertEqual((t, home, items[0]["link"]), ("Example Atom", "https://atom.example.com/", "https://atom.example.com/a"))
        self.assertEqual(brief.parse_feed(RDF)[2][0]["title"], "RDF item")
        with self.assertRaises(ValueError):
            brief.parse_feed(b"<html><body/></html>")

    def test_dates(self):
        self.assertEqual(brief.parse_date("Mon, 21 Sep 2026 08:00:00 -0300").isoformat(), "2026-09-21T11:00:00+00:00")
        self.assertEqual(brief.parse_date("2026-09-25T12:00:00.1234567Z").date(), dt.date(2026, 9, 25))
        self.assertEqual(brief.parse_date("2026-09-25").tzinfo, UTC)
        self.assertIsNone(brief.parse_date("someday"))

    def test_summary_is_trimmed_and_marked(self):
        self.assertEqual(brief.clean_summary("<p>Hello <b>world</b></p>"), "Hello world")
        long = brief.clean_summary("word " * 100, limit=20)
        self.assertTrue(long.endswith("[...]"))


class BuildTests(unittest.TestCase):
    def build(self, **kw):
        feeds = [("Atom source", "atom"), (None, "rss"), ("Broken", "bad"), (None, "rdf")]
        return brief.build(feeds, SINCE, UNTIL, fetcher=fake_fetch, **kw)

    def test_grouped_in_given_order_no_ranking(self):
        b = self.build()
        self.assertEqual([s["source"] for s in b["sections"]], ["Atom source", "Example RSS", "Example RDF"])
        self.assertEqual(b["failures"][0]["source"], "Broken")

    def test_chronological_window_and_dedupe(self):
        rss = self.build()["sections"][1]
        self.assertEqual([i["title"] for i in rss["items"]], ["Earlier post", "Later post"])
        self.assertEqual(rss["undated_skipped"], 1)
        newest = self.build(newest_first=True)["sections"][1]
        self.assertEqual([i["title"] for i in newest["items"]], ["Later post", "Earlier post"])

    def test_partial_coverage_flag(self):
        b = self.build()
        self.assertIsNone(b["sections"][1]["covers_from"])  # RSS reaches back before the window
        self.assertIsNone(b["sections"][0]["covers_from"])  # one-item feed: assume full history
        entries = "".join(
            f'<entry><title>e{d}</title><link href="https://x.example/{d}"/><updated>2026-09-2{d}T00:00:00Z</updated></entry>'
            for d in range(3, 9))
        recent = f'<feed xmlns="http://www.w3.org/2005/Atom"><title>Busy</title>{entries}</feed>'.encode()
        busy = brief.build([(None, "busy")], SINCE, UNTIL, fetcher=lambda u: recent)
        self.assertEqual(busy["sections"][0]["covers_from"][:10], "2026-09-23")
        self.assertIn("Partial coverage", brief.render_md(busy))

    def test_markdown_links_every_item(self):
        md = brief.render_md(self.build(with_summary=True))
        self.assertIn("- 2026-09-21: [Earlier post](https://rss.example.com/1)", md)
        self.assertIn("Feed summary: Second post.", md)
        self.assertIn("## Feeds that could not be read", md)

    def test_feeds_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
            fh.write("# comment\nName | https://a.example/feed\nhttps://b.example/rss\n\n")
        try:
            self.assertEqual(brief.read_feeds_file(fh.name),
                             [("Name", "https://a.example/feed"), (None, "https://b.example/rss")])
        finally:
            os.remove(fh.name)


if __name__ == "__main__":
    unittest.main()
