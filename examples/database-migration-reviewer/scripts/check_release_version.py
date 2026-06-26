#!/usr/bin/env python3
"""Fail when release-relevant changes omit version or changelog updates."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install pyyaml") from exc

RELEASE_RELEVANT_PREFIXES = (
    "SOUL.md",
    "AGENTS.md",
    "README.md",
    "config.yaml",
    "distribution.yaml",
    ".env.EXAMPLE",
    "mcp.json",
    "skills/",
    "templates/",
    "scripts/",
    ".github/workflows/",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "github-repo-metadata.yaml",
    "requirements.txt",
    "Makefile",
    "docs/",
)

IGNORED_PATHS = {
    "CHANGELOG.md",
}


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)


def read_current_version(root: Path) -> str:
    data = yaml.safe_load((root / "distribution.yaml").read_text(encoding="utf-8")) or {}
    version = str(data.get("version") or "").strip()
    if not version:
        raise ValueError("distribution.yaml missing version")
    return version


def read_base_version(root: Path, base: str) -> str | None:
    proc = run_git(["show", f"{base}:distribution.yaml"], root)
    if proc.returncode != 0:
        return None
    data = yaml.safe_load(proc.stdout) or {}
    return str(data.get("version") or "").strip() or None


def changed_files(root: Path, base: str) -> list[str] | None:
    proc = run_git(["diff", "--name-only", f"{base}...HEAD"], root)
    if proc.returncode != 0:
        proc = run_git(["diff", "--name-only", base, "HEAD"], root)
    if proc.returncode != 0:
        return None
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def is_release_relevant(path: str) -> bool:
    if path in IGNORED_PATHS:
        return False
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in RELEASE_RELEVANT_PREFIXES)


def changelog_has_version(root: Path, version: str) -> bool:
    path = root / "CHANGELOG.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return re.search(rf"^##\s+\[?{re.escape(version)}\]?\b", text, flags=re.MULTILINE) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check release version discipline")
    parser.add_argument("--base", default="origin/main", help="Git base ref to compare against")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--strict", action="store_true", help="Fail instead of skip when base ref is unavailable")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = changed_files(root, args.base)
    if files is None:
        message = f"Could not compare against base ref {args.base}"
        if args.strict:
            print(f"ERROR: {message}")
            return 1
        print(f"SKIP: {message}")
        return 0

    relevant = [path for path in files if is_release_relevant(path)]
    if not relevant:
        print("No release-relevant changes detected.")
        return 0

    current_version = read_current_version(root)
    base_version = read_base_version(root, args.base)
    if base_version is None:
        message = f"Could not read distribution.yaml from {args.base}"
        if args.strict:
            print(f"ERROR: {message}")
            return 1
        print(f"SKIP: {message}")
        return 0

    errors: list[str] = []
    if current_version == base_version:
        errors.append(
            f"distribution.yaml version did not change. Base and current version are both {current_version}."
        )
    if not changelog_has_version(root, current_version):
        errors.append(f"CHANGELOG.md is missing an entry for version {current_version}.")

    if errors:
        print("Release version check failed.")
        print("Release-relevant files changed:")
        for path in relevant:
            print(f"- {path}")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Release version check passed for version {current_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
