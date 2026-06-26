# Catalog submission snippets

Use this when a generated Hermes profile is ready to share in a profile directory, awesome list, documentation page, or resource roundup.

The goal is a useful catalog entry, not a link drop. Adapt the output to the target repository's contribution rules before opening any PR.

## Render a Markdown card

```bash
python3 scripts/render_catalog_entry.py . \
  --format markdown \
  --source-url https://github.com/YOUR_ORG/YOUR_PROFILE_REPO
```

## Render a YAML manifest snippet

```bash
python3 scripts/render_catalog_entry.py . \
  --format yaml \
  --source-url https://github.com/YOUR_ORG/YOUR_PROFILE_REPO
```

## Render a README resource-list line

```bash
python3 scripts/render_catalog_entry.py . \
  --format resource-line \
  --source-url https://github.com/YOUR_ORG/YOUR_PROFILE_REPO
```

## Render a PR body starter

```bash
python3 scripts/render_catalog_entry.py . \
  --format pr-body \
  --source-url https://github.com/YOUR_ORG/YOUR_PROFILE_REPO
```

## Write output to a file

```bash
python3 scripts/render_catalog_entry.py . \
  --format markdown \
  --source-url https://github.com/YOUR_ORG/YOUR_PROFILE_REPO \
  --output /tmp/catalog-entry.md
```

## Safety checklist

Before submitting generated text anywhere:

1. Replace placeholder source URLs.
2. Confirm the target catalog accepts this format.
3. Keep the value proposition factual and short.
4. Do not invent affiliations, support channels, audits, production guarantees, or community links.
5. Run `make validate` in the profile repo.
6. If the target catalog has a template, paste only the relevant fields into that template.

The renderer reads `distribution.yaml` and, when present, `github-repo-metadata.yaml`. It includes install command, use case, safety constraints, template lineage, topic hints, and a reminder to follow the target catalog's rules.
