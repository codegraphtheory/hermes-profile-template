# Demo: Install and use the profile builder

This walkthrough records a safe install-style demo for `profile-architect` using a temporary `HERMES_HOME`. The scripted smoke test skips the install step when the Hermes CLI is not available, which keeps CI and contributor laptops deterministic.

## Setup

```bash
export DEMO_ROOT="${TMPDIR:-/tmp}/hermes-profile-demo-install"
export HERMES_HOME="$DEMO_ROOT/hermes-home"
mkdir -p "$DEMO_ROOT"
```

Narration:

> Before installing anything, the demo redirects Hermes runtime state into a disposable home directory. That prevents the recording from reading or showing real profiles, sessions, memories, or credentials.

## Scripted smoke path

```bash
python3 scripts/demo_fixture.py . --demo all --keep
```

## Manual recording path

```bash
hermes profile install . --name profile-architect-demo --yes --force
hermes profile info profile-architect-demo
```

Optional prompt:

```text
Turn "a release checklist reviewer" into a fantastic installable Hermes profile repo under /tmp/hermes-profile-demo-install/release-checklist-reviewer. Expand the idea into a mature agent prompt first, preserve it in docs/profile-prompt.md, then generate the repo and run validation. Use no real credentials.
```

## Redaction notes

- Keep `HERMES_HOME` pointed at the temporary demo directory for the full recording.
- Do not display real Hermes profile lists, auth files, API keys, browser sessions, or private repositories.
- Prefer a clean terminal profile with no shell prompt path that reveals a personal username.

## Cleanup

```bash
python3 scripts/demo_cleanup.py "$DEMO_ROOT"
```
