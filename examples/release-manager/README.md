# Release Manager

Coordinates release readiness checks, changelog discipline, smoke validation, and rollout notes.

Template lineage: built from [codegraphtheory/hermes-profile-template](https://github.com/codegraphtheory/hermes-profile-template).

This is a Hermes Agent profile distribution. It can be installed with `hermes profile install` and updated from git.

## Why this profile exists

Release work needs visible evidence: version changes, changelog entries, validation output, smoke checks, rollout notes, and rollback paths. This example shows a profile for release management, CI readiness, changelog discipline, and deployment review.

Use it when a maintainer wants a release packet that is ready for PR comments, release notes, or handoff.

Generated from [`profile.params.yaml`](profile.params.yaml).

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
