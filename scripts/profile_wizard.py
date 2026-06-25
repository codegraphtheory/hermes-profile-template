#!/usr/bin/env python3
"""Interactive wizard that writes profile.params.yaml and kicks off generation.

Usage (interactive):
    python3 scripts/profile_wizard.py

Usage (non-interactive / CI):
    python3 scripts/profile_wizard.py \\
        --name my-agent \\
        --display-name "My Agent" \\
        --description "Does useful things." \\
        --author "Alice" \\
        --output-dir /tmp/my-agent-output \\
        --params-out /tmp/my-agent.params.yaml \\
        --no-generate
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def _ask(prompt: str, default: str = "", required: bool = False) -> str:
    if default:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "
    while True:
        value = input(display).strip()
        if not value:
            value = default
        if value or not required:
            return value
        print("  This field is required.")


def _ask_list(prompt: str, hint: str = "") -> list[str]:
    print(f"{prompt}")
    if hint:
        print(f"  ({hint})")
    print("  Enter one per line. Empty line to finish.")
    items: list[str] = []
    while True:
        line = input("  > ").strip()
        if not line:
            break
        items.append(line)
    return items


def _ask_bool(prompt: str, default: bool = True) -> bool:
    default_str = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please enter y or n.")


def _ask_choice(prompt: str, choices: list[str], default: str = "") -> list[str]:
    print(f"{prompt}")
    for i, c in enumerate(choices, 1):
        mark = "*" if c == default else " "
        print(f"  {mark} {i}. {c}")
    print("  Enter numbers separated by spaces, or press Enter to accept all.")
    raw = input("  > ").strip()
    if not raw:
        return list(choices)
    selected: list[str] = []
    for token in raw.split():
        try:
            idx = int(token) - 1
            if 0 <= idx < len(choices):
                selected.append(choices[idx])
        except ValueError:
            pass
    return selected or list(choices)


# ---------------------------------------------------------------------------
# Param collection
# ---------------------------------------------------------------------------

AVAILABLE_TOOLSETS = ["file", "terminal", "skills", "web", "session_search", "clarify"]


def collect_params_interactive() -> dict:
    print("\n" + "=" * 60)
    print("  Hermes Profile Wizard")
    print("  Answer the prompts to generate profile.params.yaml")
    print("=" * 60 + "\n")

    name = _ask("Profile name (lowercase-kebab-case)", required=True)
    # Normalise to kebab-case
    import re
    name = re.sub(r"[^a-z0-9-]", "-", name.lower()).strip("-")

    display_name = _ask("Display name", default=name.replace("-", " ").title())
    description = _ask("One-sentence description of what this profile does", required=True)
    author = _ask("Author name", default="Hermes profile author")
    version = _ask("Version", default="0.1.0")
    license_ = _ask("License", default="MIT")

    print()
    toolsets = _ask_choice(
        "Toolsets to include (press Enter to keep all):",
        AVAILABLE_TOOLSETS,
    )

    print()
    target_users = _ask("Who are the target users of this profile?",
                        default="Developers building or reviewing software")

    print()
    add_env = _ask_bool("Do you need required environment variables?", default=False)
    env_requires: list[dict] = []
    if add_env:
        print("  For each env var enter: NAME  description  (required? y/n)")
        while True:
            var_name = input("  Variable name (empty to finish): ").strip().upper()
            if not var_name:
                break
            var_desc = input(f"  Description for {var_name}: ").strip()
            var_req = _ask_bool(f"  Is {var_name} required?", default=False)
            env_requires.append({"name": var_name, "description": var_desc, "required": var_req})

    print()
    principles = _ask_list(
        "Core principles (what should this profile always do)?",
        hint="e.g. 'Prefer simple solutions over clever ones'",
    )
    if not principles:
        principles = [
            "Ship working artifacts, not plans alone.",
            "Use tools to inspect live state before making factual claims.",
            "Keep user data private and never expose secrets.",
        ]

    print()
    scope = _ask_list(
        "Scope items (what is this profile for)?",
        hint="e.g. 'Build and verify software changes'",
    )
    if not scope:
        scope = ["Complete the user's stated goal with clear verification."]

    print()
    refusals = _ask_list(
        "Refusals (what should this profile never do)?",
        hint="e.g. 'Credential theft or secret exposure'",
    )
    if not refusals:
        refusals = [
            "Credential theft or secret exposure.",
            "Hidden persistence, backdoors, or deceptive automation.",
            "Fabricated facts or affiliations.",
        ]

    print()
    safety_boundaries = _ask(
        "Describe any additional safety boundaries (optional)", default=""
    )

    print()
    topics_raw = _ask(
        "GitHub topics (comma-separated)",
        default="hermes-agent,ai-agents,agent-profile",
    )
    github_topics = [t.strip() for t in topics_raw.split(",") if t.strip()]

    params: dict = {
        "name": name,
        "display_name": display_name,
        "description": description,
        "author": author,
        "version": version,
        "license": license_,
        "hermes_requires": ">=0.12.0",
        "model_provider": "openrouter",
        "model_default": "anthropic/claude-sonnet-4",
        "template_source": {
            "name": "codegraphtheory/hermes-profile-template",
            "url": "https://github.com/codegraphtheory/hermes-profile-template",
            "relationship": "generated-from-template",
        },
        "toolsets": toolsets,
        "env_requires": env_requires,
        "principles": principles,
        "scope": scope,
        "refusals": refusals,
        "output_contract": [
            "Result.",
            "Files changed.",
            "Verification command and exact outcome.",
            "Remaining risks or manual steps.",
        ],
        "github_topics": github_topics,
    }

    if target_users:
        params["target_users"] = target_users
    if safety_boundaries:
        params["safety_boundaries"] = safety_boundaries

    return params


def collect_params_from_args(args: argparse.Namespace) -> dict:
    import re
    name = re.sub(r"[^a-z0-9-]", "-", args.name.lower()).strip("-")
    return {
        "name": name,
        "display_name": args.display_name or name.replace("-", " ").title(),
        "description": args.description or f"A Hermes agent profile named {name}.",
        "author": args.author or "Hermes profile author",
        "version": args.version,
        "license": args.license,
        "hermes_requires": ">=0.12.0",
        "model_provider": "openrouter",
        "model_default": "anthropic/claude-sonnet-4",
        "template_source": {
            "name": "codegraphtheory/hermes-profile-template",
            "url": "https://github.com/codegraphtheory/hermes-profile-template",
            "relationship": "generated-from-template",
        },
        "toolsets": AVAILABLE_TOOLSETS,
        "env_requires": [],
        "principles": [
            "Ship working artifacts, not plans alone.",
            "Use tools to inspect live state before making factual claims.",
            "Keep user data private and never expose secrets.",
            "Prefer simple maintainable solutions over clever ones.",
        ],
        "scope": ["Complete the user's stated goal with clear verification."],
        "refusals": [
            "Credential theft or secret exposure.",
            "Hidden persistence, backdoors, or deceptive automation.",
            "Fabricated facts or affiliations.",
            "Unsafe destructive actions without explicit user approval.",
        ],
        "output_contract": [
            "Result.",
            "Files changed.",
            "Verification command and exact outcome.",
            "Remaining risks or manual steps.",
        ],
        "github_topics": ["hermes-agent", "ai-agents", "agent-profile"],
    }


# ---------------------------------------------------------------------------
# Write params
# ---------------------------------------------------------------------------

def write_params(params: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is None:
        # Fallback: minimal hand-rolled YAML writer for basic types
        lines: list[str] = []
        for key, value in params.items():
            if isinstance(value, str):
                if "\n" in value or ":" in value or value.startswith(("'", '"')):
                    escaped = value.replace("'", "''")
                    lines.append(f"{key}: '{escaped}'")
                else:
                    lines.append(f"{key}: {value}")
            elif isinstance(value, bool):
                lines.append(f"{key}: {'true' if value else 'false'}")
            elif isinstance(value, list):
                if not value:
                    lines.append(f"{key}: []")
                else:
                    lines.append(f"{key}:")
                    for item in value:
                        if isinstance(item, dict):
                            first = True
                            for k, v in item.items():
                                prefix = "  - " if first else "    "
                                lines.append(f"{prefix}{k}: {v}")
                                first = False
                        else:
                            lines.append(f"  - {item}")
            elif isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        out_path.write_text(
            yaml.dump(params, default_flow_style=False, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Interactive wizard to create a Hermes profile params file and optionally run generation."
    )
    p.add_argument("--name", help="Profile name (lowercase-kebab-case)")
    p.add_argument("--display-name", dest="display_name", help="Human-readable display name")
    p.add_argument("--description", help="One-sentence description")
    p.add_argument("--author", help="Author name")
    p.add_argument("--version", default="0.1.0", help="Version string (default: 0.1.0)")
    p.add_argument("--license", default="MIT", help="License identifier (default: MIT)")
    p.add_argument(
        "--params-out",
        dest="params_out",
        default="profile.params.yaml",
        help="Where to write the params file (default: profile.params.yaml)",
    )
    p.add_argument(
        "--output-dir",
        dest="output_dir",
        default=None,
        help="Output directory for generated profile (passed to generate_profile.py)",
    )
    p.add_argument(
        "--no-generate",
        dest="no_generate",
        action="store_true",
        help="Write params file only; do not invoke the generator",
    )
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    non_interactive = bool(args.name)

    if non_interactive:
        if not args.name:
            print("ERROR: --name is required in non-interactive mode.", file=sys.stderr)
            return 2
        params = collect_params_from_args(args)
    else:
        try:
            params = collect_params_interactive()
        except (KeyboardInterrupt, EOFError):
            print("\nWizard cancelled.", file=sys.stderr)
            return 1

    params_path = Path(args.params_out).resolve()
    params_path.parent.mkdir(parents=True, exist_ok=True)
    write_params(params, params_path)
    print(f"\nParams written to: {params_path}")

    if args.no_generate:
        print(f"\nTo generate your profile, run:")
        generator = Path(__file__).parent / "generate_profile.py"
        out = args.output_dir or f"/tmp/hermes-{params['name']}"
        print(f"  python3 {generator} --params {params_path} --output {out}")
        return 0

    # Invoke generator
    generator = Path(__file__).parent / "generate_profile.py"
    if not generator.exists():
        print(f"\nGenerator not found at {generator}. Params file is ready.", file=sys.stderr)
        print(f"Run manually: python3 scripts/generate_profile.py --params {params_path}")
        return 0

    out_dir = args.output_dir or f"/tmp/hermes-{params['name']}"
    print(f"\nRunning generator → {out_dir}")
    result = subprocess.run(
        [sys.executable, str(generator), "--params", str(params_path), "--output", out_dir],
        text=True,
    )
    if result.returncode != 0:
        print(f"\nGenerator exited with code {result.returncode}.", file=sys.stderr)
        return result.returncode

    print(f"\nProfile generated at: {out_dir}")
    print(f"To install: hermes profile install {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
