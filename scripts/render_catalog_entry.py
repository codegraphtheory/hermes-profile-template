#!/usr/bin/env python3
"""Render non-spammy catalog submission snippets for a Hermes profile distribution."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install pyyaml") from exc

SUPPORTED_FORMATS = ("markdown", "yaml", "resource-line", "pr-body")
DEFAULT_SOURCE_URL = "https://github.com/YOUR_ORG/YOUR_PROFILE_REPO"


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing required file: {path}") from exc
    except Exception as exc:
        raise SystemExit(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Expected YAML mapping in {path}")
    return data


def as_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value:
        return [str(value).strip()]
    return []


def short_sentence(text: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    trimmed = text[: limit - 1].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{trimmed}."


def install_command(source_url: str) -> str:
    return f"hermes profile install {source_url} --alias"


def load_profile(root: Path, source_url: str) -> dict[str, Any]:
    manifest = load_yaml(root / "distribution.yaml")
    metadata_path = root / "github-repo-metadata.yaml"
    metadata = load_yaml(metadata_path) if metadata_path.exists() else {}
    name = as_text(manifest.get("name"), root.name)
    description = short_sentence(as_text(manifest.get("description"), f"Hermes Agent profile: {name}"))
    topics = as_list(metadata.get("topics"))
    env_requires = []
    for item in manifest.get("env_requires") or []:
        if isinstance(item, dict) and item.get("name"):
            env_requires.append(
                {
                    "name": str(item["name"]),
                    "required": bool(item.get("required", True)),
                    "description": as_text(item.get("description"), "Required by this profile"),
                }
            )
    template_source = manifest.get("template_source") if isinstance(manifest.get("template_source"), dict) else {}
    return {
        "name": name,
        "description": description,
        "version": as_text(manifest.get("version"), "0.0.0"),
        "license": as_text(manifest.get("license"), "unspecified"),
        "author": as_text(manifest.get("author"), "unspecified"),
        "source_url": source_url,
        "install_command": install_command(source_url),
        "topics": topics,
        "env_requires": env_requires,
        "template_source": template_source or None,
        "safety": "Does not include runtime state, secrets, memories, sessions, or private user data. Validate before publishing with `make validate`.",
    }


def render_markdown(profile: dict[str, Any]) -> str:
    topic_text = ", ".join(f"`{topic}`" for topic in profile["topics"][:10]) or "Add catalog-appropriate topics before submitting."
    template = profile.get("template_source") or {}
    lineage = ""
    if template.get("url"):
        lineage = f"\n- Source template: [{template.get('name') or 'profile template'}]({template['url']})"
    return f"""## {profile['name']}

{profile['description']}

- Install: `{profile['install_command']}`
- Source: {profile['source_url']}
- Version: `{profile['version']}`
- License: `{profile['license']}`
- Topics: {topic_text}{lineage}
- Safety: {profile['safety']}

Before submitting this entry, adapt it to the target catalog's contribution rules and remove placeholders that do not apply.
""".rstrip() + "\n"


def render_yaml(profile: dict[str, Any]) -> str:
    data = {
        "name": profile["name"],
        "description": profile["description"],
        "source_url": profile["source_url"],
        "install": profile["install_command"],
        "version": profile["version"],
        "license": profile["license"],
        "topics": profile["topics"],
        "env_requires": profile["env_requires"],
        "safety": profile["safety"],
        "catalog_submission_note": "Follow the target catalog's contribution rules; do not invent affiliations, support channels, or production claims.",
    }
    if profile.get("template_source"):
        data["template_source"] = profile["template_source"]
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)


def render_resource_line(profile: dict[str, Any]) -> str:
    return f"- [{profile['name']}]({profile['source_url']}) — {profile['description']} Install: `{profile['install_command']}`\n"


def render_pr_body(profile: dict[str, Any]) -> str:
    return f"""## Catalog submission

This PR proposes adding `{profile['name']}`, a Hermes Agent profile distribution.

## User value

{profile['description']}

## Install

```bash
{profile['install_command']}
```

## Safety and maintenance notes

- Source: {profile['source_url']}
- Version: {profile['version']}
- License: {profile['license']}
- Safety: {profile['safety']}
- I checked this target catalog's contribution rules before submitting.
- This entry does not claim unofficial affiliations, audits, support channels, or production guarantees.
""".rstrip() + "\n"


def render(profile: dict[str, Any], fmt: str) -> str:
    if fmt == "markdown":
        return render_markdown(profile)
    if fmt == "yaml":
        return render_yaml(profile)
    if fmt == "resource-line":
        return render_resource_line(profile)
    if fmt == "pr-body":
        return render_pr_body(profile)
    raise SystemExit(f"Unsupported format: {fmt}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render catalog submission snippets for a Hermes profile distribution")
    parser.add_argument("profile_dir", nargs="?", default=".", help="Profile distribution directory, default: current directory")
    parser.add_argument("--format", choices=SUPPORTED_FORMATS, default="markdown", help="Output format")
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL, help="Published repository URL or placeholder to include in output")
    parser.add_argument("--output", help="Write output to this file instead of stdout")
    parser.add_argument("--dump-json", action="store_true", help="Debug: emit the normalized profile data as JSON")
    args = parser.parse_args()

    root = Path(args.profile_dir).resolve()
    profile = load_profile(root, args.source_url)
    output = json.dumps(profile, indent=2, sort_keys=True) + "\n" if args.dump_json else render(profile, args.format)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
