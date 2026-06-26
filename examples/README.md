# Searchable Examples Gallery

This directory contains generated profile examples for reference.

## Available Examples

| Profile | Type | Description |
|---------|------|-------------|
| basic-developer | Developer | Simple developer profile |
| open-source-maintainer | Maintainer | Open source maintainer showcase |
| data-scientist | Data | Data science portfolio |
| devops-engineer | DevOps | DevOps and infrastructure profile |
| full-stack-creator | Creator | Full-stack development profile |

## CLI Usage

```bash
# List all examples
python scripts/list_examples.py

# Show a specific example
python scripts/list_examples.py --show basic-developer

# Generate from example template
python scripts/list_examples.py --generate open-source-maintainer --output ./my-profile
```
