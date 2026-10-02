#!/usr/bin/env python3
"""Inventory what a repository depends on, including runtimes, images and CI.

Stdlib only. Walks the repository (skipping node_modules, .git, vendor and
build output) and reads the manifests it knows. Every entry keeps the file and
line it came from so findings can be traced back.

Usage:
  python3 list_deps.py [REPO] [--format json|md] [--npm-deprecated]

--npm-deprecated asks the npm registry (registry.npmjs.org) whether the exact
version locked in package-lock.json is marked deprecated by its publisher.
That flag is the publisher's own statement, so it can be cited directly.

Entry kinds: package, runtime, image, ci-action, ci-runner.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    tomllib = None

SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", "out", ".next",
             "__pycache__", ".venv", "venv", "target", "coverage", ".turbo"}


def entry(kind, ecosystem, name, spec, path, line=None, **extra):
    e = {"kind": kind, "ecosystem": ecosystem, "name": name, "spec": spec,
         "file": path, "line": line}
    e.update(extra)
    return e


def line_of(text: str, needle: str) -> int | None:
    for no, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return no
    return None


def parse_package_json(text, path, lock=None):
    data = json.loads(text)
    out = []
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        for name, spec in (data.get(section) or {}).items():
            e = entry("package", "npm", name, spec, path, line_of(text, f'"{name}"'), section=section)
            if lock and name in lock:
                e["locked"] = lock[name]
            out.append(e)
    for name, spec in (data.get("engines") or {}).items():
        out.append(entry("runtime", "npm-engines", name, spec, path, line_of(text, f'"{name}"')))
    if data.get("packageManager"):
        pm = data["packageManager"]
        name, _, ver = pm.partition("@")
        out.append(entry("runtime", "packageManager", name, ver, path, line_of(text, "packageManager")))
    return out


def read_package_lock(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    versions = {}
    for key, meta in (data.get("packages") or {}).items():
        if key.startswith("node_modules/") and key.count("node_modules/") == 1:
            versions[key[len("node_modules/"):]] = meta.get("version")
    for name, meta in (data.get("dependencies") or {}).items():  # lockfile v1
        versions.setdefault(name, meta.get("version"))
    return versions


REQ_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*([^;#]*)")


def parse_requirements(text, path):
    out = []
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("#", "-", "git+", "http")):
            continue
        m = REQ_RE.match(line)
        if m:
            out.append(entry("package", "pypi", m.group(1), m.group(3).strip(), path, no))
    return out


def parse_pyproject(text, path):
    if tomllib is None:
        return [entry("package", "pypi", "(pyproject.toml not parsed: needs Python 3.11+)", "", path)]
    data = tomllib.loads(text)
    out = []
    project = data.get("project") or {}
    if project.get("requires-python"):
        out.append(entry("runtime", "python", "python", project["requires-python"], path,
                         line_of(text, "requires-python")))
    for dep in project.get("dependencies") or []:
        m = REQ_RE.match(dep)
        if m:
            out.append(entry("package", "pypi", m.group(1), m.group(3).strip(), path, line_of(text, dep)))
    poetry = ((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {}
    for name, spec in poetry.items():
        spec = spec if isinstance(spec, str) else (spec.get("version", "") if isinstance(spec, dict) else "")
        kind = "runtime" if name == "python" else "package"
        out.append(entry(kind, "pypi" if kind == "package" else "python", name, spec, path,
                         line_of(text, name)))
    return out


def parse_go_mod(text, path):
    out = []
    in_block = False
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.split("//")[0].strip()
        if line.startswith("go "):
            out.append(entry("runtime", "go", "go", line[3:].strip(), path, no))
        elif line.startswith("toolchain "):
            out.append(entry("runtime", "go", "toolchain", line[10:].strip(), path, no))
        elif line.startswith("require ("):
            in_block = True
        elif in_block and line == ")":
            in_block = False
        elif in_block and line:
            parts = line.split()
            if len(parts) >= 2:
                out.append(entry("package", "go", parts[0], parts[1], path, no,
                                 indirect="// indirect" in raw))
        elif line.startswith("require "):
            parts = line.split()
            if len(parts) >= 3:
                out.append(entry("package", "go", parts[1], parts[2], path, no))
    return out


GEM_RE = re.compile(r"""^\s*gem\s+['"]([^'"]+)['"](?:\s*,\s*['"]([^'"]+)['"])?""")
RUBY_RE = re.compile(r"""^\s*ruby\s+['"]([^'"]+)['"]""")


def parse_gemfile(text, path):
    out = []
    for no, line in enumerate(text.splitlines(), 1):
        m = GEM_RE.match(line)
        if m:
            out.append(entry("package", "rubygems", m.group(1), m.group(2) or "", path, no))
            continue
        m = RUBY_RE.match(line)
        if m:
            out.append(entry("runtime", "ruby", "ruby", m.group(1), path, no))
    return out


def parse_cargo(text, path):
    if tomllib is None:
        return []
    data = tomllib.loads(text)
    out = []
    pkg = data.get("package") or {}
    if pkg.get("rust-version"):
        out.append(entry("runtime", "rust", "rust", pkg["rust-version"], path, line_of(text, "rust-version")))
    for section in ("dependencies", "dev-dependencies", "build-dependencies"):
        for name, spec in (data.get(section) or {}).items():
            spec = spec if isinstance(spec, str) else (spec.get("version", "") if isinstance(spec, dict) else "")
            out.append(entry("package", "crates", name, spec, path, line_of(text, name), section=section))
    return out


def parse_composer(text, path):
    data = json.loads(text)
    out = []
    for section in ("require", "require-dev"):
        for name, spec in (data.get(section) or {}).items():
            kind = "runtime" if name == "php" or name.startswith("ext-") else "package"
            out.append(entry(kind, "packagist", name, spec, path, line_of(text, f'"{name}"'), section=section))
    return out


def parse_version_file(text, path):
    base = os.path.basename(path)
    runtime = {".nvmrc": "node", ".node-version": "node", ".python-version": "python",
               ".ruby-version": "ruby", "runtime.txt": "runtime"}[base]
    first = next((l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")), "")
    return [entry("runtime", runtime, runtime, first, path, 1)] if first else []


def parse_tool_versions(text, path):
    out = []
    for no, line in enumerate(text.splitlines(), 1):
        parts = line.split("#")[0].split()
        if len(parts) >= 2:
            out.append(entry("runtime", "asdf", parts[0], parts[1], path, no))
    return out


FROM_RE = re.compile(r"^\s*FROM\s+(?:--platform=\S+\s+)?(\S+)", re.I)


def parse_dockerfile(text, path):
    out = []
    for no, line in enumerate(text.splitlines(), 1):
        m = FROM_RE.match(line)
        if m and not m.group(1).startswith("$"):
            image = m.group(1)
            name, _, tag = image.partition(":") if "@" not in image else (image, "", "")
            out.append(entry("image", "docker", name, tag or "latest", path, no))
    return out


USES_RE = re.compile(r"^\s*-?\s*uses:\s*['\"]?([^'\"\s#]+)")
RUNS_ON_RE = re.compile(r"^\s*runs-on:\s*['\"]?([\w.-]+)")


def parse_workflow(text, path):
    out = []
    for no, line in enumerate(text.splitlines(), 1):
        m = USES_RE.match(line)
        if m and not m.group(1).startswith("./"):
            name, _, ref = m.group(1).partition("@")
            out.append(entry("ci-action", "github-actions", name, ref, path, no))
            continue
        m = RUNS_ON_RE.match(line)
        if m and not m.group(1).startswith("$"):
            out.append(entry("ci-runner", "github-actions", m.group(1), "", path, no))
    return out


def classify(rel):
    base = os.path.basename(rel)
    parts = rel.replace(os.sep, "/").split("/")
    if base == "package.json":
        return "package.json"
    if re.fullmatch(r"requirements.*\.txt", base):
        return "requirements"
    if base in ("pyproject.toml", "go.mod", "Gemfile", "Cargo.toml", "composer.json", ".tool-versions"):
        return base
    if base in (".nvmrc", ".node-version", ".python-version", ".ruby-version", "runtime.txt"):
        return "version-file"
    if base == "Dockerfile" or base.startswith("Dockerfile.") or base.endswith(".Dockerfile"):
        return "Dockerfile"
    if len(parts) >= 3 and parts[-3] == ".github" and parts[-2] == "workflows" and base.endswith((".yml", ".yaml")):
        return "workflow"
    return None


def scan(repo):
    results, errors = [], []
    for root, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, repo)
            kind = classify(rel)
            if not kind:
                continue
            try:
                with open(full, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                if kind == "package.json":
                    lock_path = os.path.join(root, "package-lock.json")
                    lock = read_package_lock(lock_path) if os.path.exists(lock_path) else None
                    results += parse_package_json(text, rel, lock)
                elif kind == "requirements":
                    results += parse_requirements(text, rel)
                elif kind == "pyproject.toml":
                    results += parse_pyproject(text, rel)
                elif kind == "go.mod":
                    results += parse_go_mod(text, rel)
                elif kind == "Gemfile":
                    results += parse_gemfile(text, rel)
                elif kind == "Cargo.toml":
                    results += parse_cargo(text, rel)
                elif kind == "composer.json":
                    results += parse_composer(text, rel)
                elif kind == ".tool-versions":
                    results += parse_tool_versions(text, rel)
                elif kind == "version-file":
                    results += parse_version_file(text, rel)
                elif kind == "Dockerfile":
                    results += parse_dockerfile(text, rel)
                elif kind == "workflow":
                    results += parse_workflow(text, rel)
            except Exception as exc:  # noqa: BLE001 - keep scanning, report the file
                errors.append({"file": rel, "error": str(exc)})
    return results, errors


def npm_deprecated(name, version, timeout=15):
    url = "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@/") + "/" + urllib.parse.quote(version)
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "list-deps/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    return data.get("deprecated"), url


def render_md(results, errors):
    rows = ["| kind | ecosystem | name | spec | locked | where | npm deprecated |",
            "| --- | --- | --- | --- | --- | --- | --- |"]
    for e in results:
        where = f"{e['file']}:{e['line']}" if e.get("line") else e["file"]
        dep = e.get("npm_deprecated") or ""
        rows.append(f"| {e['kind']} | {e['ecosystem']} | {e['name']} | {e['spec']} | "
                    f"{e.get('locked') or ''} | {where} | {dep.replace('|', '/')} |")
    if errors:
        rows += ["", "Files that could not be parsed:"] + [f"- {x['file']}: {x['error']}" for x in errors]
    return "\n".join(rows) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Inventory dependencies, runtimes, images and CI actions.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--format", choices=["json", "md"], default="json")
    ap.add_argument("--npm-deprecated", action="store_true",
                    help="query registry.npmjs.org for the deprecated flag of locked npm versions")
    args = ap.parse_args(argv)

    results, errors = scan(args.repo)
    if args.npm_deprecated:
        for e in results:
            if e["ecosystem"] == "npm" and e.get("locked"):
                try:
                    msg, url = npm_deprecated(e["name"], e["locked"])
                    if msg:
                        e["npm_deprecated"] = msg
                        e["npm_source"] = url
                except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                    errors.append({"file": e["file"], "error": f"npm lookup failed for {e['name']}: {exc}"})

    if args.format == "md":
        sys.stdout.write(render_md(results, errors))
    else:
        json.dump({"repo": os.path.abspath(args.repo), "entries": results, "errors": errors}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
