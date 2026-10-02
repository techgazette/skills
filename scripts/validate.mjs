#!/usr/bin/env node
// Validate every skills/<name>/SKILL.md against the Agent Skills specification
// (https://agentskills.io/specification) plus the stricter rules documented for
// Claude API / claude.ai uploads, and a few repository conventions.
//
// Usage: node scripts/validate.mjs [repo-root]
// Exit code 0 when everything passes, 1 otherwise. Node 18+, no dependencies.

import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, resolve, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(process.argv[2] ?? join(dirname(fileURLToPath(import.meta.url)), ".."));
const skillsDir = join(root, "skills");

// Fields defined by the spec. Uploads to claude.ai and the Skills API reject any other key.
const ALLOWED_KEYS = new Set(["name", "description", "license", "compatibility", "metadata", "allowed-tools"]);
const NAME_MAX = 64;
const DESCRIPTION_MAX = 1024;
const COMPATIBILITY_MAX = 500;
const RESERVED_WORDS = ["anthropic", "claude"]; // platform.claude.com Agent Skills overview
const XML_TAG = /<\/?[A-Za-z][^>]*>/;
const EMOJI = /[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{FE0F}]/u;

const errors = [];
const warnings = [];
const err = (file, msg) => errors.push(`${relative(root, file)}: ${msg}`);
const warn = (file, msg) => warnings.push(`${relative(root, file)}: ${msg}`);

function unquote(raw, file, key) {
  const v = raw.trim();
  if (v.startsWith('"')) {
    if (!v.endsWith('"') || v.length < 2) err(file, `${key}: unterminated double-quoted string`);
    try { return JSON.parse(v); } catch { err(file, `${key}: invalid double-quoted string`); return v; }
  }
  if (v.startsWith("'")) {
    if (!v.endsWith("'") || v.length < 2) err(file, `${key}: unterminated single-quoted string`);
    return v.slice(1, -1).replace(/''/g, "'");
  }
  // Plain YAML scalars: reject the cases that change meaning or fail to parse.
  if (/: /.test(v) || / #/.test(v)) err(file, `${key}: plain value contains ": " or " #"; quote it`);
  if (/^[&*!|>%@`{[\]]/.test(v)) err(file, `${key}: plain value starts with a YAML indicator; quote it`);
  return v;
}

// Minimal frontmatter parser for the subset skills use: top-level scalars,
// block scalars (| and >), and one level of string-to-string mapping (metadata).
function parseFrontmatter(text, file) {
  const lines = text.split(/\r?\n/);
  if (lines[0] !== "---") { err(file, "first line must be '---' (frontmatter must start the file)"); return null; }
  const end = lines.indexOf("---", 1);
  if (end === -1) { err(file, "frontmatter has no closing '---'"); return null; }
  const fm = {};
  const seen = new Set();
  for (let i = 1; i < end; i++) {
    const line = lines[i];
    if (!line.trim() || line.trimStart().startsWith("#")) continue;
    const m = /^([A-Za-z0-9_-]+):(?:\s+(.*))?$/.exec(line);
    if (!m) { err(file, `cannot parse frontmatter line ${i + 1}: ${JSON.stringify(line)}`); continue; }
    const [, key, rest = ""] = m;
    if (seen.has(key)) err(file, `duplicate key '${key}'`);
    seen.add(key);
    if (rest === "" ) {
      const map = {};
      while (i + 1 < end && /^\s+\S/.test(lines[i + 1])) {
        const sub = /^\s+([A-Za-z0-9_.-]+):\s+(.*)$/.exec(lines[++i]);
        if (!sub) { err(file, `cannot parse nested line ${i + 1} under '${key}'`); continue; }
        map[sub[1]] = unquote(sub[2], file, `${key}.${sub[1]}`);
      }
      fm[key] = map;
    } else if (/^[|>][+-]?$/.test(rest)) {
      const body = [];
      while (i + 1 < end && (/^\s+/.test(lines[i + 1]) || lines[i + 1] === "")) body.push(lines[++i].trim());
      fm[key] = rest.startsWith(">") ? body.join(" ").replace(/\s+/g, " ").trim() : body.join("\n").trim();
    } else {
      fm[key] = unquote(rest, file, key);
    }
  }
  return { fm, bodyLines: lines.length - end - 1 };
}

function validateSkill(dir) {
  const name = dir.split(/[\\/]/).pop();
  const file = join(dir, "SKILL.md");
  if (!existsSync(file)) { err(dir, "missing SKILL.md"); return; }
  const text = readFileSync(file, "utf8");
  const parsed = parseFrontmatter(text, file);
  if (!parsed) return;
  const { fm, bodyLines } = parsed;

  for (const key of Object.keys(fm)) {
    if (!ALLOWED_KEYS.has(key)) err(file, `unknown frontmatter key '${key}' (allowed: ${[...ALLOWED_KEYS].join(", ")})`);
  }

  const n = fm.name;
  if (typeof n !== "string" || !n) err(file, "name is required");
  else {
    if (n.length > NAME_MAX) err(file, `name is ${n.length} characters (max ${NAME_MAX})`);
    if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(n)) err(file, "name must be lowercase a-z, 0-9 and single hyphens, not starting or ending with '-'");
    if (n !== name) err(file, `name '${n}' must match its folder '${name}'`);
    for (const w of RESERVED_WORDS) if (n.includes(w)) err(file, `name must not contain reserved word '${w}'`);
  }

  const d = fm.description;
  if (typeof d !== "string" || !d.trim()) err(file, "description is required and must be non-empty");
  else {
    if (d.length > DESCRIPTION_MAX) err(file, `description is ${d.length} characters (max ${DESCRIPTION_MAX})`);
    if (XML_TAG.test(d)) err(file, "description must not contain XML tags");
    if (!/\buse (it )?when\b/i.test(d)) warn(file, "description should say when to use the skill ('Use when ...')");
  }

  if (fm.compatibility !== undefined) {
    if (typeof fm.compatibility !== "string" || !fm.compatibility) err(file, "compatibility must be a non-empty string");
    else if (fm.compatibility.length > COMPATIBILITY_MAX) err(file, `compatibility is ${fm.compatibility.length} characters (max ${COMPATIBILITY_MAX})`);
  }
  if (fm.metadata !== undefined && (typeof fm.metadata !== "object" || Array.isArray(fm.metadata))) {
    err(file, "metadata must be a mapping of string keys to string values");
  }
  if (fm.license !== undefined && !fm.license) err(file, "license must not be empty");

  if (bodyLines > 500) warn(file, `body is ${bodyLines} lines; the spec recommends under 500`);

  // Repository conventions: an examples/ folder, and referenced files exist.
  const ex = join(dir, "examples");
  if (!existsSync(ex) || readdirSync(ex).length === 0) err(dir, "needs a non-empty examples/ folder");
  for (const m of text.matchAll(/`((?:scripts|examples|references|assets)\/[^`\s]+)`/g)) {
    if (!existsSync(join(dir, m[1]))) err(file, `references missing file ${m[1]}`);
  }
}

function walk(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    if ([".git", "node_modules", "__pycache__"].includes(entry)) continue;
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) walk(p, out); else out.push(p);
  }
  return out;
}

if (!existsSync(skillsDir)) {
  console.error(`no skills/ directory under ${root}`);
  process.exit(1);
}
const skills = readdirSync(skillsDir).filter((d) => statSync(join(skillsDir, d)).isDirectory()).sort();
for (const s of skills) validateSkill(join(skillsDir, s));

// The Claude Code plugin marketplace must list exactly the skills that exist.
const mp = join(root, ".claude-plugin", "marketplace.json");
if (existsSync(mp)) {
  try {
    const data = JSON.parse(readFileSync(mp, "utf8"));
    const listed = (data.plugins ?? []).flatMap((p) => p.skills ?? []).map((s) => s.replace(/^\.\//, "").replace(/\/$/, ""));
    for (const s of listed) if (!existsSync(join(root, s, "SKILL.md"))) err(mp, `lists ${s}, which has no SKILL.md`);
    for (const s of skills) if (!listed.includes(`skills/${s}`)) err(mp, `does not list skills/${s}`);
  } catch (e) {
    err(mp, `invalid JSON: ${e.message}`);
  }
}

// House rule: no emoji in any text file.
for (const f of walk(root)) {
  if (!/\.(md|mjs|js|py|json|txt|yml|yaml|ts|toml)$|LICENSE$/.test(f)) continue;
  const lines = readFileSync(f, "utf8").split("\n");
  lines.forEach((l, i) => { if (EMOJI.test(l)) err(f, `emoji on line ${i + 1}`); });
}

for (const w of warnings) console.log(`warning: ${w}`);
if (errors.length) {
  for (const e of errors) console.error(`error: ${e}`);
  console.error(`\n${errors.length} error(s) in ${skills.length} skill(s).`);
  process.exit(1);
}
console.log(`OK: ${skills.length} skill(s) valid: ${skills.join(", ")}`);
