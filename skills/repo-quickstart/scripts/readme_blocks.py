#!/usr/bin/env python3
"""List every fenced code block in a README, verbatim, with its location.

Stdlib only. The point is to copy code from the README without retyping it:
each block is emitted byte for byte (minus the fences), with its start and end
line, the language tag, the nearest heading above it, and hints about whether
it looks like an install command or a usage example.

Usage:
  python3 readme_blocks.py README.md
  python3 readme_blocks.py https://raw.githubusercontent.com/OWNER/REPO/HEAD/README.md
  python3 readme_blocks.py README.md --format md
  python3 readme_blocks.py README.md --block 2      # print block 2 only, raw

Only fenced blocks (``` or ~~~) are read. Indented code and code inside HTML
<pre> tags are reported as a warning so you can check them by hand.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request

FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})\s*([^`\s]*)?.*$")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
SETEXT_RE = re.compile(r"^ {0,3}(=+|-+)\s*$")

INSTALL_RE = re.compile(
    r"\b(?:npm (?:i|install|add)|pnpm (?:add|install|i)|yarn (?:add|global add)|bun (?:add|install)|"
    r"npx |pip3? install|pipx install|uv (?:add|pip install|tool install)|poetry add|conda install|"
    r"go (?:get|install)|cargo (?:add|install)|gem install|bundle add|composer require|"
    r"brew install|apt(?:-get)? install|dnf install|choco install|winget install|scoop install|"
    r"docker (?:pull|run)|helm install|dotnet add package|"
    r"curl [^\n|]*\|\s*(?:sh|bash)|go mod download)", re.I)
PROMPT_RE = re.compile(r"^\s*(?:\$|>>>|PS>|C:\\>)\s", re.M)
SHELL_PROMPT_RE = re.compile(r"^\s*(?:\$|PS>|C:\\>)\s", re.M)
SHELL_LANGS = {"sh", "bash", "shell", "console", "zsh", "shell-session", "powershell", "ps1", "cmd", "bat", "fish"}


def read_source(src: str) -> str:
    if re.match(r"^https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": "readme-blocks/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", "replace")
    with open(src, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def parse(text: str) -> tuple[list[dict], list[str]]:
    lines = text.splitlines()
    blocks, warnings = [], []
    heading = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        h = HEADING_RE.match(line)
        if h:
            heading = h.group(2)
        elif i > 0 and SETEXT_RE.match(line) and lines[i - 1].strip() and not FENCE_RE.match(lines[i - 1]):
            heading = lines[i - 1].strip()
        if re.match(r"(?i)^\s*<pre\b", line):
            warnings.append(f"line {i + 1}: <pre> block not parsed, check by hand")
        m = FENCE_RE.match(line)
        if not m:
            i += 1
            continue
        indent, fence, lang = len(m.group(1)), m.group(2), (m.group(3) or "").lower()
        if fence[0] == "`" and "`" in line[indent + len(fence):]:
            i += 1  # not a fence: backticks in the info string
            continue
        body = []
        j = i + 1
        closed = False
        while j < len(lines):
            close = re.match(rf"^ {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}\s*$", lines[j])
            if close:
                closed = True
                break
            # CommonMark: strip up to the opening fence's indentation from content lines
            content = lines[j]
            strip = min(indent, len(content) - len(content.lstrip(" ")))
            body.append(content[strip:])
            j += 1
        code = "\n".join(body)
        blocks.append({
            "index": len(blocks) + 1,
            "start_line": i + 1,
            "end_line": j + 1 if closed else len(lines),
            "lang": lang,
            "heading": heading,
            "code": code,
            "looks_like_install": bool(INSTALL_RE.search(code)),
            "shell": lang in SHELL_LANGS or bool(SHELL_PROMPT_RE.search(code)),
            "has_prompts": bool(PROMPT_RE.search(code)),
            "closed": closed,
        })
        if not closed:
            warnings.append(f"line {i + 1}: code fence never closed")
        i = j + 1
    if re.search(r"(?m)^(?: {4}|\t)\S", text) and not blocks:
        warnings.append("README seems to use indented code blocks; they are not listed")
    return blocks, warnings


def render_md(src: str, blocks: list[dict], warnings: list[str]) -> str:
    out = [f"Source: {src}", f"Blocks: {len(blocks)}", ""]
    for b in blocks:
        tags = [t for t, on in (("install", b["looks_like_install"]), ("shell", b["shell"]),
                                ("prompts", b["has_prompts"])) if on]
        out.append(f"### Block {b['index']}: lines {b['start_line']}-{b['end_line']}, "
                   f"lang={b['lang'] or 'none'}, under \"{b['heading']}\""
                   + (f" [{', '.join(tags)}]" if tags else ""))
        fence = "````" if "```" in b["code"] else "```"
        out += [fence + b["lang"], b["code"], fence, ""]
    out += [f"warning: {w}" for w in warnings]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="List fenced code blocks in a README, verbatim.")
    ap.add_argument("source", help="README path or raw URL")
    ap.add_argument("--format", choices=["json", "md"], default="json")
    ap.add_argument("--block", type=int, help="print only this block's code, raw")
    args = ap.parse_args(argv)
    try:
        text = read_source(args.source)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not read {args.source}: {exc}", file=sys.stderr)
        return 2
    blocks, warnings = parse(text)
    if args.block is not None:
        if not 1 <= args.block <= len(blocks):
            print(f"error: block {args.block} does not exist (found {len(blocks)})", file=sys.stderr)
            return 1
        sys.stdout.write(blocks[args.block - 1]["code"] + "\n")
        return 0
    if args.format == "md":
        sys.stdout.write(render_md(args.source, blocks, warnings))
    else:
        json.dump({"source": args.source, "blocks": blocks, "warnings": warnings}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
