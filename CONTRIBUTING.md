# Contributing

Thanks for improving this Hermes profile distribution.

## Development loop

1. Inspect the current repository state.
2. Make focused changes.
3. Run validation:

```bash
python3 scripts/validate_profile.py .
```

4. Run generator smoke tests when scripts, templates, or default profile files change:

```bash
python3 scripts/generate_profile.py \
  --params templates/profile.params.yaml \
  --output /tmp/profile-template-smoke
python3 /tmp/profile-template-smoke/scripts/validate_profile.py /tmp/profile-template-smoke
```

5. For release-relevant changes, bump `distribution.yaml` and add a matching `CHANGELOG.md` entry.

## Profile quality bar

A good profile distribution has:

- Clear `SOUL.md` identity, mission, boundaries, and output contract.
- Safe `config.yaml` defaults with credentials kept outside git.
- Reusable bundled skills with valid `SKILL.md` frontmatter.
- Accurate `distribution.yaml` metadata.
- README install and validation instructions.
- No runtime state, secrets, local caches, or private user data.

## Pull request checklist

- [ ] `python3 scripts/validate_profile.py .` passes.
- [ ] Generated profile smoke test passes when relevant.
- [ ] Version and changelog are updated for release-relevant changes.
- [ ] New docs do not claim unconfigured tools, credentials, community links, or integrations.
- [ ] No secrets, runtime files, or local caches are committed.
