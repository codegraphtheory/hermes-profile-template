#!/usr/bin/env python3
"""Render catalog-ready snippets from distribution.yaml."""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def load_manifest(root: Path) -> dict:
    data = yaml.safe_load((root / "distribution.yaml").read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit("distribution.yaml must be a YAML mapping")
    return data


def render_markdown(data: dict, source_url: str) -> str:
    name = data.get("name", "unknown-profile")
    desc = data.get("description", "Hermes profile distribution.")
    return f"- [{name}]({source_url}) - {desc} Install: `hermes profile install {source_url} --alias`"


def render_yaml(data: dict, source_url: str) -> str:
    payload = {
        "name": data.get("name"),
        "description": data.get("description"),
        "source_url": source_url,
        "install": f"hermes profile install {source_url} --alias",
        "topics": data.get("github_topics", []),
    }
    return yaml.safe_dump(payload, sort_keys=False).strip()


def render_pr_body(data: dict, source_url: str) -> str:
    return "\n".join([
        "## Profile catalog submission",
        "",
        f"Profile: `{data.get('name')}`",
        f"Source: {source_url}",
        f"Install: `hermes profile install {source_url} --alias`",
        "",
        "I verified this is a Hermes profile distribution with documented install and validation steps.",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description="Render profile catalog submission snippets.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--format", choices=["markdown", "yaml", "pr-body", "all"], default="markdown")
    args = parser.parse_args()
    data = load_manifest(Path(args.path))
    outputs = {
        "markdown": render_markdown(data, args.source_url),
        "yaml": render_yaml(data, args.source_url),
        "pr-body": render_pr_body(data, args.source_url),
    }
    if args.format == "all":
        for name, text in outputs.items():
            print(f"## {name}\n{text}\n")
    else:
        print(outputs[args.format])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
