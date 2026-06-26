# Generated profile CI

Generated Hermes profile repos should validate on every pull request. This template ships two assets:

1. Reusable local action: `.github/actions/validate-profile/action.yml` (copied during generation)
2. Workflow template: `templates/generated-repo/github/workflows/validate-profile.yml`

## Copy into a generated repo

If you generated a profile with `scripts/generate_profile.py`, the repo already includes `.github/workflows/validate.yml` and the reusable action.

To adopt the standalone template manually:

```bash
mkdir -p .github/workflows
cp templates/generated-repo/github/workflows/validate-profile.yml .github/workflows/validate-profile.yml
```

Ensure `.github/actions/validate-profile/action.yml` exists (copied from this template repository).

## What CI runs

- Install `requirements.txt`
- `python -m py_compile scripts/*.py`
- `python scripts/validate_profile.py .`

No secrets are required for baseline validation.

## Local equivalent

```bash
make validate
make compile
```

Or use the composite action locally through `act` if you mirror the workflow file above.
