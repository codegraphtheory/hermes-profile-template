#!/usr/bin/env python3
"""Interactive Hermes profile design wizard.

Prompts for an archetype class and optional bundle, then writes profile.params.yaml.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml  # type: ignore

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "wizard"
DEFAULT_CLASSES = TEMPLATE_DIR / "classes.yaml"
DEFAULT_BUNDLES = TEMPLATE_DIR / "bundles.yaml"
DEFAULT_OUTPUT = Path("profile.params.yaml")


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Wizard config not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Wizard config must be a YAML mapping: {path}")
    return data


def list_choices(items: list[dict], key: str = "slug") -> list[str]:
    return [item.get(key, item.get("name", "")) for item in items if isinstance(item, dict)]


def pick(prompt: str, choices: list[str], default: str | None = None) -> str:
    print(prompt)
    for idx, choice in enumerate(choices, 1):
        print(f"  {idx}) {choice}")
    default_idx = 1
    if default and default in choices:
        default_idx = choices.index(default) + 1
    while True:
        raw = input(f"Select [{default_idx}]: ").strip() or str(default_idx)
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        print(f"Please enter 1-{len(choices)}")


def ask_optional(prompt: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    raw = input(f"{prompt} {suffix}: ").strip().lower() or ("y" if default else "n")
    return raw.startswith("y")


def build_params(archetype: dict, bundle: dict | None) -> dict:
    params: dict = {
        "name": archetype.get("default_name", "custom-profile"),
        "display_name": archetype.get("default_display_name", "Custom Hermes Profile"),
        "description": archetype.get("description", ""),
        "author": archetype.get("author", "profile author"),
        "version": "0.1.0",
        "license": "MIT",
        "hermes_requires": ">=0.12.0",
        "model_provider": archetype.get("model_provider", "openrouter"),
        "model_default": archetype.get("model_default", "anthropic/claude-sonnet-4"),
        "template_source": {
            "name": "codegraphtheory/hermes-profile-template",
            "url": "https://github.com/codegraphtheory/hermes-profile-template",
            "relationship": "generated-from-template",
        },
        "toolsets": list(archetype.get("toolsets", [])),
        "env_requires": list(archetype.get("env_requires", [])),
        "principles": list(archetype.get("principles", [])),
        "scope": list(archetype.get("scope", [])),
        "refusals": list(archetype.get("refusals", [])),
        "output_contract": list(archetype.get("output_contract", [])),
        "github_topics": list(archetype.get("github_topics", [])),
    }

    if bundle:
        if bundle.get("extends_toolsets"):
            existing = params["toolsets"]
            for item in bundle["extends_toolsets"]:
                if item not in existing:
                    existing.append(item)
        if bundle.get("extends_principles"):
            params["principles"].extend(
                [item for item in bundle["extends_principles"] if item not in params["principles"]]
            )
        if bundle.get("extends_scope"):
            params["scope"].extend(
                [item for item in bundle["extends_scope"] if item not in params["scope"]]
            )
        if bundle.get("default_name"):
            params["name"] = bundle["default_name"]
        if bundle.get("default_display_name"):
            params["display_name"] = bundle["default_display_name"]
        if bundle.get("description"):
            params["description"] = bundle["description"]
    return params


def write_params(path: Path, params: dict, *, force: bool = False) -> None:
    if path.exists() and not force:
        raise SystemExit(f"Refusing to overwrite {path}. Re-run with --force or choose --output.")
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml.safe_dump(
        params,
        path.open("w"),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def try_write_params(path: Path, params: dict, *, force: bool = False) -> None:
    try:
        write_params(path, params, force=force)
        print(f"\nWrote {path}")
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Failed to write {path}: {exc}")


def run_wizard(classes_path: Path, bundles_path: Path, output_path: Path, *, force: bool = False) -> int:
    if not classes_path.exists():
        raise SystemExit(f"Missing classes config: {classes_path}")
    classes = load_yaml(classes_path).get("classes", [])
    if not classes:
        raise SystemExit(f"No classes defined in {classes_path}")

    class_names = list_choices(classes, "slug")
    print("Select a profile class.\n")
    chosen_class_slug = pick("Profile class:", class_names)
    archetype = next(item for item in classes if item.get("slug") == chosen_class_slug)

    bundle = None
    bundles = []
    if bundles_path.exists():
        bundles = load_yaml(bundles_path).get("bundles", [])

    if bundles:
        bundle_names = ["<none>"] + list_choices(bundles, "name")
        bundle_slug = pick("\nOptional companion bundle:", bundle_names, default=bundle_names[0])
        if bundle_slug != "<none>":
            bundle = next(item for item in bundles if item.get("name") == bundle_slug)

    confirm = ask_optional(f"\nWrite profile params to {output_path}?", default=True)
    if not confirm:
        print("Aborted.")
        return 0

    params = build_params(archetype, bundle)
    try_write_params(output_path, params, force=force)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive profile design wizard")
    parser.add_argument("--classes", default=str(DEFAULT_CLASSES))
    parser.add_argument("--bundles", default=str(DEFAULT_BUNDLES))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--non-interactive", action="store_true", help="Skip prompts and use defaults")
    parser.add_argument("--force", action="store_true", help="Overwrite output file if it exists")
    args = parser.parse_args()

    if args.non_interactive:
        params = {
            "name": "custom-profile",
            "display_name": "Custom Hermes Profile",
            "description": "Interactive wizard output",
            "author": "Hermes profile author",
            "version": "0.1.0",
            "license": "MIT",
            "hermes_requires": ">=0.12.0",
            "model_provider": "openrouter",
            "model_default": "anthropic/claude-sonnet-4",
            "template_source": {
                "name": "codegraphtheory/hermes-profile-template",
                "url": "https://github.com/codegraphtheory/hermes-profile-template",
                "relationship": "generated-from-template",
            },
            "toolsets": ["file", "terminal", "skills", "web", "session_search", "clarify"],
            "env_requires": [],
            "principles": [],
            "scope": [],
            "refusals": [],
            "output_contract": [],
            "github_topics": [],
        }
        try_write_params(Path(args.output), params, force=args.force)
        return 0

    return run_wizard(Path(args.classes), Path(args.bundles), Path(args.output), force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
