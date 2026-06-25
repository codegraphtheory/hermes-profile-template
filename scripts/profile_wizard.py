#!/usr/bin/env python3
"""Guided wizard for writing profile.params.yaml and optionally generating a profile."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install -r requirements.txt") from exc


DEFAULT_TOOLSETS = ["file", "terminal", "skills", "web", "session_search", "clarify"]
DEFAULT_TOPICS = ["hermes-agent", "ai-agents", "agent-profile", "profile-distribution", "developer-tools"]
DEFAULT_REFUSALS = [
    "Credential theft or secret exposure.",
    "Hidden persistence, backdoors, or deceptive automation.",
    "Fabricated facts, links, audits, or affiliations.",
]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("profile name must contain at least one alphanumeric character")
    return value


def split_values(values: list[str] | None) -> list[str]:
    if not values:
        return []
    result: list[str] = []
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item and item not in result:
                result.append(item)
    return result


def prompt_text(label: str, default: str = "", *, required: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{label}{suffix}: ").strip() or default
        if value or not required:
            return value
        print("This value is required.")


def prompt_list(label: str, default: list[str]) -> list[str]:
    raw_default = ", ".join(default)
    value = prompt_text(label, raw_default)
    return split_values([value]) or default


def prompt_env_requires() -> list[dict[str, Any]]:
    env_items: list[dict[str, Any]] = []
    print("Environment variables are names and descriptions only. Do not enter real keys or secrets.")
    while True:
        name = prompt_text("Env var name, blank to finish")
        if not name:
            return env_items
        description = prompt_text("Description", "Required by this profile")
        required = prompt_text("Required? yes/no", "no").lower() in {"y", "yes", "true", "1"}
        env_items.append({"name": name.strip().upper(), "description": description, "required": required})


def parse_env_specs(values: list[str] | None) -> list[dict[str, Any]]:
    env_items: list[dict[str, Any]] = []
    for spec in values or []:
        parts = [part.strip() for part in spec.split(":", 2)]
        if not parts or not parts[0]:
            continue
        description = parts[1] if len(parts) > 1 and parts[1] else "Required by this profile"
        required = False
        if len(parts) > 2:
            required = parts[2].lower() in {"required", "true", "yes", "1"}
        env_items.append({"name": parts[0].upper(), "description": description, "required": required})
    return env_items


def build_params(args: argparse.Namespace) -> dict[str, Any]:
    if args.non_interactive:
        if not args.name or not args.description:
            raise ValueError("--name and --description are required with --non-interactive")
        name = args.name
        display_name = args.display_name or slugify(args.name).replace("-", " ").title()
        description = args.description
        target_users = split_values(args.target_user) or ["Developers who need a focused Hermes profile."]
        toolsets = split_values(args.toolset) or DEFAULT_TOOLSETS
        env_requires = parse_env_specs(args.env)
        bundled_skills = split_values(args.bundled_skill) or ["profile-specific-skill"]
        safety_boundaries = split_values(args.safety_boundary) or DEFAULT_REFUSALS
        output_dir = args.profile_output or f"../{slugify(name)}"
    else:
        name = prompt_text("Profile name", required=True)
        display_name = prompt_text("Display name", slugify(name).replace("-", " ").title())
        description = prompt_text("Description", required=True)
        target_users = prompt_list("Target users, comma-separated", ["Developers who need a focused Hermes profile."])
        toolsets = prompt_list("Toolsets, comma-separated", DEFAULT_TOOLSETS)
        bundled_skills = prompt_list("Bundled skills to include or skip", ["profile-specific-skill"])
        env_requires = prompt_env_requires()
        safety_boundaries = prompt_list("Safety boundaries, comma-separated", DEFAULT_REFUSALS)
        output_dir = prompt_text("Generated profile output directory", f"../{slugify(name)}")

    scope = [description, *[f"Support {user}" for user in target_users]]
    if bundled_skills:
        scope.append("Bundle or adapt skills: " + ", ".join(bundled_skills))

    return {
        "name": slugify(name),
        "display_name": display_name,
        "description": description,
        "author": args.author or "Hermes profile author",
        "version": "0.1.0",
        "license": "MIT",
        "hermes_requires": ">=0.12.0",
        "model_provider": args.model_provider or "openrouter",
        "model_default": args.model_default or "anthropic/claude-sonnet-4",
        "template_source": {
            "name": "codegraphtheory/hermes-profile-template",
            "url": "https://github.com/codegraphtheory/hermes-profile-template",
            "relationship": "generated-from-template",
        },
        "toolsets": toolsets,
        "env_requires": env_requires,
        "bundled_skills": bundled_skills,
        "wizard_output_dir": output_dir,
        "principles": [
            "Be useful before being clever.",
            "Use tools when they materially improve correctness.",
            "Keep user data private and never expose secrets.",
            "Verify important claims with evidence.",
        ],
        "scope": scope,
        "refusals": safety_boundaries,
        "output_contract": ["Result.", "Files changed or generated.", "Verification command and exact outcome.", "Next step."],
        "github_topics": DEFAULT_TOPICS,
    }


def write_params(path: Path, params: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(params, sort_keys=False, default_flow_style=False), encoding="utf-8")


def run_generator(params_path: Path, output_dir: Path, *, force: bool) -> None:
    command = [
        sys.executable,
        str(Path(__file__).resolve().parent / "generate_profile.py"),
        "--params",
        str(params_path),
        "--output",
        str(output_dir),
    ]
    if force:
        command.append("--force")
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create profile.params.yaml with a guided Hermes profile wizard")
    parser.add_argument("--non-interactive", action="store_true", help="Require flags instead of prompting")
    parser.add_argument("--name", help="Profile slug or name")
    parser.add_argument("--display-name", help="Human-readable profile name")
    parser.add_argument("--description", help="One-sentence profile mission")
    parser.add_argument("--target-user", action="append", help="Target user or comma-separated user list")
    parser.add_argument("--toolset", action="append", help="Toolset or comma-separated toolset list")
    parser.add_argument("--env", action="append", help="Env var as NAME:description:required|optional")
    parser.add_argument("--bundled-skill", action="append", help="Bundled skill to include or skip")
    parser.add_argument("--safety-boundary", action="append", help="Safety boundary or comma-separated boundary list")
    parser.add_argument("--author", help="Profile author")
    parser.add_argument("--model-provider", help="Hermes model provider")
    parser.add_argument("--model-default", help="Default model")
    parser.add_argument("--params-output", default="profile.params.yaml", help="Path to write profile params YAML")
    parser.add_argument("--profile-output", help="Generated profile output directory")
    parser.add_argument("--generate", action="store_true", help="Run scripts/generate_profile.py after writing params")
    parser.add_argument("--force", action="store_true", help="Overwrite generated profile output when --generate is used")
    args = parser.parse_args()

    try:
        params = build_params(args)
        params_path = Path(args.params_output).resolve()
        write_params(params_path, params)
        print(f"Wrote params: {params_path}")
        output_dir = Path(args.profile_output or params["wizard_output_dir"]).resolve()
        if args.generate:
            run_generator(params_path, output_dir, force=args.force)
            print(f"Generated profile: {output_dir}")
        else:
            print("Next command:")
            print(f"  python3 scripts/generate_profile.py --params {params_path} --output {output_dir}")
        return 0
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
