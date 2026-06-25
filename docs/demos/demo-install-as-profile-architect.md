# Demo: Install as profile-architect and Use Interactively

This demo shows installing this repo as a Hermes profile named `profile-architect`
and using it as an interactive profile builder.

**Estimated duration:** 3–4 minutes

---

## Setup

```bash
# Start a clean demo workspace
source scripts/demo_fixture.sh
```

---

## Commands (copy-pasteable)

```bash
# Install the template as a Hermes profile
hermes profile install github.com/codegraphtheory/hermes-profile-template \
  --name profile-architect \
  --alias \
  --yes

# Verify installation
hermes profile list

# Start an interactive session
profile-architect chat
```

**Inside the chat session:**

```
You: Create a profile for a Python code reviewer that checks style and tests.
```

```
You: Generate the distribution and validate it.
```

```
You: Show me the scorecard output.
```

---

## Voiceover script

> "After sourcing the fixture, we install this template as a Hermes profile
> called 'profile-architect'. The --alias flag makes it available as a
> standalone command."
>
> "'hermes profile list' confirms it installed correctly alongside any
> other profiles we have."
>
> "We start a chat session. In plain English we describe the profile we
> want. profile-architect generates the params file, runs the generator,
> and returns a validated distribution — all in one conversation."
>
> "The scorecard at the end gives a numeric quality signal we can paste
> directly into the generated README or a release note."

---

## Redaction checklist

Before publishing a recording of this demo:

- [ ] No real `OPENROUTER_API_KEY` or `GITHUB_TOKEN` visible
- [ ] No real home directory path in terminal output
- [ ] HERMES_HOME points to `/tmp/hermes-profile-builder-demo/hermes-home`
- [ ] No personal profile names or private repo URLs visible
- [ ] Shell prompt shows `[hermes-demo]` not your real hostname

---

## Cleanup

```bash
source scripts/demo_cleanup.sh
```
