# Demo: Install This Repo As Profile Architect

## Goal

Show how this repository can be installed as an interactive Hermes profile builder while keeping local state isolated.

## Setup

Install Hermes Agent and keep it on `PATH`. The demo script uses a temporary `HERMES_HOME` so the recording does not touch your normal Hermes state.

## Recording Commands

Smoke-test the install path when Hermes is available:

```bash
python3 scripts/demo_fixture.py . --demo install --keep
```

Manual version for narration:

```bash
tmpdir="$(mktemp -d)"
export HERMES_HOME="$tmpdir/hermes-home"
hermes profile install . --name profile-architect-demo --alias --yes
profile-architect-demo chat
```

## Narration

1. The install command uses the repository as a local Hermes profile source.
2. `HERMES_HOME` points to a temporary directory to avoid exposing real profiles or sessions.
3. The installed profile keeps the template scripts and profile params so it can generate new profiles interactively.
4. After the recording, the temporary directory can be removed.

## Redaction Notes

- Confirm the prompt shows the temporary `HERMES_HOME`, not your real home directory.
- Do not record real profile aliases, auth state, model keys, memories, sessions, or private repositories.
- Avoid typing prompts that include private customer or project information.
