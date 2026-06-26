#!/usr/bin/env python3
"""Interactive wizard that writes profile.params.yaml for first-time authors."""
from __future__ import annotations

import argparse
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
    },
    "researcher": {
        "name": "research-assistant",
        "display_name": "Research Assistant",
        "description": "Builds source-grounded briefs with uncertainty labels and reusable handoff notes.",
        "toolsets": ["web", "file"],
        "principles": ["Cite sources before conclusions.", "Separate facts, estimates, and assumptions."],
        "github_topics": ["hermes-agent", "research", "knowledge-management"],
    },
    "operator": {
        "name": "release-operator",
        "display_name": "Release Operator",
        "description": "Coordinates release readiness, smoke validation, changelogs, and rollout notes.",
        "toolsets": ["terminal", "file", "github"],
        "principles": ["Never ship without a rollback path.", "Automate checks before relying on memory."],
        "github_topics": ["hermes-agent", "release-management", "devops"],
    },
}
BUNDLES = {
    "open-source": {"toolsets": ["github"], "scope": ["Review contribution workflow and public docs."], "topics": ["open-source"]},
    "safe-demo": {"toolsets": ["terminal"], "scope": ["Record demos only in temporary workspaces."], "topics": ["demo"]},
    "security": {"toolsets": ["terminal", "file"], "scope": ["Scan for secrets and runtime state."], "topics": ["security"]},
}


def merge_unique(base: list[str], extra: list[str]) -> list[str]:
    result = list(base)
    for item in extra:
        if item not in result:
            result.append(item)
    return result


def build_params(kind: str, bundles: list[str]) -> dict:
    if kind not in CLASSES:
        raise ValueError(f"Unknown profile class: {kind}")
    data = dict(CLASSES[kind])
    scope: list[str] = ["Stay within the profile mission.", "Ask for missing deployment details only when required."]
    topics = list(data["github_topics"])
    toolsets = list(data["toolsets"])
    for bundle_name in bundles:
        bundle = BUNDLES[bundle_name]
        scope = merge_unique(scope, bundle.get("scope", []))
        topics = merge_unique(topics, bundle.get("topics", []))
        toolsets = merge_unique(toolsets, bundle.get("toolsets", []))
    return {
        "name": data["name"],
        "display_name": data["display_name"],
        "description": data["description"],
        "version": "0.1.0",
        "author": "Profile Author",
        "license": "MIT",
        "hermes_requires": ">=0.12.0",
        "model_provider": "openrouter",
        "model_default": "anthropic/claude-sonnet-4",
        "toolsets": toolsets,
        "env_requires": [],
        "principles": data["principles"],
        "scope": scope,
        "refusals": ["Do not expose secrets, private state, or unsupported claims."],
        "output_contract": ["Summarize evidence.", "List risks and next actions."],
        "github_topics": topics,
        "template_source": {"url": "https://github.com/codegraphtheory/hermes-profile-template", "relationship": "generated-from-template"},
    }


def choose(prompt: str, choices: list[str]) -> str:
    print(prompt)
    for idx, choice in enumerate(choices, 1):
        print(f"  {idx}) {choice}")
    while True:
        raw = input("Select: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        if raw in choices:
            return raw
        print(f"Enter 1-{len(choices)} or one of: {', '.join(choices)}")


def write_params(path: Path, params: dict, *, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"Refusing to overwrite {path}. Re-run with --force or choose --output.")
    path.write_text(yaml.safe_dump(params, sort_keys=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a profile.params.yaml from guided choices.")
    parser.add_argument("--class", dest="profile_class", choices=sorted(CLASSES))
    parser.add_argument("--bundle", action="append", choices=sorted(BUNDLES), default=[])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    profile_class = args.profile_class or choose("Choose a profile class", sorted(CLASSES))
    params = build_params(profile_class, args.bundle)
    write_params(args.output, params, force=args.force)
    print(f"Wrote {args.output}")
    print("Next: python3 scripts/generate_profile.py --params {0} --output ../{1}".format(args.output, params["name"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
