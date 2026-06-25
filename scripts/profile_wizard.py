#!/usr/bin/env python3
"""
Interactive wizard that writes a profile.params.yaml file for Hermes profile generation.

Usage (interactive):
    python3 scripts/profile_wizard.py

Usage (non-interactive / CI):
    python3 scripts/profile_wizard.py --non-interactive \
        --name my-profile \
        --display-name "My Profile" \
        --description "Does something useful."

After running, pass the output file to the generator:
    python3 scripts/generate_profile.py --params profile.params.yaml --output ./output
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML is required: pip install pyyaml")

REPO_ROOT = Path(__file__).parent.parent
TEMPLATE   = REPO_ROOT / "templates" / "profile.params.yaml"
DEFAULT_OUT = Path("profile.params.yaml")

# ── helpers ───────────────────────────────────────────────────────────────────

def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("name must contain at least one alphanumeric character")
    return value


def prompt(label: str, default: str = "", required: bool = True) -> str:
    display = f"[{default}] " if default else ""
    while True:
        answer = input(f"  {label} {display}> ").strip()
        if answer:
            return answer
        if default:
            return default
        if not required:
            return ""
        print(f"  ⚠  '{label}' is required.")


def prompt_list(label: str, default: list[str]) -> list[str]:
    print(f"\n  {label}")
    print(f"  (current: {', '.join(default) if default else 'none'})")
    print("  Enter items one per line. Empty line to finish.")
    items: list[str] = []
    while True:
        item = input("    + ").strip()
        if not item:
            break
        items.append(item)
    return items if items else default


def confirm(question: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    answer = input(f"  {question} [{hint}] ").strip().lower()
    if not answer:
        return default
    return answer.startswith("y")


def load_template() -> dict[str, Any]:
    if TEMPLATE.exists():
        return yaml.safe_load(TEMPLATE.read_text(encoding="utf-8")) or {}
    return {}


def build_params(args: argparse.Namespace, interactive: bool) -> dict[str, Any]:
    tpl = load_template()

    if interactive:
        print("\n" + "=" * 60)
        print("  Hermes Profile Wizard")
        print("  Answer the questions below. Press Enter to accept the default.")
        print("=" * 60 + "\n")

    def ask(field: str, label: str, default: str, required: bool = True) -> str:
        cli_val = getattr(args, field.replace("-", "_"), None)
        if cli_val:
            return cli_val
        if not interactive:
            return default
        return prompt(label, default=default, required=required)

    raw_name     = ask("name",         "Profile slug name",  tpl.get("name", "my-profile"))
    name         = slugify(raw_name)
    display_name = ask("display_name", "Display name",       tpl.get("display_name", name.replace("-", " ").title()))
    description  = ask("description",  "One-line description", tpl.get("description", "A Hermes agent profile."))
    author       = ask("author",       "Author",             tpl.get("author", "Hermes profile author"))
    version      = ask("version",      "Version",            tpl.get("version", "0.1.0"))
    license_     = ask("license",      "License",            tpl.get("license", "MIT"))

    # Toolsets
    default_toolsets = tpl.get("toolsets", ["file", "terminal", "skills", "web"])
    if interactive and not getattr(args, "non_interactive", False):
        toolsets = prompt_list("Toolsets to enable", default_toolsets)
    else:
        toolsets = default_toolsets

    # Principles
    default_principles = tpl.get("principles", [
        "Ship working artifacts, not plans alone.",
        "Use tools to inspect live state before making factual claims.",
        "Keep user data private and never expose secrets.",
        "Prefer simple maintainable solutions over clever ones.",
    ])
    if interactive and confirm("\nCustomise principles?", default=False):
        principles = prompt_list("Principles (one per line)", default_principles)
    else:
        principles = default_principles

    # Scope
    default_scope = tpl.get("scope", [
        "Build and verify software changes.",
        "Explain tradeoffs clearly.",
        "Leave the repository in a clean, reviewable state.",
    ])
    if interactive and confirm("\nCustomise scope?", default=False):
        scope = prompt_list("Scope items (one per line)", default_scope)
    else:
        scope = default_scope

    # Refusals
    default_refusals = tpl.get("refusals", [
        "Credential theft or secret exposure.",
        "Hidden persistence, backdoors, or deceptive automation.",
        "Fabricated facts, links, audits, or affiliations.",
        "Unsafe destructive actions without explicit user approval.",
    ])
    refusals = default_refusals

    # GitHub topics
    default_topics = tpl.get("github_topics", [
        "hermes-agent",
        "ai-agents",
        "agent-profile",
        "profile-distribution",
        "developer-tools",
    ])
    github_topics = default_topics

    return {
        "name":         name,
        "display_name": display_name,
        "description":  description,
        "author":       author,
        "version":      version,
        "license":      license_,
        "hermes_requires": tpl.get("hermes_requires", ">=0.12.0"),
        "model_provider":  tpl.get("model_provider", "openrouter"),
        "model_default":   tpl.get("model_default", "anthropic/claude-sonnet-4"),
        "template_source": tpl.get("template_source", {
            "name": "codegraphtheory/hermes-profile-template",
            "url":  "https://github.com/codegraphtheory/hermes-profile-template",
            "relationship": "generated-from-template",
        }),
        "toolsets":        toolsets,
        "env_requires":    tpl.get("env_requires", []),
        "principles":      principles,
        "scope":           scope,
        "refusals":        refusals,
        "output_contract": tpl.get("output_contract", [
            "Result.",
            "Files changed.",
            "Verification command and exact outcome.",
            "Remaining risks or manual steps.",
        ]),
        "profile_prompt":  tpl.get("profile_prompt", ""),
        "github_topics":   github_topics,
    }


# ── main ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactive wizard to create a Hermes profile.params.yaml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--non-interactive", "-y", action="store_true",
                        help="Skip all prompts and use defaults / flag values (for CI)")
    parser.add_argument("--output", "-o", default=str(DEFAULT_OUT),
                        help=f"Output path for the params file (default: {DEFAULT_OUT})")
    parser.add_argument("--generate", action="store_true",
                        help="Run generate_profile.py after writing the params file")
    parser.add_argument("--generate-output", default="./output",
                        help="Output directory for generate_profile.py (default: ./output)")

    # Field overrides (usable in both interactive and non-interactive mode)
    parser.add_argument("--name",         help="Profile slug name")
    parser.add_argument("--display-name", help="Human-readable display name")
    parser.add_argument("--description",  help="One-line description of the profile")
    parser.add_argument("--author",       help="Profile author name")
    parser.add_argument("--version",      default="", help="Profile version (default: 0.1.0)")
    parser.add_argument("--license",      default="", help="License identifier (default: MIT)")
    return parser.parse_args()


def main() -> None:
    args       = parse_args()
    interactive = not args.non_interactive

    params = build_params(args, interactive)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.dump(params, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    print(f"\n  ✅ Written: {out_path}")
    print(f"     name        : {params['name']}")
    print(f"     display_name: {params['display_name']}")
    print(f"     description : {params['description']}")

    if args.generate:
        import subprocess
        gen = REPO_ROOT / "scripts" / "generate_profile.py"
        if not gen.exists():
            print(f"\n  ⚠  generate_profile.py not found at {gen}")
            sys.exit(1)
        print(f"\n  Running generate_profile.py ...")
        result = subprocess.run(
            [sys.executable, str(gen), "--params", str(out_path), "--output", args.generate_output],
            check=False,
        )
        sys.exit(result.returncode)

    print(f"\n  Next step:")
    print(f"    python3 scripts/generate_profile.py --params {out_path} --output ./output")
    print(f"    make validate\n")


if __name__ == "__main__":
    main()
