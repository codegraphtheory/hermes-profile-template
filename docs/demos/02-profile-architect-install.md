# Demo 2: Install profile-architect and build interactively

Record a demo that installs this repository as a Hermes profile, then uses it as an interactive profile builder.

## Voiceover script

1. "Authors can install this template itself as a Hermes profile called profile-architect."
2. "The install uses an isolated temporary HERMES_HOME so no private profiles are shown."
3. "From chat or prompts, the profile expands a one-line idea into a mature design prompt."
4. "The generated distribution includes validation scripts and install instructions."
5. "If Hermes CLI is unavailable, skip the install step and show the generate-and-validate demo instead."

## Commands

```bash
python3 scripts/demo_fixture.py . --demo all
```

Manual install path when Hermes CLI is available:

```bash
export DEMO_ROOT="$(mktemp -d)"
export HERMES_HOME="$DEMO_ROOT/hermes-home"
hermes profile install . --name profile-architect-demo --yes --force
hermes -p profile-architect-demo chat
rm -rf "$DEMO_ROOT"
```

## What to show on screen

- Temporary `HERMES_HOME` path
- Successful install message
- Prompt expansion example (use a generic sentence like "a database migration reviewer")
- Never show real API keys or private repositories

## Cleanup

```bash
bash scripts/demo_cleanup.sh
```
