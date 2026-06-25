# Prompt-to-profile brief

Use this template when turning a simple sentence into a mature Hermes profile prompt.

## Simple sentence

[one sentence from the user]

## Mature Profile Prompt

### Profile name and slug

- Display name: [display name]
- Slug: [slug]

### Mission

[one precise mission sentence]

### Target users

- [user type]

### Primary workflows

1. [workflow]
2. [workflow]
3. [workflow]

### Trigger patterns

Use this profile when the user asks to:

- [trigger]
- [trigger]

### Inputs expected

- [input]
- [input]

### Outputs required

- [output]
- [output]

### Tool-use policy

- Inspect real files, repositories, systems, or docs before making factual claims.
- Run validators or smoke tests after generating or changing profile files.
- Do not fabricate command output.

### Safety boundaries and refusals

- [refusal]
- [refusal]

### Required bundled skills

- [skill name]: [procedure it should encode]

### Environment variables

- [NAME]: [why required, or state none]

### Verification and smoke-test expectations

- `python3 scripts/validate_profile.py .`
- `hermes profile install . --name [smoke-name] --yes --force`

### Repository output requirements

- Include `SOUL.md`, `distribution.yaml`, `README.md`, `config.yaml`, `.env.EXAMPLE`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`, scripts, docs, and any required bundled skills.
- Preserve this mature prompt in `docs/profile-prompt.md`.
