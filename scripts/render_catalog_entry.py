#!/usr/bin/env python3
"""Render catalog submission snippets for Hermes profile distributions."""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install -r requirements.txt") from exc


DEFAULT_CONSTRAINTS = [
    "No secrets or private user data are included.",
    "Claims should be verified against the source repository before publication.",
    "Follow the target catalog's contribution rules before submitting.",
]


@dataclass(frozen=True)
class CatalogProfile:
    name: str
    display_name: str
    description: str
    source_url: str
    install_command: str
    use_case: str
    constraints: list[str]


def slug_to_display(slug: str) -> str:
    words = [part for part in re.split(r"[-_\s]+", slug) if part]
    return " ".join(word.capitalize() for word in words) or slug


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value:
        return [str(value).strip()]
    return []


def build_profile(root: Path, source_url: str | None) -> CatalogProfile:
    manifest_path = root / "distribution.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing required file: {manifest_path}")
    manifest = load_yaml(manifest_path)
    name = str(manifest.get("name") or "").strip()
    if not name:
        raise ValueError("distribution.yaml missing required field: name")
    description = str(manifest.get("description") or "").strip()
    if not description:
        raise ValueError("distribution.yaml missing required field: description")
    display_name = str(manifest.get("display_name") or slug_to_display(name)).strip()
    source = (source_url or f"https://github.com/YOUR_ORG/{name}").rstrip("/")
    constraints = as_list(manifest.get("catalog_constraints")) or DEFAULT_CONSTRAINTS
    return CatalogProfile(
        name=name,
        display_name=display_name,
        description=description,
        source_url=source,
        install_command=f"hermes profile install {source} --alias",
        use_case=str(manifest.get("catalog_use_case") or description).strip(),
        constraints=constraints,
    )


def render_markdown(profile: CatalogProfile) -> str:
    constraints = "\n".join(f"- {item}" for item in profile.constraints)
    return f"""# {profile.display_name}

{profile.description}

- Source: {profile.source_url}
- Install: `{profile.install_command}`
- Use case: {profile.use_case}

## Safety and submission notes

{constraints}
"""


def render_yaml(profile: CatalogProfile) -> str:
    payload = [
        {
            "name": profile.name,
            "display_name": profile.display_name,
            "source": profile.source_url,
            "install": profile.install_command,
            "role": profile.description,
            "use_case": profile.use_case,
            "safety": profile.constraints,
        }
    ]
    return yaml.safe_dump(payload, sort_keys=False, width=120)


def render_resource_line(profile: CatalogProfile) -> str:
    return (
        f"- [{profile.display_name}]({profile.source_url}) - {profile.description} "
        f"Install with `{profile.install_command}`. Follow the target catalog's contribution rules."
    )


def render_pr_body(profile: CatalogProfile) -> str:
    constraints = "\n".join(f"- {item}" for item in profile.constraints)
    return f"""## Catalog entry

Source: {profile.source_url}

Install:

```bash
{profile.install_command}
```

Use case:

{profile.use_case}

Safety and submission notes:

{constraints}

I checked the target catalog format before submitting and avoided unsupported claims, affiliations, or support channels.
"""


def render(profile: CatalogProfile, output_format: str) -> str:
    renderers = {
        "markdown": render_markdown,
        "yaml": render_yaml,
        "resource-line": render_resource_line,
        "pr-body": render_pr_body,
    }
    if output_format == "all":
        sections = []
        for name in ["markdown", "yaml", "resource-line", "pr-body"]:
            sections.append(f"--- {name} ---\n{renderers[name](profile).rstrip()}")
        return "\n\n".join(sections) + "\n"
    return renderers[output_format](profile).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render catalog snippets for a Hermes profile distribution")
    parser.add_argument("path", nargs="?", default=".", help="Profile repository path")
    parser.add_argument(
        "--format",
        choices=["all", "markdown", "yaml", "resource-line", "pr-body"],
        default="markdown",
        help="Snippet format to render",
    )
    parser.add_argument("--source-url", help="Public source URL to include in generated snippets")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    try:
        profile = build_profile(root, args.source_url)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(render(profile, args.format), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
