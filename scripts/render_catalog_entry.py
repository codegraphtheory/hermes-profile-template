#!/usr/bin/env python3
"""Render catalog submission snippets for Hermes profile distributions."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install pyyaml") from exc

REMINDER_TEXT = """> [!IMPORTANT]
> **Catalog Submission Guidelines**:
> - Always review the target catalog's `CONTRIBUTING.md` or submission rules before creating a pull request.
> - Ensure your description is concise, accurate, and lists real user-facing value.
> - Verify that all local tests (e.g., `make validate` or `make smoke`) pass before submission.
> - Do not include marketing fluff, fake claims, or unverified benchmarks.
"""


def infer_org(root: Path) -> str:
    # Try reading from git remote
    proc = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, capture_output=True, text=True)
    if proc.returncode == 0:
        url = proc.stdout.strip()
        match = re.search(r"(?:github\.com[:/])([^/]+)", url)
        if match:
            return match.group(1)

    # Try reading from github-repo-metadata.yaml homepage
    meta_path = root / "github-repo-metadata.yaml"
    if meta_path.exists():
        try:
            data = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
            homepage = data.get("homepage", "")
            if homepage:
                match = re.search(r"(?:github\.com[:/])([^/]+)", homepage)
                if match:
                    return match.group(1)
        except Exception:
            pass

    return "YOUR_ORG"


def render_template(tmpl_content: str, replacements: dict[str, str]) -> str:
    rendered = tmpl_content
    for key, val in replacements.items():
        placeholder = "{{" + key + "}}"
        rendered = rendered.replace(placeholder, val)
    return rendered


def get_markdown_card(replacements: dict[str, str]) -> str:
    return f"""### {replacements['display_name']}

- **Use Case**: {replacements['description']}
- **Installation Command**: `hermes profile install github.com/{replacements['org']}/{replacements['profile_slug']}`
- **Source Repository**: https://github.com/{replacements['org']}/{replacements['profile_slug']}
- **Safety Constraints**: 
  - Do not expose private keys, credentials, or personal API tokens in configurations.
  - Profile runs in isolated environment separating session database, logs, and workspace.
"""


def get_yaml_manifest(root: Path, replacements: dict[str, str]) -> str:
    tmpl_path = root / "templates" / "catalog" / "manifest-profile.yaml.tmpl"
    if tmpl_path.exists():
        content = tmpl_path.read_text(encoding="utf-8")
        return render_template(content, replacements)

    return f"""  - name: {replacements['profile_slug']}
    template: profiles/{replacements['profile_slug']}
    role: {replacements['description']}
    model_tier: sonnet
    channels: [cli]
    tokens:
      required:
        - {{ key: ANTHROPIC_API_KEY, provider: anthropic }}
      optional:
        - {{ key: OPENROUTER_API_KEY, provider: openrouter }}
    recommended_plugins: []
"""


def get_readme_line(replacements: dict[str, str]) -> str:
    return f"- [{replacements['display_name']}](https://github.com/{replacements['org']}/{replacements['profile_slug']}) - {replacements['description']} (Install: `hermes profile install github.com/{replacements['org']}/{replacements['profile_slug']}`)"


def get_pr_body(replacements: dict[str, str]) -> str:
    return f"""Hello! I would like to submit my custom Hermes Agent profile to your catalog.

### Profile Details
- **Name**: {replacements['display_name']}
- **Installation**: `hermes profile install github.com/{replacements['org']}/{replacements['profile_slug']}`
- **Description/Use Case**: {replacements['description']}
- **Repository URL**: https://github.com/{replacements['org']}/{replacements['profile_slug']}

*This profile distribution is verified. Local validation and smoke tests pass successfully.*
"""


def get_flat_md(root: Path, replacements: dict[str, str]) -> str:
    tmpl_path = root / "templates" / "catalog" / "flat-profile.md.tmpl"
    if tmpl_path.exists():
        content = tmpl_path.read_text(encoding="utf-8")
        return render_template(content, replacements)
    return "Flat Markdown template not found."


def main() -> int:
    parser = argparse.ArgumentParser(description="Render catalog submission snippets for Hermes profile distributions")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--org", help="Override GitHub organization/user name")
    parser.add_argument("--format", default="all", choices=["card", "yaml", "readme", "pr", "flat-md", "all"],
                        help="Select format of output snippet")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    dist_yaml = root / "distribution.yaml"

    if not dist_yaml.exists():
        print(f"ERROR: distribution.yaml does not exist in: {root}", file=sys.stderr)
        return 1

    try:
        data = yaml.safe_load(dist_yaml.read_text(encoding="utf-8")) or {}
        profile_slug = str(data.get("name") or "").strip()
        description = str(data.get("description") or "").strip()
    except Exception as exc:
        print(f"ERROR: Failed to parse distribution.yaml: {exc}", file=sys.stderr)
        return 1

    if not profile_slug:
        print("ERROR: distribution.yaml is missing profile name", file=sys.stderr)
        return 1

    # Form display name by converting kebab-case to Title Case
    display_name = " ".join(word.capitalize() for word in profile_slug.split("-"))
    org = args.org or infer_org(root)

    replacements = {
        "profile_slug": profile_slug,
        "display_name": display_name,
        "description": description,
        "org": org,
    }

    output_parts = []

    if args.format in ("card", "all"):
        output_parts.append("## Concise Markdown Card\n")
        output_parts.append(get_markdown_card(replacements))
        output_parts.append("\n" + "=" * 40 + "\n")

    if args.format in ("yaml", "all"):
        output_parts.append("## YAML Manifest Snippet\n")
        output_parts.append(get_yaml_manifest(root, replacements))
        output_parts.append("\n" + "=" * 40 + "\n")

    if args.format in ("readme", "all"):
        output_parts.append("## README Resource Line\n")
        output_parts.append(get_readme_line(replacements))
        output_parts.append("\n" + "=" * 40 + "\n")

    if args.format in ("pr", "all"):
        output_parts.append("## PR Body Starter Text\n")
        output_parts.append(get_pr_body(replacements))
        output_parts.append("\n" + "=" * 40 + "\n")

    if args.format in ("flat-md", "all"):
        output_parts.append("## Flat Markdown Profile Page\n")
        output_parts.append(get_flat_md(root, replacements))
        output_parts.append("\n" + "=" * 40 + "\n")

    output_parts.append("## Reminder\n")
    output_parts.append(REMINDER_TEXT)

    print("".join(output_parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
