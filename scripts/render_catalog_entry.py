#!/usr/bin/env python3
"""
Render catalog submission entries from a Hermes profile distribution.

Reads distribution.yaml and emits ready-to-paste snippets for:
  --format markdown   Markdown card for awesome-lists and README galleries
  --format yaml       YAML manifest snippet for profile directories
  --format readme     Single resource-list line for README files
  --format pr         PR body starter text for catalog submissions

Usage:
    python3 scripts/render_catalog_entry.py [PROFILE_DIR]
    python3 scripts/render_catalog_entry.py --format yaml
    python3 scripts/render_catalog_entry.py --format all
    python3 scripts/render_catalog_entry.py examples/security-reviewer --format markdown

Note:
    Always read the target catalog's contribution rules before submitting.
    Replace SOURCE_URL with your published repository URL.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML is required: pip install pyyaml")

FORMATS = ("markdown", "yaml", "readme", "pr", "all")


def load_dist(profile_dir: Path) -> dict:
    dist_file = profile_dir / "distribution.yaml"
    if not dist_file.exists():
        raise SystemExit(f"distribution.yaml not found in {profile_dir}")
    data = yaml.safe_load(dist_file.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit("distribution.yaml must be a YAML mapping")
    return data


def render_markdown(dist: dict) -> str:
    name         = dist.get("name", "unknown")
    display_name = dist.get("display_name", name)
    description  = dist.get("description", "")
    version      = dist.get("version", "0.1.0")
    license_     = dist.get("license", "MIT")
    topics       = dist.get("github_topics", [])
    topics_str   = " ".join(f"`{t}`" for t in topics) if topics else ""

    return f"""## {display_name}

> {description}

**Install:**
```bash
hermes profile install github.com/YOUR_ORG/{name}
```

**Validate:**
```bash
python3 scripts/validate_profile.py .
```

| Field | Value |
|-------|-------|
| Version | {version} |
| License | {license_} |
| Source | [github.com/YOUR_ORG/{name}](https://github.com/YOUR_ORG/{name}) |
{f'| Topics | {topics_str} |' if topics_str else ''}

> ⚠️  Replace `YOUR_ORG/{name}` with your published repository path before submitting.
> Read the target catalog's contribution guidelines before opening a PR.
"""


def render_yaml(dist: dict) -> str:
    name         = dist.get("name", "unknown")
    display_name = dist.get("display_name", name)
    description  = dist.get("description", "")
    version      = dist.get("version", "0.1.0")
    license_     = dist.get("license", "MIT")
    env_requires = dist.get("env_requires", [])

    required_tokens = []
    for req in env_requires:
        if isinstance(req, dict) and req.get("required", True):
            required_tokens.append({"key": req["name"], "provider": "custom"})

    entry = {
        "name":        name,
        "display_name": display_name,
        "description": description,
        "version":     version,
        "license":     license_,
        "source":      f"https://github.com/YOUR_ORG/{name}",
        "install":     f"hermes profile install github.com/YOUR_ORG/{name}",
    }
    if required_tokens:
        entry["tokens"] = {"required": required_tokens}

    result = yaml.dump(entry, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return (
        "# Paste this snippet into the catalog manifest.\n"
        "# Replace YOUR_ORG with your GitHub username or org.\n\n"
        + result
    )


def render_readme(dist: dict) -> str:
    name         = dist.get("name", "unknown")
    display_name = dist.get("display_name", name)
    description  = dist.get("description", "")
    return (
        f"- [{display_name}](https://github.com/YOUR_ORG/{name}) — {description}\n"
        "  <!-- Replace YOUR_ORG with your published repository path -->"
    )


def render_pr(dist: dict) -> str:
    name         = dist.get("name", "unknown")
    display_name = dist.get("display_name", name)
    description  = dist.get("description", "")
    version      = dist.get("version", "0.1.0")

    return f"""## Add {display_name} to the catalog

**Profile:** `{name}` v{version}
**Source:** https://github.com/YOUR_ORG/{name}
**Install:** `hermes profile install github.com/YOUR_ORG/{name}`

### What it does

{description}

### Checklist

- [ ] Profile passes `python3 scripts/validate_profile.py .`
- [ ] No fake links, benchmarks, or community affiliations
- [ ] No secrets or runtime state committed
- [ ] Source repository is publicly accessible

> ⚠️  Replace `YOUR_ORG/{name}` with your actual repository before submitting.
> Read this catalog's contribution rules before opening a PR.
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render catalog submission entries from a Hermes profile distribution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("profile_dir", nargs="?", default=".",
                        help="Path to profile distribution root (default: .)")
    parser.add_argument("--format", "-f", choices=FORMATS, default="all",
                        help="Output format (default: all)")
    args = parser.parse_args()

    profile_dir = Path(args.profile_dir)
    if not profile_dir.exists():
        print(f"Error: {profile_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    dist = load_dist(profile_dir)

    if args.format in ("markdown", "all"):
        print("─" * 60)
        print("MARKDOWN CARD")
        print("─" * 60)
        print(render_markdown(dist))

    if args.format in ("yaml", "all"):
        print("─" * 60)
        print("YAML MANIFEST SNIPPET")
        print("─" * 60)
        print(render_yaml(dist))

    if args.format in ("readme", "all"):
        print("─" * 60)
        print("README RESOURCE-LIST LINE")
        print("─" * 60)
        print(render_readme(dist))
        print()

    if args.format in ("pr", "all"):
        print("─" * 60)
        print("PR BODY STARTER")
        print("─" * 60)
        print(render_pr(dist))


if __name__ == "__main__":
    main()
