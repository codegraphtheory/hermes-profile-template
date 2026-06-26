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

## Recommended GitHub metadata for generated profiles

Generated profile repositories should be easy to find, easy to evaluate, and honest about what is configured. Use `github-repo-metadata.yaml` as the repeatable source for repository description, homepage, and topics before applying metadata with `scripts/apply_github_metadata.py`.

### Description formula

Use one concise sentence that names the installable artifact, target workflow, and strongest concrete capability:

```text
Installable Hermes Agent profile for [target user or workflow], specializing in [domain], [primary capability], and [expected output].
```

Examples:

- `Installable Hermes Agent profile for application security review, specializing in threat modeling, code-risk summaries, and remediation checklists.`
- `Installable Hermes Agent profile for research teams, specializing in source-grounded briefs, evidence synthesis, and uncertainty labels.`
- `Installable Hermes Agent profile for code review teams, specializing in repository analysis, review checklists, and evidence-backed handoffs.`

Keep the description factual. Do not claim official affiliation, audits, customer adoption, community channels, or live integrations unless the generated profile actually includes and documents them.

### Homepage recommendation

For public generated profiles, point `homepage` at the repository README or published documentation:

```yaml
homepage: https://github.com/YOUR_ORG/YOUR_PROFILE_REPO#readme
```

If the profile has a GitHub Pages site or hosted docs, use that instead only when it is public, maintained, and linked back to the repository.

### Default topics

Every public generated profile should include these base topics:

```yaml
topics:
  - hermes-agent
  - agent-profile
  - profile-distribution
  - ai-agents
  - developer-tools
  - automation
```

Add `profile-template` only for template or starter repositories. Add `mcp` or provider-specific topics only when the profile actually configures that integration.

### Domain-specific topic examples

Add a few domain topics that match the profile's real use case.

Security profile:

```yaml
topics:
  - security
  - application-security
  - code-review
  - vulnerability-assessment
  - threat-modeling
```

Data or research profile:

```yaml
topics:
  - research-assistant
  - data-analysis
  - source-grounded
  - literature-review
  - evidence-synthesis
```

Code review or developer-tools profile:

```yaml
topics:
  - code-review
  - developer-tools
  - software-engineering
  - repository-analysis
  - ci-cd
```

Operations or release profile:

```yaml
topics:
  - release-management
  - ci-cd
  - changelog
  - smoke-testing
  - workflow-automation
```

### Example `github-repo-metadata.yaml`

```yaml
description: Installable Hermes Agent profile for code review teams, specializing in repository analysis, review checklists, and evidence-backed handoffs.
homepage: https://github.com/YOUR_ORG/codebase-reviewer#readme
topics:
  - hermes-agent
  - agent-profile
  - profile-distribution
  - ai-agents
  - developer-tools
  - automation
  - code-review
  - software-engineering
  - repository-analysis
```

Preview metadata changes before applying them:

```bash
python3 scripts/apply_github_metadata.py --repo YOUR_ORG/YOUR_PROFILE_REPO
```

Apply only after reviewing the dry run:

```bash
python3 scripts/apply_github_metadata.py --repo YOUR_ORG/YOUR_PROFILE_REPO --apply
```

## Non-goals

This template does not ship credentials, memories, user sessions, private runtime data, or provider accounts. It also does not create a native GitHub fork or template lineage after the fact. When native GitHub linkage is not possible, use explicit lineage in README text, `distribution.yaml`, and `.github/template-source.yml`.

## Compatibility rule

If Hermes Agent core changes distribution semantics, this template should follow core. The source of truth for install and update behavior is Hermes Agent itself. The source of truth for authoring hygiene in this repository is the local validator and smoke test.
