# Safe demo kit

Use this kit to record scaffold, validation, and install walkthroughs without exposing local secrets or private Hermes state.

## Guided demos

| Demo | Doc | One-liner |
| --- | --- | --- |
| Generate + validate | [01-generate-and-validate.md](01-generate-and-validate.md) | `python3 scripts/demo_fixture.py . --demo generate` |
| Install + builder flow | [02-profile-architect-install.md](02-profile-architect-install.md) | `python3 scripts/demo_fixture.py . --demo all` |

Each doc includes voiceover bullets, exact commands, on-screen checklist, and cleanup steps.

## Smoke checks

```bash
python3 scripts/demo_fixture.py . --demo generate
python3 scripts/demo_fixture.py . --demo all
bash scripts/demo_cleanup.sh
```

The install demo uses a temporary `HERMES_HOME` and skips itself when the Hermes CLI is unavailable unless `--require-hermes` is set.

## Redaction checklist

- Record only temporary workspaces created by `scripts/demo_fixture.py`.
- Never show `.env`, `auth.json`, real API keys, memories, sessions, logs, or private repositories.
- Keep credentials as placeholders in `.env.EXAMPLE`.
- Show validation output, generated file names, and install commands.
