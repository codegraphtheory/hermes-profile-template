# Hermes Profile Template: AI Agent Instructions

This repository is designed to be edited by AI coding agents. Follow these rules exactly.

## Mission

Help users build high quality Hermes Agent profile distributions. A finished profile must be installable with `hermes profile install`, safe to publish, easy to understand, and pleasant to customize.

## Hard rules

1. Read this file before editing.
2. Never commit secrets. `.env` is forbidden. `.env.EXAMPLE` is allowed.
3. Never write API keys, OAuth tokens, cookies, session dumps, or private user data.
4. Never modify user-owned runtime paths: `memories/`, `sessions/`, `state.db*`, `auth.json`, `logs/`, `workspace/`, `plans/`, `local/`, `cache/`.
5. Preserve Hermes distribution compatibility. Keep `distribution.yaml` at repository root.
6. Keep the profile installable with `hermes profile install <source>`.
7. Run `python3 scripts/validate_profile.py .` after substantive edits.
8. Use clear, direct language in profile instructions. Avoid vague roleplay.
9. Keep skills reusable and focused. A skill should describe a procedure, not session history.
10. If changing config defaults, explain why in README or comments.
11. For public profile repos, add discoverability topics covering Hermes, the profile domain, and installability.
12. For profile catalog PRs, match the target catalog shape. Prefer a complete catalog-native profile entry over a bare link.

## Files and ownership

| Path | Purpose | Notes |
|---|---|---|
| `distribution.yaml` | Hermes distribution manifest | Required |
| `SOUL.md` | Profile identity and operating principles | Strongly recommended |
| `config.yaml` | Safe profile defaults | No secrets |
| `.env.EXAMPLE` | Env var template | No real values |
| `mcp.json` | MCP server stubs | Avoid local private paths by default |
| `skills/` | Bundled Hermes skills | Each skill needs `SKILL.md` frontmatter |
| `templates/` | Source templates for new profiles and skills | Placeholders are allowed here |
| `scripts/` | Validation and generation tools | Must run on Python 3.10+ |

## Profile design standard

A strong `SOUL.md` should include:

- Name and role.
- First principles.
- Scope of work.
- What the profile refuses to do.
- Tool-use expectations.
- Output contract.
- Quality bar.
- Safety and privacy rules.

Avoid:

- Hidden authority claims.
- Instructions to bypass user approval.
- Claims that the agent has tools not enabled in config.
- Unverifiable external community links.
- Secret or credential examples with real-looking values.

## Skill design standard

Each skill must have YAML frontmatter at byte 0:

```yaml
---
name: example-skill
description: "One sentence describing when to use the skill."
version: 0.1.0
author: Hermes profile template
license: MIT
---
```

Then include:

- When to use.
- Inputs expected.
- Step-by-step workflow.
- Verification steps.
- Pitfalls.

## Validation

Run:

```bash
python3 scripts/validate_profile.py .
```

For a generated profile, run the validator inside that generated directory too.

## Deterministic generation

Use `scripts/generate_profile.py` for reproducible profile creation from parameters:

```bash
python3 scripts/generate_profile.py --params templates/profile.params.yaml --output ../my-profile
```

The params file is the source of truth. Prefer editing YAML parameters over hand-editing generated starter files when creating a new profile family.

When this template is installed as a Hermes profile, the installed profile must retain `scripts/` and `templates/` so it can create new profiles interactively from chat.

## Commit style

Use conventional commits:

- `feat: add profile scaffold`
- `fix: tighten secret validation`
- `docs: clarify install path`
- `chore: update CI`

## Handoff format

When finishing, report:

1. Files changed.
2. Validation command and exact result.
3. Any remaining risks or manual steps.
