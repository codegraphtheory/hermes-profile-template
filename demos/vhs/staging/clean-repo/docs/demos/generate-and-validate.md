# Demo: Generate and validate a profile

This walkthrough records a clean scaffold-to-validation demo from repository templates. It uses only temporary directories and placeholder configuration.

## Setup

```bash
python3 scripts/demo_fixture.py . --demo generate --keep
```

Narration:

> This demo starts from the Hermes profile template, creates a disposable workspace, generates a profile from checked-in sample parameters, and validates the generated repository before anything is published.

## Manual recording path

Use this path when you want to show each command in the terminal instead of the compact smoke runner.

```bash
export DEMO_ROOT="${TMPDIR:-/tmp}/hermes-profile-demo-generate"
export DEMO_OUTPUT="$DEMO_ROOT/generated-profile"
mkdir -p "$DEMO_ROOT"
python3 scripts/generate_profile.py --params templates/profile.params.yaml --output "$DEMO_OUTPUT"
python3 "$DEMO_OUTPUT/scripts/validate_profile.py" "$DEMO_OUTPUT"
find "$DEMO_OUTPUT" -maxdepth 2 -type f | sort | sed "s#$DEMO_ROOT#\$DEMO_ROOT#g"
```

## Redaction notes

- Show `$DEMO_ROOT`, `$DEMO_OUTPUT`, or `$DEMO_WORKSPACE`, not a personal home directory.
- Do not open `.env`, shell history, auth files, local Hermes state, memories, sessions, or logs.
- If the terminal prints an absolute temporary path, replace it with `$DEMO_ROOT` in captions or blur it in the recording.

## Cleanup

```bash
python3 scripts/demo_cleanup.py "$DEMO_ROOT"
```
