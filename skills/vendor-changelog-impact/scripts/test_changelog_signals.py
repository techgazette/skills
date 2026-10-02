import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import changelog_signals as cs  # noqa: E402

CHANGELOG = """# Changelog
## 2.0.0
- Breaking: `client.fetchAll()` was removed. Use `client.list()`.
- Added dark mode.
## 1.9.0
- The `LEGACY_AUTH` flag is deprecated and will be removed on 2027-01-15.
- Fixed a typo.
"""


class SignalTests(unittest.TestCase):
    def test_finds_only_signal_lines(self):
        sigs = cs.find_signals(CHANGELOG)
        self.assertEqual([s["line"] for s in sigs], [3, 6])
        self.assertIn("breaking", sigs[0]["kinds"])
        self.assertIn("removal", sigs[0]["kinds"])
        self.assertIn("deprecation", sigs[1]["kinds"])

    def test_heading_and_dates(self):
        sigs = cs.find_signals(CHANGELOG)
        self.assertEqual(sigs[0]["heading"], "2.0.0")
        self.assertEqual(sigs[1]["heading"], "1.9.0")
        self.assertEqual(sigs[1]["dates"], ["2027-01-15"])

    def test_quote_is_verbatim(self):
        sigs = cs.find_signals(CHANGELOG)
        self.assertEqual(sigs[1]["quote"], CHANGELOG.splitlines()[5].strip())

    def test_identifiers(self):
        ids = cs.identifiers("Breaking: `client.fetchAll()` was removed. Use `client.list()`.")
        self.assertIn("client.fetchAll", ids)
        self.assertIn("client.list", ids)
        self.assertIn("LEGACY_AUTH", cs.identifiers("The LEGACY_AUTH flag is deprecated"))
        self.assertIn("/v1/users", cs.identifiers("GET /v1/users is sunset"))

    def test_dates_in_several_formats(self):
        line = "Removed on March 31, 2027, 1 April 2027 and in Q3 2027"
        self.assertEqual([m.group(0) for m in cs.DATE_RE.finditer(line)],
                         ["March 31, 2027", "1 April 2027", "Q3 2027"])

    def test_repo_search_skips_node_modules(self):
        with tempfile.TemporaryDirectory() as repo:
            os.makedirs(os.path.join(repo, "src"))
            os.makedirs(os.path.join(repo, "node_modules", "x"))
            with open(os.path.join(repo, "src", "a.ts"), "w") as fh:
                fh.write("const x = 1;\nclient.fetchAll();\n")
            with open(os.path.join(repo, "node_modules", "x", "b.js"), "w") as fh:
                fh.write("client.fetchAll();\n")
            hits = cs.search_repo(repo, ["client.fetchAll"])
            self.assertEqual(hits["client.fetchAll"], [os.path.join("src", "a.ts") + ":2"])

    def test_html_to_text_keeps_headings_and_code(self):
        text = cs.html_to_text("<h2>v3</h2><p>The <code>old()</code> call is deprecated.</p><script>x</script>")
        self.assertIn("## v3", text)
        self.assertIn("`old()`", text)
        self.assertNotIn("x\n", text + "\n")

    def test_example_fixture(self):
        here = os.path.dirname(__file__)
        ex = os.path.join(here, "..", "examples")
        with open(os.path.join(ex, "acme-changelog.md")) as fh:
            sigs = cs.find_signals(fh.read())
        ids = sorted({i for s in sigs for i in s["identifiers"]})
        hits = cs.search_repo(os.path.join(ex, "sample-repo"), ids)
        self.assertTrue(hits["Acme-Signature-V1"])
        self.assertTrue(hits["charges.create"])
        self.assertFalse(hits["/v1/customers/search"])


if __name__ == "__main__":
    unittest.main()
