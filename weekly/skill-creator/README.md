# skill-creator

The Tech Gazette's Skill of the week for 2026-10-25. Made by Anthropic; linked here, not copied.

## What the skill does

A skill for creating new skills and iteratively improving them.

Its own description: "Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy."

## When to use it

Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.

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
cp -r skill-creator ~/.claude/skills/
```

## Source, credit and license

Made by Anthropic, in anthropics/skills: https://github.com/anthropics/skills/tree/HEAD/skills/skill-creator
License: Apache-2.0 (https://github.com/anthropics/skills/blob/HEAD/skills/skill-creator/LICENSE.txt). This repository links to the skill and does not copy it; install it from its source.

## On The Tech Gazette

Skill of the week, 2026-10-25: https://techgazette.com.br/skills/

## Files in the original skill

- LICENSE.txt
- SKILL.md
- agents/analyzer.md
- agents/comparator.md
- agents/grader.md
- assets/eval_review.html
- eval-viewer/generate_review.py
- eval-viewer/viewer.html
- references/schemas.md
- scripts/__init__.py
- scripts/aggregate_benchmark.py
- scripts/generate_report.py
- scripts/improve_description.py
- scripts/package_skill.py
- scripts/quick_validate.py
- scripts/run_eval.py
- scripts/run_loop.py
- scripts/utils.py
