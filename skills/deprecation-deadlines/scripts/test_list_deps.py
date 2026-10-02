import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import list_deps as ld  # noqa: E402


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


class ParserTests(unittest.TestCase):
    def test_requirements(self):
        out = ld.parse_requirements("# c\nDjango==4.2.1\nrequests[socks]>=2.31 ; python_version>'3.8'\n-r base.txt\n", "r.txt")
        self.assertEqual([(e["name"], e["spec"], e["line"]) for e in out],
                         [("Django", "==4.2.1", 2), ("requests", ">=2.31", 3)])

    def test_go_mod(self):
        text = "module x\n\ngo 1.21\n\nrequire (\n\tgithub.com/a/b v1.2.3\n\tgolang.org/x/c v0.1.0 // indirect\n)\nrequire github.com/d/e v2.0.0\n"
        out = ld.parse_go_mod(text, "go.mod")
        self.assertEqual(out[0]["name"], "go")
        self.assertEqual(out[0]["spec"], "1.21")
        names = [e["name"] for e in out if e["kind"] == "package"]
        self.assertEqual(names, ["github.com/a/b", "golang.org/x/c", "github.com/d/e"])
        self.assertTrue(out[2]["indirect"])

    def test_gemfile(self):
        out = ld.parse_gemfile("source 'https://rubygems.org'\nruby '3.1.4'\ngem 'rails', '~> 7.0'\ngem \"pg\"\n", "Gemfile")
        self.assertEqual([(e["kind"], e["name"], e["spec"]) for e in out],
                         [("runtime", "ruby", "3.1.4"), ("package", "rails", "~> 7.0"), ("package", "pg", "")])

    def test_dockerfile_and_workflow(self):
        img = ld.parse_dockerfile("FROM --platform=linux/amd64 node:18-alpine AS build\nFROM $BASE\n", "Dockerfile")
        self.assertEqual([(e["name"], e["spec"]) for e in img], [("node", "18-alpine")])
        wf = ld.parse_workflow("jobs:\n  t:\n    runs-on: ubuntu-20.04\n    steps:\n      - uses: actions/cache@v3\n      - uses: ./local\n", "ci.yml")
        self.assertEqual([(e["kind"], e["name"], e["spec"]) for e in wf],
                         [("ci-runner", "ubuntu-20.04", ""), ("ci-action", "actions/cache", "v3")])

    def test_composer_marks_php_as_runtime(self):
        out = ld.parse_composer('{"require": {"php": "^8.1", "laravel/framework": "^10.0"}}', "composer.json")
        self.assertEqual([(e["kind"], e["name"]) for e in out],
                         [("runtime", "php"), ("package", "laravel/framework")])


class ScanTests(unittest.TestCase):
    def test_scan_uses_lockfile_and_skips_node_modules(self):
        with tempfile.TemporaryDirectory() as repo:
            write(repo, "package.json", '{"dependencies": {"left-pad": "^1.0.0"}, "engines": {"node": ">=18"}}')
            write(repo, "package-lock.json", '{"packages": {"node_modules/left-pad": {"version": "1.3.0"}}}')
            write(repo, "node_modules/x/package.json", '{"dependencies": {"ignored": "1"}}')
            write(repo, ".github/workflows/ci.yml", "    steps:\n      - uses: actions/checkout@v4\n")
            write(repo, "svc/.python-version", "3.9.18\n")
            entries, errors = ld.scan(repo)
            self.assertEqual(errors, [])
            names = {e["name"] for e in entries}
            self.assertNotIn("ignored", names)
            pad = next(e for e in entries if e["name"] == "left-pad")
            self.assertEqual(pad["locked"], "1.3.0")
            self.assertIn("actions/checkout", names)
            py = next(e for e in entries if e["ecosystem"] == "python")
            self.assertEqual((py["spec"], py["file"]), ("3.9.18", os.path.join("svc", ".python-version")))

    def test_bad_manifest_is_reported_not_fatal(self):
        with tempfile.TemporaryDirectory() as repo:
            write(repo, "package.json", "{not json")
            write(repo, "go.mod", "go 1.22\n")
            entries, errors = ld.scan(repo)
            self.assertEqual(len(errors), 1)
            self.assertEqual(entries[0]["name"], "go")

    def test_example_repo(self):
        ex = os.path.join(os.path.dirname(__file__), "..", "examples", "sample-repo")
        entries, errors = ld.scan(ex)
        self.assertEqual(errors, [])
        found = {(e["name"], e["spec"]) for e in entries}
        self.assertIn(("actions/upload-artifact", "v3"), found)
        self.assertIn(("node", "20"), found)


if __name__ == "__main__":
    unittest.main()
