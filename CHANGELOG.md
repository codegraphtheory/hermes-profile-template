# Changelog

All notable changes to this Hermes profile distribution are documented here.

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
