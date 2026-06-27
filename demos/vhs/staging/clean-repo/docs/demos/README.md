# Safe demo kit

Use this kit to record scaffold, validation, and install walkthroughs without exposing local secrets or private Hermes state.

## Smoke checks

```bash
python3 scripts/demo_fixture.py . --demo generate
python3 scripts/demo_fixture.py . --demo all
```

The install demo uses a temporary `HERMES_HOME` and skips itself when the Hermes CLI is unavailable unless `--require-hermes` is set.

## Redaction checklist

- Record only temporary workspaces created by `scripts/demo_fixture.py`.
- Never show `.env`, `auth.json`, real API keys, memories, sessions, logs, or private repositories.
- Keep credentials as placeholders in `.env.EXAMPLE`.
- Show validation output, generated file names, and install commands.
