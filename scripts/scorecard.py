#!/usr/bin/env python3
"""Profile quality scorecard with JSON and Markdown output.

Extends validation with advisory quality checks and produces a structured
scorecard report suitable for CI, PR comments, and README snippets.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install pyyaml") from exc


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    name: str
    status: str  # "pass" | "warn" | "fail"
    message: str = ""
    details: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "message": self.message, "details": self.details}


@dataclass
class Scorecard:
    distribution: str
    version: str
    timestamp: str
    summary: dict[str, int] = field(default_factory=lambda: {"pass": 0, "warn": 0, "fail": 0})
    checks: list[dict[str, str]] = field(default_factory=list)

    def add(self, result: CheckResult) -> None:
        self.checks.append(result.to_dict())
        self.summary[result.status] = self.summary.get(result.status, 0) + 1

    def passed(self) -> bool:
        return self.summary.get("fail", 0) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "distribution": self.distribution,
            "version": self.version,
            "timestamp": self.timestamp,
            "summary": dict(self.summary),
            "checks": list(self.checks),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_yaml_safe(path: Path) -> dict[str, Any] | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)


def find_distribution(root: Path) -> Path | None:
    path = root / "distribution.yaml"
    return path if path.exists() else None


def read_distribution(root: Path) -> dict[str, Any]:
    path = find_distribution(root)
    if path is None:
        return {}
    data = load_yaml_safe(path)
    return data or {}


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_manifest_fields(root: Path, scorecard: Scorecard) -> None:
    """Check required manifest fields are present and well-formed."""
    dist = read_distribution(root)
    required = ["name", "version", "description"]
    for key in required:
        val = str(dist.get(key, "")).strip()
        if not val:
            scorecard.add(CheckResult(
                name=f"manifest:{key}",
                status="fail",
                message=f"distribution.yaml missing required field: {key}",
            ))
        else:
            scorecard.add(CheckResult(
                name=f"manifest:{key}",
                status="pass",
                message=f"{key}: {val[:60]}",
            ))

    name = str(dist.get("name", ""))
    if name and not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", name):
        scorecard.add(CheckResult(
            name="manifest:name_format",
            status="fail",
            message="distribution.yaml name must be lowercase kebab case",
        ))

    # version format check (semver-like)
    version = str(dist.get("version", ""))
    if version and not re.match(r"^\d+\.\d+\.\d+", version):
        scorecard.add(CheckResult(
            name="manifest:version_format",
            status="warn",
            message=f"Version '{version}' is not semver-like (expected X.Y.Z)",
        ))


def check_readme_has_install(root: Path, scorecard: Scorecard) -> None:
    """README should contain an install command."""
    readme = root / "README.md"
    if not readme.exists():
        scorecard.add(CheckResult(
            name="readme:exists",
            status="fail",
            message="README.md is missing",
        ))
        return

    scorecard.add(CheckResult(
        name="readme:exists",
        status="pass",
        message="README.md present",
    ))

    text = readme.read_text(encoding="utf-8")
    install_patterns = [
        r"pip install",
        r"hermes install",
        r"git clone",
        r"npm install",
        r"cargo install",
        r"brew install",
        r"make install",
        r"go install",
        r"curl.*install",
    ]
    found_install = any(re.search(p, text, re.IGNORECASE) for p in install_patterns)
    if found_install:
        scorecard.add(CheckResult(
            name="readme:install_command",
            status="pass",
            message="README contains an install command",
        ))
    else:
        scorecard.add(CheckResult(
            name="readme:install_command",
            status="warn",
            message="README may be missing an install command",
        ))


def check_env_example(root: Path, scorecard: Scorecard) -> None:
    """.env.EXAMPLE should document required environment variables."""
    env_example = root / ".env.EXAMPLE"
    if not env_example.exists():
        scorecard.add(CheckResult(
            name="env:example_exists",
            status="fail",
            message=".env.EXAMPLE is missing",
        ))
        return

    scorecard.add(CheckResult(
        name="env:example_exists",
        status="pass",
        message=".env.EXAMPLE present",
    ))

    text = env_example.read_text(encoding="utf-8").strip()
    if not text:
        scorecard.add(CheckResult(
            name="env:example_content",
            status="warn",
            message=".env.EXAMPLE is empty",
        ))
        return

    # Check declared env vars are documented
    dist = read_distribution(root)
    env_requires = dist.get("env_requires", [])
    if not isinstance(env_requires, list):
        env_requires = []

    missing_from_example = []
    for item in env_requires:
        if isinstance(item, dict) and item.get("name"):
            if item["name"] not in text:
                missing_from_example.append(item["name"])

    if missing_from_example:
        scorecard.add(CheckResult(
            name="env:declared_in_example",
            status="fail",
            message=f"Env vars declared in distribution.yaml but missing from .env.EXAMPLE: {', '.join(missing_from_example)}",
        ))
    else:
        scorecard.add(CheckResult(
            name="env:declared_in_example",
            status="pass",
            message="All declared env vars are documented in .env.EXAMPLE",
        ))


def check_license(root: Path, scorecard: Scorecard) -> None:
    """License file should exist."""
    license_paths = ["LICENSE", "LICENSE.txt", "LICENSE.md"]
    found = any((root / lp).exists() for lp in license_paths)
    if found:
        scorecard.add(CheckResult(
            name="license:exists",
            status="pass",
            message="License file present",
        ))
    else:
        scorecard.add(CheckResult(
            name="license:exists",
            status="warn",
            message="No license file found",
        ))


def check_security_docs(root: Path, scorecard: Scorecard) -> None:
    """Security documentation should exist."""
    if (root / "SECURITY.md").exists():
        scorecard.add(CheckResult(
            name="security:policy",
            status="pass",
            message="SECURITY.md present",
        ))
    else:
        scorecard.add(CheckResult(
            name="security:policy",
            status="warn",
            message="SECURITY.md is missing",
        ))


def check_changelog(root: Path, scorecard: Scorecard) -> None:
    """CHANGELOG.md should exist and have an entry for the current version."""
    dist = read_distribution(root)
    version = str(dist.get("version", "")).strip()

    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        scorecard.add(CheckResult(
            name="changelog:exists",
            status="warn",
            message="CHANGELOG.md is missing",
        ))
        return

    scorecard.add(CheckResult(
        name="changelog:exists",
        status="pass",
        message="CHANGELOG.md present",
    ))

    if version:
        text = changelog.read_text(encoding="utf-8")
        has_entry = re.search(rf"^##\s+\[?{re.escape(version)}\]?\b", text, flags=re.MULTILINE)
        if has_entry:
            scorecard.add(CheckResult(
                name="changelog:version_entry",
                status="pass",
                message=f"CHANGELOG has entry for version {version}",
            ))
        else:
            scorecard.add(CheckResult(
                name="changelog:version_entry",
                status="warn",
                message=f"CHANGELOG missing entry for version {version}",
            ))


def check_github_topics(root: Path, scorecard: Scorecard) -> None:
    """GitHub topics should be defined in distribution.yaml or metadata."""
    dist = read_distribution(root)
    topics = dist.get("github_topics", [])
    if isinstance(topics, list) and len(topics) >= 3:
        scorecard.add(CheckResult(
            name="github:topics",
            status="pass",
            message=f"{len(topics)} GitHub topics defined",
        ))
    elif isinstance(topics, list) and len(topics) > 0:
        scorecard.add(CheckResult(
            name="github:topics",
            status="warn",
            message=f"Only {len(topics)} GitHub topics defined (recommend >= 3)",
        ))
    else:
        scorecard.add(CheckResult(
            name="github:topics",
            status="warn",
            message="No GitHub topics defined in distribution.yaml",
        ))


def check_contributing(root: Path, scorecard: Scorecard) -> None:
    """CONTRIBUTING.md should exist."""
    if (root / "CONTRIBUTING.md").exists():
        scorecard.add(CheckResult(
            name="contributing:exists",
            status="pass",
            message="CONTRIBUTING.md present",
        ))
    else:
        scorecard.add(CheckResult(
            name="contributing:exists",
            status="warn",
            message="CONTRIBUTING.md is missing",
        ))


def check_no_secrets_or_runtime(root: Path, scorecard: Scorecard) -> None:
    """Check for runtime files or secrets that should not be committed."""
    forbidden_dirs = {
        "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        "htmlcov", "dist", "build", "node_modules", ".venv", "venv",
        "memories", "sessions", "logs", "workspace", "local", "cache",
    }
    forbidden_files = {".coverage", "coverage.xml", ".env", "auth.json", "state.db"}
    forbidden_suffixes = (".pyc", ".pyo", ".pyd")

    issues = []
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_dir() and path.name in forbidden_dirs:
            issues.append(f"Runtime directory committed: {path.relative_to(root)}")
        if path.is_file():
            if path.name in forbidden_files:
                issues.append(f"Forbidden file committed: {path.relative_to(root)}")
            if path.suffix in forbidden_suffixes:
                issues.append(f"Cache artifact committed: {path.relative_to(root)}")

    if issues:
        scorecard.add(CheckResult(
            name="repo:no_runtime_artifacts",
            status="fail",
            message="Runtime or cache artifacts found in repository",
            details="\n".join(issues[:5]),
        ))
    else:
        scorecard.add(CheckResult(
            name="repo:no_runtime_artifacts",
            status="pass",
            message="No runtime artifacts committed",
        ))


def check_has_tests(root: Path, scorecard: Scorecard) -> None:
    """Check for test files."""
    test_patterns = ["test_*.py", "*_test.py", "tests/", "spec/", "__tests__/"]
    has_tests = False
    for pattern in test_patterns:
        if any(root.rglob(pattern)):
            has_tests = True
            break

    if has_tests:
        scorecard.add(CheckResult(
            name="testing:tests_exist",
            status="pass",
            message="Test files found",
        ))
    else:
        scorecard.add(CheckResult(
            name="testing:tests_exist",
            status="warn",
            message="No test files found",
        ))


def check_ci_config(root: Path, scorecard: Scorecard) -> None:
    """Check for CI configuration."""
    ci_paths = [
        root / ".github" / "workflows",
        root / ".gitlab-ci.yml",
        root / ".circleci" / "config.yml",
        root / "Jenkinsfile",
        root / ".drone.yml",
    ]
    has_ci = any(p.exists() for p in ci_paths)
    if has_ci:
        scorecard.add(CheckResult(
            name="ci:configured",
            status="pass",
            message="CI configuration found",
        ))
    else:
        scorecard.add(CheckResult(
            name="ci:configured",
            status="warn",
            message="No CI configuration found",
        ))


def check_install_smoke(root: Path, scorecard: Scorecard) -> None:
    """Check that an install smoke command is documented."""
    makefile = root / "Makefile"
    if makefile.exists():
        text = makefile.read_text(encoding="utf-8")
        if re.search(r"^smoke:", text, re.MULTILINE):
            scorecard.add(CheckResult(
                name="smoke:make_target",
                status="pass",
                message="Makefile has smoke target",
            ))
            return

    readme = root / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        if re.search(r"(smoke|install.*test|verify)", text, re.IGNORECASE):
            scorecard.add(CheckResult(
                name="smoke:documented",
                status="pass",
                message="Smoke/verification command documented in README",
            ))
            return

    scorecard.add(CheckResult(
        name="smoke:documented",
        status="warn",
        message="No smoke test or install verification command found",
    ))


# ---------------------------------------------------------------------------
# Scorecard runner
# ---------------------------------------------------------------------------

def run_scorecard(root: Path) -> Scorecard:
    dist = read_distribution(root)
    name = str(dist.get("name", root.name))
    version = str(dist.get("version", "0.0.0"))

    scorecard = Scorecard(
        distribution=name,
        version=version,
        timestamp=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    checks = [
        check_manifest_fields,
        check_readme_has_install,
        check_env_example,
        check_license,
        check_security_docs,
        check_changelog,
        check_github_topics,
        check_contributing,
        check_no_secrets_or_runtime,
        check_has_tests,
        check_ci_config,
        check_install_smoke,
    ]

    for check_fn in checks:
        check_fn(root, scorecard)

    return scorecard


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_terminal(scorecard: Scorecard) -> str:
    lines = [
        f"📊 Profile Scorecard: {scorecard.distribution} v{scorecard.version}",
        f"   Timestamp: {scorecard.timestamp}",
        f"   Summary: ✅ {scorecard.summary.get('pass', 0)}  ⚠️ {scorecard.summary.get('warn', 0)}  ❌ {scorecard.summary.get('fail', 0)}",
        "",
    ]
    for check in scorecard.checks:
        icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(check["status"], "❓")
        lines.append(f"  {icon} {check['name']}: {check['message']}")
        if check.get("details"):
            for detail in check["details"].split("\n"):
                lines.append(f"     {detail}")

    if scorecard.summary.get("fail", 0) > 0:
        lines.append("")
        lines.append("❌ Scorecard has failures that should be addressed.")
    elif scorecard.summary.get("warn", 0) > 0:
        lines.append("")
        lines.append("⚠️ Scorecard passed with warnings.")
    else:
        lines.append("")
        lines.append("✅ Scorecard passed all checks.")

    return "\n".join(lines)


def format_markdown(scorecard: Scorecard) -> str:
    lines = [
        f"# 📊 Profile Scorecard: {scorecard.distribution} v{scorecard.version}",
        "",
        f"**Timestamp:** {scorecard.timestamp}",
        "",
        "## Summary",
        "",
        f"| Status | Count |",
        f"|--------|-------|",
        f"| ✅ Pass | {scorecard.summary.get('pass', 0)} |",
        f"| ⚠️ Warn | {scorecard.summary.get('warn', 0)} |",
        f"| ❌ Fail | {scorecard.summary.get('fail', 0)} |",
        "",
        "## Checks",
        "",
    ]
    for check in scorecard.checks:
        icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(check["status"], "❓")
        lines.append(f"### {icon} {check['name']}")
        lines.append(f"")
        lines.append(f"**Status:** {check['status']}")
        lines.append(f"")
        lines.append(f"{check['message']}")
        if check.get("details"):
            lines.append("")
            lines.append("```")
            lines.append(check["details"])
            lines.append("```")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Profile quality scorecard — advisory checks beyond validation",
    )
    parser.add_argument("path", nargs="?", default=".", help="Profile distribution root")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--markdown", action="store_true", help="Output Markdown")
    parser.add_argument("--output", "-o", help="Write output to file")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 2

    scorecard = run_scorecard(root)

    if args.json:
        output = json.dumps(scorecard.to_dict(), indent=2)
    elif args.markdown:
        output = format_markdown(scorecard)
    else:
        output = format_terminal(scorecard)

    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(f"Scorecard written to {args.output}")
    else:
        print(output)

    return 0 if scorecard.passed() else 1


if __name__ == "__main__":
    raise SystemExit(main())
