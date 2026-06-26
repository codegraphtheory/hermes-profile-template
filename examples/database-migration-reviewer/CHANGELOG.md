# Changelog

All notable changes to this Hermes profile distribution are documented here.

## 0.6.5

- Integrated community contributor toolkit: release readiness, scorecard, discovery, wizard, demo, catalog, examples, and reusable validation action.
- Credited first-time contributor PR authors through co-author trailers while consolidating overlapping implementations into one verified maintainer integration.

## 0.6.4

- Fixed live Hermes profile evaluation so generated agents run from the generated profile directory instead of inheriting the template author's repo context.
- Added isolated live-profile installation, configurable provider/model/timeout/max-turn controls, and cleanup for noisy Hermes CLI warning output.
- Stopped generated customer profiles from bundling template authoring skills, keeping generated agents focused on their domain workflow.
- Reworked the local web demo into a finite-state interface with discrete prompt, progress, and fullscreen results panels plus smooth transitions and back/start-over navigation.

## 0.6.3

- Added real Hermes LLM calls to the local web demo pipeline: one call expands the sentence into a mature profile prompt, another reviews generated profile quality.
- Split backend work into explicit status stages so the UI receives snappier progress updates instead of jumping from start to finish.
- Added inline generated-file preview endpoints and clickable file rows in the web UI, so users can inspect files without downloading the zip.
- Added `--profile-prompt-file` support to `scripts/generate_from_sentence.py` so Hermes-refined prompts can drive deterministic repo generation.

## 0.6.2

- Fixed local web demo layout collisions by separating the prompt pane, status rail, and detail workbench columns.
- Added an embedded playable demo iframe directly in the result window.
- Added a clearer generated-output summary with quality checks, important files, install command, and artifact links.
- Exposed generated file metadata and validation-quality signals from the local backend result payload.

## 0.6.1

- Redesigned the local web demo into a fixed fullscreen windowpane experience.
- Replaced the marketing-style landing page with a single sentence text box as the initial state.
- Added progressive workbench panels that unveil prompt, params, repo, demo, diagram, validation, and package details as generation runs.
- Added richer job status metadata for the frontend while keeping the backend local and standard-library based.

## 0.6.0

- Added `scripts/generate_from_sentence.py`, a deterministic local backend entrypoint that turns one sentence into an installable Hermes profile repo.
- Added generated demo artifacts: `demo/index.html`, `docs/playable-demo.md`, `docs/output-diagram.svg`, and `docs/validation-report.md`.
- Added safe zip packaging for generated profile downloads.
- Added `web-demo/server.py` and a static local webpage that submits generation jobs and displays download, demo, diagram, prompt, and validation links.
- Added `make sentence-smoke` and `make web-demo` shortcuts.
- Documented the local web demo and the one-sentence generation path.

## 0.5.0

- Added a bundled `prompt-engineering` skill that expands a simple profile idea into a mature Hermes profile prompt and generation brief.
- Added `templates/prompts/prompt-to-profile.md` as a reusable prompt expansion template.
- Updated `profile-architect` and `profile-craft` workflows so short user ideas are expanded before params generation.
- Added `profile_prompt` support to generated params and `docs/profile-prompt.md` output so generated repos preserve the mature prompt that shaped them.
- Updated generated profile READMEs to explain the preserved design prompt and regeneration workflow.
- Updated support-file copying so generated repos include the template's authoring skills without copying unrelated runtime skills.

## 0.4.0

- Rebuilt the README around the literal prompt-to-installable-profile-repo workflow.
- Clarified every usage path so it ends in validation and `hermes profile install`.
- Updated the installed profile instructions to require repository creation, validation, and optional smoke install when users ask for a new profile.
- Updated the bundled `profile-craft` skill with a prompt-to-repo workflow.
- Added the interactive profile-builder demo script to the documented usage path.
- Fixed generated `config.yaml` model keys so installed template and generated profiles resolve models correctly in Hermes.
- Fixed prompt-to-repo generation from an installed profile so seeded runtime skills are not copied into generated repos.

## 0.3.0

- Clarified that this repository is a developer authoring system built on top of Hermes Agent's native profile distribution runtime.
- Added a profile distribution contract document that separates Hermes core responsibilities, template responsibilities, and author responsibilities.
- Added `requirements.txt` and `Makefile` shortcuts for repeatable dependency installation, validation, smoke tests, generation smoke tests, release checks, and cleanup.
- Updated CI to install dependencies through `requirements.txt` and compile scripts as part of validation.
- Updated generated distributions to include the same convenience dependency and Makefile workflow.

## 0.2.0

- Added release metadata guard, changelog discipline, and pull request release checks.
- Added contributor and security documentation for public profile distributions.
- Hardened validation and ignore rules for runtime state, local caches, and generated artifacts.
- Added install smoke testing for repository validation, generation, and Hermes profile installation.
- Added repeatable GitHub repository metadata automation for descriptions, homepage, and topics.

## 0.1.0

- Initial Hermes profile template with deterministic generation, validation, bundled profile-craft skill, catalog snippets, and installable distribution metadata.
