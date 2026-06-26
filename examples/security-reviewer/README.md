# Security Reviewer

Reviews code changes for security vulnerabilities, dependency risks, and secret exposure.

Template lineage: built from [codegraphtheory/hermes-profile-template](https://github.com/codegraphtheory/hermes-profile-template).

This is a Hermes Agent profile distribution. It can be installed with `hermes profile install` and updated from git.

## Install

```bash
hermes profile install github.com/YOUR_ORG/security-reviewer --alias
security-reviewer chat
```

For local development:

```bash
python3 -m pip install -r requirements.txt
make validate
hermes profile install . --name security-reviewer-local --yes
hermes -p security-reviewer-local chat
```

## Design prompt

The mature prompt used to generate or refine this profile is preserved in:

```text
docs/profile-prompt.md
```

When starting from a simple sentence, expand it with `skills/prompt-engineering/SKILL.md`, place the mature prompt in `templates/profile.params.yaml` as `profile_prompt`, then regenerate or update this profile.

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
