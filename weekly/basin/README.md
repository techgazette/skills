# basin

The Tech Gazette's Skill of the week for 2026-11-08. Made by Cloudflare; linked here, not copied.

## What the skill does

Basin ingests and transforms events, manages Apache Iceberg tables in R2, and queries them with distributed SQL.

Its own description: "Build and troubleshoot Cloudflare Basin analytics workflows with Basin Pipelines, Basin Catalog, and Basin SQL. Use for streaming data into R2 Iceberg tables, managing catalogs, or querying those tables; also use for requests using the former Data Platform, Pipelines, R2 Data Catalog, or R2 SQL names."

## When to use it

Use for streaming data into R2 Iceberg tables, managing catalogs, or querying those tables; also use for requests using the former Data Platform, Pipelines, R2 Data Catalog, or R2 SQL names.

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
cp -r basin ~/.claude/skills/
```

## Source, credit and license

Made by Cloudflare, in cloudflare/skills: https://github.com/cloudflare/skills/tree/HEAD/skills/basin
License: Apache-2.0 (https://github.com/cloudflare/skills/blob/HEAD/LICENSE). This repository links to the skill and does not copy it; install it from its source.

## On The Tech Gazette

Skill of the week, 2026-11-08: https://techgazette.com.br/skills/

## Files in the original skill

- SKILL.md
- references/catalog/README.md
- references/catalog/api.md
- references/catalog/configuration.md
- references/catalog/gotchas.md
- references/catalog/patterns.md
- references/pipelines/README.md
- references/pipelines/api.md
- references/pipelines/configuration.md
- references/pipelines/gotchas.md
- references/pipelines/patterns.md
- references/skill-feedback.md
- references/sql/README.md
- references/sql/api.md
- references/sql/configuration.md
- references/sql/gotchas.md
- references/sql/patterns.md
