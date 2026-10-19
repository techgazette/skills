# mcp-builder

The Tech Gazette's Skill of the week for 2026-10-18. Made by Anthropic; linked here, not copied.

## What the skill does

Create MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools.

Its own description: "Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK)."

## When to use it

Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).

## How to install it

For Claude Code, as the source's README (https://github.com/anthropics/skills#readme) says:

```text
/plugin marketplace add anthropics/skills
/plugin install example-skills@anthropic-agent-skills
```

"After installing the plugin, you can use the skill by just mentioning it."

Or copy the folder for Claude Code (https://code.claude.com/docs/en/skills):

```text
git clone https://github.com/anthropics/skills
cd skills/skills
mkdir -p ~/.claude/skills
cp -r mcp-builder ~/.claude/skills/
```

## Source, credit and license

Made by Anthropic, in anthropics/skills: https://github.com/anthropics/skills/tree/HEAD/skills/mcp-builder
License: Apache-2.0 (https://github.com/anthropics/skills/blob/HEAD/skills/mcp-builder/LICENSE.txt). This repository links to the skill and does not copy it; install it from its source.

## On The Tech Gazette

Skill of the week, 2026-10-18: https://techgazette.com.br/skills/

## Files in the original skill

- LICENSE.txt
- SKILL.md
- reference/evaluation.md
- reference/mcp_best_practices.md
- reference/node_mcp_server.md
- reference/python_mcp_server.md
- scripts/connections.py
- scripts/evaluation.py
- scripts/example_evaluation.xml
- scripts/requirements.txt
