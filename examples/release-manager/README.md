# Release Manager

Coordinates changelog updates, smoke validation, and rollout notes for safe releases.

This is a Hermes Agent profile distribution. It can be installed with `hermes profile install` and updated from git.

## Install

```bash
hermes profile install github.com/YOUR_ORG/release-manager --alias
release-manager chat
```

For local development:

```bash
python3 -m pip install -r requirements.txt
make validate
hermes profile install . --name release-manager-local --yes
hermes -p release-manager-local chat
```

## Design prompt

The mature prompt used to generate or refine this profile is preserved in:

```text
docs/profile-prompt.md
```

This document is included for transparency so reviewers can understand the profile's design intent.

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
