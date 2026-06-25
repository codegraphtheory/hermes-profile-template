# Changelog

All notable changes to this Hermes profile distribution are documented here.

## 0.3.1

- Added release readiness checklist workflow.

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
