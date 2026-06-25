# Demo: Generate And Validate A Profile

## Goal

Show a first-time author how to create a profile from deterministic params and validate it before publishing.

## Setup

```bash
python3 -m pip install -r requirements.txt
```

## Recording Commands

Smoke-test the path in a temporary workspace:

```bash
python3 scripts/demo_fixture.py . --demo generate --keep
```

Manual version for narration:

```bash
tmpdir="$(mktemp -d)"
python3 scripts/generate_profile.py \
  --params templates/profile.params.yaml \
  --output "$tmpdir/generated-profile"
python3 "$tmpdir/generated-profile/scripts/validate_profile.py" "$tmpdir/generated-profile"
```

## Narration

1. The params file is the source of truth for a repeatable starter profile.
2. The generator writes the profile into a temporary workspace, not into a private project directory.
3. Validation runs immediately so the recording shows a real quality gate.
4. The generated profile can be inspected, committed, or discarded after review.

## Redaction Notes

- Record only the temporary output directory.
- Do not open `.env`, shell history, auth files, memories, sessions, or local workspace paths.
- Keep all credentials as placeholders.
