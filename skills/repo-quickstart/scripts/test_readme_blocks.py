import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import readme_blocks as rb  # noqa: E402

README = """Tool
====

Short intro with `inline code`.

## Installation

```console
$ npm install --save-dev tool
```

## Usage

~~~js
const tool = require("tool");
tool.run({ verbose: true });   // keep the spacing
~~~

  ```text
  indented fence content
    keeps relative indent
  ```

````md
```inner```
````
"""


class ParseTests(unittest.TestCase):
    def setUp(self):
        self.blocks, self.warnings = rb.parse(README)

    def test_counts_and_lines(self):
        self.assertEqual(len(self.blocks), 4)
        self.assertEqual((self.blocks[0]["start_line"], self.blocks[0]["end_line"]), (8, 10))

    def test_headings_atx_and_setext(self):
        self.assertEqual(self.blocks[0]["heading"], "Installation")
        self.assertEqual(self.blocks[1]["heading"], "Usage")
        blocks, _ = rb.parse("Title\n=====\n\n```\nx\n```\n")
        self.assertEqual(blocks[0]["heading"], "Title")

    def test_code_is_verbatim(self):
        self.assertEqual(self.blocks[0]["code"], "$ npm install --save-dev tool")
        self.assertEqual(self.blocks[1]["code"],
                         'const tool = require("tool");\ntool.run({ verbose: true });   // keep the spacing')
        self.assertEqual(self.blocks[2]["code"], "indented fence content\n  keeps relative indent")
        self.assertEqual(self.blocks[3]["code"], "```inner```")

    def test_hints(self):
        self.assertTrue(self.blocks[0]["looks_like_install"])
        self.assertTrue(self.blocks[0]["shell"])
        self.assertTrue(self.blocks[0]["has_prompts"])
        self.assertFalse(self.blocks[1]["looks_like_install"])
        self.assertFalse(self.blocks[1]["shell"])

    def test_python_repl_is_not_shell(self):
        blocks, _ = rb.parse("```python\n>>> import x\n# a comment\n```\n")
        self.assertTrue(blocks[0]["has_prompts"])
        self.assertFalse(blocks[0]["shell"])

    def test_unclosed_fence_warns(self):
        blocks, warnings = rb.parse("```sh\npip install x\n")
        self.assertFalse(blocks[0]["closed"])
        self.assertTrue(any("never closed" in w for w in warnings))

    def test_install_patterns(self):
        for cmd in ("pip install x", "go install example.com/x@latest", "cargo add serde",
                    "brew install x", "curl -fsSL https://x.sh | sh", "uv add x", "gem install x"):
            self.assertTrue(rb.INSTALL_RE.search(cmd), cmd)
        self.assertFalse(rb.INSTALL_RE.search("npm test"))

    def test_render_md_uses_longer_fence_when_needed(self):
        out = rb.render_md("README.md", self.blocks, self.warnings)
        self.assertIn("````md\n```inner```\n````", out)


if __name__ == "__main__":
    unittest.main()
