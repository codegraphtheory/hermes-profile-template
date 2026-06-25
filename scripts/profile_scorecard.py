#!/usr/bin/env python3
"""Profile quality scorecard for Hermes profile distributions.

Produces a quality signal across multiple dimensions. Hard failures cause a
nonzero exit. Advisory warnings are reported but do not affect the exit code.

Usage:
    python3 scripts/profile_scorecard.py [path] [--json] [--markdown]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

PASS = "pass"
WARN = "warn"
FAIL = "fail"


class Check:
    def __init__(self, key: str, label: str, status: str, detail: str = "") -> None:
        self.key = key
        self.label = label
        self.status = status  # pass | warn | fail
        self.detail = detail

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"key": self.key, "label": self.label, "status": self.status}
        if self.detail:
            d["detail"] = self.detail
        return d


class Scorecard:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.checks: list[Check] = []

    def add(self, key: str, label: str, status: str, detail: str = "") -> None:
        self.checks.append(Check(key, label, status, detail))

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == PASS)

    @property
    def warned(self) -> int:
        return sum(1 for c in self.checks if c.status == WARN)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.status == FAIL)

    @property
    def score(self) -> int:
        return self.passed

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def has_failures(self) -> bool:
        return self.failed > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "score": self.score,
            "total": self.total,
            "passed": self.passed,
            "warned": self.warned,
            "failed": self.failed,
            "checks": [c.to_dict() for c in self.checks],
        }


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict[str, Any] | None:
    if yaml is None or not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None


def check_required_files(sc: Scorecard) -> None:
    required = [
        "distribution.yaml", "SOUL.md", "README.md",
        "AGENTS.md", "config.yaml", ".env.EXAMPLE",
    ]
    missing = [f for f in required if not (sc.root / f).is_file()]
    if missing:
        sc.add("required_files", "Required manifest files present",
               FAIL, f"Missing: {', '.join(missing)}")
    else:
        sc.add("required_files", "Required manifest files present", PASS)


def check_manifest_fields(sc: Scorecard) -> None:
    path = sc.root / "distribution.yaml"
    if not path.exists():
        sc.add("manifest_fields", "Manifest required fields populated", FAIL,
               "distribution.yaml not found")
        return
    data = _load_yaml(path) or {}
    missing = [k for k in ("name", "version", "description") if not str(data.get(k, "")).strip()]
    if missing:
        sc.add("manifest_fields", "Manifest required fields populated",
               FAIL, f"Missing fields: {', '.join(missing)}")
    else:
        sc.add("manifest_fields", "Manifest required fields populated", PASS)
    # advisory: author and license
    advisory = [k for k in ("author", "license") if not str(data.get(k, "")).strip()]
    if advisory:
        sc.add("manifest_advisory", "Manifest advisory fields (author, license) populated",
               WARN, f"Not set: {', '.join(advisory)}")
    else:
        sc.add("manifest_advisory", "Manifest advisory fields (author, license) populated", PASS)


def check_readme_install_command(sc: Scorecard) -> None:
    path = sc.root / "README.md"
    if not path.exists():
        sc.add("readme_install", "README includes install command", FAIL, "README.md not found")
        return
    text = path.read_text(encoding="utf-8")
    has_install = "hermes profile install" in text or "hermes install" in text
    if has_install:
        sc.add("readme_install", "README includes install command", PASS)
    else:
        sc.add("readme_install", "README includes install command", WARN,
               "No 'hermes profile install' command found in README.md")


def check_env_example_documented(sc: Scorecard) -> None:
    dist = _load_yaml(sc.root / "distribution.yaml") or {}
    env_requires = dist.get("env_requires") or []
    if not isinstance(env_requires, list) or not env_requires:
        sc.add("env_documented", "Env vars documented in .env.EXAMPLE", PASS,
               "No env_requires declared")
        return
    example_text = ""
    example_path = sc.root / ".env.EXAMPLE"
    if example_path.exists():
        example_text = example_path.read_text(encoding="utf-8")
    missing = []
    for item in env_requires:
        if isinstance(item, dict) and item.get("name"):
            if item["name"] not in example_text:
                missing.append(item["name"])
    if missing:
        sc.add("env_documented", "Env vars documented in .env.EXAMPLE",
               FAIL, f"Undocumented: {', '.join(missing)}")
    else:
        sc.add("env_documented", "Env vars documented in .env.EXAMPLE", PASS)


def check_no_runtime_files(sc: Scorecard) -> None:
    forbidden_dirs = {
        "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        "htmlcov", "dist", "build", "hook-sessions", ".env",
        "auth.json", "state.db", "memories", "sessions", "logs",
        "workspace", "plans", "local", "cache",
    }
    forbidden_suffixes = (".pyc", ".pyo", ".pyd")
    found: list[str] = []
    for path in sc.root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_dir() and path.name in forbidden_dirs:
            found.append(str(path.relative_to(sc.root)))
        elif path.is_file():
            if path.name.endswith(forbidden_suffixes):
                found.append(str(path.relative_to(sc.root)))
    if found:
        sc.add("no_runtime_files", "No runtime or cache artifacts committed",
               FAIL, f"Found: {', '.join(found[:5])}" + (" ..." if len(found) > 5 else ""))
    else:
        sc.add("no_runtime_files", "No runtime or cache artifacts committed", PASS)


def check_skill_frontmatter(sc: Scorecard) -> None:
    skills_dir = sc.root / "skills"
    if not skills_dir.exists():
        sc.add("skill_frontmatter", "Skill YAML frontmatter valid", PASS, "No skills directory")
        return
    invalid: list[str] = []
    for skill_md in skills_dir.rglob("SKILL.md"):
        text = skill_md.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            invalid.append(str(skill_md.relative_to(sc.root)))
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            invalid.append(str(skill_md.relative_to(sc.root)))
            continue
        if yaml is not None:
            try:
                meta = yaml.safe_load(parts[1]) or {}
                for key in ("name", "description"):
                    if not meta.get(key):
                        invalid.append(str(skill_md.relative_to(sc.root)))
                        break
            except Exception:
                invalid.append(str(skill_md.relative_to(sc.root)))
    if invalid:
        sc.add("skill_frontmatter", "Skill YAML frontmatter valid",
               FAIL, f"Invalid: {', '.join(invalid)}")
    else:
        sc.add("skill_frontmatter", "Skill YAML frontmatter valid", PASS)


def check_github_topics(sc: Scorecard) -> None:
    # Check github-repo-metadata.yaml or README for topic recommendations
    metadata_path = sc.root / "github-repo-metadata.yaml"
    if metadata_path.exists():
        data = _load_yaml(metadata_path) or {}
        topics = data.get("topics") or []
        if topics:
            sc.add("github_topics", "GitHub topic recommendations present", PASS,
                   f"{len(topics)} topic(s) defined")
            return
    # Fall back to README check
    readme = sc.root / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        if "topic" in text.lower() or "tag" in text.lower():
            sc.add("github_topics", "GitHub topic recommendations present", WARN,
                   "Topics mentioned in README but no github-repo-metadata.yaml found")
            return
    sc.add("github_topics", "GitHub topic recommendations present", WARN,
           "No github-repo-metadata.yaml with topics found")


def check_license(sc: Scorecard) -> None:
    has_license = (sc.root / "LICENSE").is_file() or (sc.root / "LICENSE.md").is_file()
    dist = _load_yaml(sc.root / "distribution.yaml") or {}
    license_field = str(dist.get("license", "")).strip()
    if has_license and license_field:
        sc.add("license", "LICENSE file and manifest license field present", PASS)
    elif has_license:
        sc.add("license", "LICENSE file and manifest license field present", WARN,
               "LICENSE file found but license not set in distribution.yaml")
    elif license_field:
        sc.add("license", "LICENSE file and manifest license field present", WARN,
               "license set in distribution.yaml but no LICENSE file found")
    else:
        sc.add("license", "LICENSE file and manifest license field present", WARN,
               "No LICENSE file and no license field in distribution.yaml")


def check_changelog(sc: Scorecard) -> None:
    changelog = sc.root / "CHANGELOG.md"
    if not changelog.exists():
        sc.add("changelog", "CHANGELOG.md present and references current version", WARN,
               "CHANGELOG.md not found")
        return
    dist = _load_yaml(sc.root / "distribution.yaml") or {}
    version = str(dist.get("version", "")).strip()
    text = changelog.read_text(encoding="utf-8")
    if version and version in text:
        sc.add("changelog", "CHANGELOG.md present and references current version", PASS)
    elif version:
        sc.add("changelog", "CHANGELOG.md present and references current version", WARN,
               f"CHANGELOG.md does not mention current version {version}")
    else:
        sc.add("changelog", "CHANGELOG.md present and references current version", PASS,
               "CHANGELOG.md present (version not declared)")


def check_smoke_command(sc: Scorecard) -> None:
    readme = sc.root / "README.md"
    makefile = sc.root / "Makefile"
    has_smoke = False
    if makefile.exists() and "smoke" in makefile.read_text(encoding="utf-8"):
        has_smoke = True
    if readme.exists() and "smoke" in readme.read_text(encoding="utf-8").lower():
        has_smoke = True
    if has_smoke:
        sc.add("smoke_command", "Install smoke test command present", PASS)
    else:
        sc.add("smoke_command", "Install smoke test command present", WARN,
               "No smoke target in Makefile or smoke docs in README.md")


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

ICONS = {PASS: "✓", WARN: "⚠", FAIL: "✗"}
COLORS = {PASS: "\033[32m", WARN: "\033[33m", FAIL: "\033[31m"}
RESET = "\033[0m"


def render_terminal(sc: Scorecard, *, color: bool = True) -> str:
    lines: list[str] = []
    lines.append(f"\nHermes Profile Scorecard — {sc.root}")
    lines.append("─" * 60)
    for c in sc.checks:
        icon = ICONS[c.status]
        label = c.label
        detail = f"  → {c.detail}" if c.detail else ""
        if color and sys.stdout.isatty():
            clr = COLORS[c.status]
            lines.append(f"  {clr}{icon}{RESET}  {label}")
        else:
            lines.append(f"  {icon}  {label}")
        if detail:
            lines.append(f"       {detail}")
    lines.append("─" * 60)
    summary = (
        f"Score: {sc.score}/{sc.total}  "
        f"({sc.passed} passed, {sc.warned} warned, {sc.failed} failed)"
    )
    if color and sys.stdout.isatty():
        clr = COLORS[FAIL] if sc.has_failures else (COLORS[WARN] if sc.warned else COLORS[PASS])
        lines.append(f"  {clr}{summary}{RESET}")
    else:
        lines.append(f"  {summary}")
    verdict = "FAIL — hard failures present" if sc.has_failures else "PASS"
    lines.append(f"  Verdict: {verdict}\n")
    return "\n".join(lines)


def render_markdown(sc: Scorecard) -> str:
    lines: list[str] = []
    lines.append(f"## Hermes Profile Scorecard\n")
    lines.append(f"**Score:** {sc.score}/{sc.total} "
                 f"({sc.passed} passed · {sc.warned} warned · {sc.failed} failed)\n")
    lines.append("| Status | Check | Detail |")
    lines.append("|--------|-------|--------|")
    for c in sc.checks:
        icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}[c.status]
        detail = c.detail.replace("|", "\\|") if c.detail else ""
        lines.append(f"| {icon} | {c.label} | {detail} |")
    verdict = "**FAIL** — hard failures present." if sc.has_failures else "**PASS**"
    lines.append(f"\n{verdict}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_scorecard(root: Path) -> Scorecard:
    sc = Scorecard(root)
    check_required_files(sc)
    check_manifest_fields(sc)
    check_readme_install_command(sc)
    check_env_example_documented(sc)
    check_no_runtime_files(sc)
    check_skill_frontmatter(sc)
    check_github_topics(sc)
    check_license(sc)
    check_changelog(sc)
    check_smoke_command(sc)
    return sc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quality scorecard for Hermes profile distributions"
    )
    parser.add_argument("path", nargs="?", default=".",
                        help="Path to profile root (default: current directory)")
    parser.add_argument("--json", action="store_true", dest="json_out",
                        help="Output machine-readable JSON")
    parser.add_argument("--markdown", action="store_true",
                        help="Output Markdown summary (for PR comments or READMEs)")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 2

    sc = run_scorecard(root)

    if args.json_out:
        print(json.dumps(sc.to_dict(), indent=2))
    elif args.markdown:
        print(render_markdown(sc))
    else:
        print(render_terminal(sc))

    return 1 if sc.has_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
