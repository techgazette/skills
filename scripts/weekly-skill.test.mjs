// Tests for weekly-skill.mjs. Run: node --test scripts/
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { applySkill, buildCommitMessage, missingSections, validateWeek, InputError } from "./weekly-skill.mjs";

const good = () => ({
  name: "algorithmic-art",
  date: "2026-10-04",
  summary: "Creating algorithmic art using p5.js.",
  whenToUse: { trigger: "Use this when users request generative art." },
  install: {
    readme: { agent: "Claude Code", lines: ["/plugin marketplace add anthropics/skills"], url: "https://github.com/anthropics/skills#readme" },
    copy: [{ agent: "Claude Code", docs: "https://code.claude.com/docs/en/skills", lines: ["cp -r algorithmic-art ~/.claude/skills/"] }],
  },
  example: { request: ["Make a flow field"], output: ["sketch.js"], from: "README", section: "Usage" },
  credit: { vendor: "Anthropic", repo: "anthropics/skills", source: "https://github.com/anthropics/skills/tree/HEAD/skills/algorithmic-art" },
  license: { spdx: "Apache-2.0", file: "https://github.com/anthropics/skills/blob/HEAD/skills/algorithmic-art/LICENSE.txt" },
  url: "https://techgazette.com.br/skills/",
});
const doc = (...skills) => JSON.stringify({ version: 1, week: "2026-41", skills });
const one = (s) => validateWeek(doc(s)).skills[0];

test("commit message carries every section, subject first", () => {
  const msg = buildCommitMessage(one(good()), ["weekly/algorithmic-art/README.md"]);
  const lines = msg.split("\n");
  assert.equal(lines[0], "Add algorithmic-art: Creating algorithmic art using p5.js");
  assert.equal(lines[1], "");
  for (const h of ["## What the skill does", "## When to use it", "## How to install it", "## Worked example", "## Source, credit and license", "## On The Tech Gazette", "## Files added or changed"]) assert.ok(msg.includes(h), h);
  assert.ok(msg.includes("- weekly/algorithmic-art/README.md"));
  assert.ok(msg.includes("Apache-2.0"));
  assert.ok(msg.includes("https://techgazette.com.br/skills/"));
});

test("an unfilled optional section is omitted, not invented", () => {
  const s = good(); delete s.example;
  const msg = buildCommitMessage(one(s), ["x"]);
  assert.ok(!msg.includes("## Worked example"));
});

test("missing required sections fail instead of committing", () => {
  for (const k of ["summary", "whenToUse", "install", "credit", "license", "url"]) {
    const s = good(); delete s[k];
    const v = one(s);
    assert.ok(missingSections(v).includes(k), k);
    assert.throws(() => buildCommitMessage(v, ["x"]), (e) => e instanceof InputError && e.message.includes(k));
  }
  assert.throws(() => buildCommitMessage(one(good()), []), /no files changed/);
});

test("rejects unsafe or oversized input", () => {
  const bad = (patch) => assert.throws(() => validateWeek(doc({ ...good(), ...patch })), InputError);
  bad({ name: "../etc" });
  bad({ name: "Bad Name" });
  bad({ name: "a".repeat(65) });
  bad({ date: "yesterday" });
  bad({ summary: "x".repeat(401) });
  bad({ summary: "line\nbreak" });
  bad({ url: "http://techgazette.com.br/skills/" });
  bad({ url: "https://evil.example/skills/" });
  bad({ license: { spdx: "Proprietary", file: "https://github.com/a/b" } });
  bad({ whenToUse: { ask: "```\nrm -rf /" } });
  assert.throws(() => validateWeek("x".repeat(300 * 1024)), /larger than/);
  assert.throws(() => validateWeek("{nope"), /not JSON/);
  assert.throws(() => validateWeek(JSON.stringify({ version: 2, skills: [] })), /version/);
  assert.throws(() => validateWeek(doc(good(), good())), /twice/);
});

test("writes only weekly/, README and CHANGELOG; a repeat run changes nothing", () => {
  const root = mkdtempSync(join(tmpdir(), "weekly-"));
  writeFileSync(join(root, "README.md"), "# Skills\n\n## The skills\n\n## Install\n\nx\n");
  const s = one(good());
  const first = applySkill(root, s);
  assert.deepEqual(first.changed.sort(), ["CHANGELOG.md", "README.md", "weekly/algorithmic-art/README.md", "weekly/algorithmic-art/entry.json"]);
  const readme = readFileSync(join(root, "README.md"), "utf8");
  assert.ok(readme.includes("| 2026-10-04 | [algorithmic-art](weekly/algorithmic-art/README.md) | [Anthropic]"));
  assert.ok(readme.indexOf("## Skill of the week") < readme.indexOf("## Install"));
  assert.ok(readFileSync(join(root, "CHANGELOG.md"), "utf8").includes("## 2026-10-04"));
  assert.ok(readFileSync(join(root, "weekly/algorithmic-art/README.md"), "utf8").includes("## How to install it"));
  assert.deepEqual(applySkill(root, s).changed, []);
  assert.ok(!existsSync(join(root, "skills")));
});
