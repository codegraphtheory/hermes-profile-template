# Demo: generate and validate a profile from flags

Goal: show the template's scaffold → validate → smoke path in about 90 seconds without exposing local secrets.

## Setup before recording

```bash
scripts/demo_fixture.sh
export HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE="/tmp/hermes-profile-template-demo.workspace.EXAMPLE"
export HERMES_HOME="/tmp/hermes-profile-template-demo.home.EXAMPLE"
```

Use the real temporary paths printed by `scripts/demo_fixture.sh`. They should start with `/tmp/hermes-profile-template-demo.`.

## Commands to record

```bash
python3 scripts/new_profile.py \
  --name security-reviewer \
  --display-name "Security Reviewer" \
  --description "Reviews code and architecture changes for security risk" \
  --output "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/security-reviewer"
```

```bash
python3 "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/security-reviewer/scripts/validate_profile.py" \
  "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/security-reviewer"
```

```bash
find "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/security-reviewer" -maxdepth 2 -type f | sort
```

```bash
printf 'Install after publishing:\nhermes profile install github.com/YOUR_ORG/security-reviewer --alias\n'
```

```bash
scripts/demo_cleanup.sh "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/demo-fixture.env"
```

## Narration script

> This repository turns a profile idea into an installable Hermes profile distribution. I start with a clean temporary workspace and temporary Hermes home, so no real credentials or local profile state can appear in the recording.
>
> Now I generate a concrete security reviewer profile from flags. The generated repository includes the manifest, identity, config, scripts, docs, and validation tooling.
>
> Validation checks the manifest, skill frontmatter, forbidden runtime paths, broken placeholders, JSON/YAML shape, and common secret patterns.
>
> After publishing the generated profile repository, users can install it with `hermes profile install github.com/YOUR_ORG/security-reviewer --alias`.

## Recording notes

- Keep the terminal at the repository root.
- Do not show `~/.hermes`, `.env`, `auth.json`, browser sessions, or private paths.
- If `find` output is too noisy, use `tree -a -L 2` only if `tree` is already installed; do not make it a dependency.
