#!/usr/bin/env python3
"""Release readiness checks for Hermes profile distributions."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

RELEASE_RELEVANT_PREFIXES = (
    ".github/",
    "docs/",
    "skills/",
    "templates/",
    "scripts/",
    "web-demo/",
    "examples/",
    "SOUL.md",
    "AGENTS.md",
    "README.md",
    "Makefile",
    "requirements.txt",
    "distribution.yaml",
    "config.yaml",
    "mcp.json",
)
IGNORED_PATHS = {"CHANGELOG.md"}
FORBIDDEN_NAMES = {".env", "auth.json", "state.db", "state.db-shm", "state.db-wal"}
FORBIDDEN_PARTS = {"memories", "sessions", "logs", "workspace", "plans", ".pytest_cache", "__pycache__"}
SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str
    hint: str = ""


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)


def changed_files(root: Path, base: str) -> list[str] | None:
    proc = run_git(root, ["diff", "--name-only", f"{base}...HEAD"])
    if proc.returncode != 0:
        proc = run_git(root, ["diff", "--name-only", base, "HEAD"])
    if proc.returncode != 0:
        return None
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def read_manifest_version_text(text: str) -> str | None:
    data = yaml.safe_load(text) or {}
    version = str(data.get("version") or "").strip()
    return version or None


def current_version(root: Path) -> str | None:
    manifest = root / "distribution.yaml"
    if not manifest.exists():
        return None
    return read_manifest_version_text(manifest.read_text(encoding="utf-8"))


def base_version(root: Path, base: str) -> str | None:
    proc = run_git(root, ["show", f"{base}:distribution.yaml"])
    if proc.returncode != 0:
        return None
    return read_manifest_version_text(proc.stdout)


def is_release_relevant(path: str) -> bool:
    if path in IGNORED_PATHS:
        return False
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in RELEASE_RELEVANT_PREFIXES)


def iter_validation_paths(root: Path) -> list[Path]:
    proc = run_git(root, ["ls-files", "--cached", "--others", "--exclude-standard", "-z"])
    if proc.returncode == 0:
        return [root / item for item in proc.stdout.split("\0") if item]
    return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


def check_version(root: Path, base: str, strict: bool) -> CheckResult:
    files = changed_files(root, base)
    if files is None:
        status = "FAIL" if strict else "SKIP"
        return CheckResult("version", status, f"Could not compare against {base}", "Fetch the base ref before running release readiness.")
    relevant = [path for path in files if is_release_relevant(path)]
    if not relevant:
        return CheckResult("version", "PASS", "No release-relevant changes detected.")
    now = current_version(root)
    before = base_version(root, base)
    if not now:
        return CheckResult("version", "FAIL", "distribution.yaml is missing a version.")
    if before and before == now:
        return CheckResult("version", "FAIL", f"Release-relevant files changed but version stayed {now}.", "Bump distribution.yaml and add a matching changelog heading.")
    return CheckResult("version", "PASS", f"Version is release-ready: {before or 'unknown'} -> {now}.")


def check_changelog(root: Path) -> CheckResult:
    version = current_version(root)
    changelog = root / "CHANGELOG.md"
    if not version:
        return CheckResult("changelog", "FAIL", "Cannot read current distribution version.")
    if not changelog.exists():
        return CheckResult("changelog", "FAIL", "CHANGELOG.md is missing.")
    text = changelog.read_text(encoding="utf-8")
    if re.search(rf"^##\s+{re.escape(version)}\b", text, re.MULTILINE):
        return CheckResult("changelog", "PASS", f"Found CHANGELOG.md heading for {version}.")
    return CheckResult("changelog", "FAIL", f"Missing CHANGELOG.md heading for {version}.")


def check_command(root: Path, name: str, cmd: list[str]) -> CheckResult:
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    detail = (proc.stdout + proc.stderr).strip().splitlines()[-12:]
    joined = "\n".join(detail) if detail else "command produced no output"
    return CheckResult(name, "PASS" if proc.returncode == 0 else "FAIL", joined)


def check_runtime_and_secrets(root: Path) -> CheckResult:
    hits: list[str] = []
    for path in iter_validation_paths(root):
        rel = path.relative_to(root)
        if path.name in FORBIDDEN_NAMES or set(rel.parts) & FORBIDDEN_PARTS:
            hits.append(str(rel))
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".zip", ".pack", ".idx"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(f"{rel}: matches {pattern.pattern}")
                break
    if hits:
        return CheckResult("runtime-and-secrets", "FAIL", "\n".join(hits[:20]))
    return CheckResult("runtime-and-secrets", "PASS", "No forbidden runtime paths or token-like secrets found.")


def markdown_report(results: list[CheckResult]) -> str:
    lines = ["# Release readiness report", "", "| Check | Status | Detail |", "| --- | --- | --- |"]
    for result in results:
        detail = result.detail.replace("|", "\\|").replace("\n", "<br>")
        if result.hint:
            detail += "<br>Hint: " + result.hint.replace("|", "\\|")
        lines.append(f"| {result.name} | {result.status} | {detail} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check release readiness for this Hermes profile distribution.")
    parser.add_argument("--base", default="origin/main", help="Base ref for version discipline checks.")
    parser.add_argument("--strict", action="store_true", help="Fail instead of skipping when the base ref is unavailable.")
    args = parser.parse_args()
    root = Path.cwd()
    results = [
        check_version(root, args.base, args.strict),
        check_changelog(root),
        check_command(root, "profile-validation", [sys.executable, "scripts/validate_profile.py", "."]),
        check_command(root, "python-compile", [sys.executable, "-m", "py_compile", *[str(p) for p in sorted((root / "scripts").glob("*.py"))]]),
        check_runtime_and_secrets(root),
    ]
    print(markdown_report(results))
    return 0 if all(result.status in {"PASS", "SKIP"} for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
