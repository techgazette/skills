# The Tech Gazette skills

Agent Skills for developers who need answers they can check. Each skill tells the agent
to quote sources exactly, copy code verbatim, and say "not found" instead of guessing.

A skill is a folder with a `SKILL.md` file (YAML frontmatter plus instructions), and
optionally scripts and other files. The format is the open
[Agent Skills specification](https://agentskills.io/specification), so the same folders
work in Claude Code, the Claude apps and API, OpenAI Codex, GitHub Copilot and the other
tools listed at [agentskills.io](https://agentskills.io).

## The skills

| Skill | Use it when |
| --- | --- |
| [vendor-changelog-impact](skills/vendor-changelog-impact/SKILL.md) | A vendor publishes release notes and you need to know what in your repo they break, with quotes and `file:line`. |
| [deprecation-deadlines](skills/deprecation-deadlines/SKILL.md) | You want a dated checklist of runtimes, packages, images and CI actions reaching end of life, each cited to the vendor. |
| [repo-quickstart](skills/repo-quickstart/SKILL.md) | You want the exact install line and first working example from a README, copied verbatim. |
| [primary-source-check](skills/primary-source-check/SKILL.md) | You are about to publish a technical claim and want every number, name and date checked against the primary source. |
| [weekly-tech-brief](skills/weekly-tech-brief/SKILL.md) | You want a chronological, per-source weekly brief from feeds you choose, every item linked, nothing ranked. |

Every skill has a worked example in its `examples/` folder. Helper scripts use only the
Python standard library and have tests next to them.

<!-- weekly:start -->
## Skill of the week

Every week The Tech Gazette picks one Agent Skill from a vendor's official repository. Each is
linked from [weekly/](weekly/) with what it does, when to use it, how to install it, its credit and
its license. The skills themselves stay in their publishers' repositories.

| Date | Skill | Source | License | What it does |
| --- | --- | --- | --- | --- |
| 2026-10-11 | [canvas-design](weekly/canvas-design/README.md) | [Anthropic](https://github.com/anthropics/skills/tree/HEAD/skills/canvas-design) | Apache-2.0 | These are instructions for creating design philosophies - aesthetic movements that are then EXPRESSED VISUALLY. Output only .md files, .pdf files, and .png files. |
<!-- weekly:end -->

## Install

### Claude Code

As a plugin marketplace (installs all five skills):

```text
/plugin marketplace add techgazette/skills
/plugin install developer-skills@tech-gazette-skills
```

Or copy individual skill folders. Personal skills live in `~/.claude/skills/<skill-name>/`
and load in all your projects; project skills live in `.claude/skills/<skill-name>/` and
can be committed for your team:

```bash
git clone https://github.com/techgazette/skills.git
cp -r skills/skills/repo-quickstart ~/.claude/skills/
```

Claude loads a skill when your request matches its description, or you can call it
directly, for example `/repo-quickstart` (or `/developer-skills:repo-quickstart` when
installed as a plugin). See the [Claude Code skills docs](https://code.claude.com/docs/en/skills).

### Claude apps (claude.ai)

Zip a skill folder and upload it under Settings > Features. Custom skills need a plan with
code execution enabled; see [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude).

```bash
cd skills && zip -r repo-quickstart.zip repo-quickstart
```

### Claude API

Upload a skill through the Skills API (`/v1/skills`) and use it with the code execution
tool. API skills run in a container without network access, so pass changelogs, READMEs,
sources and feeds as files instead of URLs. See
[Using Agent Skills with the API](https://platform.claude.com/docs/en/build-with-claude/skills-guide).

### OpenAI Codex

Copy skill folders into `.agents/skills/` in your repository, or `$HOME/.agents/skills/`
for all repositories. See [Codex skills](https://developers.openai.com/codex/skills).

### GitHub Copilot

Project skills go in `.github/skills/`, `.claude/skills/` or `.agents/skills/`; personal
skills in `~/.copilot/skills/` or `~/.agents/skills/`. See
[About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills).

### Other tools

Any tool that supports the Agent Skills format can read these folders. The list of
clients and their setup docs is at [agentskills.io](https://agentskills.io).

## Running the helpers yourself

The scripts work without an agent:

```bash
python3 skills/repo-quickstart/scripts/readme_blocks.py README.md --format md
python3 skills/deprecation-deadlines/scripts/list_deps.py . --format md
python3 skills/weekly-tech-brief/scripts/brief.py feeds.txt --days 7
```

Each script has `--help`.

## Validate

```bash
node scripts/validate.mjs
for d in skills/*/scripts; do (cd "$d" && python3 -m unittest) || break; done
```

`validate.mjs` checks every `SKILL.md` against the specification (name format and match
with its folder, description present and at most 1,024 characters, only spec fields) and
this repository's conventions. CI runs both on every push and pull request.

## Made by The Tech Gazette

These skills come from how [The Tech Gazette](https://techgazette.com.br) works: every
claim tied to its primary source, every code sample copied as published. Follow us on
Instagram at [@the.tech.gazette](https://www.instagram.com/the.tech.gazette/).

## License and disclaimer

Apache License 2.0, see [LICENSE](LICENSE). The skills are provided as-is, without
warranty. They guide an AI agent, which can still make mistakes: review its output,
especially before publishing or changing code.

Contributions are welcome, see [CONTRIBUTING.md](CONTRIBUTING.md).
