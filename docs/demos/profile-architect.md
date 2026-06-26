# Demo: install this repo as `profile-architect`

Goal: show the interactive profile-builder loop without using your real Hermes profile home.

## Setup before recording

```bash
scripts/demo_fixture.sh
export HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE="/tmp/hermes-profile-template-demo.workspace.EXAMPLE"
export HERMES_HOME="/tmp/hermes-profile-template-demo.home.EXAMPLE"
```

Use the real temporary paths printed by `scripts/demo_fixture.sh`.

## Commands to record

Install the template into the temporary Hermes home:

```bash
HERMES_HOME="$HERMES_HOME" hermes profile install . \
  --name profile-architect-demo \
  --yes
```

Start the profile:

```bash
HERMES_HOME="$HERMES_HOME" hermes -p profile-architect-demo chat
```

Paste this prompt:

```text
Create a Hermes profile for a database migration reviewer. It should inspect SQL diffs, flag destructive migrations, and generate rollback checklists. Write it into the demo workspace and run validation.
```

If you want a non-interactive fallback for a short recording, show the deterministic generator instead:

```bash
python3 scripts/generate_profile.py \
  --params templates/profile.params.yaml \
  --output "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/generated-from-params"
```

```bash
python3 "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/generated-from-params/scripts/validate_profile.py" \
  "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/generated-from-params"
```

Cleanup:

```bash
scripts/demo_cleanup.sh "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/demo-fixture.env"
```

## Narration script

> The same repository can be installed as a Hermes profile. I install it into a temporary Hermes home so the recording never touches my real profiles, memories, sessions, or auth files.
>
> Now `profile-architect-demo` can act as an interactive profile builder. The prompt asks for a database migration reviewer. The profile should produce a deterministic params file or generated profile directory, then run validation before claiming it is ready.
>
> This is the useful loop: idea in, installable profile distribution out, with validation as the receipt.

## Redaction notes

- A real chat session may show model/provider names from the temporary config. That is fine; do not show API keys.
- Do not run this against your normal `HERMES_HOME` for public recordings.
- Keep prompts concrete. Avoid client names, private databases, or unpublished repo URLs.
