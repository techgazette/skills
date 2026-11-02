# slack-gif-creator

The Tech Gazette's Skill of the week for 2026-11-01. Made by Anthropic; linked here, not copied.

## What the skill does

A toolkit providing utilities and knowledge for creating animated GIFs optimized for Slack.

Its own description: "Knowledge and utilities for creating animated GIFs optimized for Slack. Provides constraints, validation tools, and animation concepts. Use when users request animated GIFs for Slack like "make me a GIF of X doing Y for Slack.""

## When to use it

Use when users request animated GIFs for Slack like "make me a GIF of X doing Y for Slack."

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
cp -r slack-gif-creator ~/.claude/skills/
```

## Source, credit and license

Made by Anthropic, in anthropics/skills: https://github.com/anthropics/skills/tree/HEAD/skills/slack-gif-creator
License: Apache-2.0 (https://github.com/anthropics/skills/blob/HEAD/skills/slack-gif-creator/LICENSE.txt). This repository links to the skill and does not copy it; install it from its source.

## On The Tech Gazette

Skill of the week, 2026-11-01: https://techgazette.com.br/skills/

## Files in the original skill

- LICENSE.txt
- SKILL.md
- core/easing.py
- core/frame_composer.py
- core/gif_builder.py
- core/validators.py
- requirements.txt
