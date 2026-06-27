# Demo script: install the template as a profile builder

This demo shows the most interesting workflow in this repository: install the template itself as a Hermes profile, then use that profile to create a new installable Hermes profile distribution.

Target length: 2 to 3 minutes.

## Demo goal

Show that `hermes-profile-template` is not only a static GitHub template. It can also be installed as a Hermes profile that helps a user design, generate, validate, and publish new profile distributions.

## Safety setup

Use a clean demo workspace so no personal files, API keys, sessions, or memories appear on screen.

```bash
export DEMO_ROOT="/tmp/hermes-profile-builder-demo"
export HERMES_HOME="$DEMO_ROOT/hermes-home"
rm -rf "$DEMO_ROOT"
mkdir -p "$DEMO_ROOT"
cd "$DEMO_ROOT"
```

Before recording, verify you are not showing secrets:

```bash
printenv | grep -Ei 'api|token|key|secret|password' || true
```

If that prints anything sensitive, clear the terminal before recording.

## Opening narration

"I am going to install `hermes-profile-template` as a Hermes profile called `profile-architect`. Then I will use it to create a new specialized profile distribution in a few minutes. The result is a normal GitHub-ready Hermes profile repo with validation, metadata, docs, and safe defaults."

## Scene 1: Install the template as a Hermes profile

Command:

```bash
hermes profile install github.com/codegraphtheory/hermes-profile-template \
  --name profile-architect \
  --alias \
  --yes
```

Narration:

"Hermes core handles profile install and isolation. This repository supplies the authoring workflow: profile design prompts, generation scripts, validation, CI, and release hygiene."

Expected beats to show:

- install completes successfully
- profile path is shown
- alias `profile-architect` is available

Optional verification:

```bash
hermes profile info profile-architect
```

## Scene 2: Ask the profile builder to create a new profile

Start the profile:

```bash
profile-architect chat
```

Paste this prompt:

```text
Create a Hermes profile distribution for a database migration reviewer.

Use case:
- Reviews SQL migration diffs before deploy.
- Flags destructive operations like dropped columns, table rewrites, missing rollback plans, unsafe locks, and irreversible data changes.
- Produces a short risk summary and a rollback checklist.

Repository requirements:
- Write the generated profile under /tmp/hermes-profile-builder-demo/database-migration-reviewer.
- Include a clear SOUL.md, distribution.yaml, README.md, config.yaml, .env.EXAMPLE, AGENTS.md, CONTRIBUTING.md, SECURITY.md, and one bundled skill for migration review.
- Run validation before finishing.
- Do not use real credentials.
```

Narration while it works:

"The profile builder turns a product description into a structured profile distribution. The important part is that it does not stop at prose. It should write files and run validation."

## Scene 3: Show the generated repository

In a second terminal, or after the profile returns:

```bash
cd /tmp/hermes-profile-builder-demo/database-migration-reviewer
find . -maxdepth 2 -type f | sort
```

Show the key files:

```bash
sed -n '1,120p' distribution.yaml
sed -n '1,80p' SOUL.md
sed -n '1,100p' README.md
```

Narration:

"This is now an installable Hermes profile distribution. It has a manifest, agent instructions, docs, environment examples, and bundled skills. It is ready for a GitHub repository after review."

## Scene 4: Validate and smoke install

Run validation from the generated profile root:

```bash
python3 scripts/validate_profile.py .
```

If the generated profile includes a Makefile:

```bash
make validate
```

Smoke install it into the same temporary Hermes home:

```bash
hermes profile install . --name migration-reviewer-demo --yes --force
hermes profile info migration-reviewer-demo
```

Narration:

"The final check is not just that files exist. Hermes can install the generated profile as a real isolated profile. That is the difference between a README template and an installable profile distribution."

## Scene 5: Close with the publishing path

Show the final publish commands without running them:

```bash
git init -b main
git add .
git commit -m "feat: initial database migration reviewer profile"
git remote add origin git@github.com:YOUR_ORG/database-migration-reviewer.git
git push -u origin main
```

Narration:

"From here, publish the generated directory as a GitHub repo. Users can install it with one command:"

```bash
hermes profile install github.com/YOUR_ORG/database-migration-reviewer --alias
```

## Cleanup

After recording:

```bash
hermes profile delete profile-architect --yes || true
hermes profile delete migration-reviewer-demo --yes || true
rm -rf /tmp/hermes-profile-builder-demo
```

## Short version for a 60-second cut

1. Install builder:

```bash
hermes profile install github.com/codegraphtheory/hermes-profile-template --name profile-architect --alias --yes
```

2. Launch:

```bash
profile-architect chat
```

3. Prompt:

```text
Create a Hermes profile distribution for a database migration reviewer. Write it to /tmp/hermes-profile-builder-demo/database-migration-reviewer and run validation before finishing.
```

4. Show output:

```bash
cd /tmp/hermes-profile-builder-demo/database-migration-reviewer
find . -maxdepth 2 -type f | sort
python3 scripts/validate_profile.py .
hermes profile install . --name migration-reviewer-demo --yes --force
```

## Title ideas

- "Turn a prompt into an installable Hermes profile repo"
- "Using Hermes to build Hermes profiles"
- "From idea to validated agent profile in 3 minutes"

## Thumbnail text

```text
Prompt to Profile Repo
Hermes Profile Template
```

## Description for posting

```text
Demo: install hermes-profile-template as a Hermes profile builder, ask it for a database migration reviewer, then validate and smoke-install the generated profile distribution.
```
