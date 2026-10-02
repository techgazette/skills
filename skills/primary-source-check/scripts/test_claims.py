import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import claims  # noqa: E402


def values(text, kind=None):
    return [c["value"] for c in claims.extract(text) if kind is None or c["kind"] == kind]


class ExtractTests(unittest.TestCase):
    def test_numbers_units_currency(self):
        got = values("Latency fell 40% to 120 ms, the plan costs $20 and has 1,024 seats.", "number")
        self.assertEqual(got, ["40%", "120 ms", "$20", "1,024"])

    def test_versions_and_dates_win_over_numbers(self):
        cl = claims.extract("Node.js v20.11.1 shipped on 2024-01-23 and March 5, 2026.")
        kinds = {(c["kind"], c["value"]) for c in cl}
        self.assertIn(("version", "v20.11.1"), kinds)
        self.assertIn(("date", "2024-01-23"), kinds)
        self.assertIn(("date", "March 5, 2026"), kinds)
        self.assertNotIn(("number", "20"), kinds)

    def test_quotes_and_names(self):
        cl = claims.extract('The Linux Foundation said "we will not change the license terms".')
        self.assertIn(("quote", "we will not change the license terms"), {(c["kind"], c["value"]) for c in cl})
        self.assertIn("Linux Foundation", values('The Linux Foundation said "x".', "name"))
        self.assertIn("OpenAI", values("It was OpenAI that shipped it.", "name"))
        self.assertIn("GPT-5", values("It runs GPT-5 now.", "name"))

    def test_single_digits_skipped(self):
        self.assertEqual(values("Step 1 of the guide", "number"), [])


class MatchTests(unittest.TestCase):
    def test_exact_variant_and_missing(self):
        src = {"s": "The limit is 1024 characters. Released March 5, 2026. Usage grew 40 percent."}
        self.assertEqual(claims.find("1,024", "number", src)[0], "found-variant")
        self.assertEqual(claims.find("2026-03-05", "date", src)[0], "found-variant")
        self.assertEqual(claims.find("40%", "number", src)[0], "found-variant")
        self.assertEqual(claims.find("2,048", "number", src)[0], "not-found")
        self.assertEqual(claims.find("1024", "number", src)[0], "found")

    def test_no_partial_number_match(self):
        src = {"s": "Released in 2026 with version v1.25."}
        self.assertEqual(claims.find("20", "number", src)[0], "found")  # exact substring, flagged for review
        self.assertEqual(claims.find("v1.2", "version", {"s": "Version V1.25 only"})[0], "not-found")

    def test_date_variants(self):
        self.assertIn("2026-03-05", claims.date_variants("Mar. 5th, 2026"))
        self.assertIn("5 march 2026", claims.date_variants("2026-03-05"))
        self.assertEqual(claims.date_variants("sometime"), [])

    def test_html_is_stripped(self):
        path = os.path.join(os.path.dirname(__file__), "_tmp_src.html")
        with open(path, "w") as fh:
            fh.write("<html><body><p>Max <b>64</b> characters</p><script>var x=999</script></body></html>")
        try:
            text = claims.read(path)
            self.assertIn("64", text)
            self.assertNotIn("999", text)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
