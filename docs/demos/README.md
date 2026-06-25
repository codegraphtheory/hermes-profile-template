# Terminal Demo Kit & Recording Guide

This kit contains scripts, setup commands, and narration guidelines to record clean, safe, and professional terminal demos for the **Hermes Profile Template** without leaking credentials, private user data, or personal filesystem paths.

---

## 🔒 Redaction Checklist

Before you hit record, go through these verification steps to ensure no secrets or sensitive context leak in your recording:

1. **Clear Active Shell Context**:
   - Check your shell prompt (`PS1`). If it contains your full username or private host names, temporarily simplify it:
     ```bash
     export PS1="$ "
     ```
2. **Neutralize Private Filesystem Paths**:
   - Do not record in your user home directory `/home/username`. Instead, run the demo fixture script to switch to a clean temporary workspace under `/tmp`.
3. **Redact Environment Variables / API Keys**:
   - Ensure you are not printing environment variables containing real keys (like `OPENROUTER_API_KEY`, `GITHUB_TOKEN`).
   - Mock them if necessary, or use a temporary test account key.
4. **Purge Shell History**:
   - Disable history writing or start a shell with history writing off:
     ```bash
     unset HISTFILE
     ```
5. **Verify active profiles in Hermes**:
   - Ensure the default profiles directory is isolated using a temporary `HERMES_HOME`.

---

## 📹 Recording with Asciinema

We recommend recording terminal demos using **[asciinema](https://asciinema.org/)** because it captures text format (meaning viewers can copy and paste commands directly from the player) and yields extremely small file sizes.

1. **Install asciinema**:
   - macOS: `brew install asciinema`
   - Linux: `sudo apt install asciinema` (or package manager equivalent)
2. **Start recording**:
   ```bash
   asciinema rec docs/demos/profile-scaffold.cast
   ```
3. **Stop recording**:
   - Press `Ctrl-D` or type `exit` in the shell.
4. **Play back local recording**:
   ```bash
   asciinema play docs/demos/profile-scaffold.cast
   ```

---

## 🎬 Demo 1: Scaffolding and Validating a Profile

**Goal**: Show how to quickly generate a custom, clean profile distribution from CLI flags and run validation checks.

### Setup (Run first)
```bash
# Initialize isolated workspace
source scripts/demo_fixture.sh
```

### Script & Narration

| Step | Terminal Commands | Narration & Voiceover Guidance |
| :--- | :--- | :--- |
| **1. Intro** | `pwd` | *"Today we're going to create a custom Hermes profile distribution template from scratch using flags."* |
| **2. Scaffolding** | `python3 scripts/new_profile.py --name code-cleaner --display-name "Code Cleaner" --description "Reviews codebase files to remove unused imports and dead code." --output ../code-cleaner` | *"We use `scripts/new_profile.py` to specify our profile name, display name, description, and target output directory. This scaffold configures the starter files."* |
| **3. Inspect Output** | `cd ../code-cleaner`<br>`ls -la` | *"Let's change into the output directory. As you can see, we have a fully formed profile structure including `distribution.yaml`, `config.yaml`, and `SOUL.md`."* |
| **4. Validation** | `python3 scripts/validate_profile.py .` | *"Before publishing, we validate the profile. Running the validator ensures that all mandatory fields are filled, JSON files are formatted correctly, and no secrets or runtime cache folders are tracked."* |
| **5. Finish** | `make validate` | *"Our profile successfully passes validation and is ready to commit and publish to GitHub!"* |

---

## 🎬 Demo 2: Installing as `profile-architect`

**Goal**: Show how to install the template as an interactive profile builder and use it to design other profiles using natural language.

### Setup (Run first)
```bash
# Initialize isolated workspace
source scripts/demo_fixture.sh
```

### Script & Narration

| Step | Terminal Commands | Narration & Voiceover Guidance |
| :--- | :--- | :--- |
| **1. Intro** | `hermes --version` | *"We can install this profile template itself directly into Hermes as a specialist assistant."* |
| **2. Installation** | `hermes profile install . --name profile-architect --yes` | *"Using `hermes profile install . --name profile-architect`, we mount our distribution locally into an isolated profile sandbox."* |
| **3. Verify install** | `hermes profile info profile-architect` | *"Running profile info shows our newly installed distribution details, including version and required environment variables."* |
| **4. Scaffolding** | `hermes -p profile-architect chat` | *"Now we can invoke the assistant profile to help us design another profile. We'll start a session and ask it to scaffold a profile for us."* |
| **5. Chat prompt** | *Type prompt:*<br>`Create a Hermes profile for a dockerfile security scanner. It should check docker files for root user execution.` | *"Let's ask it to create a Dockerfile scanner. The profile-architect loads the skills from this template and scaffolds a starter workspace for us interactively."* |
| **6. Clean up** | `exit`<br>`source scripts/demo_cleanup.sh` | *"Once finished, we clean up the temporary profiles. This leaves our main workspace completely pristine."* |
