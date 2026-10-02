# Walkthrough: checking a paragraph about the Agent Skills format

A real check, run on 2026-10-01. The draft is `draft.md` in this folder. It contains one
wrong number and one number taken out of context; both are typical mistakes.

## Request

> I'm publishing this paragraph today. Check it against the official sources.

## Step 2: helper output

```bash
python3 ../scripts/claims.py check draft.md \
  https://agentskills.io/specification.md \
  https://agentskills.io/home.md \
  https://code.claude.com/docs/en/skills.md --format md
```

Exit code: 1 (one item not found).

```text
| line | kind | claim | status | where |
| --- | --- | --- | --- | --- |
| 1 | name | Agent Skills | found | https://agentskills.io/specification.md: ...ng further. # Specification > The complete format specification for Agent Skills. ## Directory structure A skill is a directory containing, at minim...; https://agentskills.io/home.md: ...his file to discover all available pages before exploring further. # Agent Skills Overview > A standardized way to give AI agents new capabilities and... |
| 2 | number | 64 | found | https://agentskills.io/specification.md: ...\| Field \| Required \| Constraints \| \| - \| - \| - \| \| `name` \| Yes \| Max 64 characters. Lowercase letters, numbers, and hyphens only. Must not st...; https://code.claude.com/docs/en/skills.md: ...o': '#00add8', '.rs': '#dea584', '.rb': '#cc342d', '.css': '#264de4', '.html': '#e34c26', '.json': '#6b7280', '.md': '#083fa1'... |
| 3 | number | 2,048 | not-found |  |
| 3 | name | SKILL | found | https://agentskills.io/specification.md: ...irectory structure A skill is a directory containing, at minimum, a `SKILL.md` file: ``` skill-name/ ├── SKILL.md # Required: metadata...; https://agentskills.io/home.md: ...tructionsUrl: "https://github.com/vinhnx/vtcode/blob/main/docs/skills/SKILLS_GUIDE.md", sourceCodeUrl: "https://github.com/vinhnx/VTCode" }, {... |
| 4 | number | 500 | found | https://agentskills.io/specification.md: ...r reference to a bundled license file. \| \| `compatibility` \| No \| Max 500 characters. Indicates environment requirements (intended product, sys...; https://code.claude.com/docs/en/skills.md: ...ing-skill-frontmatter-outside-claude-code). Accepts a string of up to 500 characters. Claude Code accepts the field but doesn't act on it. \| #... |
| 4 | number | 5,000 tokens | found | https://code.claude.com/docs/en/skills.md: ...recent invocation of each skill after the summary, keeping the first 5,000 tokens of each. Re-attached skills share a combined budget of 25,000 tokens.... |
| 4 | name | Claude Code | found | https://agentskills.io/specification.md: ...**Examples:** ```yaml theme={null} compatibility: Designed for Claude Code (or similar products) ``` ```yaml theme={null} compatibility:...; https://agentskills.io/home.md: ...sourceCodeUrl: "https://github.com/microsoft/vscode" }, { name: "Claude Code", description: "Claude Code is an agentic coding tool that reads yo... |
| 5 | number | 1,536 | found | https://code.claude.com/docs/en/skills.md: ...st: the combined `description` and `when_to_use` text is truncated at 1,536 characters in the skill listing to reduce context usage. \| \| `when_to... |

8 claims, 1 not found in the sources.
```

## Steps 3 and 4: reading the matches

- "64": the specification's `name` row says "Max 64 characters." Confirmed. (The second
  hit, in a color table on the Claude Code page, is irrelevant; this is why every match
  is read in context.)
- "2,048": not in any source. The specification's `description` row says "Max 1024
  characters." Mismatch.
- "500 lines": the script matched "500" to the `compatibility` limit, which is a different
  fact. Reading the specification finds the real sentence: "Keep your main `SKILL.md`
  under 500 lines." Confirmed, from a different sentence than the script showed.
- "5,000 tokens": the script found "5,000 tokens" on the Claude Code page, but that
  sentence is about re-attaching skills after compaction. The specification says
  "Instructions (< 5000 tokens recommended)". Confirmed against the specification,
  and the word "recommends" in the draft matches the source's "recommended".
- "1,536": confirmed, Claude Code docs.
- Not extracted by the script, checked by hand: "originally developed by Anthropic" and
  "open standard". The agentskills.io overview says: "The Agent Skills format was
  originally developed by Anthropic, released as an open standard, and has been adopted
  by a growing number of agent products." Confirmed.

## Final report

```markdown
## Source check: Agent Skills paragraph, 2026-10-01
Sources read: https://agentskills.io/specification (2026-10-01), https://agentskills.io/home (2026-10-01), https://code.claude.com/docs/en/skills (2026-10-01)

| # | Claim in draft | Verdict | Source says | Source |
| - | --- | --- | --- | --- |
| 1 | "originally developed by Anthropic, is now an open standard" | Confirmed | "The Agent Skills format was originally developed by Anthropic, released as an open standard, and has been adopted by a growing number of agent products." | https://agentskills.io/home |
| 2 | "name can have up to 64 characters" | Confirmed | "Max 64 characters." | https://agentskills.io/specification#frontmatter |
| 3 | "description up to 2,048 characters" | Mismatch | "Max 1024 characters. Non-empty." | https://agentskills.io/specification#frontmatter |
| 4 | "keeping SKILL.md under 500 lines" | Confirmed | "Keep your main `SKILL.md` under 500 lines." | https://agentskills.io/specification#progressive-disclosure |
| 5 | "instructions under 5,000 tokens" | Confirmed | "Instructions (< 5000 tokens recommended)" | https://agentskills.io/specification#progressive-disclosure |
| 6 | "truncates ... at 1,536 characters in the skill listing" | Confirmed | "the combined `description` and `when_to_use` text is truncated at 1,536 characters in the skill listing" | https://code.claude.com/docs/en/skills |

### Fixes
- Line 3: replace "up to 2,048 characters" with "up to 1,024 characters" (source: https://agentskills.io/specification).
```
