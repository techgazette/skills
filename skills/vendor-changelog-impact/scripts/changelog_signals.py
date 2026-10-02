#!/usr/bin/env python3
"""Find impact signals in a vendor changelog and locate them in a repository.

Stdlib only. This script does NOT decide what affects the user. It produces
candidates: changelog lines that announce a deprecation, removal, breaking
change or deadline, the identifiers named on those lines, and where those
identifiers appear in the repository. The agent must read each candidate in
context before reporting it.

Usage:
  python3 changelog_signals.py --changelog CHANGELOG.md --repo /path/to/repo
  python3 changelog_signals.py --changelog https://example.com/changelog --repo .
  python3 changelog_signals.py --changelog notes.txt --repo . --format md

Output (JSON, default): {"source": ..., "signals": [{"line", "heading",
"quote", "kinds", "dates", "identifiers", "repo_hits": {id: [file:line]}}]}
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.request

SIGNAL_PATTERNS = {
    "deprecation": r"\bdeprecat\w*",
    "removal": r"\b(?:removed?|removing|removal|drop(?:ped|ping)?\s+support)\b",
    "breaking": r"\bbreaking\b|\bbackwards?[- ]incompatible\b",
    "end-of-life": r"\bend[- ]of[- ](?:life|support)\b|\bEOL\b|\bsunset\w*|\bretire[sd]?\b|\bshut\s*down\b|\bdecommission\w*",
    "no-longer": r"\bno longer\b|\bwill (?:stop|cease)\b|\bwill be (?:disabled|turned off|unavailable)\b",
    "action-required": r"\baction required\b|\bmust (?:upgrade|update|migrate|switch)\b|\bmigrat(?:e|ion) (?:to|by|before)\b",
}
SIGNAL_RE = {k: re.compile(v, re.I) for k, v in SIGNAL_PATTERNS.items()}

MONTHS = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"
    rf"|\b{MONTHS}\.? \d{{1,2}}(?:st|nd|rd|th)?,? \d{{4}}\b"
    rf"|\b\d{{1,2}} {MONTHS}\.? \d{{4}}\b"
    rf"|\b{MONTHS} \d{{4}}\b"
    r"|\bQ[1-4] \d{4}\b",
    re.I,
)

# Identifiers worth searching for: `code spans`, URL paths, dotted names,
# function calls, CONSTANT_CASE and long camelCase words.
IDENT_RES = [
    re.compile(r"`([^`\n]{2,80})`"),
    re.compile(r"(?<![\w/])(/v\d+[\w/{}.-]*)"),
    re.compile(r"\b([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)+)\(?"),
    re.compile(r"(?<![.\w])([A-Za-z_][\w]*)\(\)"),
    re.compile(r"\b([A-Z][A-Z0-9]*_[A-Z0-9_]+)\b"),
    re.compile(r"\b([a-z]+[A-Z][A-Za-z0-9]{3,})\b"),
]
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*\S)\s*$|^\s*(v?\d+\.\d+(?:\.\d+)?\b.*)$")

SKIP_DIRS = {".git", "node_modules", "dist", "build", "out", ".next", "vendor",
             "__pycache__", ".venv", "venv", "target", "coverage", ".turbo"}
TEXT_EXT = {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".py", ".go", ".rb",
            ".java", ".kt", ".cs", ".php", ".rs", ".swift", ".json", ".yaml",
            ".yml", ".toml", ".ini", ".cfg", ".env", ".tf", ".sh", ".sql",
            ".md", ".txt", ".lock", ".gradle", ".xml", ".vue", ".svelte"}
MAX_FILE_BYTES = 1_000_000
MAX_HITS = 5


def fetch(source: str) -> str:
    if re.match(r"^https?://", source):
        req = urllib.request.Request(source, headers={"User-Agent": "changelog-signals/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode(resp.headers.get_content_charset() or "utf-8", "replace")
        if "<html" in raw[:2000].lower() or "<body" in raw.lower():
            return html_to_text(raw)
        return raw
    with open(source, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", "", raw)
    raw = re.sub(r"(?i)<h([1-6])[^>]*>", lambda m: "\n" + "#" * int(m.group(1)) + " ", raw)
    raw = re.sub(r"(?i)<code[^>]*>(.*?)</code>", r"`\1`", raw)
    raw = re.sub(r"(?i)<(br|/p|/li|/h[1-6]|/div|/tr)[^>]*>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    text = html.unescape(raw)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def identifiers(line: str) -> list[str]:
    found: list[str] = []
    for rx in IDENT_RES:
        for m in rx.finditer(line):
            ident = m.group(1).strip().rstrip(".,;:()")
            if len(ident) < 3 or ident.lower().startswith(("http", "www.")):
                continue
            if re.fullmatch(r"v?\d+(\.\d+)*", ident):
                continue
            if ident not in found:
                found.append(ident)
    return found


def find_signals(text: str) -> list[dict]:
    signals = []
    heading = ""
    for no, line in enumerate(text.splitlines(), 1):
        h = HEADING_RE.match(line)
        if h and len(line) < 120:
            heading = (h.group(2) or h.group(3) or "").strip()
        kinds = [k for k, rx in SIGNAL_RE.items() if rx.search(line)]
        if not kinds:
            continue
        signals.append({
            "line": no,
            "heading": heading,
            "quote": line.strip(),
            "kinds": kinds,
            "dates": [m.group(0) for m in DATE_RE.finditer(line)],
            "identifiers": identifiers(line),
        })
    return signals


def iter_repo_files(repo: str):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = os.path.join(root, name)
            ext = os.path.splitext(name)[1].lower()
            if ext not in TEXT_EXT and name not in {"Dockerfile", "Gemfile", "Makefile"}:
                continue
            try:
                if os.path.getsize(path) > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield path


def search_repo(repo: str, idents: list[str]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {i: [] for i in idents}
    if not idents:
        return hits
    for path in iter_repo_files(repo):
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()
        except OSError:
            continue
        rel = os.path.relpath(path, repo)
        for no, line in enumerate(lines, 1):
            for ident in idents:
                if len(hits[ident]) < MAX_HITS and ident in line:
                    hits[ident].append(f"{rel}:{no}")
    return hits


def render_md(result: dict) -> str:
    out = [f"Source: {result['source']}", ""]
    for s in result["signals"]:
        out.append(f"- line {s['line']} [{', '.join(s['kinds'])}] under \"{s['heading']}\"")
        out.append(f"  > {s['quote']}")
        if s["dates"]:
            out.append(f"  dates: {', '.join(s['dates'])}")
        used = {k: v for k, v in s["repo_hits"].items() if v}
        if used:
            for ident, where in used.items():
                out.append(f"  repo uses `{ident}`: {', '.join(where)}")
        else:
            out.append("  repo hits: none found for the identifiers on this line")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--changelog", required=True, help="file path or http(s) URL")
    ap.add_argument("--repo", default=".", help="repository root to search")
    ap.add_argument("--format", choices=["json", "md"], default="json")
    ap.add_argument("--only-hits", action="store_true",
                    help="keep only signals whose identifiers appear in the repo")
    args = ap.parse_args(argv)

    try:
        text = fetch(args.changelog)
    except Exception as exc:  # noqa: BLE001 - report any fetch failure plainly
        print(f"error: could not read {args.changelog}: {exc}", file=sys.stderr)
        return 2

    signals = find_signals(text)
    all_idents = sorted({i for s in signals for i in s["identifiers"]})
    hits = search_repo(args.repo, all_idents)
    for s in signals:
        s["repo_hits"] = {i: hits.get(i, []) for i in s["identifiers"]}
    if args.only_hits:
        signals = [s for s in signals if any(s["repo_hits"].values())]

    result = {"source": args.changelog, "signals": signals}
    if args.format == "md":
        sys.stdout.write(render_md(result))
    else:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
