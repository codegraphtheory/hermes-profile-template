# Reusable GitHub Actions validation

Generated profile repositories can validate themselves on every pull request without adding secrets or paid GitHub features.

## Option 1: call the shared action

Create `.github/workflows/validate-profile.yml` in the generated profile repository:

```yaml
name: Validate Hermes Profile Distribution

on:
  pull_request:
  push:
    branches: [main]

jobs:
  validate-profile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
      - name: Validate Hermes profile distribution
        uses: codegraphtheory/hermes-profile-template/.github/actions/validate-profile@main
        with:
          install-smoke: "false"
```

This runs:

1. `python -m pip install -r requirements.txt` when `requirements.txt` exists.
2. `python -m py_compile scripts/*.py` when Python scripts exist.
3. `python scripts/validate_profile.py .`.
4. Generator smoke when `scripts/generate_profile.py` and `templates/profile.params.yaml` exist.
5. Optional install smoke when `install-smoke: "true"` and `scripts/smoke_install.sh` exists.

## Option 2: copy the workflow template

This repository also includes a copyable workflow template:

```bash
mkdir -p .github/workflows
cp templates/github-actions/validate-profile.yml .github/workflows/validate-profile.yml
```

Review the `uses:` line before publishing. Pin to a tag or commit SHA if your project requires immutable CI dependencies.

## Inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `python-command` | `python` | Python executable used by the action. |
| `install-dependencies` | `true` | Install `requirements.txt` if present. |
| `validate-command` | `python scripts/validate_profile.py .` | Main validation command. |
| `compile-scripts` | `true` | Compile `scripts/*.py` without writing bytecode. |
| `generator-smoke` | `true` | Generate and validate a temporary profile when generator files exist. |
| `install-smoke` | `false` | Run `scripts/smoke_install.sh`; the script skips Hermes install when Hermes CLI is unavailable. |
| `generated-output-dir` | `/tmp/hermes-profile-action-generated` | Temporary generated profile path. |

## Failure messages

The action fails early with actionable messages when:

- `distribution.yaml` is missing, which usually means the workflow is running from the wrong repository root.
- `scripts/validate_profile.py` fails, which means the profile distribution contract is broken.
- Python scripts do not compile.
- Generator smoke cannot generate or validate a temporary profile.

No API keys, OAuth tokens, GitHub secrets, or paid GitHub features are required for the baseline workflow.
