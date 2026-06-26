# Security Reviewer

A Hermes agent profile for systematic security code review.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Install

```bash
hermes profile install github.com/YOUR_ORG/security-reviewer
```

## Usage

```bash
hermes profile install github.com/YOUR_ORG/security-reviewer --name sec
sec chat
```

Describe the code or repository you want reviewed. The agent will perform
a structured security review and produce an actionable report.

## Validate

```bash
make validate
make smoke
```

## Security

See [SECURITY.md](SECURITY.md) for how to report vulnerabilities.

## License

MIT — see [LICENSE](LICENSE).

---

_Generated from [hermes-profile-template](https://github.com/codegraphtheory/hermes-profile-template)_
