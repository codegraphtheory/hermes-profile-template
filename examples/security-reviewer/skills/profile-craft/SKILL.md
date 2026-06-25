---
name: profile-craft
description: "Design and validate Hermes Agent profile distributions, including SOUL.md, distribution.yaml, skills, config, MCP stubs, and release readiness."
version: 0.1.0
author: Hermes profile template
license: MIT
metadata:
  hermes:
    tags: [hermes, profiles, distribution, templates, skills, validation]
---

# Profile Craft

Use this skill when creating or improving a Hermes Agent profile distribution. The default deliverable is a repository directory that can be validated and installed with `hermes profile install`, not just a written plan.

## Inputs

- Target user or team.
- Primary job to be done.
- Required tools and integrations.
- Risk level and data sensitivity.
- Expected output style.

## Workflow

### Prompt-to-repo workflow

When a user asks for a new profile from a prompt:

1. Ask only for missing essentials: profile name, mission, target user, required integrations, data sensitivity, risk level, and output style.
2. If enough information is present, proceed with sensible defaults.
3. Write a params YAML file using `templates/profile.params.yaml` as the schema reference.
4. Run `python3 scripts/generate_profile.py --params <params.yaml> --output <target-dir>`.
5. Run `python3 <target-dir>/scripts/validate_profile.py <target-dir>`.
6. If Hermes is available, run `hermes profile install <target-dir> --name <smoke-name> --yes --force`.
7. Report generated repo path, validation output, smoke-install output if run, and next publish command.

### Profile design workflow

1. Define the profile mission in one sentence.
2. Define boundaries: what the profile does, does not do, and refuses.
3. Draft `SOUL.md` with first principles and output contract.
4. Add or refine `distribution.yaml`.
5. Keep `config.yaml` minimal and safe.
6. Add only skills that are directly needed.
7. Add `.env.EXAMPLE` for env vars, but never real secrets.
8. For deterministic starter creation, edit a params YAML file and run `python3 scripts/generate_profile.py --params <params.yaml> --output <target-dir>`.
9. Run `python3 scripts/validate_profile.py .`.
10. Test local install with `hermes profile install . --name <smoke-name> --yes` when Hermes is available.
11. Update README with install, usage, validation, and catalog contribution instructions.
12. If the profile should be discoverable in profile catalogs, create small catalog-native entries using `templates/catalog/`. Match the target repo format instead of pasting a generic link.
13. Before any public push, scan staged files, latest commit metadata, PR body text, and added diff lines for private identity strings, secrets, and project-specific style constraints.

## Quality checklist

- The profile has a single clear purpose.
- Every required env var is documented.
- Skills are procedural and reusable.
- No runtime state is committed.
- Validation passes.
- Generator output validates from a temporary directory.
- Local `hermes profile install . --name <smoke-name> --yes` succeeds when Hermes is available.
- The README explains install, usage, validation, and risks.
- Public repository topics cover framework, domain, and installability keywords.

## Pitfalls

- Overloading one profile with too many roles.
- Copying secrets into examples.
- Adding MCP servers that require private local paths.
- Forgetting to bump `distribution.yaml` version.
- Claiming capabilities that the profile config does not enable.
- Using curly-brace template tokens outside `templates/`; validators treat those as unresolved. Use `[question]` style markers in skill references.
- Opening profile catalog PRs that only add a link. Add a catalog-native profile file or manifest entry when the target repo expects one.
