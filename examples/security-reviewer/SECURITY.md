# Security Policy

## Supported versions

The current `main` branch and the latest tagged release receive security fixes.

## Reporting a vulnerability

Please do not disclose vulnerabilities, leaked secrets, or private user data in public issues.

Report security concerns by opening a private GitHub security advisory when available, or by contacting the repository maintainers through a trusted private channel listed on the repository profile.

Include:

- Affected file or feature.
- Reproduction steps, if safe to share.
- Impact and likely severity.
- Suggested mitigation, if known.

## Secret handling

Never commit `.env`, API keys, OAuth tokens, cookies, session dumps, local memories, logs, runtime databases, or private user data. Use `.env.EXAMPLE` with placeholder values only.

## Profile distribution safety

Generated profiles should be installable with `hermes profile install`, should keep credentials external, and should document any required third-party services in `distribution.yaml` and `.env.EXAMPLE`.
