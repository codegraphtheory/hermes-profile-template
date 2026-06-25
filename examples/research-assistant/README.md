# Research Assistant

Builds evidence-backed research briefs with source tracking, uncertainty labels, and reusable handoff notes.

Template lineage: built from [codegraphtheory/hermes-profile-template](https://github.com/codegraphtheory/hermes-profile-template).

This is a Hermes Agent profile distribution. It can be installed with `hermes profile install` and updated from git.

## Why this profile exists

Research gets more reusable when sourced facts, inference, uncertainty, and open questions are separated. This example shows a profile for research briefs, evidence indexes, knowledge management, documentation support, and decision handoffs.

Use it when a team needs a compact source-indexed brief instead of a loose chat summary.

Generated from [`profile.params.yaml`](profile.params.yaml).

## Install

```bash
hermes profile install github.com/YOUR_ORG/research-assistant --alias
research-assistant chat
```

For local development:

```bash
python3 -m pip install -r requirements.txt
make validate
hermes profile install . --name research-assistant-local --yes
hermes -p research-assistant-local chat
```

## Generate another profile from this one

This distribution includes a deterministic generator:

```bash
python3 scripts/generate_profile.py   --params templates/profile.params.yaml   --output ../my-new-profile
```

Edit `templates/profile.params.yaml` first to customize name, mission, principles, env vars, and toolsets.

## Quality gates

```bash
make validate
make smoke
```

If you do not use `make`, run `python3 scripts/validate_profile.py .` and `scripts/smoke_install.sh` directly.

## Release discipline

For changes that affect profile behavior, generated files, config, docs, skills, scripts, or distribution metadata:

1. Bump `version` in `distribution.yaml`.
2. Add a matching `## <version>` entry to `CHANGELOG.md`.
3. Run `make release-check` before opening a pull request.

## Safety

Do not commit `.env`, credentials, memories, sessions, logs, runtime databases, or user data. See `SECURITY.md` for vulnerability reporting and secret-handling expectations. See `CONTRIBUTING.md` for the validation and release checklist.
