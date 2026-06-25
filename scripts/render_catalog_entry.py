#!/usr/bin/env python3
"""Render catalog submission entries for a Hermes profile distribution.

Reads distribution.yaml from a profile root and emits clean, non-spammy
entries suitable for awesome lists, profile directories, and catalog PRs.

Usage:
    # Markdown card (default)
    python3 scripts/render_catalog_entry.py [path]

    # YAML manifest snippet
    python3 scripts/render_catalog_entry.py [path] --format yaml

    # README resource-list line
    python3 scripts/render_catalog_entry.py [path] --format readme-line

    # PR body starter
    python3 scripts/render_catalog_entry.py [path] --format pr-body

    # All formats at once
    python3 scripts/render_catalog_entry.py [path] --format all

    # Point at a specific distribution.yaml
    python3 scripts/render_catalog_entry.py --dist path/to/distribution.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

FORMATS = ("markdown", "yaml", "readme-line", "pr-body", "all")

CATALOG_REMINDER = (
    "<!-- REMINDER: Read the target catalog's contribution guidelines before "
    "submitting. Follow their format requirements exactly and avoid duplicate entries. -->"
)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_distribution(dist_path: Path) -> dict[str, Any]:
    if yaml is None:
        raise SystemExit(
            "ERROR: PyYAML is required. Install with: python3 -m pip install pyyaml"
        )
    if not dist_path.exists():
        raise SystemExit(f"ERROR: {dist_path} not found")
    try:
        data = yaml.safe_load(dist_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise SystemExit(f"ERROR: Could not parse {dist_path}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"ERROR: {dist_path} must be a YAML mapping")
    return data


def _field(data: dict, key: str, fallback: str = "") -> str:
    return str(data.get(key) or fallback).strip()


def _env_names(data: dict) -> list[str]:
    env = data.get("env_requires") or []
    if not isinstance(env, list):
        return []
    return [e["name"] for e in env if isinstance(e, dict) and e.get("name")]


def _source_url(data: dict, dist_path: Path) -> str:
    ts = data.get("template_source")
    if isinstance(ts, dict) and ts.get("url"):
        # Derive the generated repo URL from the template source — use placeholder
        pass
    # Try github-repo-metadata.yaml in same directory
    meta_path = dist_path.parent / "github-repo-metadata.yaml"
    if meta_path.exists() and yaml is not None:
        try:
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
            if isinstance(meta, dict) and meta.get("url"):
                return str(meta["url"]).strip()
        except Exception:
            pass
    return "https://github.com/YOUR_ORG/" + _field(data, "name", "your-profile")


def _install_cmd(data: dict, source_url: str) -> str:
    slug = source_url.replace("https://github.com/", "")
    return f"hermes profile install {slug}"


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def render_markdown(data: dict, source_url: str) -> str:
    name = _field(data, "name", "unknown-profile")
    display = _field(data, "display_name") or name.replace("-", " ").title()
    description = _field(data, "description", "A Hermes Agent profile.")
    author = _field(data, "author")
    license_ = _field(data, "license")
    version = _field(data, "version")
    env_names = _env_names(data)
    install = _install_cmd(data, source_url)

    lines: list[str] = [
        CATALOG_REMINDER,
        "",
        f"### [{display}]({source_url})",
        "",
        description,
        "",
        f"**Install:** `{install}`",
        "",
    ]

    if env_names:
        lines += [
            f"**Required env vars:** {', '.join(f'`{e}`' for e in env_names)}",
            "",
        ]

    meta: list[str] = []
    if version:
        meta.append(f"version {version}")
    if author:
        meta.append(f"by {author}")
    if license_:
        meta.append(f"{license_} license")
    if meta:
        lines += [" · ".join(meta), ""]

    lines += [
        "**Safety constraints:**",
        "- Does not fabricate claims, links, or affiliations.",
        "- Does not expose secrets or private user data.",
        "- Does not take destructive actions without explicit approval.",
        "",
        f"[Source]({source_url}) · "
        f"[Report an issue]({source_url}/issues)",
    ]

    return "\n".join(lines)


def render_yaml(data: dict, source_url: str) -> str:
    name = _field(data, "name", "unknown-profile")
    description = _field(data, "description", "A Hermes Agent profile.")
    env_names = _env_names(data)

    required_tokens = [{"key": "ANTHROPIC_API_KEY", "provider": "anthropic"}]
    optional_tokens: list[dict] = []
    for e in env_names:
        optional_tokens.append({"key": e, "provider": "profile"})

    entry: dict[str, Any] = {
        "name": name,
        "source": source_url,
        "description": description,
        "install": _install_cmd(data, source_url),
        "tokens": {
            "required": required_tokens,
            "optional": optional_tokens,
        },
    }

    if yaml is not None:
        rendered = yaml.dump(
            entry, default_flow_style=False, allow_unicode=True, sort_keys=False
        ).rstrip()
    else:
        rendered = f"name: {name}\nsource: {source_url}\ndescription: {description}"

    return "\n".join([
        "# " + CATALOG_REMINDER.lstrip("<!-- ").rstrip(" -->"),
        rendered,
    ])


def render_readme_line(data: dict, source_url: str) -> str:
    display = _field(data, "display_name") or _field(data, "name", "Profile").replace("-", " ").title()
    description = _field(data, "description", "A Hermes Agent profile.")
    # Truncate description to one sentence
    first_sentence = description.split(".")[0].strip()
    return (
        f"- [{display}]({source_url}) — {first_sentence}. "
        f"`hermes profile install {source_url.replace('https://github.com/', '')}`"
    )


def render_pr_body(data: dict, source_url: str) -> str:
    name = _field(data, "name", "unknown-profile")
    display = _field(data, "display_name") or name.replace("-", " ").title()
    description = _field(data, "description", "A Hermes Agent profile.")
    author = _field(data, "author")
    license_ = _field(data, "license")
    install = _install_cmd(data, source_url)
    env_names = _env_names(data)

    lines: list[str] = [
        CATALOG_REMINDER,
        "",
        f"## Add {display} to the catalog",
        "",
        "### What this profile does",
        "",
        description,
        "",
        "### Install",
        "",
        f"```",
        install,
        f"```",
        "",
        "### Source",
        "",
        source_url,
        "",
    ]

    if env_names:
        lines += [
            "### Required environment variables",
            "",
        ] + [f"- `{e}`" for e in env_names] + [""]

    if author or license_:
        lines.append("### Metadata")
        lines.append("")
        if author:
            lines.append(f"- Author: {author}")
        if license_:
            lines.append(f"- License: {license_}")
        lines.append("")

    lines += [
        "### Safety constraints",
        "",
        "- Does not fabricate claims, links, benchmarks, or affiliations.",
        "- Does not expose secrets or private user data.",
        "- Does not take destructive actions without explicit approval.",
        "",
        "### Checklist",
        "",
        "- [ ] I have read this catalog's contribution guidelines",
        "- [ ] This profile is not already listed",
        "- [ ] The install command has been tested",
        "- [ ] The description is accurate and does not contain marketing claims",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render catalog submission entries for a Hermes profile distribution."
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Path to profile root directory (default: current directory)"
    )
    parser.add_argument(
        "--dist",
        help="Path to distribution.yaml directly (overrides path argument)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=FORMATS,
        default="markdown",
        help="Output format: markdown (default), yaml, readme-line, pr-body, all"
    )
    args = parser.parse_args()

    if args.dist:
        dist_path = Path(args.dist).resolve()
    else:
        dist_path = (Path(args.path) / "distribution.yaml").resolve()

    data = load_distribution(dist_path)
    source_url = _source_url(data, dist_path)

    sep = "\n" + "-" * 60 + "\n"

    fmt = args.format
    if fmt == "markdown" or fmt == "all":
        print(render_markdown(data, source_url))
    if fmt == "all":
        print(sep)
    if fmt == "yaml" or fmt == "all":
        print(render_yaml(data, source_url))
    if fmt == "all":
        print(sep)
    if fmt == "readme-line" or fmt == "all":
        print(render_readme_line(data, source_url))
    if fmt == "all":
        print(sep)
    if fmt == "pr-body" or fmt == "all":
        print(render_pr_body(data, source_url))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
