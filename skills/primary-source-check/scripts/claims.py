#!/usr/bin/env python3
"""Extract checkable facts from a draft and look for each one in the sources.

Stdlib only. "Checkable" means the parts of a sentence that are easy to get
wrong and easy to verify: numbers (with units and currency), percentages,
versions, dates, quoted phrases and proper names. The script does exact and
lightly normalized text matching. It cannot tell whether a number that appears
in the source refers to the same thing as in the draft; that judgment is the
agent's job.

Usage:
  python3 claims.py extract draft.md
  python3 claims.py check draft.md source1.html https://vendor.example/post [--format md]

Statuses: found (verbatim), found-variant (same value written differently,
e.g. 1,024 vs 1024 or 2026-03-05 vs March 5, 2026), not-found.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.request

MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]
MON_RE = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"

PATTERNS = [
    ("date", re.compile(
        r"\b\d{4}-\d{2}-\d{2}\b"
        rf"|\b{MON_RE}\.? \d{{1,2}}(?:st|nd|rd|th)?,? \d{{4}}\b"
        rf"|\b\d{{1,2}} {MON_RE}\.? \d{{4}}\b"
        rf"|\b{MON_RE} \d{{4}}\b")),
    ("version", re.compile(r"\bv?\d+\.\d+(?:\.\d+)+(?:[-+][\w.]+)?\b|\bv\d+(?:\.\d+)?\b")),
    ("quote", re.compile(r"[\"“]([^\"”\n]{12,300})[\"”]")),
    ("number", re.compile(
        r"(?:(?:US)?\$|R\$|€|£)?\s?\d{1,3}(?:[,.  ]\d{3})+(?:\.\d+)?"
        r"(?:\s?(?:%|percent|million|billion|trillion|[kKMGTP]B|ms|s\b|x\b|tokens|users|requests))?"
        r"|(?:(?:US)?\$|R\$|€|£)?\s?\d+(?:\.\d+)?"
        r"(?:\s?(?:%|percent|million|billion|trillion|[kKMGTP]B|ms|s\b|x\b|tokens|users|requests))?")),
    ("name", re.compile(
        r"\b(?:[A-Z][a-z]*[A-Z0-9][\w-]*|[A-Z]{2,}[\w-]*\d[\w.-]*|[A-Z][\w-]+(?:\s+(?:[A-Z][\w-]+|\d[\w.]*))+)\b")),
]
STOP_NAMES = {"The", "This", "That", "These", "It", "In", "On", "At", "A", "An", "And", "But", "If"}


def read(src: str) -> str:
    if re.match(r"^https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": "claims-check/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode(resp.headers.get_content_charset() or "utf-8", "replace")
    else:
        with open(src, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    if re.search(r"(?i)<(html|body|p|div)\b", raw[:5000]):
        raw = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", raw)
        raw = re.sub(r"(?i)<(br|/p|/li|/h[1-6]|/div|/tr|/td|/th)[^>]*>", "\n", raw)
        raw = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return raw


def extract(text: str) -> list[dict]:
    claims, taken = [], []

    def overlaps(a, b):
        return any(not (b <= s or a >= e) for s, e in taken)

    for no, line in enumerate(text.splitlines(), 1):
        taken.clear()
        for kind, rx in PATTERNS:
            for m in rx.finditer(line):
                value = (m.group(1) if kind == "quote" else m.group(0)).strip()
                start, end = m.span()
                if kind != "quote" and overlaps(start, end):
                    continue
                if kind == "number" and (len(re.sub(r"\D", "", value)) < 2 and not re.search(r"[%$€£]|[a-z]", value)):
                    continue  # skip lone single digits like list markers
                if kind == "name":
                    words = value.split()
                    while words and words[0] in STOP_NAMES:
                        words.pop(0)
                    value = " ".join(words)
                    if not value or (len(words) == 1 and not re.search(r"[A-Z].*[A-Z0-9]", value)):
                        continue
                if kind != "quote":
                    taken.append((start, end))
                claims.append({"line": no, "kind": kind, "value": value, "context": line.strip()})
    return claims


def norm(text: str) -> str:
    text = text.lower().replace(" ", " ")
    text = re.sub(r"[‘’]", "'", text)
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"[‐-―]", "-", text)
    return re.sub(r"\s+", " ", text)


def date_variants(value: str) -> list[str]:
    d = None
    v = value.replace(",", "").replace(".", "")
    v = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", v)
    for fmt in ("%Y-%m-%d", "%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y"):
        try:
            d = dt.datetime.strptime(v, fmt).date()
            break
        except ValueError:
            continue
    if not d:
        return []
    month = MONTHS[d.month - 1]
    return [d.isoformat(), f"{month} {d.day}, {d.year}", f"{month} {d.day} {d.year}",
            f"{d.day} {month} {d.year}", f"{month[:3]} {d.day}, {d.year}", f"{d.day} {month[:3]} {d.year}"]


def number_variants(value: str) -> list[str]:
    v = norm(value).strip()
    out = {v}
    digits = re.sub(r"(?<=\d)[,  ](?=\d{3}\b)", "", v)
    out.add(digits)
    m = re.match(r"^([^\d]*)(\d+)(\.\d+)?(.*)$", digits)
    if m and len(m.group(2)) > 3:
        grouped = f"{int(m.group(2)):,}"
        out.add(m.group(1) + grouped + (m.group(3) or "") + m.group(4))
        out.add(m.group(1) + grouped.replace(",", ".") + (m.group(3) or "").replace(".", ",") + m.group(4))
    for x in list(out):
        out.add(x.replace("%", " percent").replace("  ", " "))
        out.add(x.replace(" percent", "%"))
        out.add(re.sub(r"\s+(?=%|[kmgtp]b\b)", "", x))
    return [x for x in out if x]


def find(value: str, kind: str, sources: dict[str, str]) -> tuple[str, list[dict]]:
    hits = []
    for name, text in sources.items():
        idx = text.find(value)
        if idx >= 0:
            hits.append({"source": name, "status": "found", "snippet": snippet(text, idx, len(value))})
    if hits:
        return "found", hits
    variants = {norm(value)}
    if kind == "date":
        variants.update(date_variants(value))
    if kind == "number":
        variants.update(number_variants(value))
    for name, text in sources.items():
        ntext = norm(text)
        for var in variants:
            idx = find_token(ntext, var)
            if idx >= 0:
                hits.append({"source": name, "status": "found-variant", "matched": var,
                             "snippet": snippet(ntext, idx, len(var))})
                break
    return ("found-variant" if hits else "not-found"), hits


def find_token(haystack: str, needle: str) -> int:
    # Do not let "20" match inside "2026" or "v1.2" inside "v1.25".
    rx = re.compile(r"(?<![\w.])" + re.escape(needle) + r"(?![\w]|\.\d)")
    m = rx.search(haystack)
    return m.start() if m else -1


def snippet(text: str, idx: int, length: int, pad: int = 70) -> str:
    s = text[max(0, idx - pad): idx + length + pad]
    return re.sub(r"\s+", " ", s).strip()


def render_md(results: list[dict]) -> str:
    out = ["| line | kind | claim | status | where |", "| --- | --- | --- | --- | --- |"]
    for r in results:
        where = "; ".join(f"{h['source']}: ...{h['snippet']}..." for h in r["hits"][:2]) or ""
        cell = lambda s: s.replace("|", "\\|")  # noqa: E731
        out.append(f"| {r['line']} | {r['kind']} | {cell(r['value'])} | {r['status']} | {cell(where)} |")
    missing = sum(1 for r in results if r["status"] == "not-found")
    out.append("")
    out.append(f"{len(results)} claims, {missing} not found in the sources.")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Extract checkable claims and look them up in sources.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("draft")
    c = sub.add_parser("check")
    c.add_argument("draft")
    c.add_argument("sources", nargs="+", help="files or http(s) URLs")
    for p in (e, c):
        p.add_argument("--format", choices=["json", "md"], default="json")
    args = ap.parse_args(argv)

    claims = extract(read(args.draft))
    if args.cmd == "extract":
        if args.format == "md":
            for cl in claims:
                print(f"- line {cl['line']} {cl['kind']}: {cl['value']}")
        else:
            json.dump(claims, sys.stdout, indent=2)
            sys.stdout.write("\n")
        return 0

    sources, failed = {}, []
    for src in args.sources:
        try:
            sources[src] = read(src)
        except Exception as exc:  # noqa: BLE001
            failed.append(f"{src}: {exc}")
    for f in failed:
        print(f"warning: could not read {f}", file=sys.stderr)
    if not sources:
        print("error: no source could be read", file=sys.stderr)
        return 2

    results = []
    for cl in claims:
        status, hits = find(cl["value"], cl["kind"], sources)
        results.append({**cl, "status": status, "hits": hits})
    if args.format == "md":
        sys.stdout.write(render_md(results))
    else:
        json.dump({"sources": list(sources), "unreadable": failed, "results": results}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    return 1 if any(r["status"] == "not-found" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
