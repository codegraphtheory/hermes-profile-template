# Secret-safe demo kit

Use this kit to record clean terminal demos without exposing real API keys, auth files, memories, sessions, or personal project paths.

The demos use temporary directories under `/tmp` and a temporary `HERMES_HOME`. Asciinema is optional; a normal screen recorder is fine.

## Create a clean fixture

From the repository root:

```bash
scripts/demo_fixture.sh
```

Copy the two `export` lines it prints before recording:

```bash
export HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE="/tmp/hermes-profile-template-demo.workspace.EXAMPLE"
export HERMES_HOME="/tmp/hermes-profile-template-demo.home.EXAMPLE"
```

Do not use your real Hermes home, real `.env`, or personal profile directory during a public recording.

## Demo 1: generate and validate a profile from flags

See [`generate-from-flags.md`](generate-from-flags.md).

This path shows the fastest concrete value:

1. Scaffold a realistic `security-reviewer` profile.
2. Validate the generated distribution.
3. Show the install command without installing into a real profile home.

## Demo 2: install this repo as `profile-architect`

See [`profile-architect.md`](profile-architect.md).

This path shows the product loop:

1. Install this repository as a profile builder.
2. Start `profile-architect chat`.
3. Ask it to design a database migration reviewer profile.
4. Show generated files or validation output.

## Smoke-test one demo path locally

```bash
scripts/demo_smoke.sh
```

The smoke script creates a temporary fixture, generates a profile from flags, validates it, and installs `profile-architect-demo` into the temporary `HERMES_HOME` when the Hermes CLI is available.

## Cleanup

If you used `scripts/demo_fixture.sh`, it printed a cleanup command:

```bash
scripts/demo_cleanup.sh /tmp/hermes-profile-template-demo.workspace.EXAMPLE/demo-fixture.env
```

The cleanup script refuses to remove paths outside `/tmp/hermes-profile-template-demo.*`.

## Redaction checklist

Before recording:

- Close terminals showing real `.env`, `auth.json`, `~/.hermes`, memories, sessions, logs, or private repos.
- Use the temporary `HERMES_HOME` from `scripts/demo_fixture.sh`.
- Use `/tmp` workspaces, not `/Users/YOUR_NAME/...` or private client paths.
- Use placeholder repository URLs such as `github.com/YOUR_ORG/security-reviewer` until the profile is public.
- Disable shell history display if your prompt or terminal plugin shows past commands.
- Do not paste real API keys. `.env.EXAMPLE` is safe; `.env` is not.

Before publishing:

- Watch the recording once at normal speed.
- Check for home-directory paths, tokens, browser tabs, notification popups, and terminal scrollback.
- Do not commit generated video files in this repository unless a future issue explicitly asks for them.
