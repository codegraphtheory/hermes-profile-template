# AI Prompt: Design a Hermes Profile

Use this prompt with Hermes, Claude Code, Codex, Cursor, or another coding agent.

```text
We are designing a Hermes Agent profile distribution.

Target user: <who uses it>
Primary job: <what it does>
Risk level: <low, medium, high>
Required tools: <web, terminal, file, github, etc.>
Required integrations: <MCP, GitHub, Slack, etc.>
Output style: <brief, artifact pyramid, report, code patch, etc.>

Read AGENTS.md first. Then create or improve distribution.yaml, SOUL.md, config.yaml, .env.EXAMPLE, README.md, and any bundled skills. Keep it installable with hermes profile install. Do not add secrets. Run python3 scripts/validate_profile.py . before finishing and report the exact result.
```
