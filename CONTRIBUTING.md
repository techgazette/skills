# Contributing

Thanks for helping. Issues and pull requests are welcome.

## Adding or changing a skill

1. One folder per skill under `skills/`, named in lowercase with hyphens. The folder
   name and the `name` field in `SKILL.md` must match.
2. Frontmatter uses only the fields in the [Agent Skills specification](https://agentskills.io/specification):
   `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.
   Claude Code accepts more fields, but uploads to claude.ai and the Claude API reject them.
3. The `description` says what the skill does and when to use it, in under 1,024 characters.
4. Instructions are step by step and include guardrails. Keep `SKILL.md` under 500 lines;
   move long reference material to `references/`.
5. Helper scripts use the standard library only (Python 3.9+ or Node 18+), print useful
   errors, and come with tests in the same `scripts/` folder.
6. Add an `examples/` file with a realistic input and the output the skill should produce.
   If the example uses real sources, say when they were read. If it is invented, say so.
7. Add the skill to `.claude-plugin/marketplace.json`.
8. No emoji.

## Before opening a pull request

```bash
node scripts/validate.mjs
for d in skills/*/scripts; do (cd "$d" && python3 -m unittest) || break; done
```

Both run in CI on every pull request.

## License

By contributing you agree that your contribution is licensed under the Apache License 2.0,
the license of this repository.
