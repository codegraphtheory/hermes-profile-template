#!/usr/bin/env python3
"""Produce a deterministic quality scorecard for a Hermes profile distribution."""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - validate_profile reports this too.
    yaml = None

SCRIPT_DIR = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_profile  # noqa: E402


@dataclass(frozen=True)
class Check:
    id: str
    title: str
    severity: str
    status: str
    details: tuple[str, ...]
    remediation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "status": self.status,
            "details": list(self.details),
            "remediation": self.remediation,
        }


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except UnicodeDecodeError:
        return ""


def load_mapping(path: Path) -> dict[str, Any]:
    if yaml is None or not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def validation_errors(root: Path) -> list[str]:
    errors: list[str] = []
    with contextlib.redirect_stdout(io.StringIO()):
        validate_profile.check_required(root, errors)
        validate_profile.check_manifest(root, errors)
        validate_profile.check_json(root, errors)
        validate_profile.check_skills(root, errors)
        validate_profile.check_forbidden_paths(root, errors)
        validate_profile.check_symlinks(root, errors)
        validate_profile.check_secrets(root, errors)
        validate_profile.check_placeholders(root, errors)
    return errors


def pass_check(check_id: str, title: str, detail: str, remediation: str = "No action needed.") -> Check:
    return Check(check_id, title, "required", "pass", (detail,), remediation)


def fail_check(check_id: str, title: str, details: list[str], remediation: str) -> Check:
    return Check(check_id, title, "required", "fail", tuple(details), remediation)


def warn_check(check_id: str, title: str, details: list[str], remediation: str) -> Check:
    return Check(check_id, title, "advisory", "warn", tuple(details), remediation)


def advisory_pass(check_id: str, title: str, detail: str, remediation: str = "No action needed.") -> Check:
    return Check(check_id, title, "advisory", "pass", (detail,), remediation)


def has_install_command(readme: str) -> bool:
    return bool(re.search(r"hermes\s+profile\s+install\b", readme, re.IGNORECASE))


def has_smoke_command(readme: str) -> bool:
    patterns = [
        r"hermes\s+profile\s+install\s+\.",
        r"make\s+smoke\b",
        r"smoke[_-]install\.sh",
    ]
    return any(re.search(pattern, readme, re.IGNORECASE) for pattern in patterns)


def manifest_topics(manifest: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
    candidates = manifest.get("topics") or manifest.get("github_topics") or metadata.get("topics") or []
    if isinstance(candidates, list):
        return [str(item).strip() for item in candidates if str(item).strip()]
    return []


def build_scorecard(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest = load_mapping(root / "distribution.yaml")
    metadata = load_mapping(root / "github-repo-metadata.yaml")
    readme = read_text(root / "README.md")
    env_example = read_text(root / ".env.EXAMPLE")
    errors = validation_errors(root)

    checks: list[Check] = []
    if errors:
        checks.append(fail_check(
            "validator.required",
            "Existing profile validator passes",
            errors,
            "Run python3 scripts/validate_profile.py . and fix each ERROR line before publishing.",
        ))
    else:
        checks.append(pass_check(
            "validator.required",
            "Existing profile validator passes",
            "scripts/validate_profile.py reported no hard validation errors.",
        ))

    required_fields = ["name", "version", "description"]
    missing_fields = [field for field in required_fields if not str(manifest.get(field, "")).strip()]
    if missing_fields:
        checks.append(fail_check(
            "manifest.required_fields",
            "Required manifest fields are present",
            [f"distribution.yaml is missing: {', '.join(missing_fields)}"],
            "Set name, version, and description in distribution.yaml.",
        ))
    else:
        checks.append(pass_check(
            "manifest.required_fields",
            "Required manifest fields are present",
            "distribution.yaml includes name, version, and description.",
        ))

    required_env = [item for item in manifest.get("env_requires", []) if isinstance(item, dict) and item.get("name")]
    missing_env_docs = [str(item["name"]) for item in required_env if str(item["name"]) not in env_example]
    if missing_env_docs:
        checks.append(fail_check(
            "env.required_docs",
            ".env.EXAMPLE documents declared env vars",
            [f"Declared env var missing from .env.EXAMPLE: {name}" for name in missing_env_docs],
            "Add every env_requires name to .env.EXAMPLE with a placeholder value, not a real secret.",
        ))
    else:
        checks.append(pass_check(
            "env.required_docs",
            ".env.EXAMPLE documents declared env vars",
            "All declared env_requires names appear in .env.EXAMPLE.",
        ))

    if has_install_command(readme):
        checks.append(advisory_pass(
            "readme.install_command",
            "README includes a Hermes install command",
            "README.md contains a hermes profile install command.",
        ))
    else:
        checks.append(warn_check(
            "readme.install_command",
            "README includes a Hermes install command",
            ["README.md does not show a hermes profile install command."],
            "Add a copy-pasteable hermes profile install command near the top of README.md.",
        ))

    if has_smoke_command(readme):
        checks.append(advisory_pass(
            "readme.smoke_command",
            "README includes an install smoke command",
            "README.md includes a local install smoke path.",
        ))
    else:
        checks.append(warn_check(
            "readme.smoke_command",
            "README includes an install smoke command",
            ["README.md does not show how to smoke-test the install."],
            "Document make smoke, scripts/smoke_install.sh, or hermes profile install . --force.",
        ))

    if (root / "LICENSE").is_file() or str(manifest.get("license", "")).strip():
        checks.append(advisory_pass(
            "license.present",
            "License is declared",
            "A LICENSE file or distribution.yaml license value is present.",
        ))
    else:
        checks.append(warn_check(
            "license.present",
            "License is declared",
            ["No LICENSE file or distribution.yaml license value found."],
            "Add a LICENSE file or a license field to distribution.yaml before publication.",
        ))

    topics = manifest_topics(manifest, metadata)
    if topics:
        checks.append(advisory_pass(
            "metadata.topics",
            "GitHub topic recommendations are present",
            f"Found {len(topics)} topic recommendation(s).",
        ))
    else:
        checks.append(warn_check(
            "metadata.topics",
            "GitHub topic recommendations are present",
            ["No topics found in distribution.yaml or github-repo-metadata.yaml."],
            "Add discoverability topics such as hermes-agent, profile-distribution, and the profile domain.",
        ))

    if (root / "CHANGELOG.md").is_file():
        checks.append(advisory_pass(
            "release.changelog",
            "Changelog is present",
            "CHANGELOG.md exists.",
        ))
    else:
        checks.append(warn_check(
            "release.changelog",
            "Changelog is present",
            ["CHANGELOG.md is missing."],
            "Add CHANGELOG.md so release notes have a stable home.",
        ))

    check_dicts = [check.to_dict() for check in sorted(checks, key=lambda item: item.id)]
    hard_failures = sum(1 for check in check_dicts if check["status"] == "fail")
    advisory_warnings = sum(1 for check in check_dicts if check["status"] == "warn")
    passed = sum(1 for check in check_dicts if check["status"] == "pass")
    score = max(0, 100 - hard_failures * 25 - advisory_warnings * 5)

    return {
        "profile": str(root),
        "summary": {
            "score": score,
            "total_checks": len(check_dicts),
            "passed": passed,
            "hard_failures": hard_failures,
            "advisory_warnings": advisory_warnings,
        },
        "checks": check_dicts,
    }


def render_text(scorecard: dict[str, Any]) -> str:
    summary = scorecard["summary"]
    lines = [
        "Hermes profile quality scorecard",
        f"Profile: {scorecard['profile']}",
        f"Score: {summary['score']}/100",
        f"Passed: {summary['passed']} | Hard failures: {summary['hard_failures']} | Advisory warnings: {summary['advisory_warnings']}",
        "",
    ]
    symbol = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}
    for check in scorecard["checks"]:
        lines.append(f"[{symbol[check['status']]}] {check['id']}: {check['title']}")
        for detail in check["details"]:
            lines.append(f"  - {detail}")
        if check["status"] != "pass":
            lines.append(f"  Remediation: {check['remediation']}")
    return "\n".join(lines) + "\n"


def render_markdown(scorecard: dict[str, Any]) -> str:
    summary = scorecard["summary"]
    lines = [
        "## Hermes profile quality scorecard",
        "",
        f"- Score: `{summary['score']}/100`",
        f"- Passed: `{summary['passed']}`",
        f"- Hard failures: `{summary['hard_failures']}`",
        f"- Advisory warnings: `{summary['advisory_warnings']}`",
        "",
        "| Status | Check | Details | Remediation |",
        "| --- | --- | --- | --- |",
    ]
    label = {"pass": "Pass", "warn": "Advisory warning", "fail": "Hard failure"}
    for check in scorecard["checks"]:
        details = "<br>".join(check["details"]).replace("|", "\\|")
        remediation = check["remediation"].replace("|", "\\|")
        lines.append(f"| {label[check['status']]} | `{check['id']}` | {details} | {remediation} |")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Produce a Hermes profile quality scorecard")
    parser.add_argument("path", nargs="?", default=".", help="Profile repository path")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Emit deterministic JSON for CI/tooling")
    output.add_argument("--markdown", action="store_true", help="Emit Markdown suitable for PR comments")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(args.path)
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 2
    scorecard = build_scorecard(root)
    if args.json:
        print(json.dumps(scorecard, indent=2, sort_keys=False))
    elif args.markdown:
        print(render_markdown(scorecard), end="")
    else:
        print(render_text(scorecard), end="")
    return 1 if scorecard["summary"]["hard_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
