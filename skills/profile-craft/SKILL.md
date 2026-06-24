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

Use this skill when creating or improving a Hermes Agent profile distribution.

## Inputs

- Target user or team.
- Primary job to be done.
- Required tools and integrations.
- Risk level and data sensitivity.
- Expected output style.

## Workflow

1. Define the profile mission in one sentence.
2. Define boundaries: what the profile does, does not do, and refuses.
3. Draft `SOUL.md` with first principles and output contract.
4. Add or refine `distribution.yaml`.
5. Keep `config.yaml` minimal and safe.
6. Add only skills that are directly needed.
7. Add `.env.EXAMPLE` for env vars, but never real secrets.
8. Run `python3 scripts/validate_profile.py .`.
9. Test local install with `hermes profile install . --name <smoke-name> --yes` when Hermes is available.
10. Update README with install and usage instructions.

## Quality checklist

- The profile has a single clear purpose.
- Every required env var is documented.
- Skills are procedural and reusable.
- No runtime state is committed.
- Validation passes.
- The README explains install, usage, and risks.

## Pitfalls

- Overloading one profile with too many roles.
- Copying secrets into examples.
- Adding MCP servers that require private local paths.
- Forgetting to bump `distribution.yaml` version.
- Claiming capabilities that the profile config does not enable.
