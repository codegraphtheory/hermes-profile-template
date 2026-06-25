# Hermes Profile Examples

These examples are complete generated Hermes profile distributions. Each one includes the params file used to generate it, install instructions, validation commands, and domain-specific README keywords so authors can see what a publishable generated profile looks like.

Use this gallery to compare profile shapes before creating your own repo from a prompt, flags, or a params file.

## Gallery

| Example | Use case | Install command | Search keywords |
|---|---|---|---|
| [`security-reviewer`](security-reviewer/) | Reviews code and architecture changes for application security risk before production. | `hermes profile install github.com/YOUR_ORG/security-reviewer --alias` | security, security review, application security, code review |
| [`database-migration-reviewer`](database-migration-reviewer/) | Reviews SQL migrations for deploy safety, rollback readiness, locks, and data-loss risk. | `hermes profile install github.com/YOUR_ORG/database-migration-reviewer --alias` | database, migrations, SQL, rollback, deploy safety |
| [`release-manager`](release-manager/) | Coordinates release readiness, changelog discipline, smoke validation, and rollout notes. | `hermes profile install github.com/YOUR_ORG/release-manager --alias` | release management, CI, changelog, smoke testing |
| [`research-assistant`](research-assistant/) | Builds source-indexed research briefs with uncertainty labels and reusable handoff notes. | `hermes profile install github.com/YOUR_ORG/research-assistant --alias` | research, knowledge management, documentation, analysis |

Machine-readable gallery metadata is available in [`gallery.json`](gallery.json).

## Validation

Validate each example from the repository root:

```bash
python3 scripts/validate_profile.py examples/security-reviewer
python3 scripts/validate_profile.py examples/database-migration-reviewer
python3 scripts/validate_profile.py examples/release-manager
python3 scripts/validate_profile.py examples/research-assistant
```

Each example can also run its own local gate:

```bash
cd examples/security-reviewer
make validate
```

## Source Params

The source params used to generate the examples live in [`_source_params/`](_source_params/). The exact params file is also copied into each example as `profile.params.yaml` so the generated profile is self-describing.

Regenerate an example after editing its params:

```bash
python3 scripts/generate_profile.py \
  --params examples/_source_params/security-reviewer.params.yaml \
  --output examples/security-reviewer \
  --force
cp examples/_source_params/security-reviewer.params.yaml examples/security-reviewer/profile.params.yaml
```

Never add real credentials, runtime state, local memories, sessions, logs, or private user data to examples.
