#!/usr/bin/env python3
"""Deterministically generate a Hermes profile distribution from a params file."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install pyyaml") from exc


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("name must contain at least one alphanumeric character")
    return value


def as_list(value: Any, default: list[str] | None = None) -> list[str]:
    if value is None:
        return list(default or [])
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else list(default or [])


def yaml_quote(value: str) -> str:
    return yaml.safe_dump(str(value), default_flow_style=True).strip()


def render_bullets(items: list[str], fallback: str) -> str:
    items = items or [fallback]
    return "\n".join(f"- {item}" for item in items)


def render_numbered(items: list[str], fallback_items: list[str]) -> str:
    items = items or fallback_items
    return "\n".join(f"{idx}. {item}" for idx, item in enumerate(items, start=1))


def load_params(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("params file must contain a YAML mapping")
    return data


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def render_distribution(params: dict[str, Any], slug: str, description: str) -> str:
    env_requires = params.get("env_requires") or []
    if not isinstance(env_requires, list):
        raise ValueError("env_requires must be a list")
    manifest: dict[str, Any] = {
        "name": slug,
        "version": str(params.get("version") or "0.1.0"),
        "description": description,
        "hermes_requires": str(params.get("hermes_requires") or ">=0.12.0"),
        "author": str(params.get("author") or "Hermes profile author"),
        "license": str(params.get("license") or "MIT"),
    }
    template_source = params.get("template_source")
    if template_source:
        if not isinstance(template_source, dict):
            raise ValueError("template_source must be a mapping")
        manifest["template_source"] = template_source
    manifest.update(
        {
            "env_requires": env_requires,
            "distribution_owned": [
                "SOUL.md",
                "config.yaml",
                "mcp.json",
                "skills/",
                "templates/",
                "scripts/",
                "distribution.yaml",
                "README.md",
                "AGENTS.md",
                "CHANGELOG.md",
                "CONTRIBUTING.md",
                "SECURITY.md",
                "github-repo-metadata.yaml",
                "requirements.txt",
                "Makefile",
                "docs/",
                ".env.EXAMPLE",
            ],
        }
    )
    return yaml.safe_dump(manifest, sort_keys=False, default_flow_style=False)


def render_env_example(params: dict[str, Any]) -> str:
    lines = [
        "# Copy this file to .env and fill in real values for your own machine.",
        "# Never commit .env.",
        "",
    ]
    env_requires = params.get("env_requires") or []
    if not env_requires:
        lines.append("# Add profile-specific environment variables here when needed.")
    for item in env_requires:
        if not isinstance(item, dict) or not item.get("name"):
            raise ValueError("each env_requires item must be a mapping with name")
        name = str(item["name"])
        desc = str(item.get("description") or "Required by this profile")
        required = bool(item.get("required", True))
        default = str(item.get("default") or "")
        lines.append(f"# {desc}")
        lines.append(f"# {'required' if required else 'optional'}")
        lines.append(f"{name}={default}")
        lines.append("")
    return "\n".join(lines)


def render_config(params: dict[str, Any]) -> str:
    toolsets = as_list(params.get("toolsets"), ["file", "terminal", "skills", "web", "session_search", "clarify"])
    max_turns = int(params.get("max_turns") or 90)
    cwd = str(params.get("cwd") or ".")
    return yaml.safe_dump(
        {
            "model": {
                "provider": str(params.get("model_provider") or "openrouter"),
                "model": str(params.get("model_default") or "anthropic/claude-sonnet-4"),
            },
            "toolsets": toolsets,
            "agent": {"max_turns": max_turns, "tool_use_enforcement": True},
            "terminal": {"backend": "local", "cwd": cwd},
            "compression": {"enabled": True},
            "display": {"tool_progress": True},
            "memory": {"memory_enabled": True, "user_profile_enabled": True},
            "security": {"redact_secrets": True},
            "approvals": {"mode": "manual"},
        },
        sort_keys=False,
    )


def render_soul(params: dict[str, Any], display_name: str, description: str) -> str:
    principles = as_list(
        params.get("principles"),
        [
            "Be useful before being clever.",
            "Use tools when they materially improve correctness.",
            "Keep user data private and never expose secrets.",
            "Verify important claims with evidence.",
            "Prefer maintainable artifacts over transient chat output.",
        ],
    )
    scope = as_list(params.get("scope"), [description, "Produce clear, actionable outputs.", "Call out uncertainty and risks."])
    refusals = as_list(
        params.get("refusals"),
        [
            "Credential theft or secret exposure.",
            "Hidden persistence, backdoors, or deceptive automation.",
            "Fabricated facts, links, audits, or affiliations.",
            "Unsafe changes without explicit user approval.",
        ],
    )
    output_contract = as_list(
        params.get("output_contract"),
        [
            "Result.",
            "Evidence or command output when relevant.",
            "Risks, assumptions, or blockers.",
            "Next step.",
        ],
    )
    return f"""# {display_name}

You are {display_name}, a focused Hermes Agent profile.

## Mission

{description}

## First principles

{render_numbered(principles, [])}

## Scope

This profile is responsible for:

{render_bullets(scope, description)}

## Trigger patterns

Use this profile when the user asks for work that matches its mission, needs repeatable methodology, or should produce durable artifacts rather than an informal chat answer.

## Refusals

Refuse requests that require:

{render_bullets(refusals, "Unsafe or deceptive behavior.")}

## Tool-use expectations

- Inspect live state before making factual claims about files, repos, systems, versions, or current events.
- Run validators, tests, or smoke checks after changing generated profile files.
- Report exact commands and outcomes when verification matters.
- State blockers clearly instead of inventing plausible output.

## Output contract

Default to concise responses with:

{render_numbered(output_contract, [])}

For architecture, planning, review, or multi-step implementation work, prefer a durable artifact path or a structured handoff over a loose chat summary.

## Quality bar

Work is not complete until it is verified or the blocker is stated clearly.
"""


def render_agents(display_name: str) -> str:
    return f"""# {display_name}: Agent Instructions

This profile is designed to be maintained by AI coding agents.

## Hard rules

1. Never commit secrets. `.env` is forbidden. `.env.EXAMPLE` is allowed.
2. Preserve `distribution.yaml` at the repository root.
3. Keep the profile installable with `hermes profile install <source>`.
4. Run `python3 scripts/validate_profile.py .` after substantive edits.
5. Keep instructions concrete and operational.
6. Do not claim tools or integrations that are not configured.

## Interactive profile creation

If the user asks this profile to create another Hermes profile:

1. Ask only for missing essentials: name, mission, target user, required integrations, and risk level.
2. Write a params YAML file using `templates/profile.params.yaml` as the schema reference.
3. Run `python3 scripts/generate_profile.py --params <params.yaml> --output <target-dir>`.
4. Run `python3 <target-dir>/scripts/validate_profile.py <target-dir>`.
5. Report the target path and validation output.

## Handoff format

When finishing, report files changed, commands run, validation output, and remaining manual steps.
"""


def render_readme(params: dict[str, Any], slug: str, display_name: str, description: str) -> str:
    template_source = params.get("template_source")
    lineage = ""
    if isinstance(template_source, dict) and template_source.get("url"):
        template_name = str(template_source.get("name") or "profile template")
        template_url = str(template_source["url"])
        lineage = f"\nTemplate lineage: built from [{template_name}]({template_url}).\n"
    return f"""# {display_name}

{description}
{lineage}
This is a Hermes Agent profile distribution. It can be installed with `hermes profile install` and updated from git.

## Install

```bash
hermes profile install github.com/YOUR_ORG/{slug} --alias
{slug} chat
```

For local development:

```bash
python3 -m pip install -r requirements.txt
make validate
hermes profile install . --name {slug}-local --yes
hermes -p {slug}-local chat
```

## Design prompt

The mature prompt used to generate or refine this profile is preserved in:

```text
docs/profile-prompt.md
```

When starting from a simple sentence, expand it with `skills/prompt-engineering/SKILL.md`, place the mature prompt in `templates/profile.params.yaml` as `profile_prompt`, then regenerate or update this profile.

## Generate another profile from this one

This distribution includes a deterministic generator:

```bash
python3 scripts/generate_profile.py \
  --params templates/profile.params.yaml \
  --output ../my-new-profile
```

Edit `templates/profile.params.yaml` first to customize name, mission, principles, env vars, and toolsets.

## Quality gates

```bash
make validate
make smoke
```

If you do not use `make`, run `python3 scripts/validate_profile.py .` and `scripts/smoke_install.sh` directly.

## Release discipline

For changes that affect profile behavior, generated files, config, docs, skills, scripts, or distribution metadata:

1. Bump `version` in `distribution.yaml`.
2. Add a matching `## <version>` entry to `CHANGELOG.md`.
3. Run `make release-check` before opening a pull request.

## Safety

Do not commit `.env`, credentials, memories, sessions, logs, runtime databases, or user data. See `SECURITY.md` for vulnerability reporting and secret-handling expectations. See `CONTRIBUTING.md` for the validation and release checklist.
"""


def render_github_metadata(slug: str, description: str, params: dict[str, Any]) -> str:
    topics = as_list(
        params.get("github_topics"),
        [
            "hermes-agent",
            "ai-agents",
            "agent-profile",
            "profile-distribution",
            "developer-tools",
        ],
    )
    data = {
        "description": description,
        "homepage": str(params.get("github_homepage") or ""),
        "topics": topics[:20],
    }
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)


def render_template_source_file(params: dict[str, Any]) -> str | None:
    template_source = params.get("template_source")
    if not template_source:
        return None
    if not isinstance(template_source, dict):
        raise ValueError("template_source must be a mapping")
    data = {
        "template": template_source,
        "notes": [
            "GitHub native generated-from-template linkage is only available when a repository is created through GitHub's template flow.",
            "This file records template lineage explicitly for humans and automation.",
        ],
    }
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)


def render_profile_prompt(params: dict[str, Any], display_name: str, description: str) -> str:
    profile_prompt = str(params.get("profile_prompt") or "").strip()
    if profile_prompt:
        return f"""# Mature Profile Prompt

This document preserves the expanded prompt used to generate this Hermes profile distribution.

{profile_prompt}
"""
    return f"""# Mature Profile Prompt

This profile was generated from structured params. Use this document to record the mature profile prompt when regenerating or substantially redesigning the profile.

## Profile

{display_name}

## Mission

{description}

## Regeneration note

For future changes, start with a simple sentence, expand it with the prompt-engineering workflow in `skills/prompt-engineering/SKILL.md`, write the result to the `profile_prompt` field in `templates/profile.params.yaml`, then regenerate or edit the profile with validation.
"""


def render_params_example(slug: str, display_name: str, description: str, author: str) -> str:
    data = {
        "name": slug,
        "display_name": display_name,
        "description": description,
        "author": author,
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
        "principles": [
            "Be useful before being clever.",
            "Use tools when they materially improve correctness.",
            "Keep user data private and never expose secrets.",
            "Verify important claims with evidence.",
        ],
        "scope": [description, "Produce clear, actionable outputs."],
        "refusals": [
            "Credential theft or secret exposure.",
            "Hidden persistence, backdoors, or deceptive automation.",
            "Fabricated facts, links, audits, or affiliations.",
        ],
        "output_contract": ["Result.", "Evidence or command output when relevant.", "Next step."],
        "profile_prompt": (
            "Create a mature Hermes profile prompt before generation. "
            "Capture mission, target users, workflows, trigger patterns, inputs, "
            "outputs, tool-use policy, safety boundaries, required skills, "
            "verification, and repository output requirements."
        ),
        "github_topics": [
            "hermes-agent",
            "ai-agents",
            "agent-profile",
            "profile-distribution",
            "developer-tools",
        ],
    }
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)


def copy_support_files(template_root: Path, output: Path) -> None:
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
    for rel in ["scripts", ".github"]:
        src = template_root / rel
        if src.exists():
            shutil.copytree(src, output / rel, dirs_exist_ok=True, ignore=ignore)
    # When this repository is installed as a Hermes profile, Hermes may seed the
    # profile with many bundled user skills. Do not copy that entire runtime
    # skills directory into generated repos. Only copy this template's own
    # authoring skills as starter examples.
    for skill_name in ["profile-craft", "prompt-engineering"]:
        skill_dir = template_root / "skills" / skill_name
        if skill_dir.exists():
            shutil.copytree(
                skill_dir,
                output / "skills" / skill_name,
                dirs_exist_ok=True,
                ignore=ignore,
            )
    for rel in ["LICENSE", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md", "requirements.txt", "Makefile"]:
        src_file = template_root / rel
        if src_file.exists():
            shutil.copy2(src_file, output / rel)
    docs_dir = template_root / "docs"
    if docs_dir.exists():
        shutil.copytree(docs_dir, output / "docs", dirs_exist_ok=True, ignore=ignore)
    catalog_templates = template_root / "templates" / "catalog"
    if catalog_templates.exists():
        shutil.copytree(catalog_templates, output / "templates" / "catalog", dirs_exist_ok=True, ignore=ignore)
    gitignore = output / ".gitignore"
    if not gitignore.exists():
        write(
            gitignore,
            ".env\n*.db\n*.db-shm\n*.db-wal\n*.pyc\n*.pyo\n*.pyd\n.coverage\ncoverage.xml\nhtmlcov/\ndist/\nbuild/\n*.egg-info/\nlogs/\nsessions/\nmemories/\nworkspace/\nplans/\nlocal/\ncache/\nhook-sessions/\n.heavy-coder/hook-sessions/\n__pycache__/\n.pytest_cache/\n.mypy_cache/\n.ruff_cache/\n.DS_Store\n",
        )


def generate(params: dict[str, Any], output: Path, force: bool, template_root: Path) -> None:
    name = str(params.get("name") or "").strip()
    if not name:
        raise ValueError("params missing required field: name")
    slug = slugify(name)
    display_name = str(params.get("display_name") or name.replace("-", " ").title())
    description = str(params.get("description") or "").strip()
    if not description:
        raise ValueError("params missing required field: description")
    author = str(params.get("author") or "Hermes profile author")

    if output.exists():
        if not force:
            raise FileExistsError(f"output exists. Pass --force to overwrite: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    write(output / "distribution.yaml", render_distribution(params, slug, description))
    write(output / "SOUL.md", render_soul(params, display_name, description))
    write(output / "AGENTS.md", render_agents(display_name))
    write(output / "README.md", render_readme(params, slug, display_name, description))
    write(output / "config.yaml", render_config(params))
    write(output / ".env.EXAMPLE", render_env_example(params))
    write(output / "mcp.json", "{\n  \"mcpServers\": {}\n}")
    write(output / "github-repo-metadata.yaml", render_github_metadata(slug, description, params))
    write(output / "templates" / "profile.params.yaml", render_params_example(slug, display_name, description, author))
    copy_support_files(template_root, output)
    write(output / "docs" / "profile-prompt.md", render_profile_prompt(params, display_name, description))
    template_source_file = render_template_source_file(params)
    if template_source_file:
        write(output / ".github" / "template-source.yml", template_source_file)

    result = subprocess.run(
        ["python3", str(output / "scripts" / "validate_profile.py"), str(output)],
        text=True,
        capture_output=True,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministically generate a Hermes profile distribution")
    parser.add_argument("--params", required=True, help="YAML file describing the profile")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--force", action="store_true", help="Overwrite output directory if it exists")
    args = parser.parse_args()

    template_root = Path(__file__).resolve().parents[1]
    params = load_params(Path(args.params).resolve())
    output = Path(args.output).resolve()
    generate(params, output, args.force, template_root)
    print(f"Created Hermes profile distribution: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
