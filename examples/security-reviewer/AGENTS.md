# Security Reviewer: Agent Instructions

This profile is designed to be maintained by AI coding agents.

## Hard rules

1. Never commit secrets. `.env` is forbidden. `.env.EXAMPLE` is allowed.
2. Preserve `distribution.yaml` at the repository root.
3. Keep the profile installable with `hermes profile install <source>`.
4. Run `python3 scripts/validate_profile.py .` after substantive edits.
5. Keep instructions concrete and operational.
6. Do not claim tools or integrations that are not configured.

## Interactive profile creation

If the user asks this profile to create another Hermes profile:

1. Ask only for missing essentials: name, mission, target user, required integrations, and risk level.
2. Write a params YAML file using `templates/profile.params.yaml` as the schema reference.
3. Run `python3 scripts/generate_profile.py --params <params.yaml> --output <target-dir>`.
4. Run `python3 <target-dir>/scripts/validate_profile.py <target-dir>`.
5. Report the target path and validation output.

## Handoff format

When finishing, report files changed, commands run, validation output, and remaining manual steps.
