#!/usr/bin/env python3
"""Interactive wizard that writes profile.params.yaml for first-time authors."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

DEFAULT_OUTPUT = Path("profile.params.yaml")

CLASSES = {
    "engineer": {
        "name": "engineering-reviewer",
        "display_name": "Engineering Reviewer",
        "description": "Reviews code, architecture, and release plans for production readiness.",
        "toolsets": ["terminal", "file", "github"],
        "principles": ["Prefer verified evidence over claims.", "Keep changes small and reversible."],
        "github_topics": ["hermes-agent", "code-review", "software-quality"],
        "env_requires": [],
    },
    "researcher": {
        "name": "research-assistant",
        "display_name": "Research Assistant",
        "description": "Builds source-grounded briefs with uncertainty labels and reusable handoff notes.",
        "toolsets": ["web", "file"],
        "principles": ["Cite sources before conclusions.", "Separate facts, estimates, and assumptions."],
        "github_topics": ["hermes-agent", "research", "knowledge-management"],
        "env_requires": [],
    },
    "operator": {
        "name": "release-operator",
        "display_name": "Release Operator",
        "description": "Coordinates release readiness, smoke validation, changelogs, and rollout notes.",
        "toolsets": ["terminal", "file", "github"],
        "principles": ["Never ship without a rollback path.", "Automate checks before relying on memory."],
        "github_topics": ["hermes-agent", "release-management", "devops"],
        "env_requires": [],
    },
    "security": {
        "name": "security-reviewer",
        "display_name": "Security Reviewer",
        "description": "Audits code and configs for secrets, vulnerabilities, and unsafe patterns.",
        "toolsets": ["terminal", "file"],
        "principles": [
            "Flag secrets immediately.",
            "Never write or suggest real credentials.",
            "Err on the side of caution.",
        ],
        "github_topics": ["hermes-agent", "security", "code-audit"],
        "env_requires": [],
    },
    "data": {
        "name": "data-analyst",
        "display_name": "Data Analyst",
        "description": "Explores datasets, writes analysis plans, and produces evidence-backed summaries.",
        "toolsets": ["terminal", "file"],
        "principles": [
            "Distinguish correlation from causation.",
            "Show sample size and confidence.",
            "Document assumptions.",
        ],
        "github_topics": ["hermes-agent", "data-analysis", "analytics"],
        "env_requires": [],
    },
}

BUNDLES = {
    "open-source": {
        "toolsets": ["github"],
        "scope": ["Review contribution workflow and public docs."],
        "topics": ["open-source"],
    },
    "safe-demo": {
        "toolsets": ["terminal"],
        "scope": ["Record demos only in temporary workspaces."],
        "topics": ["demo"],
    },
    "security": {
        "toolsets": ["terminal", "file"],
        "scope": ["Scan for secrets and runtime state."],
        "topics": ["security"],
    },
    "api-integration": {
        "toolsets": ["web", "terminal"],
        "scope": ["Call external APIs only with explicit user approval."],
        "topics": ["api", "integration"],
    },
    "database": {
        "toolsets": ["terminal"],
        "scope": ["Never mutate production data without explicit confirmation."],
        "topics": ["database", "sql"],
    },
}


def merge_unique(base: list[str], extra: list[str]) -> list[str]:
    result = list(base)
    for item in extra:
        if item not in result:
            result.append(item)
    return result


def _ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    raw = input(f"{prompt}{hint}: ").strip()
    return raw if raw else default


def _ask_list(prompt: str, example: str = "") -> list[str]:
    hint = f" (e.g. {example})" if example else " (comma-separated, or leave blank)"
    raw = input(f"{prompt}{hint}: ").strip()
    if not raw:
        return []
    return [v.strip() for v in raw.split(",") if v.strip()]


def _choose(prompt: str, choices: list[str]) -> str:
    print(f"\n{prompt}")
    for idx, choice in enumerate(choices, 1):
        print(f"  {idx}) {choice}")
    while True:
        raw = input("Select: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        if raw in choices:
            return raw
        print(f"  Enter 1-{len(choices)} or one of: {', '.join(choices)}")


def interactive_params() -> dict:
    """Prompt the user for every profile field and return a params dict."""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Hermes Profile Wizard — interactive mode")
    print("  Press Enter to accept the default shown in [brackets].")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    profile_class = _choose(
        "Choose a profile class:",
        sorted(CLASSES),
    )
    base = CLASSES[profile_class]

    name = _ask("Profile slug (repo name, no spaces)", base["name"])
    display_name = _ask("Display name", base["display_name"])
    description = _ask("One-sentence description", base["description"])
    version = _ask("Version", "0.1.0")
    author = _ask("Author name", "Profile Author")

    env_vars = _ask_list(
        "Required environment variables",
        "OPENAI_API_KEY, GITHUB_TOKEN",
    )

    extra_topics = _ask_list("Extra GitHub topics", "python, automation")
    topics = merge_unique(list(base["github_topics"]), extra_topics)

    bundle_names = _ask_list(
        f"Bundles to apply ({', '.join(sorted(BUNDLES))})",
        "open-source",
    )
    valid_bundles = [b for b in bundle_names if b in BUNDLES]

    toolsets = list(base["toolsets"])
    scope: list[str] = [
        "Stay within the profile mission.",
        "Ask for missing details only when required.",
    ]
    for bundle_name in valid_bundles:
        bundle = BUNDLES[bundle_name]
        toolsets = merge_unique(toolsets, bundle.get("toolsets", []))
        scope = merge_unique(scope, bundle.get("scope", []))
        topics = merge_unique(topics, bundle.get("topics", []))

    return {
        "name": name,
        "display_name": display_name,
        "description": description,
        "version": version,
        "author": author,
        "license": "MIT",
        "hermes_requires": ">=0.12.0",
        "model_provider": "openrouter",
        "model_default": "anthropic/claude-sonnet-4",
        "toolsets": toolsets,
        "env_requires": env_vars,
        "principles": list(base["principles"]),
        "scope": scope,
        "refusals": ["Do not expose secrets, private state, or unsupported claims."],
        "output_contract": ["Summarize evidence.", "List risks and next actions."],
        "github_topics": topics,
        "template_source": {
            "url": "https://github.com/codegraphtheory/hermes-profile-template",
            "relationship": "generated-from-template",
        },
    }


def build_params(
    profile_class: str,
    bundles: list[str],
    *,
    name: str = "",
    display_name: str = "",
    description: str = "",
    version: str = "0.1.0",
    author: str = "Profile Author",
    env_requires: list[str] | None = None,
    extra_topics: list[str] | None = None,
) -> dict:
    """Build a params dict non-interactively from explicit arguments."""
    if profile_class not in CLASSES:
        raise ValueError(
            f"Unknown profile class: {profile_class!r}. Choose from: {sorted(CLASSES)}"
        )
    base = CLASSES[profile_class]
    scope: list[str] = [
        "Stay within the profile mission.",
        "Ask for missing deployment details only when required.",
    ]
    topics = list(base["github_topics"])
    toolsets = list(base["toolsets"])
    for bundle_name in bundles:
        if bundle_name not in BUNDLES:
            raise ValueError(
                f"Unknown bundle: {bundle_name!r}. Choose from: {sorted(BUNDLES)}"
            )
        bundle = BUNDLES[bundle_name]
        scope = merge_unique(scope, bundle.get("scope", []))
        topics = merge_unique(topics, bundle.get("topics", []))
        toolsets = merge_unique(toolsets, bundle.get("toolsets", []))
    if extra_topics:
        topics = merge_unique(topics, extra_topics)
    return {
        "name": name or base["name"],
        "display_name": display_name or base["display_name"],
        "description": description or base["description"],
        "version": version,
        "author": author,
        "license": "MIT",
        "hermes_requires": ">=0.12.0",
        "model_provider": "openrouter",
        "model_default": "anthropic/claude-sonnet-4",
        "toolsets": toolsets,
        "env_requires": env_requires if env_requires is not None else list(base.get("env_requires", [])),
        "principles": list(base["principles"]),
        "scope": scope,
        "refusals": ["Do not expose secrets, private state, or unsupported claims."],
        "output_contract": ["Summarize evidence.", "List risks and next actions."],
        "github_topics": topics,
        "template_source": {
            "url": "https://github.com/codegraphtheory/hermes-profile-template",
            "relationship": "generated-from-template",
        },
    }


def write_params(path: Path, params: dict, *, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(
            f"Refusing to overwrite {path}. Re-run with --force or choose a different --output path."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(params, sort_keys=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Interactive wizard that writes profile.params.yaml for first-time profile authors.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fully interactive — prompted for every field:
  python3 scripts/profile_wizard.py

  # Non-interactive (CI-safe):
  python3 scripts/profile_wizard.py --class engineer --bundle open-source --output /tmp/params.yaml --force

  # Write params then generate the profile in one command:
  python3 scripts/profile_wizard.py --class researcher --generate --output /tmp/params.yaml --output-dir /tmp/my-profile --force
""",
    )
    parser.add_argument(
        "--class", dest="profile_class", choices=sorted(CLASSES),
        help="Profile class (skips interactive class prompt)",
    )
    parser.add_argument(
        "--bundle", dest="bundles", action="append", choices=sorted(BUNDLES),
        default=[], metavar="BUNDLE", help="Apply a bundle (repeatable)",
    )
    parser.add_argument("--name", help="Profile slug override")
    parser.add_argument("--display-name", help="Display name override")
    parser.add_argument("--description", help="Description override")
    parser.add_argument("--version", default="0.1.0", help="Version (default: 0.1.0)")
    parser.add_argument("--author", default="Profile Author", help="Author name")
    parser.add_argument(
        "--env-requires", action="append", default=[], metavar="VAR",
        help="Required env var (repeatable)",
    )
    parser.add_argument(
        "--topic", dest="extra_topics", action="append", default=[], metavar="TOPIC",
        help="Extra GitHub topic (repeatable)",
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help="Where to write the params file (default: profile.params.yaml)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing output file")
    parser.add_argument(
        "--generate", action="store_true",
        help="Run generate_profile.py after writing params",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        help="Output directory for generate_profile.py (required with --generate)",
    )
    args = parser.parse_args()

    if args.profile_class:
        params = build_params(
            args.profile_class,
            args.bundles,
            name=args.name or "",
            display_name=args.display_name or "",
            description=args.description or "",
            version=args.version,
            author=args.author,
            env_requires=args.env_requires or None,
            extra_topics=args.extra_topics or None,
        )
    else:
        params = interactive_params()

    write_params(args.output, params, force=args.force)
    print(f"\n✓ Wrote {args.output}")

    generate_script = Path(__file__).parent / "generate_profile.py"

    if args.generate:
        if not args.output_dir:
            print("Error: --output-dir is required with --generate", file=sys.stderr)
            return 1
        print(f"\nRunning generate_profile.py → {args.output_dir}")
        result = subprocess.run(
            [sys.executable, str(generate_script),
             "--params", str(args.output),
             "--output", str(args.output_dir)],
            check=False,
        )
        return result.returncode

    print(f"\nNext step:")
    print(f"  python3 {generate_script} --params {args.output} --output ../{params['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
