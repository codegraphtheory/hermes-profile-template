#!/usr/bin/env python3
"""Produce a deterministic publishability scorecard for a Hermes profile."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install pyyaml") from exc

import validate_profile

SCHEMA_VERSION = "hermes-profile-scorecard/v0.1"
RECOMMENDED_TOPICS = {
    "hermes-agent",
    "ai-agents",
    "agent-profile",
    "profile-distribution",
}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def check_result(
    check_id: str,
    title: str,
    severity: str,
    status: str,
    message: str,
    remediation: str = "",
    details: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "title": title,
        "severity": severity,
        "status": status,
        "message": message,
        "remediation": remediation,
        "details": sorted(details or []),
    }


def run_existing_validator(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    if not root.exists():
        return check_result(
            "profile.validation",
            "Existing profile validation",
            "required",
            "fail",
            f"Profile path does not exist: {root}",
            "Pass an existing profile distribution path.",
        )
    validate_profile.check_required(root, errors)
    validate_profile.check_manifest(root, errors)
    validate_profile.check_json(root, errors)
    validate_profile.check_skills(root, errors)
    validate_profile.check_forbidden_paths(root, errors)
    validate_profile.check_symlinks(root, errors)
    validate_profile.check_secrets(root, errors)
    validate_profile.check_placeholders(root, errors)
    if errors:
        return check_result(
            "profile.validation",
            "Existing profile validation",
            "required",
            "fail",
            "Profile fails the existing hard validator.",
            "Run python3 scripts/validate_profile.py . and fix each error.",
            errors,
        )
    return check_result(
        "profile.validation",
        "Existing profile validation",
        "required",
        "pass",
        "Profile passes the existing hard validator.",
    )


def advisory(
    status: bool,
    check_id: str,
    title: str,
    pass_message: str,
    warn_message: str,
    remediation: str,
) -> dict[str, Any]:
    return check_result(
        check_id,
        title,
        "advisory",
        "pass" if status else "warning",
        pass_message if status else warn_message,
        "" if status else remediation,
    )


def readme_install_check(root: Path) -> dict[str, Any]:
    text = read_text(root / "README.md").lower()
    ok = "hermes profile install" in text
    return advisory(
        ok,
        "readme.install_command",
        "README install command",
        "README includes a Hermes profile install command.",
        "README does not show a Hermes profile install command.",
        "Add a copy-pasteable `hermes profile install ... --alias` command near the top of README.md.",
    )


def readme_quality_gate_check(root: Path) -> dict[str, Any]:
    text = read_text(root / "README.md").lower()
    has_validate = "make validate" in text or "validate_profile.py" in text
    has_smoke = "make smoke" in text or "smoke_install.sh" in text
    details: list[str] = []
    if not has_validate:
        details.append("README does not mention make validate or validate_profile.py")
    if not has_smoke:
        details.append("README does not mention make smoke or smoke_install.sh")
    if has_validate and has_smoke:
        return check_result(
            "readme.quality_gates",
            "README validation and smoke commands",
            "advisory",
            "pass",
            "README documents validation and smoke commands.",
        )
    return check_result(
        "readme.quality_gates",
        "README validation and smoke commands",
        "advisory",
        "warning",
        "README is missing one or more quality gate commands.",
        "Document how maintainers should run validation and smoke checks before publishing.",
        details,
    )


def env_example_check(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    env_requires = manifest.get("env_requires") or []
    if not env_requires:
        return check_result(
            "env.example_docs",
            ".env.EXAMPLE documentation",
            "advisory",
            "pass",
            "No required environment variables are declared.",
        )
    text = read_text(root / ".env.EXAMPLE")
    lines = text.splitlines()
    missing_docs: list[str] = []
    for item in env_requires:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        name = str(item["name"])
        line_index = next((idx for idx, line in enumerate(lines) if line.startswith(f"{name}=")), -1)
        nearby = lines[max(0, line_index - 3) : line_index] if line_index >= 0 else []
        if not any(line.strip().startswith("#") and len(line.strip()) > 1 for line in nearby):
            missing_docs.append(name)
    if not missing_docs:
        return check_result(
            "env.example_docs",
            ".env.EXAMPLE documentation",
            "advisory",
            "pass",
            ".env.EXAMPLE documents declared environment variables.",
        )
    return check_result(
        "env.example_docs",
        ".env.EXAMPLE documentation",
        "advisory",
        "warning",
        ".env.EXAMPLE lists variables without nearby explanatory comments.",
        "Add short comments above each environment variable placeholder.",
        missing_docs,
    )


def metadata_topics_check(root: Path) -> dict[str, Any]:
    data = load_yaml_file(root / "github-repo-metadata.yaml")
    topics = data.get("topics") if isinstance(data, dict) else []
    topic_set = {str(topic).strip() for topic in topics or []}
    missing = sorted(RECOMMENDED_TOPICS - topic_set)
    if not missing:
        return check_result(
            "metadata.github_topics",
            "GitHub metadata topics",
            "advisory",
            "pass",
            "GitHub metadata includes recommended Hermes discovery topics.",
        )
    return check_result(
        "metadata.github_topics",
        "GitHub metadata topics",
        "advisory",
        "warning",
        "GitHub metadata is missing recommended discovery topics.",
        "Add Hermes and profile-distribution topics to github-repo-metadata.yaml.",
        missing,
    )


def license_check(root: Path) -> dict[str, Any]:
    ok = bool(read_text(root / "LICENSE").strip())
    return advisory(
        ok,
        "repo.license",
        "License file",
        "Repository includes a non-empty LICENSE file.",
        "Repository does not include a non-empty LICENSE file.",
        "Add a LICENSE file or document why the generated profile is private-only.",
    )


def changelog_check(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    version = str(manifest.get("version") or "").strip()
    text = read_text(root / "CHANGELOG.md")
    ok = bool(version and re.search(rf"^##\s+\[?{re.escape(version)}\]?\b", text, flags=re.MULTILINE))
    return advisory(
        ok,
        "release.changelog_version",
        "Changelog version heading",
        "CHANGELOG.md includes a heading for the current manifest version.",
        "CHANGELOG.md does not include a heading for the current manifest version.",
        "Add a `## <version>` entry matching distribution.yaml before release.",
    )


def smoke_script_check(root: Path) -> dict[str, Any]:
    ok = (root / "scripts" / "smoke_install.sh").is_file()
    return advisory(
        ok,
        "smoke.install_script",
        "Install smoke script",
        "Repository includes scripts/smoke_install.sh.",
        "Repository does not include scripts/smoke_install.sh.",
        "Add or copy a local smoke script that validates generation and optional Hermes installation.",
    )


def profile_summary(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        "name": str(manifest.get("name") or ""),
        "version": str(manifest.get("version") or ""),
        "description": str(manifest.get("description") or ""),
    }


def build_scorecard(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest = load_yaml_file(root / "distribution.yaml")
    checks = [
        run_existing_validator(root),
        readme_install_check(root),
        readme_quality_gate_check(root),
        env_example_check(root, manifest),
        metadata_topics_check(root),
        license_check(root),
        changelog_check(root, manifest),
        smoke_script_check(root),
    ]
    hard_failures = [check for check in checks if check["severity"] == "required" and check["status"] == "fail"]
    warnings = [check for check in checks if check["status"] == "warning"]
    passes = [check for check in checks if check["status"] == "pass"]
    score = round((len(passes) / len(checks)) * 100) if checks else 0
    return {
        "schema_version": SCHEMA_VERSION,
        "profile": profile_summary(manifest),
        "summary": {
            "status": "fail" if hard_failures else "pass",
            "score": score,
            "total_checks": len(checks),
            "passed": len(passes),
            "warnings": len(warnings),
            "hard_failures": len(hard_failures),
            "hard_failure_details": sum(len(check["details"]) or 1 for check in hard_failures),
        },
        "checks": checks,
    }


def exit_code(scorecard: dict[str, Any]) -> int:
    return 1 if scorecard["summary"]["hard_failures"] else 0


def render_terminal(scorecard: dict[str, Any]) -> str:
    profile = scorecard["profile"]
    summary = scorecard["summary"]
    lines = [
        f"Hermes profile scorecard: {profile.get('name') or '(unknown profile)'}",
        f"Version: {profile.get('version') or '(unknown)'}",
        f"Status: {summary['status'].upper()}",
        f"Score: {summary['score']}/100",
        f"Checks: {summary['passed']} passed, {summary['warnings']} warnings, {summary['hard_failures']} hard failures",
        "",
    ]
    for check in scorecard["checks"]:
        label = {"pass": "PASS", "warning": "WARN", "fail": "FAIL"}[check["status"]]
        lines.append(f"[{label}] {check['title']}: {check['message']}")
        for detail in check["details"]:
            lines.append(f"  - {detail}")
        if check["remediation"]:
            lines.append(f"  Fix: {check['remediation']}")
    return "\n".join(lines)


def render_markdown(scorecard: dict[str, Any]) -> str:
    profile = scorecard["profile"]
    summary = scorecard["summary"]
    lines = [
        "# Hermes Profile Scorecard",
        "",
        f"- Profile: `{profile.get('name') or 'unknown'}`",
        f"- Version: `{profile.get('version') or 'unknown'}`",
        f"- Status: **{summary['status'].upper()}**",
        f"- Score: **{summary['score']}/100**",
        f"- Checks: {summary['passed']} passed, {summary['warnings']} warnings, {summary['hard_failures']} hard failures",
        "",
        "| Status | Severity | Check | Message |",
        "|---|---|---|---|",
    ]
    for check in scorecard["checks"]:
        lines.append(
            f"| {check['status']} | {check['severity']} | {check['title']} | {check['message']} |"
        )
    return "\n".join(lines)


def render_json(scorecard: dict[str, Any]) -> str:
    return json.dumps(scorecard, indent=2, sort_keys=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score publishability of a Hermes profile distribution")
    parser.add_argument("path", nargs="?", default=".", help="Profile repository root")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Emit deterministic JSON")
    output.add_argument("--markdown", action="store_true", help="Emit a Markdown summary")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    scorecard = build_scorecard(Path(args.path))
    if args.json:
        print(render_json(scorecard))
    elif args.markdown:
        print(render_markdown(scorecard))
    else:
        print(render_terminal(scorecard))
    return exit_code(scorecard)


if __name__ == "__main__":
    raise SystemExit(main())
