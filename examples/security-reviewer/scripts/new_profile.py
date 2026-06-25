#!/usr/bin/env python3
"""Create a new Hermes profile distribution from command-line parameters."""
from __future__ import annotations

import argparse
from pathlib import Path

from generate_profile import generate, slugify


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Hermes profile distribution")
    parser.add_argument("--name", required=True, help="Profile slug or display name")
    parser.add_argument("--display-name", default="", help="Human-readable profile name")
    parser.add_argument("--description", required=True, help="One sentence profile purpose")
    parser.add_argument("--author", default="Hermes profile author")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--force", action="store_true", help="Overwrite output directory if it exists")
    args = parser.parse_args()

    slug = slugify(args.name)
    display_name = args.display_name or args.name.replace("-", " ").title()
    params = {
        "name": slug,
        "display_name": display_name,
        "description": args.description,
        "author": args.author,
        "version": "0.1.0",
        "license": "MIT",
        "model_provider": "openrouter",
        "model_default": "anthropic/claude-sonnet-4",
        "template_source": {
            "name": "codegraphtheory/hermes-profile-template",
            "url": "https://github.com/codegraphtheory/hermes-profile-template",
            "relationship": "generated-from-template",
        },
        "toolsets": ["file", "terminal", "skills", "web", "session_search", "clarify"],
        "env_requires": [],
        "github_topics": [
            "hermes-agent",
            "ai-agents",
            "agent-profile",
            "profile-distribution",
            "developer-tools",
        ],
    }

    root = Path(__file__).resolve().parents[1]
    output = Path(args.output).resolve()
    generate(params, output, args.force, root)
    print(f"Created Hermes profile distribution: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
