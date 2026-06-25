#!/usr/bin/env python3
"""Profile quality scorecard for Hermes profile distributions.

Produces a quality score with JSON, Markdown, or terminal output.
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

REQUIRED_ROOT = ["distribution.yaml", "SOUL.md", "README.md", "AGENTS.md", "config.yaml", ".env.EXAMPLE"]

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]

FORBIDDEN_NAMES = {".env", "auth.json", "state.db", "memories", "sessions", "logs", "workspace", "cache"}


class Check:
    def __init__(self, name: str, weight: int = 1):
        self.name = name
        self.weight = weight
        self.passed = False
        self.message = ""
        self.skipped = False

    def ok(self, msg: str = "") -> None:
        self.passed = True
        self.message = msg

    def fail(self, msg: str) -> None:
        self.passed = False
        self.message = msg

    def skip(self, msg: str) -> None:
        self.skipped = True
        self.message = msg


def check_required_files(root: Path) -> Check:
    c = Check("required_files", weight=3)
    missing = [f for f in REQUIRED_ROOT if not (root / f).is_file()]
    if missing:
        c.fail(f"Missing: {', '.join(missing)}")
    else:
        c.ok("All required files present")
    return c


def check_manifest(root: Path) -> Check:
    c = Check("manifest_fields", weight=2)
    path = root / "distribution.yaml"
    if not path.exists():
        c.skip("No distribution.yaml")
        return c
    if yaml is None:
        c.skip("PyYAML not installed")
        return c
    data = yaml.safe_load(path.read_text()) or {}
    missing = [k for k in ["name", "version", "description"] if not str(data.get(k, "")).strip()]
    if missing:
        c.fail(f"Missing fields: {', '.join(missing)}")
    else:
        c.ok(f"name={data['name']} v{data['version']}")
    return c


def check_readme_install(root: Path) -> Check:
    c = Check("readme_install", weight=2)
    readme = root / "README.md"
    if not readme.exists():
        c.skip("No README.md")
        return c
    text = readme.read_text(errors="replace").lower()
    install_patterns = ["pip install", "npm install", "cargo install", "install", "clone", "setup"]
    found = [p for p in install_patterns if p in text]
    if found:
        c.ok(f"Install instructions found: {found[0]}")
    else:
        c.fail("No install command found in README")
    return c


def check_env_example(root: Path) -> Check:
    c = Check("env_example", weight=2)
    env_ex = root / ".env.EXAMPLE"
    dist = root / "distribution.yaml"
    if not env_ex.exists():
        c.skip("No .env.EXAMPLE")
        return c
    if not dist.exists() or yaml is None:
        c.ok(".env.EXAMPLE present")
        return c
    data = yaml.safe_load(dist.read_text()) or {}
    env_requires = data.get("env_requires", [])
    example_text = env_ex.read_text(errors="replace")
    missing = [e["name"] for e in env_requires if isinstance(e, dict) and e.get("name") and e["name"] not in example_text]
    if missing:
        c.fail(f"Env vars not documented: {', '.join(missing)}")
    else:
        c.ok(f"All {len(env_requires)} env vars documented")
    return c


def check_no_secrets(root: Path) -> Check:
    c = Check("no_secrets", weight=3)
    found = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv"}
    for path in root.rglob("*"):
        if not path.is_file() or any(part in skip_dirs for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".gif", ".pdf"}:
            continue
        try:
            text = path.read_text(errors="replace")
        except Exception:
            continue
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                found.append(str(path.relative_to(root)))
                break
    if found:
        c.fail(f"Possible secrets in: {', '.join(found[:3])}")
    else:
        c.ok("No secret patterns detected")
    return c


def check_no_runtime_files(root: Path) -> Check:
    c = Check("no_runtime_files", weight=2)
    found = []
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        name = path.name
        if name in FORBIDDEN_NAMES or name.endswith((".pyc", ".pyo")):
            found.append(str(path.relative_to(root)))
    if found:
        c.fail(f"Runtime files committed: {', '.join(found[:3])}")
    else:
        c.ok("No runtime/cache files")
    return c


def check_skills_frontmatter(root: Path) -> Check:
    c = Check("skill_frontmatter", weight=1)
    skills_dir = root / "skills"
    if not skills_dir.exists():
        c.skip("No skills directory")
        return c
    bad = []
    count = 0
    for skill_md in skills_dir.rglob("SKILL.md"):
        count += 1
        text = skill_md.read_text(errors="replace")
        if not text.startswith("---\n"):
            bad.append(str(skill_md.relative_to(root)))
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            bad.append(str(skill_md.relative_to(root)))
            continue
        if yaml is not None:
            meta = yaml.safe_load(parts[1]) or {}
            for key in ["name", "description"]:
                if not meta.get(key):
                    bad.append(f"{skill_md.relative_to(root)}: missing {key}")
    if bad:
        c.fail(f"Skill issues: {'; '.join(bad[:3])}")
    elif count > 0:
        c.ok(f"All {count} skills valid")
    else:
        c.skip("No SKILL.md files")
    return c


def check_license(root: Path) -> Check:
    c = Check("license", weight=1)
    if (root / "LICENSE").is_file():
        c.ok("LICENSE present")
    else:
        c.fail("No LICENSE file")
    return c


def check_changelog(root: Path) -> Check:
    c = Check("changelog", weight=1)
    cl = root / "CHANGELOG.md"
    if not cl.exists():
        c.skip("No CHANGELOG.md")
        return c
    text = cl.read_text(errors="replace")
    if len(text.strip()) > 50:
        c.ok("CHANGELOG has content")
    else:
        c.fail("CHANGELOG appears empty")
    return c


def check_github_topics(root: Path) -> Check:
    c = Check("github_topics", weight=1)
    meta = root / "github-repo-metadata.yaml"
    if not meta.exists():
        c.skip("No github-repo-metadata.yaml")
        return c
    if yaml is None:
        c.skip("PyYAML not installed")
        return c
    data = yaml.safe_load(meta.read_text()) or {}
    topics = data.get("topics", [])
    if len(topics) >= 3:
        c.ok(f"{len(topics)} topics defined")
    else:
        c.fail(f"Only {len(topics)} topics (need 3+)")
    return c


def compute_score(checks: list[Check]) -> float:
    total_weight = sum(c.weight for c in checks if not c.skipped)
    earned = sum(c.weight for c in checks if c.passed and not c.skipped)
    if total_weight == 0:
        return 0.0
    return round(100.0 * earned / total_weight, 1)


def format_terminal(checks: list[Check], score: float) -> str:
    lines = [f"\n{'='*50}", f"  Hermes Profile Quality Scorecard", f"{'='*50}\n"]
    for c in checks:
        icon = "SKIP" if c.skipped else ("PASS" if c.passed else "FAIL")
        lines.append(f"  [{icon}] {c.name} ({c.weight}pt)  {c.message}")
    lines.append(f"\n{'='*50}")
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
    lines.append(f"  SCORE: {score}/100 ({grade})")
    lines.append(f"{'='*50}\n")
    return "\n".join(lines)


def format_markdown(checks: list[Check], score: float) -> str:
    lines = ["## Hermes Profile Quality Scorecard\n", "| Check | Weight | Status | Detail |", "|-------|--------|--------|--------|"]
    for c in checks:
        icon = "SKIP" if c.skipped else ("PASS" if c.passed else "FAIL")
        lines.append(f"| {c.name} | {c.weight} | {icon} | {c.message} |")
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
    lines.append(f"\n**Score: {score}/100 ({grade})**\n")
    return "\n".join(lines)


def format_json(checks: list[Check], score: float) -> str:
    return json.dumps({
        "score": score,
        "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F",
        "checks": [{"name": c.name, "weight": c.weight, "passed": c.passed, "skipped": c.skipped, "message": c.message} for c in checks],
    }, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes profile quality scorecard")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--markdown", action="store_true", help="Output Markdown")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 2
    checks = [
        check_required_files(root),
        check_manifest(root),
        check_readme_install(root),
        check_env_example(root),
        check_no_secrets(root),
        check_no_runtime_files(root),
        check_skills_frontmatter(root),
        check_license(root),
        check_changelog(root),
        check_github_topics(root),
    ]
    score = compute_score(checks)
    if args.json:
        print(format_json(checks, score))
    elif args.markdown:
        print(format_markdown(checks, score))
    else:
        print(format_terminal(checks, score))
    return 0 if score >= 60 else 1


if __name__ == "__main__":
    raise SystemExit(main())
