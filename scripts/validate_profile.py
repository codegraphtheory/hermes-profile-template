#!/usr/bin/env python3
"""Validate a Hermes profile distribution template."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]

USER_OWNED = {
    ".env",
    "auth.json",
    "state.db",
    "state.db-shm",
    "state.db-wal",
    "memories",
    "sessions",
    "logs",
    "workspace",
    "plans",
    "local",
    "cache",
}

FORBIDDEN_DIR_NAMES = USER_OWNED | {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    "dist",
    "build",
    "hook-sessions",
}

FORBIDDEN_FILE_NAMES = {
    ".coverage",
    "coverage.xml",
}

FORBIDDEN_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".pyd",
)

REQUIRED_ROOT = ["distribution.yaml", "SOUL.md", "README.md", "AGENTS.md", "config.yaml", ".env.EXAMPLE"]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def iter_validation_paths(root: Path) -> list[Path]:
    """Return files to validate.

    In git repositories, validate tracked files plus unignored untracked files.
    Ignored local caches are not distribution content and should not make local
    validation fail. In generated directories without git metadata, validate the
    full tree.
    """
    if (root / ".git").exists():
        proc = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=root,
            text=False,
            capture_output=True,
        )
        if proc.returncode == 0:
            rels = [item.decode("utf-8") for item in proc.stdout.split(b"\0") if item]
            return [root / rel for rel in rels]
    return [path for path in root.rglob("*") if path.is_file()]


def load_yaml(path: Path, errors: list[str]):
    if yaml is None:
        fail(errors, "PyYAML is required. Install with: python3 -m pip install pyyaml")
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        fail(errors, f"Invalid YAML in {path}: {exc}")
        return None


def check_required(root: Path, errors: list[str]) -> None:
    for rel in REQUIRED_ROOT:
        if not (root / rel).is_file():
            fail(errors, f"Missing required file: {rel}")


def check_manifest(root: Path, errors: list[str]) -> None:
    path = root / "distribution.yaml"
    if not path.exists():
        return
    data = load_yaml(path, errors)
    if not isinstance(data, dict):
        fail(errors, "distribution.yaml must be a mapping")
        return
    for key in ["name", "version", "description"]:
        if not str(data.get(key, "")).strip():
            fail(errors, f"distribution.yaml missing required field: {key}")
    name = str(data.get("name", ""))
    if name and not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", name):
        fail(errors, "distribution.yaml name must be lowercase kebab case")
    env_requires = data.get("env_requires", [])
    template_source = data.get("template_source")
    if template_source is not None:
        if not isinstance(template_source, dict):
            fail(errors, "distribution.yaml template_source must be a mapping")
        elif template_source.get("url") and not str(template_source["url"]).startswith("https://github.com/"):
            fail(errors, "distribution.yaml template_source.url should be a GitHub HTTPS URL")
    lineage_file = root / ".github" / "template-source.yml"
    if template_source and not lineage_file.exists():
        fail(errors, "template_source is declared but .github/template-source.yml is missing")
    if lineage_file.exists():
        lineage = load_yaml(lineage_file, errors)
        if isinstance(lineage, dict) and not isinstance(lineage.get("template"), dict):
            fail(errors, ".github/template-source.yml must contain a template mapping")
    if env_requires and not isinstance(env_requires, list):
        fail(errors, "distribution.yaml env_requires must be a list")
    owned = data.get("distribution_owned", [])
    if owned and not isinstance(owned, list):
        fail(errors, "distribution.yaml distribution_owned must be a list")
    for rel in owned or []:
        rel_str = str(rel).rstrip("/")
        if rel_str and not (root / rel_str).exists():
            fail(errors, f"distribution_owned path does not exist: {rel}")
    example = (root / ".env.EXAMPLE").read_text(encoding="utf-8") if (root / ".env.EXAMPLE").exists() else ""
    for item in env_requires or []:
        if not isinstance(item, dict) or not item.get("name"):
            fail(errors, "Each env_requires entry must be a mapping with name")
            continue
        if item["name"] not in example:
            fail(errors, f"Env var {item['name']} is declared but missing from .env.EXAMPLE")


def check_json(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*.json"):
        if ".git" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(errors, f"Invalid JSON in {path.relative_to(root)}: {exc}")


def check_skills(root: Path, errors: list[str]) -> None:
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return
    for skill_md in skills_dir.rglob("SKILL.md"):
        text = skill_md.read_text(encoding="utf-8")
        rel = skill_md.relative_to(root)
        if not text.startswith("---\n"):
            fail(errors, f"Skill missing YAML frontmatter: {rel}")
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            fail(errors, f"Skill frontmatter not closed: {rel}")
            continue
        if yaml is not None:
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except Exception as exc:
                fail(errors, f"Invalid skill frontmatter in {rel}: {exc}")
                continue
            for key in ["name", "description"]:
                if not meta.get(key):
                    fail(errors, f"Skill {rel} missing frontmatter field: {key}")


def check_forbidden_paths(root: Path, errors: list[str]) -> None:
    seen_dirs: set[Path] = set()
    for path in iter_validation_paths(root):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(root)
        for parent in rel.parents:
            if str(parent) == "." or parent in seen_dirs:
                continue
            seen_dirs.add(parent)
            if parent.name in FORBIDDEN_DIR_NAMES:
                fail(errors, f"Runtime or cache directory must not be committed: {parent}")
        if path.name in FORBIDDEN_FILE_NAMES:
            fail(errors, f"Runtime or coverage file must not be committed: {rel}")
        if path.name in USER_OWNED:
            fail(errors, f"User-owned runtime file must not be committed: {rel}")
        if path.name.endswith(FORBIDDEN_SUFFIXES):
            fail(errors, f"Python cache artifact must not be committed: {rel}")


def check_symlinks(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*"):
        if path.is_symlink() and not path.exists():
            fail(errors, f"Broken symlink: {path.relative_to(root)} -> {os.readlink(path)}")


def check_secrets(root: Path, errors: list[str]) -> None:
    skip_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__"}
    for path in root.rglob("*"):
        if not path.is_file() or any(part in skip_dirs for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(errors, f"Possible secret pattern in {path.relative_to(root)}")


def check_placeholders(root: Path, errors: list[str]) -> None:
    allowed = {"templates"}
    pattern = re.compile(r"{{[a-zA-Z0-9_]+}}")
    for path in root.rglob("*"):
        if not path.is_file() or any(part in allowed for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if pattern.search(text):
            fail(errors, f"Unresolved template placeholder in {path.relative_to(root)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Hermes profile distribution")
    parser.add_argument("path", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    errors: list[str] = []
    if not root.exists():
        print(f"ERROR: path does not exist: {root}")
        return 2
    check_required(root, errors)
    check_manifest(root, errors)
    check_json(root, errors)
    check_skills(root, errors)
    check_forbidden_paths(root, errors)
    check_symlinks(root, errors)
    check_secrets(root, errors)
    check_placeholders(root, errors)
    if errors:
        print("Hermes profile validation failed")
        for err in errors:
            print(f"ERROR: {err}")
        return 1
    print(f"Hermes profile validation passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
