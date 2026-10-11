#!/usr/bin/env node
// Record The Tech Gazette's Skill of the week in this repository.
//
// Reads the site's public JSON (https://techgazette.com.br/skills/week.json),
// validates it strictly (it comes from our own domain, but is treated as
// untrusted), and for each skill writes weekly/<name>/README.md and
// weekly/<name>/entry.json, regenerates the "Skill of the week" table in
// README.md and appends to CHANGELOG.md. Weekly picks are other publishers'
// skills: they are linked, with credit and license, never copied. Nothing is
// written outside weekly/, README.md and CHANGELOG.md.
//
// Usage:
//   node scripts/weekly-skill.mjs [--url URL | --file PATH] [--commit] [--root DIR]
// With --commit, each changed skill becomes one git commit whose message is
// built from the JSON (buildCommitMessage); a week with no change makes none.
// Node 18+, no dependencies.

import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

export const DEFAULT_URL = "https://techgazette.com.br/skills/week.json";
export const MAX_BYTES = 256 * 1024;
export const MAX_SKILLS = 10;
export const NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
export const LICENSES = ["Apache-2.0", "MIT", "BSD-3-Clause", "BSD-2-Clause", "ISC", "CC-BY-4.0", "CC0-1.0", "Unlicense"];
const DATE = /^\d{4}-\d{2}-\d{2}$/;
const CONTROL = /[\u0000-\u0008\u000b-\u001f\u007f‪-‮⁦-⁩]/;
const START = "<!-- weekly:start -->";
const END = "<!-- weekly:end -->";

export class InputError extends Error {}
const fail = (msg) => { throw new InputError(msg); };

// ——— Validation ———

function str(v, where, max, { optional = false, multiline = false } = {}) {
  if (v === undefined && optional) return undefined;
  if (typeof v !== "string") fail(`${where}: expected a string`);
  const s = v.trim();
  if (!s) { if (optional) return undefined; fail(`${where}: empty`); }
  if (s.length > max) fail(`${where}: longer than ${max} characters`);
  if (CONTROL.test(s)) fail(`${where}: control characters`);
  if (!multiline && /[\r\n]/.test(s)) fail(`${where}: line breaks`);
  if (s.includes("```")) fail(`${where}: contains a code fence`);
  return s;
}

function url(v, where, { optional = false, host } = {}) {
  const s = str(v, where, 500, { optional });
  if (s === undefined) return undefined;
  let u;
  try { u = new URL(s); } catch { fail(`${where}: not a URL`); }
  if (u.protocol !== "https:") fail(`${where}: not https`);
  if (u.username || u.password) fail(`${where}: has credentials`);
  if (host && !host.includes(u.hostname)) fail(`${where}: host ${u.hostname} not allowed`);
  return u.toString();
}

function list(v, where, maxItems, maxLen, { optional = false } = {}) {
  if (v === undefined && optional) return undefined;
  if (!Array.isArray(v)) fail(`${where}: expected a list`);
  if (v.length > maxItems) fail(`${where}: more than ${maxItems} items`);
  const out = v.map((x, i) => str(x, `${where}[${i}]`, maxLen));
  if (!out.length && !optional) fail(`${where}: empty`);
  return out.length ? out : undefined;
}

const obj = (v, where, optional = false) => {
  if (v === undefined && optional) return undefined;
  if (!v || typeof v !== "object" || Array.isArray(v)) fail(`${where}: expected an object`);
  return v;
};

/** A skill entry, validated and reduced to the fields we use. Throws InputError. */
export function validateSkill(raw, i) {
  const w = `skills[${i}]`;
  obj(raw, w);
  const name = str(raw.name, `${w}.name`, 64);
  if (!NAME.test(name)) fail(`${w}.name: not slug-safe (${JSON.stringify(name)})`);
  const date = str(raw.date, `${w}.date`, 10);
  if (!DATE.test(date) || Number.isNaN(Date.parse(`${date}T00:00:00Z`))) fail(`${w}.date: not YYYY-MM-DD`);
  const wtu = obj(raw.whenToUse, `${w}.whenToUse`, true) ?? {};
  const inst = obj(raw.install, `${w}.install`, true) ?? {};
  const readme = obj(inst.readme, `${w}.install.readme`, true);
  const copy = inst.copy === undefined ? [] : Array.isArray(inst.copy) ? inst.copy : fail(`${w}.install.copy: expected a list`);
  if (copy.length > 5) fail(`${w}.install.copy: more than 5 items`);
  const ex = obj(raw.example, `${w}.example`, true);
  const credit = obj(raw.credit, `${w}.credit`, true);
  const lic = obj(raw.license, `${w}.license`, true);
  const spdx = lic ? str(lic.spdx, `${w}.license.spdx`, 40) : undefined;
  if (spdx && !LICENSES.includes(spdx)) fail(`${w}.license.spdx: ${spdx} is not a license that permits redistribution`);
  const repo = credit ? str(credit.repo, `${w}.credit.repo`, 100) : undefined;
  if (repo && !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo)) fail(`${w}.credit.repo: not owner/name`);
  return {
    name,
    date,
    summary: str(raw.summary, `${w}.summary`, 400, { optional: true }),
    description: str(raw.description, `${w}.description`, 1024, { optional: true }),
    whenToUse: {
      trigger: str(wtu.trigger, `${w}.whenToUse.trigger`, 400, { optional: true }),
      useCases: list(wtu.useCases, `${w}.whenToUse.useCases`, 8, 200, { optional: true }),
      ask: str(wtu.ask, `${w}.whenToUse.ask`, 200, { optional: true }),
    },
    install: {
      readme: readme && {
        agent: str(readme.agent, `${w}.install.readme.agent`, 60),
        lines: list(readme.lines, `${w}.install.readme.lines`, 6, 200),
        firstUse: str(readme.firstUse, `${w}.install.readme.firstUse`, 300, { optional: true }),
        url: url(readme.url, `${w}.install.readme.url`, { host: ["github.com"] }),
      },
      copy: copy.map((c, j) => {
        obj(c, `${w}.install.copy[${j}]`);
        return {
          agent: str(c.agent, `${w}.install.copy[${j}].agent`, 60),
          docs: url(c.docs, `${w}.install.copy[${j}].docs`),
          lines: list(c.lines, `${w}.install.copy[${j}].lines`, 8, 200),
        };
      }),
    },
    example: ex && {
      request: list(ex.request, `${w}.example.request`, 5, 500),
      label: str(ex.label, `${w}.example.label`, 200, { optional: true }),
      output: list(ex.output, `${w}.example.output`, 30, 300, { optional: true }),
      from: str(ex.from, `${w}.example.from`, 60),
      section: str(ex.section, `${w}.example.section`, 200),
    },
    credit: credit && {
      vendor: str(credit.vendor, `${w}.credit.vendor`, 80),
      repo,
      source: url(credit.source, `${w}.credit.source`, { host: ["github.com"] }),
    },
    license: lic && { spdx, file: url(lic.file, `${w}.license.file`, { host: ["github.com"] }) },
    files: list(raw.files, `${w}.files`, 40, 200, { optional: true }),
    url: url(raw.url, `${w}.url`, { optional: true, host: ["techgazette.com.br"] }),
  };
}

/** The whole document, validated. Throws InputError. */
export function validateWeek(text) {
  if (typeof text !== "string") fail("input: not text");
  if (Buffer.byteLength(text) > MAX_BYTES) fail(`input: larger than ${MAX_BYTES} bytes`);
  let doc;
  try { doc = JSON.parse(text); } catch { fail("input: not JSON"); }
  obj(doc, "input");
  if (doc.version !== 1) fail("input: unsupported version");
  if (!Array.isArray(doc.skills)) fail("input.skills: expected a list");
  if (doc.skills.length > MAX_SKILLS) fail(`input.skills: more than ${MAX_SKILLS}`);
  const skills = doc.skills.map(validateSkill);
  const names = new Set();
  for (const s of skills) { if (names.has(s.name)) fail(`input.skills: ${s.name} twice`); names.add(s.name); }
  return { week: str(doc.week, "input.week", 10, { optional: true }), skills };
}

// ——— Required sections ———

/** The sections every commit and README must carry; missing ones are named. */
export function missingSections(s) {
  const missing = [];
  if (!s.summary) missing.push("summary");
  if (!s.whenToUse.trigger && !s.whenToUse.useCases && !s.whenToUse.ask) missing.push("whenToUse");
  if (!s.install.readme && !s.install.copy.length) missing.push("install");
  if (!s.credit) missing.push("credit");
  if (!s.license) missing.push("license");
  if (!s.url) missing.push("url");
  return missing;
}

function assertComplete(s) {
  const missing = missingSections(s);
  if (missing.length) fail(`${s.name}: missing required sections: ${missing.join(", ")}`);
}

// ——— Text ———

const oneLine = (s) => s.replace(/\.$/, "");
const fence = (lines) => ["```text", ...lines, "```"];

/** The sections shared by the folder README and the commit message (Markdown-ish, plain enough for git). */
export function sections(s) {
  assertComplete(s);
  const out = [];
  out.push("## What the skill does", "", s.summary);
  if (s.description && s.description !== s.summary) out.push("", `Its own description: "${s.description}"`);
  out.push("", "## When to use it", "");
  if (s.whenToUse.trigger) out.push(s.whenToUse.trigger);
  if (s.whenToUse.useCases) out.push(...(s.whenToUse.trigger ? [""] : []), ...s.whenToUse.useCases.map((u) => `- ${u}`));
  if (s.whenToUse.ask) out.push("", "Example request, from its own docs:", "", ...fence([s.whenToUse.ask]));
  out.push("", "## How to install it", "");
  if (s.install.readme) {
    out.push(`For ${s.install.readme.agent}, as the source's README (${s.install.readme.url}) says:`, "", ...fence(s.install.readme.lines));
    if (s.install.readme.firstUse) out.push("", `"${s.install.readme.firstUse}"`);
  }
  for (const c of s.install.copy) {
    out.push(...(out.at(-1) === "" ? [] : [""]), `Or copy the folder for ${c.agent} (${c.docs}):`, "", ...fence(c.lines));
  }
  if (s.example) {
    out.push("", "## Worked example", "", `From its ${s.example.from}, section "${s.example.section}"${s.example.label ? ` (${s.example.label})` : ""}. The request:`, "", ...fence(s.example.request));
    if (s.example.output) out.push("", "What the agent produces, as the docs show it:", "", ...fence(s.example.output));
  }
  out.push(
    "",
    "## Source, credit and license",
    "",
    `Made by ${s.credit.vendor}, in ${s.credit.repo}: ${s.credit.source}`,
    `License: ${s.license.spdx} (${s.license.file}). This repository links to the skill and does not copy it; install it from its source.`,
    "",
    "## On The Tech Gazette",
    "",
    `Skill of the week, ${s.date}: ${s.url}`,
  );
  return out;
}

export function folderReadme(s) {
  const lines = [`# ${s.name}`, "", `The Tech Gazette's Skill of the week for ${s.date}. Made by ${s.credit.vendor}; linked here, not copied.`, "", ...sections(s)];
  if (s.files) lines.push("", "## Files in the original skill", "", ...s.files.map((f) => `- ${f}`));
  return lines.join("\n") + "\n";
}

/** The commit message for one skill. Throws InputError when a required section is missing or no file changed. */
export function buildCommitMessage(s, changedFiles, { updated = false } = {}) {
  assertComplete(s);
  if (!changedFiles?.length) fail(`${s.name}: no files changed`);
  const subject = `${updated ? "Update" : "Add"} ${s.name}: ${oneLine(s.summary)}`;
  const subj = subject.length > 100 ? `${subject.slice(0, 97).trimEnd()}...` : subject;
  return [subj, "", ...sections(s), "", "## Files added or changed", "", ...changedFiles.map((f) => `- ${f}`), ""].join("\n");
}

// ——— Index and changelog ———

const cell = (s) => s.replace(/\|/g, "\\|");

export function indexTable(entries) {
  const rows = [...entries].sort((a, b) => b.date.localeCompare(a.date) || a.name.localeCompare(b.name));
  return [
    START,
    "## Skill of the week",
    "",
    "Every week The Tech Gazette picks one Agent Skill from a vendor's official repository. Each is",
    "linked from [weekly/](weekly/) with what it does, when to use it, how to install it, its credit and",
    "its license. The skills themselves stay in their publishers' repositories.",
    "",
    "| Date | Skill | Source | License | What it does |",
    "| --- | --- | --- | --- | --- |",
    ...rows.map((e) => `| ${e.date} | [${e.name}](weekly/${e.name}/README.md) | [${cell(e.credit.vendor)}](${e.credit.source}) | ${e.license.spdx} | ${cell(e.summary)} |`),
    END,
  ].join("\n");
}

export function withIndex(readme, table) {
  const a = readme.indexOf(START);
  const b = readme.indexOf(END);
  if (a !== -1 && b > a) return readme.slice(0, a) + table + readme.slice(b + END.length);
  const anchor = readme.indexOf("\n## Install");
  if (anchor === -1) return `${readme.trimEnd()}\n\n${table}\n`;
  return `${readme.slice(0, anchor)}\n${table}\n${readme.slice(anchor)}`;
}

export function withChangelog(changelog, s, updated) {
  const head = "# Changelog\n\nSkills of the week recorded here, newest first.\n";
  const body = changelog?.startsWith("# Changelog") ? changelog.slice(changelog.indexOf("\n## ") === -1 ? changelog.length : changelog.indexOf("\n## ") + 1) : "";
  const entry = `## ${s.date}\n\n- ${updated ? "Updated" : "Added"} [${s.name}](weekly/${s.name}/README.md) by ${s.credit.vendor} (${s.license.spdx}): ${s.summary}\n`;
  return `${head}\n${entry}${body ? `\n${body}` : ""}`;
}

// ——— Writing ———

function safePath(root, ...parts) {
  const base = resolve(root, "weekly");
  const p = resolve(base, ...parts);
  if (p !== base && !p.startsWith(base + sep)) fail(`refusing to write outside weekly/: ${p}`);
  return p;
}

const read = (p) => (existsSync(p) ? readFileSync(p, "utf8") : null);

function entries(root) {
  const dir = resolve(root, "weekly");
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((d) => NAME.test(d) && existsSync(join(dir, d, "entry.json")))
    .map((d) => validateSkill(JSON.parse(readFileSync(join(dir, d, "entry.json"), "utf8")), d));
}

/**
 * Apply one skill to the tree. Returns { changed: [paths], updated } and,
 * when nothing differs, changed: [] (and nothing is written).
 */
export function applySkill(root, s) {
  assertComplete(s);
  const folder = safePath(root, s.name);
  const entryPath = safePath(root, s.name, "entry.json");
  const readmePath = safePath(root, s.name, "README.md");
  const entryJson = JSON.stringify(s, null, 2) + "\n";
  const readme = folderReadme(s);
  const oldEntry = read(entryPath);
  const updated = oldEntry !== null;
  if (oldEntry === entryJson && read(readmePath) === readme) return { changed: [], updated };
  const changed = [];
  mkdirSync(folder, { recursive: true });
  if (oldEntry !== entryJson) { writeFileSync(entryPath, entryJson); changed.push(entryPath); }
  if (read(readmePath) !== readme) { writeFileSync(readmePath, readme); changed.push(readmePath); }
  const rootReadme = join(root, "README.md");
  const before = read(rootReadme) ?? "";
  const after = withIndex(before, indexTable(entries(root)));
  if (after !== before) { writeFileSync(rootReadme, after); changed.push(rootReadme); }
  const cl = join(root, "CHANGELOG.md");
  writeFileSync(cl, withChangelog(read(cl), s, updated));
  changed.push(cl);
  return { changed: changed.map((p) => relative(root, p).split(sep).join("/")), updated };
}

async function fetchWeek(u) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 20_000);
  try {
    const r = await fetch(u, { redirect: "error", signal: ctrl.signal, headers: { accept: "application/json" } });
    if (!r.ok) fail(`fetch ${u}: HTTP ${r.status}`);
    const len = Number(r.headers.get("content-length") ?? 0);
    if (len > MAX_BYTES) fail(`fetch ${u}: larger than ${MAX_BYTES} bytes`);
    const buf = Buffer.from(await r.arrayBuffer());
    if (buf.length > MAX_BYTES) fail(`fetch ${u}: larger than ${MAX_BYTES} bytes`);
    return buf.toString("utf8");
  } finally {
    clearTimeout(t);
  }
}

export async function main(argv) {
  const arg = (k) => { const i = argv.indexOf(k); return i === -1 ? undefined : argv[i + 1]; };
  const root = resolve(arg("--root") ?? join(dirname(fileURLToPath(import.meta.url)), ".."));
  const commit = argv.includes("--commit");
  const file = arg("--file");
  const source = file ?? url(arg("--url") ?? DEFAULT_URL, "--url", { host: ["techgazette.com.br"] });
  const text = file ? readFileSync(file, "utf8") : await fetchWeek(source);
  const week = validateWeek(text);
  // Every skill must be complete before anything is written.
  for (const s of week.skills) assertComplete(s);
  let made = 0;
  for (const s of week.skills) {
    const { changed, updated } = applySkill(root, s);
    if (!changed.length) { console.log(`${s.name}: unchanged`); continue; }
    const message = buildCommitMessage(s, changed, { updated });
    if (commit) {
      execFileSync("git", ["-C", root, "add", "--", ...changed], { stdio: "inherit" });
      execFileSync("git", ["-C", root, "commit", "-F", "-"], { input: message, stdio: ["pipe", "inherit", "inherit"] });
    } else {
      console.log(`--- ${s.name}: would commit ---\n${message}`);
    }
    made++;
  }
  console.log(`${week.skills.length} skill(s) in ${source}; ${made} ${commit ? "committed" : "changed"}.`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).catch((e) => {
    console.error(`weekly-skill: ${e instanceof InputError ? "" : "unexpected error: "}${e.message}`);
    process.exit(1);
  });
}
