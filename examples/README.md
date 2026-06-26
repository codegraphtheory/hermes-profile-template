# Hermes profile examples

Complete generated profile distributions you can inspect, validate, and use as starting points.

| Example | Use case | Why it exists | Validate |
| --- | --- | --- | --- |
| [`security-reviewer`](security-reviewer/) | Reviews code and architecture for application security risk. | Shows a security-focused profile with evidence-backed findings and refusal boundaries. | `python3 scripts/validate_profile.py examples/security-reviewer` |
| [`database-migration-reviewer`](database-migration-reviewer/) | Reviews SQL migrations for rollout and rollback risk. | Demonstrates database rollout safety checks without requiring live credentials. | `python3 scripts/validate_profile.py examples/database-migration-reviewer` |
| [`release-manager`](release-manager/) | Coordinates changelog, smoke validation, and rollout notes. | Shows release hygiene: changelog drafting plus validation gates. | `python3 scripts/validate_profile.py examples/release-manager` |
| [`research-assistant`](research-assistant/) | Builds source-grounded briefs with uncertainty labels. | Demonstrates research-style outputs with explicit uncertainty handling. | `python3 scripts/validate_profile.py examples/research-assistant` |

## Install commands

Replace `YOUR_ORG` before publishing:

```bash
hermes profile install github.com/YOUR_ORG/security-reviewer --alias
hermes profile install github.com/YOUR_ORG/database-migration-reviewer --alias
hermes profile install github.com/YOUR_ORG/release-manager --alias
hermes profile install github.com/YOUR_ORG/research-assistant --alias
```

## Regenerate locally

Params live in `examples/params/`. Rebuild every example with:

```bash
python3 scripts/build_examples_gallery.py
python3 scripts/list_examples.py
```

Machine-readable metadata also lives in `gallery.json`.
