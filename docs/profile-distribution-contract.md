# Profile Distribution Contract

This repository is an authoring system for Hermes Agent profile distributions. It does not replace Hermes Agent's native distribution runtime.

## What Hermes Agent core owns

Hermes Agent provides the distribution runtime:

- `hermes profile install <source>` installs a profile distribution from git or a local directory.
- `hermes profile update <name>` reapplies distribution-owned files from the recorded source.
- `hermes profile info <name>` reports installed distribution metadata.
- Profile isolation keeps each profile's config, skills, sessions, memories, credentials, and runtime state separate.
- The installer protects user-owned runtime paths such as `.env`, `auth.json`, `state.db*`, `sessions/`, `memories/`, `logs/`, `workspace/`, `plans/`, and `local/`.

## What this template owns

This template provides developer-facing authoring and release tooling for creating distribution repositories faster:

- parameter-driven profile scaffolding with `scripts/new_profile.py`
- deterministic YAML-driven generation with `scripts/generate_profile.py`
- publish-time validation with `scripts/validate_profile.py`
- isolated install smoke tests with `scripts/smoke_install.sh`
- release metadata checks with `scripts/check_release_version.py`
- repeatable GitHub metadata setup with `scripts/apply_github_metadata.py`
- CI workflows for validation and release hygiene
- catalog snippets and explicit template lineage metadata
- an installable `profile-architect` profile that can help create other distributions interactively

## What profile authors own

Profile authors are responsible for the product decisions and operational safety of the distribution they publish:

- the target user and use case
- the SOUL.md identity, boundaries, and output contract
- bundled skills and their maintenance
- model, toolset, MCP, and cron defaults
- documented environment variables in `distribution.yaml` and `.env.EXAMPLE`
- release notes and version bumps
- repository publication, access control, and support expectations

## Non-goals

This template does not ship credentials, memories, user sessions, private runtime data, or provider accounts. It also does not create a native GitHub fork or template lineage after the fact. When native GitHub linkage is not possible, use explicit lineage in README text, `distribution.yaml`, and `.github/template-source.yml`.

## Compatibility rule

If Hermes Agent core changes distribution semantics, this template should follow core. The source of truth for install and update behavior is Hermes Agent itself. The source of truth for authoring hygiene in this repository is the local validator and smoke test.
