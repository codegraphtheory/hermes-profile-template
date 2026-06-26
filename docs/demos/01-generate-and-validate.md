# Demo 1: Generate and validate a profile

Record a terminal demo that shows deterministic generation from params, then validation, without exposing local secrets.

## Voiceover script

1. "This template can generate a complete Hermes profile distribution from a params file."
2. "We start from the bundled example params and write output into a temporary workspace."
3. "The generator copies validation scripts and CI assets into the generated repo."
4. "We run the generated validator to prove the profile is install-ready."
5. "No `.env`, sessions, or runtime databases appear in the generated tree."

## Commands

```bash
python3 scripts/demo_fixture.py . --demo generate
```

Optional manual walkthrough:

```bash
export DEMO_ROOT="$(mktemp -d)"
python3 scripts/generate_profile.py \
  --params templates/profile.params.yaml \
  --output "$DEMO_ROOT/generated-profile"
python3 "$DEMO_ROOT/generated-profile/scripts/validate_profile.py" "$DEMO_ROOT/generated-profile"
rm -rf "$DEMO_ROOT"
```

## What to show on screen

- Generated `distribution.yaml`, `SOUL.md`, and `README.md`
- Validator output ending in `Hermes profile validation passed`
- Redacted paths only (`$DEMO_WORKSPACE` when using `demo_fixture.py`)

## Cleanup

```bash
bash scripts/demo_cleanup.sh
```
