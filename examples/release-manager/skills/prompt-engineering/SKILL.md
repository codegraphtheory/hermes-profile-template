---
name: prompt-engineering
description: "Turn a simple profile idea into a mature, production-quality Hermes profile prompt and generation brief."
version: 0.1.0
author: Hermes profile template
license: MIT
metadata:
  hermes:
    tags: [prompt-engineering, hermes, profiles, agent-design, profile-generation]
---

# Prompt Engineering for Hermes Profiles

Use this skill when a user gives a short idea such as "make me a database migration reviewer" and wants a high-quality Hermes profile distribution.

The goal is not to make a longer prompt for its own sake. The goal is to turn a simple sentence into a mature profile specification that can generate an installable, safe, useful Hermes profile repo.

## Inputs

Minimum input:

- A one-sentence profile idea.

Useful optional input:

- Target user or team.
- Domain and workflow.
- Expected artifacts.
- Tools or integrations.
- Risk level and data sensitivity.
- Desired tone and output format.
- Repository output path.

## Workflow

### 1. Extract intent

From the user's simple sentence, infer:

- job to be done
- target user
- trigger situations
- expected outputs
- likely tools
- likely risks
- what must be refused

Ask at most three clarifying questions only if missing information would materially change the generated profile. Otherwise proceed with explicit assumptions.

### 2. Write a mature profile prompt

Create a `Mature Profile Prompt` with these sections:

1. Profile name and slug.
2. Mission.
3. Target users.
4. Primary workflows.
5. Trigger patterns.
6. Inputs the profile expects.
7. Outputs the profile must produce.
8. Tool-use policy.
9. Safety boundaries and refusals.
10. Required skills.
11. Environment variables, if any.
12. Verification and smoke-test expectations.
13. Repository output requirements.

Keep it specific enough that another agent could generate the profile repo without more context.

### 3. Convert mature prompt to params YAML

Map the mature prompt into `templates/profile.params.yaml` fields:

- `name`
- `display_name`
- `description`
- `toolsets`
- `env_requires`
- `principles`
- `scope`
- `refusals`
- `output_contract`
- `github_topics`

Add a `profile_prompt` field containing the mature prompt so the generated repo can preserve the design rationale in `docs/profile-prompt.md` when supported by the generator.

### 4. Generate the repository

Run:

```bash
python3 scripts/generate_profile.py --params <params.yaml> --output <target-dir>
```

Then add any profile-specific bundled skill that materially improves the profile. Keep skills narrow, procedural, and domain-specific.

### 5. Verify installability

Run:

```bash
python3 <target-dir>/scripts/validate_profile.py <target-dir>
```

When Hermes is available, also run:

```bash
hermes profile install <target-dir> --name <smoke-name> --yes --force
```

## Quality checklist

- The mature prompt is concrete, not generic.
- The generated profile has one clear job.
- The generated profile includes safety boundaries.
- The profile does not claim fake integrations, credentials, audits, or community links.
- Required env vars are documented in `.env.EXAMPLE` only.
- At least one domain-specific bundled skill is added when the workflow benefits from reusable procedure.
- Validation passes.
- Smoke install passes when Hermes is available.

## Output format

When finishing, report:

- Simple sentence received.
- Mature profile prompt path, if written.
- Params YAML path.
- Generated repository path.
- Validation command and exact result.
- Smoke-install command and exact result, or why skipped.
- Next publish command.
