#!/usr/bin/env python3
"""Interactive wizard that writes profile.params.yaml for first-time authors.

Supports both interactive and fully non-interactive (CLI flag) modes.
Builds on scripts/generate_profile.py — run this first, then generate.

Usage:
  # Interactive (prompts for everything)
  python3 scripts/profile_wizard.py

  # Non-interactive with CLI flags (great for CI smoke testing)
  python3 scripts/profile_wizard.py \\
    --name database-reviewer \\
    --display-name "Database Migration Reviewer" \\
    --description "Reviews SQL migration diffs before deploy" \\
    --author "Your Name" \\
    --output /tmp/my-profile.params.yaml \\
    --force

  # Generate from the params file
  python3 scripts/generate_profile.py \\
    --params /tmp/my-profile.params.yaml \\
    --output /tmp/my-generated-profile
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install pyyaml") from exc


DEFAULT_OUTPUT = Path("profile.params.yaml")

# ── preset building blocks ──────────────────────────────────────────────

PROFILE_CLASSES: dict[str, dict[str, Any]] = {
    "engineer": {
        "display_name": "Engineering Reviewer",
        "description": "Reviews code, architecture, and release plans for production readiness.",
        "toolsets": ["terminal", "file", "github"],
        "env_requires": [],
        "principles": [
            "Prefer verified evidence over claims.",
            "Keep changes small and reversible.",
            "Document assumptions before reaching conclusions.",
        ],
        "scope": [
            "Review code quality, architecture decisions, and release plans.",
            "Verify claims with tools before reporting.",
            "Flag risks, tradeoffs, and rollback paths.",
        ],
        "refusals": [
            "Deploying without a rollback plan.",
            "Silently modifying production data.",
            "Claiming correctness without running tests or validators.",
        ],
        "output_contract": [
            "Summary of findings.",
            "Files or areas reviewed.",
            "Risks and recommended actions.",
            "Verification commands and their output.",
        ],
        "github_topics": ["hermes-agent", "code-review", "software-quality"],
    },
    "researcher": {
        "display_name": "Research Assistant",
        "description": "Builds source-grounded briefs with uncertainty labels and reusable handoff notes.",
        "toolsets": ["web", "file"],
        "env_requires": [],
        "principles": [
            "Cite sources before conclusions.",
            "Separate facts, estimates, and assumptions.",
            "Flag confidence levels explicitly.",
        ],
        "scope": [
            "Research questions from web and local sources.",
            "Produce structured briefs with cited evidence.",
            "Identify gaps, contradictions, and open questions.",
        ],
        "refusals": [
            "Presenting speculation as fact.",
            "Omitting relevant counter-evidence.",
            "Making medical, legal, or financial recommendations.",
        ],
        "output_contract": [
            "Question or goal.",
            "Summary of findings with citations.",
            "Confidence assessment per claim.",
            "Open questions and suggested next research directions.",
        ],
        "github_topics": ["hermes-agent", "research", "knowledge-management"],
    },
    "operator": {
        "display_name": "Release Operator",
        "description": "Coordinates release readiness, smoke validation, changelogs, and rollout notes.",
        "toolsets": ["terminal", "file", "github"],
        "env_requires": [],
        "principles": [
            "Never ship without a rollback path.",
            "Automate checks before relying on memory.",
            "Document every change with a clear rationale.",
        ],
        "scope": [
            "Validate release readiness across environments.",
            "Generate changelogs and release notes.",
            "Coordinate rollout steps and rollback procedures.",
        ],
        "refusals": [
            "Skipping validation for speed.",
            "Merging unreviewed changes to release branches.",
            "Deploying with unresolved known issues.",
        ],
        "output_contract": [
            "Release summary.",
            "Validation results (tests, builds, smoke checks).",
            "Changelog entries.",
            "Rollback instructions if applicable.",
        ],
        "github_topics": ["hermes-agent", "release-management", "devops"],
    },
    "general": {
        "display_name": "Custom Agent",
        "description": "A general-purpose Hermes agent profile.",
        "toolsets": ["file", "terminal", "skills", "web", "session_search", "clarify"],
        "env_requires": [],
        "principles": [
            "Be useful before being clever.",
            "Use tools when they materially improve correctness.",
            "Keep user data private and never expose secrets.",
            "Verify important claims with evidence.",
        ],
        "scope": [
            "Accomplish the tasks described in the profile mission.",
            "Produce clear, actionable outputs.",
            "Call out uncertainty and risks.",
        ],
        "refusals": [
            "Credential theft or secret exposure.",
            "Hidden persistence, backdoors, or deceptive automation.",
            "Fabricated facts, links, audits, or affiliations.",
            "Unsafe changes without explicit user approval.",
        ],
        "output_contract": [
            "Result.",
            "Evidence or command output when relevant.",
            "Risks, assumptions, or blockers.",
            "Next step.",
        ],
        "github_topics": ["hermes-agent", "ai-agents", "profile-distribution"],
    },
}

BUNDLES: dict[str, dict[str, Any]] = {
    "open-source": {
        "toolsets": ["github"],
        "scope_extra": ["Review contribution workflow and public docs."],
        "topics_extra": ["open-source"],
    },
    "safe-demo": {
        "toolsets": ["terminal"],
        "scope_extra": ["Record demos only in temporary workspaces."],
        "topics_extra": ["demo"],
    },
    "security": {
        "toolsets": ["terminal", "file"],
        "scope_extra": ["Scan for secrets and runtime state."],
        "topics_extra": ["security"],
    },
    "database": {
        "toolsets": ["terminal", "file"],
        "scope_extra": ["Audit schema changes and migration safety."],
        "topics_extra": ["database", "migrations"],
    },
    "api-integration": {
        "toolsets": ["web"],
        "scope_extra": ["Integrate with external APIs safely."],
        "topics_extra": ["api", "integration"],
    },
}


# ── helpers ─────────────────────────────────────────────────────────────


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("name must contain at least one alphanumeric character")
    return value


def merge_unique(base: list[str], extra: list[str]) -> list[str]:
    result = list(base)
    for item in extra:
        if item not in result:
            result.append(item)
    return result


def prompt_str(prompt: str, default: str | None = None) -> str:
    """Ask the user for a string value."""
    label = f"{prompt}"
    if default is not None:
        label += f" [{default}]"
    val = input(f"  {label}: ").strip()
    if not val and default is not None:
        return default
    return val


def prompt_choices(prompt: str, choices: Sequence[str], single: bool = True) -> list[str]:
    """Ask the user to select one or more from a list."""
    print(f"\n  {prompt}")
    for idx, choice in enumerate(choices, 1):
        print(f"    {idx}) {choice}")
    print("    (enter comma-separated numbers, or 'all')")

    while True:
        raw = input("  Select: ").strip()
        if not raw:
            return [choices[0]] if single else []
        if raw.lower() == "all":
            return list(choices)

        parts = [p.strip() for p in raw.replace(",", " ").split()]
        selected: list[str] = []
        valid = True
        for p in parts:
            if p.isdigit() and 1 <= int(p) <= len(choices):
                selected.append(choices[int(p) - 1])
            elif p in choices:
                selected.append(p)
            else:
                valid = False
                break

        if selected and valid:
            # Deduplicate while preserving order
            seen: set[str] = set()
            result: list[str] = []
            for item in selected:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result

        print(f"  Enter 1-{len(choices)} or comma-separated values.")


def prompt_list(prompt: str, hint: str = "value") -> list[str]:
    """Ask the user to enter multiple lines; empty line finishes."""
    print(f"\n  {prompt}")
    print(f"  (Enter one {hint} per line. Empty line when done.)")
    items: list[str] = []
    while True:
        val = input(f"    [{len(items) + 1}] ").strip()
        if not val:
            break
        items.append(val)
    return items


def prompt_bool(prompt: str, default: bool = True) -> bool:
    default_str = "Y/n" if default else "y/N"
    val = input(f"  {prompt} [{default_str}]: ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes", "true")


# ── interactive session ────────────────────────────────────────────────


def run_interactive() -> dict[str, Any]:
    """Run an interactive wizard session. Returns a params dict."""
    print("\n  ═══════════════════════════════════════════")
    print("   Hermes Profile Wizard 🧙")
    print("  ═══════════════════════════════════════════\n")
    print("  Answer the prompts below to create your profile.params.yaml.\n")

    # Start from a class preset
    print("  Step 1 — Pick a starting class")
    class_names = sorted(PROFILE_CLASSES)
    selected_class = prompt_choices(
        "Choose a profile class (this sets sensible defaults):",
        class_names,
        single=True,
    )[0]

    params: dict[str, Any] = dict(PROFILE_CLASSES[selected_class])

    # Override basics
    print("\n  Step 2 — Customize your profile identity")
    suggested_slug = slugify(params["display_name"])
    name_raw = prompt_str(
        "Profile name (slug, e.g. 'my-reviewer')",
        default=suggested_slug,
    )
    params["name"] = slugify(name_raw)

    params["display_name"] = prompt_str(
        "Display name (e.g. 'My Reviewer')",
        default=params.get("display_name", name_raw.replace("-", " ").title()),
    )

    params["description"] = prompt_str(
        "Short description (one sentence mission)",
        default=params.get("description", ""),
    )

    params["author"] = prompt_str("Author name", default="Profile Author")
    params["version"] = prompt_str("Initial version", default="0.1.0")
    params["license"] = prompt_str("License", default="MIT")

    # Toolset / bundles
    print("\n  Step 3 — Add optional capability bundles (choose extras)")
    bundle_names = sorted(BUNDLES)
    selected_bundles = prompt_choices(
        "Optional capability bundles (can skip with Enter):",
        bundle_names,
        single=False,
    )

    # Apply bundle additions
    toolsets = list(params.get("toolsets", []))
    scope_items = list(params.get("scope", []))
    topics = list(params.get("github_topics", []))
    for bname in selected_bundles:
        bundle = BUNDLES[bname]
        toolsets = merge_unique(toolsets, bundle["toolsets"])
        scope_items = merge_unique(scope_items, bundle.get("scope_extra", []))
        topics = merge_unique(topics, bundle.get("topics_extra", []))

    params["toolsets"] = toolsets
    params["scope"] = scope_items
    params["github_topics"] = topics

    # Refine lists
    print("\n  Step 4 — Refine profile behavior")
    if prompt_bool("Customize the guiding principles?", default=False):
        params["principles"] = prompt_list(
            "Enter each principle",
            hint="principle",
        )

    if prompt_bool("Customize scope / responsibilities?", default=False):
        params["scope"] = prompt_list(
            "Enter each scope item",
            hint="scope item",
        )

    if prompt_bool("Customize refusals (things the agent should refuse)?", default=False):
        params["refusals"] = prompt_list(
            "Enter each refusal",
            hint="refusal",
        )

    if prompt_bool("Customize the output contract?", default=False):
        params["output_contract"] = prompt_list(
            "Enter each output item",
            hint="output item",
        )

    # Environment variables
    print("\n  Step 5 — Environment variables")
    if prompt_bool("Add environment variables the profile needs?", default=False):
        env_reqs: list[dict[str, Any]] = []
        while True:
            print(f"\n    Environment variable #{len(env_reqs) + 1} (empty name to finish):")
            env_name = input("    Name (e.g. GITHUB_TOKEN): ").strip()
            if not env_name:
                break
            env_desc = input("    Description: ").strip()
            env_req = prompt_bool("    Required?", default=True)
            env_reqs.append({
                "name": env_name,
                "description": env_desc or f"Required by this profile",
                "required": env_req,
            })
        params["env_requires"] = env_reqs

    # Model
    print("\n  Step 6 — Model settings")
    params["model_provider"] = prompt_str(
        "Model provider",
        default=params.get("model_provider", "openrouter"),
    )
    params["model_default"] = prompt_str(
        "Default model",
        default=params.get("model_default", "anthropic/claude-sonnet-4"),
    )

    # Template source
    params["template_source"] = {
        "name": "codegraphtheory/hermes-profile-template",
        "url": "https://github.com/codegraphtheory/hermes-profile-template",
        "relationship": "generated-from-template",
    }

    return params


# ── non-interactive builder ─────────────────────────────────────────────


def build_params_from_flags(args: argparse.Namespace) -> dict[str, Any]:
    """Build a params dict entirely from CLI flags (no prompts)."""
    # Determine class preset
    profile_class = args.profile_class or "general"
    if profile_class not in PROFILE_CLASSES:
        raise ValueError(f"Unknown profile class: {profile_class}")
    params: dict[str, Any] = dict(PROFILE_CLASSES[profile_class])

    # Override identity
    params["name"] = args.name
    params["display_name"] = args.display_name or args.name.replace("-", " ").title()
    params["description"] = args.description
    params["author"] = args.author or "Profile Author"
    params["version"] = args.version or "0.1.0"
    params["license"] = args.license or "MIT"

    # Apply bundles
    toolsets = list(params.get("toolsets", []))
    scope_items = list(params.get("scope", []))
    topics = list(params.get("github_topics", []))
    for bname in args.bundle:
        if bname in BUNDLES:
            bundle = BUNDLES[bname]
            toolsets = merge_unique(toolsets, bundle["toolsets"])
            scope_items = merge_unique(scope_items, bundle.get("scope_extra", []))
            topics = merge_unique(topics, bundle.get("topics_extra", []))
        else:
            raise ValueError(f"Unknown bundle: {bname}")
    params["toolsets"] = toolsets
    params["scope"] = scope_items
    params["github_topics"] = topics

    # Override individual list fields
    if args.principles:
        params["principles"] = args.principles
    if args.scope:
        params["scope"] = args.scope
    if args.refusals:
        params["refusals"] = args.refusals
    if args.output_contract:
        params["output_contract"] = args.output_contract

    # Environment variables
    env_reqs: list[dict[str, Any]] = []
    if args.env_requires:
        for env_spec in args.env_requires:
            parts = env_spec.split(":", 2)
            env_name = parts[0]
            env_desc = parts[1] if len(parts) > 1 else ""
            env_req = parts[2] != "optional" if len(parts) > 2 else True
            env_reqs.append({
                "name": env_name,
                "description": env_desc,
                "required": env_req,
            })
    if env_reqs:
        params["env_requires"] = env_reqs

    # Model
    params["model_provider"] = args.model_provider or params.get("model_provider", "openrouter")
    params["model_default"] = args.model_default or params.get("model_default", "anthropic/claude-sonnet-4")

    # Template source
    params["template_source"] = {
        "name": "codegraphtheory/hermes-profile-template",
        "url": "https://github.com/codegraphtheory/hermes-profile-template",
        "relationship": "generated-from-template",
    }

    return params


# ── output ──────────────────────────────────────────────────────────────


def write_params(path: Path, params: dict[str, Any], *, force: bool) -> None:
    """Write params dict to a YAML file."""
    if path.exists() and not force:
        raise SystemExit(
            f"Refusing to overwrite {path}. Re-run with --force or choose --output."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(params, sort_keys=False), encoding="utf-8")


# ── main ────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a profile.params.yaml from guided choices or CLI flags.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Non-interactive flags (all optional — omit for interactive mode)
    parser.add_argument("--class", dest="profile_class", choices=sorted(PROFILE_CLASSES))

    identity = parser.add_argument_group("profile identity (non-interactive)")
    identity.add_argument("--name", help="Profile slug (e.g. 'my-reviewer')")
    identity.add_argument("--display-name", help="Human-readable name")
    identity.add_argument("--description", help="Short one-sentence mission")
    identity.add_argument("--author", help="Author name")
    identity.add_argument("--version", default="0.1.0", help="Initial semver")
    identity.add_argument("--license", default="MIT", help="SPDX license identifier")

    integration = parser.add_argument_group("capabilities (non-interactive)")
    integration.add_argument(
        "--bundle",
        action="append",
        choices=sorted(BUNDLES),
        default=[],
        help="Add capability bundles (can be repeated)",
    )
    integration.add_argument("--principles", nargs="*", help="Guiding principles")
    integration.add_argument("--scope", nargs="*", help="Scope items")
    integration.add_argument("--refusals", nargs="*", help="Refusal conditions")
    integration.add_argument("--output-contract", nargs="*", help="Output contract items")
    integration.add_argument(
        "--env-requires",
        nargs="*",
        help="Env vars in format: NAME:description:required|optional",
    )

    model = parser.add_argument_group("model (non-interactive)")
    model.add_argument("--model-provider", help="Model provider (e.g. openrouter)")
    model.add_argument("--model-default", help="Default model id")

    io = parser.add_argument_group("output")
    io.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output YAML path")
    io.add_argument("--force", action="store_true", help="Overwrite existing output")
    io.add_argument(
        "--skip-generate",
        action="store_true",
        help="Skip the next-step hint about running generate_profile.py",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Interactive mode: when no non-interactive identity flags are given
    has_interactive_flags = any([
        args.name,
        args.description,
        args.display_name,
    ])

    if has_interactive_flags:
        # Non-interactive: name is required
        if not args.name:
            print("ERROR: --name is required in non-interactive mode.", file=sys.stderr)
            return 1
        if not args.description:
            print("ERROR: --description is required in non-interactive mode.", file=sys.stderr)
            return 1
        params = build_params_from_flags(args)
    else:
        # Interactive mode — first ask for class, then customize
        params = run_interactive()

    write_params(args.output, params, force=args.force)

    slug = slugify(params["name"])
    # Print the result
    print(f"\n  ✅ Wrote params to: {args.output}")
    print()

    if not args.skip_generate:
        print(f"  Next command:")
        print(f"    python3 scripts/generate_profile.py \\")
        print(f"      --params {args.output} \\")
        print(f"      --output ../{slug} --force")
        print(f"    python3 ../{slug}/scripts/validate_profile.py ../{slug}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
