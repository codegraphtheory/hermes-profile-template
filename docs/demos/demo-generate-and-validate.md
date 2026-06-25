# Demo: Generate and Validate a Profile from Flags

This demo shows how to generate a complete Hermes profile distribution from a
single description and validate it passes all quality checks.

**Estimated duration:** 2–3 minutes

---

## Setup

```bash
# 1. Clone the template
git clone https://github.com/codegraphtheory/hermes-profile-template
cd hermes-profile-template

# 2. Start a clean, secret-free demo workspace
source scripts/demo_fixture.sh
```

---

## Commands (copy-pasteable)

```bash
# Generate a profile using the wizard (non-interactive)
python3 scripts/profile_wizard.py \
  --non-interactive \
  --name "code-reviewer" \
  --display-name "Code Reviewer" \
  --description "Reviews pull requests and suggests improvements." \
  --output /tmp/hermes-profile-builder-demo/code-reviewer.params.yaml

# Generate the full profile distribution
python3 scripts/generate_profile.py \
  --params /tmp/hermes-profile-builder-demo/code-reviewer.params.yaml \
  --output /tmp/hermes-profile-builder-demo/code-reviewer-dist

# Validate the generated distribution
python3 scripts/validate_profile.py /tmp/hermes-profile-builder-demo/code-reviewer-dist

# Run the quality scorecard
python3 scripts/profile_scorecard.py /tmp/hermes-profile-builder-demo/code-reviewer-dist
```

---

## Expected output

```
✅ distribution.yaml found
✅ README.md found
✅ No runtime/secret files found
...
Score: 95/100
```

---

## Voiceover script

> "We start by sourcing the demo fixture — this gives us a clean sandbox
> with no real credentials or home directory paths in the recording."
>
> "Next we run the profile wizard in non-interactive mode, passing the
> name and description as flags. The wizard writes a params YAML file."
>
> "We pass that params file to the generator. It produces a complete
> repository structure: README, SOUL.md, skills, config, and CI."
>
> "Finally, the validator and scorecard confirm the distribution is
> publishable. Zero hard failures means this profile can be installed
> with 'hermes profile install'."

---

## Redaction checklist

Before publishing a recording of this demo:

- [ ] No real `OPENROUTER_API_KEY` or `GITHUB_TOKEN` visible
- [ ] No real home directory path (`/Users/yourname`) in terminal output
- [ ] No real Git remote URLs with credentials embedded
- [ ] Temporary paths use `/tmp/hermes-profile-builder-demo/` not `~/`
- [ ] Shell prompt shows `[hermes-demo]` not your real hostname

---

## Cleanup

```bash
source scripts/demo_cleanup.sh
```
