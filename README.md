# Hermes Profile Template

Build high quality Hermes Agent profile distributions quickly.

This repository is for people who want to create custom Hermes profiles that are installable, safe to publish, easy to maintain, and friendly to AI coding agents. Use it to create a new profile from a few parameters, validate the result, install it locally, then publish it for others to install with `hermes profile install`.

## What you can do with it

- Create a complete Hermes profile distribution from command-line flags.
- Create a deterministic profile from a reusable YAML params file.
- Install this repository as a Hermes profile that helps you create other profiles interactively.
- Validate a profile before publishing it.
- Publish generated profiles so other users can install them from GitHub.

## Requirements

- Hermes Agent installed and available as `hermes`.
- Python 3.10 or newer.
- `pyyaml` for validation and generation:

```bash
python3 -m pip install pyyaml
```

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

## Option 2: Create a profile from command-line flags

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

## Option 3: Create a profile from a params file

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

## Option 4: Install this repo as an interactive profile builder

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

## Validate before publishing

Run this from the profile repository root:

```bash
python3 scripts/validate_profile.py .
```

The validator checks required files, YAML and JSON syntax, the Hermes distribution manifest, environment variable documentation, skill frontmatter, common secret patterns, broken symlinks, and unresolved template placeholders.

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

Never commit `.env`, API keys, OAuth tokens, credentials, memories, sessions, logs, runtime databases, or private user data.

## License

MIT. See `LICENSE`.
