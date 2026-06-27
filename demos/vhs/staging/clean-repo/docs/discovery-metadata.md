# Discovery metadata guide

Generated profile repos should be easy to find, but the metadata should stay accurate and human-readable. Avoid keyword stuffing.

## Baseline description pattern

```text
Installable Hermes Agent profile for [specific workflow], generated from hermes-profile-template.
```

Examples:

```text
Installable Hermes Agent profile for Solidity security reviews, generated from hermes-profile-template.
Installable Hermes Agent profile for Pinecone RAG evaluation, generated from hermes-profile-template.
Installable Hermes Agent profile for open-source release readiness, generated from hermes-profile-template.
Installable Hermes Agent profile for source-grounded research briefs, generated from hermes-profile-template.
```

## Recommended baseline topics

Use a focused subset, not every topic at once:

```text
hermes-agent
ai-agents
agent-profile
profile-distribution
profile-template
prompt-to-repo
developer-tools
automation
cli
validation
```

## Workflow-specific topics

Security profile:

```text
security
code-review
smart-contracts
solidity
threat-modeling
```

RAG profile:

```text
rag
evaluation
retrieval-augmented-generation
pinecone
observability
```

Release profile:

```text
release-management
ci
changelog
smoke-testing
devops
```

Research profile:

```text
research
source-grounded
knowledge-management
documentation
```

## Files and commands

Generated repos can keep this metadata in a checked-in file:

```text
github-repo-metadata.yaml
```

After editing metadata, run:

```bash
python3 scripts/discovery_optimizer.py .
python3 scripts/validate_profile.py .
```

## Publication notes

- Keep `template_source` in `distribution.yaml` so lineage is visible.
- Use `hermes profile install github.com/OWNER/REPO --alias` in the README.
- Link only real public repos.
- Do not claim audits, users, sponsors, or affiliations that have not been verified.
