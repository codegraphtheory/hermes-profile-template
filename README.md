# Hermes Profile Template

Turn a prompt into an installable Hermes profile repo.

`hermes-profile-template` is a developer authoring system for Hermes Agent profile distributions. Install this repo as a Hermes profile, describe the profile you want, and have Hermes produce a GitHub-ready repository with `SOUL.md`, `distribution.yaml`, safe config, docs, validation scripts, CI, release checks, and install instructions.

Hermes Agent core provides profile isolation and distribution install/update commands such as `hermes profile install` and `hermes profile update`. This repository supplies the author workflow around that runtime: prompt intake, deterministic generation, validation, smoke testing, publication hygiene, and discoverability assets.

For the boundary between Hermes core and this template, see [`docs/profile-distribution-contract.md`](docs/profile-distribution-contract.md).

## The literal workflow

One simple sentence should become a mature agent prompt, then a real repository directory that can be installed with `hermes profile install`.

```bash
export DEMO_ROOT="/tmp/hermes-profile-builder-demo"
export HERMES_HOME="$DEMO_ROOT/hermes-home"
rm -rf "$DEMO_ROOT"
mkdir -p "$DEMO_ROOT"
cd "$DEMO_ROOT"

hermes profile install github.com/codegraphtheory/hermes-profile-template \
  --name profile-architect \
  --alias \
  --yes

profile-architect chat
```

Paste a one-sentence idea or a product-style prompt. The installed profile will first expand the idea into a mature profile prompt, preserve that prompt in the generated repo, then generate and validate the profile.

Minimal prompt:

```text
Turn "a database migration reviewer" into a fantastic installable Hermes profile repo under /tmp/hermes-profile-builder-demo/database-migration-reviewer. Expand the idea into a mature agent prompt first, then generate the repo and run validation.
```

More detailed prompt:

```text
Create a Hermes profile distribution for a database migration reviewer.

Use case:
- Reviews SQL migration diffs before deploy.
- Flags destructive operations like dropped columns, table rewrites, missing rollback plans, unsafe locks, and irreversible data changes.
- Produces a short risk summary and a rollback checklist.

Repository requirements:
- Write the generated profile under /tmp/hermes-profile-builder-demo/database-migration-reviewer.
- Include a clear SOUL.md, distribution.yaml, README.md, config.yaml, .env.EXAMPLE, AGENTS.md, CONTRIBUTING.md, SECURITY.md, and one bundled skill for migration review.
- Run validation before finishing.
- Do not use real credentials.
```

Verify the result:

```bash
cd /tmp/hermes-profile-builder-demo/database-migration-reviewer
python3 scripts/validate_profile.py .
hermes profile install . --name migration-reviewer-demo --yes --force
hermes profile info migration-reviewer-demo
```

If those commands pass, the prompt became an installable Hermes profile repo.

## What the generated repo contains

A generated profile repository is designed to be published as its own GitHub repo.

Typical output:

```text
SOUL.md                         Profile identity, mission, boundaries, output contract
AGENTS.md                       Instructions for AI coding agents maintaining the repo
distribution.yaml               Installable Hermes profile manifest
config.yaml                     Safe profile defaults
.env.EXAMPLE                    Documented env vars with no secrets
mcp.json                        MCP stub
README.md                       Install, use, validate, and publish instructions
CONTRIBUTING.md                 Contribution workflow and quality bar
SECURITY.md                     Secret handling and vulnerability reporting
CHANGELOG.md                    Release history
Makefile                        Local validation and smoke commands
requirements.txt                Python dependencies for scripts
scripts/validate_profile.py     Profile validator
scripts/generate_profile.py     Deterministic generator
scripts/smoke_install.sh        Local install smoke test
.github/workflows/              Validation and release guard CI
skills/                         Bundled profile-specific skills
templates/                      Params, prompt-engineering, and catalog templates
docs/profile-prompt.md          Mature prompt preserved from the user's simple idea
```

The generated repo is not just a text draft. It should validate locally and install through Hermes.

## Usage paths

Every path below ends in the same contract: a directory that passes validation and can be installed with `hermes profile install`.

### Path 1: Simple sentence to repo with the installed profile

Use this when you want the claim literally: give a short natural-language idea, let `profile-architect` expand it into a mature profile prompt, then generate the repo.

```bash
hermes profile install github.com/codegraphtheory/hermes-profile-template \
  --name profile-architect \
  --alias \
  --yes

profile-architect chat
```

Prompt pattern:

```text
Turn "[simple profile idea]" into a fantastic installable Hermes profile repo under [absolute output path]. Expand the idea into a mature agent prompt first, preserve it in docs/profile-prompt.md, then generate the repo and run validation.
```

Detailed prompt pattern:

```text
Create a Hermes profile distribution for [target user or workflow].

Use case:
- [primary job]
- [risk or quality checks]
- [expected output]

Repository requirements:
- Write the generated profile under [absolute output path].
- Include SOUL.md, distribution.yaml, README.md, config.yaml, .env.EXAMPLE, AGENTS.md, CONTRIBUTING.md, SECURITY.md, and any needed bundled skills.
- Run validation before finishing.
- Do not use real credentials.
```

Expected behavior from the installed profile:

1. Expand short input into a mature profile prompt.
2. Ask only for missing essentials.
3. Write a params YAML file with `profile_prompt` preserved.
4. Run `python3 scripts/generate_profile.py --params <params.yaml> --output <target-dir>`.
5. Run `python3 <target-dir>/scripts/validate_profile.py <target-dir>`.
6. Report the generated repo path and exact validation output.

### Path 2: Prompt to repo in one non-interactive command

Use this for demos, recordings, or CI-like experiments when your Hermes setup supports non-interactive chat.

```bash
export DEMO_ROOT="/tmp/hermes-profile-builder-demo"
export HERMES_HOME="$DEMO_ROOT/hermes-home"
rm -rf "$DEMO_ROOT"
mkdir -p "$DEMO_ROOT"

hermes profile install github.com/codegraphtheory/hermes-profile-template \
  --name profile-architect \
  --yes

hermes -p profile-architect chat -q '
Turn "a database migration reviewer" into a fantastic installable Hermes profile repo under /tmp/hermes-profile-builder-demo/database-migration-reviewer.
Expand the idea into a mature agent prompt first, preserve it in docs/profile-prompt.md, then generate the repo and run validation.
The profile should review SQL migration diffs, flag destructive operations, produce rollback checklists, and include one bundled migration-review skill.
Do not use real credentials.
'
```

Then verify:

```bash
cd /tmp/hermes-profile-builder-demo/database-migration-reviewer
python3 scripts/validate_profile.py .
hermes profile install . --name migration-reviewer-demo --yes --force
```

### Path 3: Direct generation from command-line flags

Use this when you already know the profile name and one-sentence purpose.

```bash
git clone https://github.com/codegraphtheory/hermes-profile-template.git
cd hermes-profile-template
python3 -m pip install -r requirements.txt

python3 scripts/new_profile.py \
  --name security-reviewer \
  --display-name "Security Reviewer" \
  --description "Reviews code and architecture for security risk" \
  --output ../security-reviewer

cd ../security-reviewer
python3 scripts/validate_profile.py .
hermes profile install . --name security-reviewer-local --yes
```

This path is deterministic and quick, but less expressive than the installed `profile-architect` prompt workflow.

### Path 4: Deterministic generation from a params file

Use this when you want reproducible profile generation, code review, or repeatable builds.

```bash
git clone https://github.com/codegraphtheory/hermes-profile-template.git
cd hermes-profile-template
python3 -m pip install -r requirements.txt

cp templates/profile.params.yaml /tmp/database-migration-reviewer.params.yaml
$EDITOR /tmp/database-migration-reviewer.params.yaml

python3 scripts/generate_profile.py \
  --params /tmp/database-migration-reviewer.params.yaml \
  --output ../database-migration-reviewer

cd ../database-migration-reviewer
python3 scripts/validate_profile.py .
hermes profile install . --name migration-reviewer-local --yes
```

This is the best path after the first prompt-generated draft. Commit the params file so the repo can be regenerated later.

### Path 5: Use GitHub's template button

Use this when you want a new repository that GitHub marks as generated from this template.

1. Open `https://github.com/codegraphtheory/hermes-profile-template`.
2. Click `Use this template`.
3. Clone your new repo.
4. Replace the starter profile with either Path 1, Path 3, or Path 4 output.
5. Run validation and smoke install.

```bash
git clone https://github.com/YOUR_ORG/YOUR_PROFILE_REPO.git
cd YOUR_PROFILE_REPO
python3 -m pip install -r requirements.txt
python3 scripts/validate_profile.py .
hermes profile install . --name your-profile-local --yes
```

GitHub native template lineage only exists when the repository is created through the template flow. For generated repos created another way, this template records explicit lineage in `distribution.yaml`, `.github/template-source.yml`, and README text.

## Validation contract

Before calling a profile repo done, run:

```bash
python3 scripts/validate_profile.py .
```

For this template repo, run the full local gate:

```bash
make validate
make smoke
```

The smoke script validates the repository, compiles Python scripts without writing bytecode, generates and validates a profile from `templates/profile.params.yaml`, and installs into a temporary `HERMES_HOME` when the Hermes CLI is available.

## Publication path

From the generated profile directory:

```bash
git init -b main
git add .
git commit -m "feat: initial profile distribution"
git remote add origin git@github.com:YOUR_ORG/YOUR_PROFILE_REPO.git
git push -u origin main
```

Users can install the published profile with:

```bash
hermes profile install github.com/YOUR_ORG/YOUR_PROFILE_REPO --alias
```

## Make the profile discoverable

Before publishing, make the generated repo easy to find and evaluate:

- Put the install command near the top of the README.
- Keep a clear one-sentence repository description.
- Use GitHub topics such as `hermes-agent`, `ai-agents`, `agent-profile`, `profile-distribution`, and domain-specific topics.
- Keep `github-repo-metadata.yaml` current.
- Add catalog-native snippets from `templates/catalog/` when submitting to profile catalogs or resource lists.
- Avoid fake affiliations, fake community links, fake support channels, or claims that are not configured.

Preview metadata changes:

```bash
python3 scripts/apply_github_metadata.py --repo YOUR_ORG/YOUR_PROFILE_REPO
```

Apply after reviewing the dry run:

```bash
python3 scripts/apply_github_metadata.py --repo YOUR_ORG/YOUR_PROFILE_REPO --apply
```

## What to customize

Most generated profile repos should customize:

- `SOUL.md`: identity, mission, boundaries, trigger patterns, output style.
- `distribution.yaml`: name, version, description, env vars, distribution-owned files.
- `config.yaml`: model, toolsets, terminal behavior, memory, security, approvals.
- `.env.EXAMPLE`: documented environment variables with placeholder values only.
- `skills/`: bundled reusable procedures the profile can load.
- `AGENTS.md`: instructions for AI coding agents that maintain the repo.
- `CONTRIBUTING.md`: contributor workflow and profile quality bar.
- `SECURITY.md`: vulnerability reporting and secret-handling policy.
- `github-repo-metadata.yaml`: repeatable GitHub description, homepage, and topics.
- `templates/catalog/`: snippets for external catalogs and resource lists.

Never commit `.env`, API keys, OAuth tokens, credentials, memories, sessions, logs, runtime databases, or private user data.

## Release discipline

For any change that affects profile behavior, generated files, config, docs, skills, scripts, or distribution metadata:

1. Bump `version` in `distribution.yaml`.
2. Add a matching `## <version>` entry to `CHANGELOG.md`.
3. Run the release guard before opening a pull request:

```bash
make release-check
```

The GitHub Actions release guard enforces this on pull requests.

## Demo script

A full recording script is available at [`docs/interactive-profile-builder-demo.md`](docs/interactive-profile-builder-demo.md).

Short title:

```text
Turn a prompt into an installable Hermes profile repo
```

## License

MIT. See [`LICENSE`](LICENSE).
