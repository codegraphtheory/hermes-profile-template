# Profile-builder terminal recording recipe

Record the interactive profile-builder demo from a disposable workspace. The goal is to show the prompt-to-profile loop without exposing local Hermes state, API keys, auth files, shell history, or personal project paths.

## What the recording should show

1. Install this repository as the `profile-architect` Hermes profile.
2. Start `profile-architect chat`.
3. Paste a concrete profile request, such as a database migration reviewer.
4. Show generated-profile validation output or the generated tree.
5. Stop before showing any private `.env`, auth, memory, session, or log file.

## Disposable workspace

Use a throwaway root so the terminal never displays your real Hermes home or personal project directories.

```bash
export DEMO_ROOT="/tmp/hermes-profile-builder-recording"
export HERMES_HOME="$DEMO_ROOT/hermes-home"
export PROFILE_OUT="$DEMO_ROOT/database-migration-reviewer"

rm -rf "$DEMO_ROOT"
mkdir -p "$DEMO_ROOT"
cd "$DEMO_ROOT"
```

Optional: shorten the shell prompt before recording so absolute local paths are not visible.

```bash
export PS1='demo$ '
clear
```

## Record with asciinema

Install `asciinema` if needed, then record only the disposable workspace session.

```bash
asciinema rec "$DEMO_ROOT/profile-builder-demo.cast"
```

Inside the recorded shell, run:

```bash
hermes profile install github.com/codegraphtheory/hermes-profile-template \
  --name profile-architect \
  --alias \
  --yes

profile-architect chat
```

Paste this prompt into the chat:

```text
Turn "a database migration reviewer" into a fantastic installable Hermes profile repo under /tmp/hermes-profile-builder-recording/database-migration-reviewer. Expand the idea into a mature agent prompt first, preserve it in docs/profile-prompt.md, then generate the repo and run validation. Do not use real credentials.
```

When the agent finishes, show a short verification path:

```bash
cd "$PROFILE_OUT"
python3 scripts/validate_profile.py .
find . -maxdepth 2 -type f | sort | sed 's#^./##' | head -40
```

Stop the asciinema recording with `Ctrl-D` or by typing `exit`.

## Record with a normal screen recorder

If you are using QuickTime, OBS, Loom, or another screen recorder:

1. Open a fresh terminal window.
2. Increase font size before recording.
3. Run the disposable workspace commands above.
4. Keep the terminal window cropped to the demo shell only.
5. Do not switch to browser tabs, editor windows, password managers, or other terminal panes.
6. Stop the recording before inspecting generated `.env.EXAMPLE` if your terminal scrollback includes private commands.

## Short narration script

Use this as the voiceover or on-screen talking points.

```text
This demo starts in a disposable Hermes home under /tmp, so no personal profiles or credentials are used.

First we install hermes-profile-template as profile-architect. That gives us a profile builder, not just a static template.

Then we ask it for a concrete profile: a database migration reviewer. The builder expands the short idea into a fuller profile prompt, writes an installable repository, and runs validation.

The important receipt is at the end: the generated repo has its own manifest, docs, skills, validation script, and a passing validation command. If validation passes, the output is ready to publish or install as a Hermes profile.
```

## Redaction checklist

Before publishing the recording, verify that it does not show:

- real API keys or tokens
- `.env` files
- `auth.json`
- private `HERMES_HOME` paths outside `/tmp/hermes-profile-builder-recording`
- `memories/`, `sessions/`, `logs/`, or other runtime state
- private repositories or customer names
- wallet addresses, unless the recording is explicitly about bounty payment
- shell history unrelated to the demo

Safe things to show:

- the install command
- the prompt text
- validation output
- generated file names
- `.env.EXAMPLE` placeholders, if needed

## Cleanup

Remove the demo profile and temporary Hermes home after recording.

```bash
rm -rf /tmp/hermes-profile-builder-recording
```

If you installed the demo profile into a non-temporary Hermes home by mistake, inspect your profiles and remove the demo entry manually before publishing any follow-up recording.

```bash
hermes profile list
hermes profile remove profile-architect
```

Only run the removal commands against the Hermes home you intended to use. The entire point is not turning a demo into a small archaeological incident.
