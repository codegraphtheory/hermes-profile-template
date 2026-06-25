#!/usr/bin/env python3
"""Generate a quality scorecard for Hermes profile distributions."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install -r requirements.txt") from exc


REQUIRED_MANIFEST_FIELDS = ["name", "version", "description"]
CORE_TOPICS = {"hermes-agent", "agent-profile", "profile-distribution"}
RUNTIME_NAMES = {
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
SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]


@dataclass(frozen=True)
class ScoreCheck:
    name: str
    status: str
    points: int
    max_points: int
    detail: str
    remediation: str = ""


@dataclass(frozen=True)
class Scorecard:
    path: str
    score: int
    hard_failures: int
    warnings: int
    checks: list[ScoreCheck]


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return ""


def check(status: str, name: str, detail: str, remediation: str = "", *, points: int = 1) -> ScoreCheck:
    earned = points if status == "pass" else 0
    return ScoreCheck(name, status, earned, points, detail, remediation)


def check_manifest(manifest: dict[str, Any]) -> ScoreCheck:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if not str(manifest.get(field, "")).strip()]
    if missing:
        return check("fail", "manifest-fields", "Missing required manifest fields: " + ", ".join(missing), "Fill required fields in distribution.yaml.")
    return check("pass", "manifest-fields", "distribution.yaml includes required name, version, and description.")


def check_readme_install(root: Path) -> ScoreCheck:
    if "hermes profile install" in safe_read(root / "README.md"):
        return check("pass", "readme-install", "README includes a Hermes install command.")
    return check("warning", "readme-install", "README does not show a Hermes install command.", "Add `hermes profile install ...` to README.md.")


def check_env_docs(root: Path, manifest: dict[str, Any]) -> ScoreCheck:
    env_requires = manifest.get("env_requires") or []
    env_text = safe_read(root / ".env.EXAMPLE")
    missing = []
    for item in env_requires:
        if isinstance(item, dict) and item.get("name") and str(item["name"]) not in env_text:
            missing.append(str(item["name"]))
    if missing:
        return check("fail", "env-example", ".env.EXAMPLE is missing declared env vars: " + ", ".join(missing), "Document all env_requires names in .env.EXAMPLE.")
    if not (root / ".env.EXAMPLE").exists():
        return check("warning", "env-example", ".env.EXAMPLE is missing.", "Add a placeholder-only .env.EXAMPLE file.")
    return check("pass", "env-example", ".env.EXAMPLE documents required environment variable names.")


def check_runtime_and_secrets(root: Path) -> ScoreCheck:
    findings: list[str] = []
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(root)
        if any(part in RUNTIME_NAMES for part in rel.parts):
            findings.append(str(rel))
            continue
        if not path.is_file():
            continue
        text = safe_read(path)
        if text and any(pattern.search(text) for pattern in SECRET_PATTERNS):
            findings.append(str(rel))
    if findings:
        return check("fail", "runtime-and-secrets", "Runtime or secret-like files found: " + ", ".join(findings[:8]), "Remove runtime state and secrets from the distribution.")
    return check("pass", "runtime-and-secrets", "No runtime paths or common secret patterns detected.")


def check_skill_frontmatter(root: Path) -> ScoreCheck:
    skills = list((root / "skills").rglob("SKILL.md")) if (root / "skills").exists() else []
    if not skills:
        return check("warning", "skill-frontmatter", "No bundled skills found.", "Add at least one focused skill when the profile needs custom workflow knowledge.")
    invalid: list[str] = []
    for skill in skills:
        text = safe_read(skill)
        if not text.startswith("---\n") or len(text.split("---", 2)) < 3:
            invalid.append(str(skill.relative_to(root)))
            continue
        try:
            meta = yaml.safe_load(text.split("---", 2)[1]) or {}
        except Exception:
            invalid.append(str(skill.relative_to(root)))
            continue
        if not meta.get("name") or not meta.get("description"):
            invalid.append(str(skill.relative_to(root)))
    if invalid:
        return check("fail", "skill-frontmatter", "Invalid skill frontmatter: " + ", ".join(invalid), "Add YAML frontmatter with name and description.")
    return check("pass", "skill-frontmatter", "Bundled skills have required frontmatter.")


def check_topics(root: Path) -> ScoreCheck:
    metadata = load_yaml(root / "github-repo-metadata.yaml")
    topics = {str(topic).strip().lower() for topic in metadata.get("topics", []) if str(topic).strip()}
    missing = sorted(CORE_TOPICS - topics)
    if missing:
        return check("warning", "github-topics", "GitHub metadata topics are missing: " + ", ".join(missing), "Add Hermes and profile-distribution topics to github-repo-metadata.yaml.")
    return check("pass", "github-topics", "GitHub metadata includes Hermes discovery topics.")


def check_license(root: Path) -> ScoreCheck:
    if (root / "LICENSE").exists():
        return check("pass", "license", "LICENSE is present.")
    return check("warning", "license", "LICENSE is missing.", "Add a license before publishing.")


def check_release_docs(root: Path, manifest: dict[str, Any]) -> ScoreCheck:
    version = str(manifest.get("version") or "").strip()
    changelog = safe_read(root / "CHANGELOG.md")
    if version and re.search(rf"^##\s+\[?{re.escape(version)}\]?\b", changelog, flags=re.MULTILINE):
        return check("pass", "release-changelog", f"CHANGELOG.md includes version {version}.")
    return check("warning", "release-changelog", "CHANGELOG.md does not include the current manifest version.", "Add a matching changelog heading before release.")


def check_install_smoke_docs(root: Path) -> ScoreCheck:
    readme = safe_read(root / "README.md")
    makefile = safe_read(root / "Makefile")
    if "make smoke" in readme or "smoke:" in makefile or "smoke_install.sh" in readme:
        return check("pass", "install-smoke-docs", "Install smoke command is documented or available in Makefile.")
    return check("warning", "install-smoke-docs", "Install smoke command is not documented.", "Document `make smoke` or `scripts/smoke_install.sh`.")


def analyze(root: Path) -> Scorecard:
    root = root.resolve()
    manifest = load_yaml(root / "distribution.yaml")
    checks = [
        check_manifest(manifest),
        check_readme_install(root),
        check_env_docs(root, manifest),
        check_runtime_and_secrets(root),
        check_skill_frontmatter(root),
        check_topics(root),
        check_license(root),
        check_release_docs(root, manifest),
        check_install_smoke_docs(root),
    ]
    earned = sum(item.points for item in checks)
    possible = sum(item.max_points for item in checks) or 1
    failures = sum(1 for item in checks if item.status == "fail")
    warnings = sum(1 for item in checks if item.status == "warning")
    return Scorecard(str(root), round((earned / possible) * 100), failures, warnings, checks)


def to_json(scorecard: Scorecard) -> str:
    data = asdict(scorecard)
    data["checks"] = [asdict(item) for item in scorecard.checks]
    return json.dumps(data, indent=2, sort_keys=True)


def to_markdown(scorecard: Scorecard) -> str:
    lines = [
        "# Hermes Profile Quality Scorecard",
        "",
        f"Score: **{scorecard.score}/100**",
        f"Hard failures: **{scorecard.hard_failures}**",
        f"Warnings: **{scorecard.warnings}**",
        "",
        "| Check | Status | Points | Detail | Remediation |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for item in scorecard.checks:
        lines.append(f"| {item.name} | {item.status} | {item.points}/{item.max_points} | {item.detail} | {item.remediation} |")
    return "\n".join(lines) + "\n"


def to_text(scorecard: Scorecard) -> str:
    lines = [
        f"Hermes profile quality score: {scorecard.score}/100",
        f"Hard failures: {scorecard.hard_failures}",
        f"Warnings: {scorecard.warnings}",
        "",
    ]
    for item in scorecard.checks:
        lines.append(f"[{item.status}] {item.name}: {item.detail}")
        if item.remediation:
            lines.append(f"  remediation: {item.remediation}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Hermes profile quality scorecard")
    parser.add_argument("path", nargs="?", default=".", help="Profile repository path")
    parser.add_argument("--json", action="store_true", help="Print deterministic JSON")
    parser.add_argument("--markdown", action="store_true", help="Print Markdown")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 2
    scorecard = analyze(root)
    if args.json:
        print(to_json(scorecard))
    elif args.markdown:
        print(to_markdown(scorecard), end="")
    else:
        print(to_text(scorecard))
    return 1 if scorecard.hard_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
