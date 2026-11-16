# cf-cli

The Tech Gazette's Skill of the week for 2026-11-15. Made by Cloudflare; linked here, not copied.

## What the skill does

Prefer retrieval over pre-trained knowledge. Describe the task to cf cli search, inspect the match with cf schema or --help, and preview with --dry-run before running a command you have not verified.

Its own description: "Cloudflare's official cf CLI (beta) for the public Cloudflare API and Workers projects. Use for finding and running Cloudflare commands from the terminal — sign-in and profiles, cf cli search, cf schema, cf deploy/dev/build, resource commands for DNS, zones, D1, KV, and R2 — and for choosing between cf and Wrangler in a project."

## When to use it

Use for finding and running Cloudflare commands from the terminal — sign-in and profiles, cf cli search, cf schema, cf deploy/dev/build, resource commands for DNS, zones, D1, KV, and R2 — and for choosing between cf and Wrangler in a project.

## How to install it

For Claude Code, as the source's README (https://github.com/cloudflare/skills#readme) says:

```text
/plugin marketplace add cloudflare/skills
/plugin install cloudflare@cloudflare
```

"Skills are contextual and auto-loaded based on your conversation."

Or copy the folder for Claude Code (https://code.claude.com/docs/en/skills):

```text
git clone https://github.com/cloudflare/skills
cd skills/skills
mkdir -p ~/.claude/skills
cp -r cf-cli ~/.claude/skills/
```

## Source, credit and license

Made by Cloudflare, in cloudflare/skills: https://github.com/cloudflare/skills/tree/HEAD/skills/cf-cli
License: Apache-2.0 (https://github.com/cloudflare/skills/blob/HEAD/LICENSE). This repository links to the skill and does not copy it; install it from its source.

## On The Tech Gazette

Skill of the week, 2026-11-15: https://techgazette.com.br/skills/

## Files in the original skill

- SKILL.md
- references/skill-feedback.md
