# Hermes Profile Template

A production-grade starter kit for building custom Hermes Agent profiles with AI assistance.

This repository is for people who want to ship excellent Hermes profiles, not just a loose `SOUL.md`. It gives you a complete profile distribution scaffold, profile authoring rules, validation scripts, GitHub Actions, and AI-agent instructions so Claude Code, Codex, Hermes, Cursor, and other coding agents can help you build and maintain high quality profiles safely.

## What this template optimizes for

- Fast profile creation with clear defaults.
- High quality `SOUL.md` identity documents.
- Explicit tool, skill, memory, cron, and MCP boundaries.
- Safe secret handling. No credentials in git.
- Hermes-native profile distributions using `distribution.yaml`.
- AI-friendly repository instructions through `AGENTS.md`.
- Repeatable validation before publishing.
- Easy handoff to users through `hermes profile install`.

## Repository layout

```text
.
├── AGENTS.md                         # Hard rules for AI coding agents
├── README.md                         # Human guide
├── distribution.yaml                 # Example Hermes profile distribution manifest
├── SOUL.md                           # Example profile identity document
├── config.yaml                       # Safe example Hermes config
├── .env.EXAMPLE                      # Environment variable template, no secrets
├── mcp.json                          # Example MCP config stub
├── skills/
│   └── profile-craft/SKILL.md        # Reusable skill for profile authoring
├── templates/
│   ├── profile/                      # Copyable profile distribution skeleton
│   ├── skill/                        # Copyable Hermes skill skeleton
│   └── prompts/                      # Prompts for AI-assisted profile design
├── scripts/
│   ├── new_profile.py                # Instantiate a profile from templates
│   └── validate_profile.py           # Validate distribution quality gates
└── .github/workflows/validate.yml    # CI validation
```

## Quick start

```bash
git clone https://github.com/codegraphtheory/hermes-profile-template.git
cd hermes-profile-template
python3 scripts/validate_profile.py .
```

Create a new profile distribution from the bundled template:

```bash
python3 scripts/new_profile.py \
  --name security-reviewer \
  --display-name "Security Reviewer" \
  --description "Reviews code and architecture for security risk" \
  --output ../security-reviewer
cd ../security-reviewer
python3 scripts/validate_profile.py .
```

Install the generated profile locally with Hermes:

```bash
hermes profile install ../security-reviewer --alias
security-reviewer chat
```

Publish it when ready:

```bash
git init
git add .
git commit -m "feat: initial security reviewer profile"
git remote add origin git@github.com:YOUR_ORG/security-reviewer.git
git push -u origin main
```

Users can then install it with:

```bash
hermes profile install github.com/YOUR_ORG/security-reviewer --alias
```

## What makes a good Hermes profile

A strong profile has four layers:

1. Identity: `SOUL.md` explains how the agent thinks, what it refuses, and what quality means.
2. Capabilities: `config.yaml`, `skills/`, `mcp.json`, and cron jobs define what the agent can actually do.
3. Operating contract: `AGENTS.md` tells AI coding agents how to maintain the profile without breaking it.
4. Distribution manifest: `distribution.yaml` makes the profile installable and updateable with Hermes.

## Quality gates

Run this before every commit:

```bash
python3 scripts/validate_profile.py .
```

The validator checks:

- Required files exist.
- YAML and JSON parse cleanly.
- `distribution.yaml` has required fields.
- Required env vars are documented in `.env.EXAMPLE`.
- Skills have valid frontmatter.
- No common secret patterns appear in tracked template files.
- No broken symlinks.
- No unresolved template placeholders remain outside `templates/`.

## Authoring workflow with AI

Use this prompt inside Hermes, Claude Code, Codex, or another coding agent:

```text
You are helping me build a Hermes Agent profile distribution. Read AGENTS.md first. Then inspect distribution.yaml, SOUL.md, config.yaml, skills/, and templates/. Improve the profile for a focused use case. Run python3 scripts/validate_profile.py . before finishing. Do not add secrets. Do not modify user-owned runtime files. Keep the distribution installable with hermes profile install.
```

## Distribution safety model

This template follows the Hermes profile distribution model:

- Distribution-owned: `SOUL.md`, `config.yaml`, `mcp.json`, `skills/`, `cron/`, `distribution.yaml`.
- User-owned: `.env`, `auth.json`, `memories/`, `sessions/`, `state.db*`, `logs/`, `workspace/`, `plans/`, `local/`.
- `.env.EXAMPLE` is safe to commit. `.env` is not.

## Recommended release checklist

- [ ] `python3 scripts/validate_profile.py .` passes.
- [ ] `hermes profile install . --name smoke-test --yes` succeeds in a temporary Hermes home.
- [ ] A real chat session confirms the profile loads expected instructions.
- [ ] README explains install, env vars, and intended use.
- [ ] Version in `distribution.yaml` is bumped.
- [ ] A git tag is created for reproducible installs.

## License

MIT. See `LICENSE`.
