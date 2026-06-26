# Sample Profile

Install this profile:

```bash
hermes profile install github.com/example/sample-profile --name sample-profile --yes
```

Validate and smoke test it:

```bash
python3 scripts/validate_profile.py .
hermes profile install . --name sample-profile-demo --yes --force
```
