#!/usr/bin/env python3
"""Guided interactive wizard to create a custom Hermes profile distribution."""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("Profile name must contain at least one alphanumeric character.")
    return value


def prompt_input(message: str, default: str = "", validator=None) -> str:
    """Prompt the user for input with defaults and validation."""
    while True:
        try:
            val = input(message).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nWizard aborted.")
            sys.exit(1)
        if not val and default:
            return default
        if not val and not default:
            print("Error: Input cannot be empty.")
            continue
        if validator:
            err = validator(val)
            if err:
                print(f"Error: {err}")
                continue
        return val


def main() -> int:
    parser = argparse.ArgumentParser(description="Guided wizard to build a Hermes profile distribution")
    parser.add_argument("--name", help="Profile slug or display name")
    parser.add_argument("--display-name", help="Human-readable profile name")
    parser.add_argument("--description", help="One sentence profile purpose")
    parser.add_argument("--output", help="Target output directory")
    parser.add_argument("--non-interactive", action="store_true", help="Run without prompting")
    parser.add_argument("--author", default="Hermes profile author", help="Author name")
    parser.add_argument("--version", default="0.1.0", help="Profile version")
    parser.add_argument("--license", default="MIT", help="Profile license")
    parser.add_argument("--toolsets", help="Comma-separated list of toolsets")
    parser.add_argument("--env-requires", help="Comma-separated list of required env vars (e.g. VAR1,VAR2)")
    parser.add_argument("--skip-skills", action="store_true", help="Skip bundling profile-craft skill")
    args = parser.parse_args()

    # Import generator logic
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "scripts"))
    try:
        from generate_profile import generate
    except ImportError as exc:
        print(f"ERROR: Cannot import generator logic: {exc}", file=sys.stderr)
        return 1

    if yaml is None:
        print("ERROR: PyYAML is required. Install with: python3 -m pip install pyyaml", file=sys.stderr)
        return 1

    if args.non_interactive:
        if not args.name or not args.description or not args.output:
            print("ERROR: In non-interactive mode, --name, --description, and --output are required.", file=sys.stderr)
            return 1
        slug = slugify(args.name)
        display_name = args.display_name or slug.replace("-", " ").title()
        description = args.description.strip()
        output_dir = Path(args.output).resolve()
        author = args.author
        version = args.version
        license_str = args.license
        
        # Toolsets
        if args.toolsets:
            toolsets = [t.strip() for t in args.toolsets.split(",") if t.strip()]
        else:
            toolsets = ["file", "terminal", "skills", "web", "session_search", "clarify"]
            
        # Env variables
        env_requires = []
        if args.env_requires:
            for item in args.env_requires.split(","):
                item = item.strip()
                if item:
                    env_requires.append({
                        "name": item,
                        "description": f"Required by {display_name}",
                        "required": True
                    })
        include_skills = not args.skip_skills
        refusals = [
            "Credential theft or secret exposure.",
            "Hidden persistence, backdoors, or deceptive automation.",
            "Fabricated facts, links, audits, or affiliations.",
            "Unsafe changes without explicit user approval."
        ]
        target_users = ["Developers"]
    else:
        print("=" * 60)
        print(" Welcome to the Hermes Profile Guided Wizard!")
        print(" Let's configure your new profile distribution.")
        print("=" * 60)
        print()

        # 1. Profile Name
        def validate_name(val):
            try:
                slugify(val)
                return None
            except Exception as exc:
                return str(exc)
        
        name_input = prompt_input("Profile name (e.g. security-reviewer): ", validator=validate_name)
        slug = slugify(name_input)

        # 2. Display Name
        default_display = slug.replace("-", " ").title()
        display_name = prompt_input(f"Display name (default: {default_display}): ", default=default_display)

        # 3. Description
        description = prompt_input("One-sentence description of the profile's purpose: ")

        # 4. Target Users
        users_input = prompt_input("Target users (comma-separated, default: Developers): ", default="Developers")
        target_users = [u.strip() for u in users_input.split(",") if u.strip()]

        # 5. Toolsets
        default_toolsets = "file, terminal, skills, web, session_search, clarify"
        toolsets_input = prompt_input(f"Toolsets to enable (comma-separated, default: {default_toolsets}): ", default=default_toolsets)
        toolsets = [t.strip() for t in toolsets_input.split(",") if t.strip()]

        # 6. Env vars
        env_requires = []
        env_input = prompt_input("Required environment variables (comma-separated, e.g. GITHUB_TOKEN, OPENAI_API_KEY. Leave blank if none): ", default="none")
        if env_input.lower() != "none" and env_input.strip():
            for item in env_input.split(","):
                item = item.strip()
                if not item:
                    continue
                req_input = prompt_input(f"  Is {item} strictly required? (y/n, default: y): ", default="y").lower().startswith("y")
                desc_input = prompt_input(f"  Enter description/help text for {item}: ", default=f"Required by {display_name}")
                env_requires.append({
                    "name": item,
                    "description": desc_input,
                    "required": req_input
                })

        # 7. Bundled skills
        include_skills = prompt_input("Include interactive 'profile-craft' skill in output? (y/n, default: y): ", default="y").lower().startswith("y")

        # 8. Safety boundaries
        refusals = []
        print("\nEnter custom safety boundaries/refusals (e.g. 'Do not run database drops'. One per line. Leave blank to finish):")
        while True:
            line = prompt_input("> ", default="done")
            if line.lower() == "done" or not line:
                break
            refusals.append(line)
        if not refusals:
            refusals = [
                "Credential theft or secret exposure.",
                "Hidden persistence, backdoors, or deceptive automation.",
                "Fabricated facts, links, audits, or affiliations.",
                "Unsafe changes without explicit user approval."
            ]

        # 9. Output directory
        output_input = prompt_input(f"Target output directory (default: ../{slug}): ", default=f"../{slug}")
        output_dir = Path(output_input).resolve()
        author = args.author
        version = args.version
        license_str = args.license

    # Build the params dictionary
    params = {
        "name": slug,
        "display_name": display_name,
        "description": description,
        "author": author,
        "version": version,
        "license": license_str,
        "hermes_requires": ">=0.12.0",
        "model_provider": "openrouter",
        "model_default": "anthropic/claude-sonnet-4",
        "template_source": {
            "name": "codegraphtheory/hermes-profile-template",
            "url": "https://github.com/codegraphtheory/hermes-profile-template",
            "relationship": "generated-from-template"
        },
        "toolsets": toolsets,
        "env_requires": env_requires,
        "principles": [
            "Be useful before being clever.",
            "Use tools when they materially improve correctness.",
            "Keep user data private and never expose secrets.",
            f"Address the needs of target users: {', '.join(target_users)}."
        ],
        "scope": [description, "Produce clear, actionable outputs."],
        "refusals": refusals,
        "output_contract": [
            "Result.",
            "Evidence or command output when relevant.",
            "Next step."
        ],
        "github_topics": [
            "hermes-agent",
            "ai-agents",
            "agent-profile",
            "profile-distribution",
            "developer-tools"
        ]
    }

    print()
    print("Generating profile...")

    try:
        # Generate the profile
        generate(params, output_dir, force=True, template_root=repo_root)
        
        # Write the profile.params.yaml to the output directory
        params_path = output_dir / "profile.params.yaml"
        params_path.write_text(yaml.safe_dump(params, sort_keys=False, default_flow_style=False), encoding="utf-8")
        
        # Handle skipping skills if requested
        if not include_skills:
            skill_dir = output_dir / "skills" / "profile-craft"
            if skill_dir.exists():
                shutil.rmtree(skill_dir)
                
    except Exception as exc:
        print(f"ERROR: Generation failed: {exc}", file=sys.stderr)
        return 1

    print("=" * 60)
    print(f" SUCCESS! Hermes Profile Generated: {output_dir}")
    print("=" * 60)
    print(f"Reusable config file written to: {output_dir}/profile.params.yaml")
    print()
    print("To install and run your new profile locally:")
    print(f"  cd {output_dir}")
    print("  python3 -m pip install -r requirements.txt")
    print("  make validate")
    print(f"  hermes profile install . --name {slug} --yes")
    print(f"  hermes -p {slug} chat")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
