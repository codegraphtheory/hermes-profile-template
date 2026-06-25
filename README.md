# Hermes Profile Template

Build high quality Hermes Agent profile distributions quickly.

This repository is an authoring system for developers who want to create custom Hermes profiles that are installable, safe to publish, easy to maintain, and friendly to AI coding agents. Hermes Agent core provides `hermes profile install`, `hermes profile update`, and runtime profile isolation. This template adds the developer workflow around that core: scaffolding, deterministic generation, validation, CI, release checks, and publication hygiene.

For the boundary between Hermes core and this template, see [`docs/profile-distribution-contract.md`](docs/profile-distribution-contract.md).

## What you can do with it

- Create a complete Hermes profile distribution from command-line flags.
- Create a deterministic profile from a reusable YAML params file.
- Install this repository as a Hermes profile that helps you create other profiles interactively.
- Validate a profile before publishing it.
- Publish generated profiles so other users can install them from GitHub.
- Run repeatable local quality gates through `make validate`, `make smoke`, and `make release-check`.

## Requirements

- Hermes Agent installed and available as `hermes`.
- Python 3.10 or newer.
- Python dependencies for validation and generation:

```bash
python3 -m pip install -r requirements.txt
```

You can also run `make deps`.

## Option 1: Use this as a GitHub template

Open:

```text
https://github.com/codegraphtheory/hermes-profile-template
```

Click `Use this template`, create a new repository, then clone your new repo:

```bash
git clone https://github.com/YOUR_ORG/YOUR_PROFILE_REPO.git
cd YOUR_PROFILE_REPO
python3 scripts/validate_profile.py .
```

Edit the profile files, then validate again before publishing.

Convenience commands:

```bash
make validate
make smoke
```

## Option 2: Create a profile using the interactive guided wizard

This is the most beginner-friendly path if you do not know all the required parameters up front. The wizard will prompt you for configuration details (name, description, target users, tools, required environment variables, safety boundaries, etc.), save a reusable `profile.params.yaml` file, and generate the profile distribution automatically.

```bash
git clone https://github.com/codegraphtheory/hermes-profile-template.git
cd hermes-profile-template

python3 scripts/profile_wizard.py
```

Follow the prompts on your terminal, then switch to the output directory, validate, and install:

```bash
cd ../your-new-profile
make validate
hermes profile install . --alias
your-new-profile chat
```

## Option 3: Create a profile from command-line flags

```bash
git clone https://github.com/codegraphtheory/hermes-profile-template.git
cd hermes-profile-template

python3 scripts/new_profile.py \
  --name security-reviewer \
  --display-name "Security Reviewer" \
  --description "Reviews code and architecture for security risk" \
  --output ../security-reviewer

cd ../security-reviewer
python3 scripts/validate_profile.py .
```

Install it locally:

```bash
hermes profile install . --alias
security-reviewer chat
```

## Option 4: Create a profile from a params file

Copy the sample params file:

```bash
git clone https://github.com/codegraphtheory/hermes-profile-template.git
cd hermes-profile-template
cp templates/profile.params.yaml /tmp/my-profile.params.yaml
```

Edit `/tmp/my-profile.params.yaml`, then generate:

```bash
python3 scripts/generate_profile.py \
  --params /tmp/my-profile.params.yaml \
  --output ../my-profile

cd ../my-profile
python3 scripts/validate_profile.py .
```

This is the best path when you want reproducible profile creation. The params file becomes the source of truth for the starter profile.

Generated profiles can include explicit template lineage through the `template_source` field in the params file. GitHub only shows native `generated from` or `forked from` linkage when a repository is created through those GitHub flows, so this template records lineage in `distribution.yaml`, `.github/template-source.yml`, and the generated README.

## Option 5: Install this repo as an interactive profile builder

Install the template itself as a Hermes profile:

```bash
hermes profile install github.com/codegraphtheory/hermes-profile-template \
  --name profile-architect \
  --alias

profile-architect chat
```

Then ask it to create a profile:

```text
Create a Hermes profile for a database migration reviewer. It should inspect SQL diffs, flag destructive migrations, and generate rollback checklists.
```

The installed profile will use the included generator, write a starter profile, and run validation.

## Make the profile easy to discover

Before publishing, prepare both the installable distribution and small catalog-native snippets:

- Use `templates/catalog/flat-profile.md.tmpl` for profile catalogs that store one Markdown file per profile.
- Use `templates/catalog/manifest-profile.yaml.tmpl` for manifest-driven profile kits.
- Keep catalog PRs useful in the target repo format: identity, voice, skills, triggers, constraints, and a standalone install link.
- Add GitHub topics that cover Hermes, the domain, and installability. Good defaults are `hermes-agent`, `ai-agents`, `agent-profile`, `profile-distribution`, and one or more domain topics.
- Keep `github-repo-metadata.yaml` current so descriptions, homepage, and topics can be applied repeatably.

Preview metadata changes:

```bash
python3 scripts/apply_github_metadata.py --repo YOUR_ORG/YOUR_PROFILE_REPO
```

Apply metadata after reviewing the dry run:

```bash
python3 scripts/apply_github_metadata.py --repo YOUR_ORG/YOUR_PROFILE_REPO --apply
```

## Validate before publishing

Run this from the profile repository root:

```bash
make validate
make smoke
```

The smoke script validates the repository, compiles Python scripts without writing bytecode, generates and validates a profile from `templates/profile.params.yaml`, and installs into a temporary `HERMES_HOME` when the Hermes CLI is available. If you do not use `make`, run `python3 scripts/validate_profile.py .` and `scripts/smoke_install.sh` directly.


## Release discipline

For any change that affects profile behavior, generated files, config, docs, skills, scripts, or distribution metadata, a release readiness workflow must be run.

Before opening a pull request or tagging a release:

1. Bump the `version` in `distribution.yaml`.
2. Add a matching `## <version>` entry to `CHANGELOG.md`.
3. Run the release readiness check:

```bash
make release-check
```

This runs `scripts/release_readiness.py`, which checks:
- **Version Discipline**: Ensures version changes when release-relevant files are modified (relative to a base branch, e.g., `origin/main`).
- **Changelog Validation**: Verifies that a matching release entry heading exists in `CHANGELOG.md`.
- **Profile Validation**: Runs standard checks from `validate_profile.py` (formatting, skills, metadata).
- **No Runtime Files**: Verifies no runtime, temporary, or cache files (e.g., `.env`, `state.db`) are committed.
- **No Secrets**: Scans the workspace to prevent hardcoded secrets or credentials.
- **Generator Smoke**: Runs a full template compile and verifies the generated profile passes validation.
- **Install Smoke**: If Hermes CLI is available, verifies that the profile installs successfully and contains required files.
- **Install Documentation**: Ensures that the `README.md` or other docs list the correct installation command for this repository.

It generates a detailed Markdown report summarizing the checks, status (PASS, FAIL, SKIPPED), and any remediation hints.

The GitHub Actions release guard enforces this on pull requests.

## Publish a generated profile

From the generated profile directory:

```bash
git init -b main
git add .
git commit -m "feat: initial profile"
git remote add origin git@github.com:YOUR_ORG/YOUR_PROFILE_REPO.git
git push -u origin main
```

Users can install it with:

```bash
hermes profile install github.com/YOUR_ORG/YOUR_PROFILE_REPO --alias
```

## What to customize

Most users should start with these files:

- `SOUL.md`: the profile's identity, mission, boundaries, and output style.
- `distribution.yaml`: name, version, description, env vars, and distribution-owned files.
- `config.yaml`: model, toolsets, terminal behavior, memory, security, and approval defaults.
- `.env.EXAMPLE`: documented environment variables with placeholder values only.
- `skills/`: bundled reusable procedures the profile can load.
- `AGENTS.md`: instructions for AI coding agents that maintain the profile repository.
- `CONTRIBUTING.md`: contributor workflow, profile quality bar, and PR checklist.
- `SECURITY.md`: vulnerability reporting and secret-handling policy.
- `github-repo-metadata.yaml`: repeatable GitHub description, homepage, and topic metadata.
- `templates/catalog/`: snippets for adding the profile to external Hermes profile catalogs without looking like a generic link drop.

Never commit `.env`, API keys, OAuth tokens, credentials, memories, sessions, logs, runtime databases, or private user data.

## License

MIT. See `LICENSE`.
