# Changelog

All notable changes to this Hermes profile distribution are documented here.

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
