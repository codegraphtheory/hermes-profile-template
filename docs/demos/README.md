# Safe demo kit

Use this kit to record scaffold, validation, and install walkthroughs without exposing local secrets or private Hermes state.

## Demo paths

- [Generate and validate a profile](generate-and-validate.md): records a clean scaffold-to-validation flow from template params.
- [Install and use the profile builder](install-profile-builder.md): records a temporary `HERMES_HOME` install path and optional interactive profile-builder usage.

## Smoke checks

```bash
python3 scripts/demo_fixture.py . --demo generate
python3 scripts/demo_fixture.py . --demo all
```

The install demo uses a temporary `HERMES_HOME` and skips itself when the Hermes CLI is unavailable unless `--require-hermes` is set.

## Cleanup

```bash
python3 scripts/demo_cleanup.py /tmp/hermes-profile-demo-recording
```

The cleanup helper refuses to remove a directory unless it contains the `.hermes-demo-fixture` safety marker created by `scripts/demo_fixture.py`.

## Redaction checklist

- Record only temporary workspaces created by `scripts/demo_fixture.py`.
- Never show `.env`, `auth.json`, real API keys, memories, sessions, logs, or private repositories.
- Keep credentials as placeholders in `.env.EXAMPLE`.
- Show validation output, generated file names, and install commands.
- Crop or redact usernames, home directories, shell history, browser bookmarks, and notification trays.
