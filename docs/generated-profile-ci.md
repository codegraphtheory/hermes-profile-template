# Generated profile CI

Generated Hermes profile repos should validate on every pull request. This template ships:

1. Reusable action: `.github/actions/validate-profile/action.yml`
2. Workflow template: `templates/generated-repo/github/workflows/validate-profile.yml`

## Generated repos

`scripts/generate_profile.py` copies `.github/` into generated profile distributions, including the reusable action and `validate.yml`.

## Manual adoption

```bash
mkdir -p .github/workflows .github/actions
cp -R .github/actions/validate-profile .github/actions/
cp templates/generated-repo/github/workflows/validate-profile.yml .github/workflows/validate-profile.yml
```

## Local equivalent

```bash
make validate
make compile
```

No secrets are required for baseline validation.
