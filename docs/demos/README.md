# Demo Kit

Use this kit to record clean terminal demos for Hermes profile authors without exposing local secrets or private state.

## Demos

- [Generate and validate a profile](generate-and-validate.md)
- [Install this repo as Profile Architect](profile-architect-install.md)

## Smoke Test

Run the generated-profile demo in a temporary workspace:

```bash
python3 scripts/demo_fixture.py . --demo generate
```

Run every available demo path. The install demo is skipped when `hermes` is not on `PATH` unless `--require-hermes` is set:

```bash
python3 scripts/demo_fixture.py . --demo all
```

Use `--keep` only when you need to inspect or record the temporary workspace after the command completes.

## Redaction Checklist

- Use only temporary directories created by `scripts/demo_fixture.py`.
- Set a temporary `HERMES_HOME` before install demos.
- Do not record `.env`, `auth.json`, tokens, memories, sessions, logs, or local private paths.
- Keep API keys as placeholders in `.env.EXAMPLE`; never type real credentials during a recording.
- Show validation output and generated file names, not private editor tabs or shell history.
