#!/usr/bin/env python3
"""
Profile quality scorecard for Hermes profile distributions.

Usage:
    python3 scripts/profile_scorecard.py [PROFILE_DIR]
    python3 scripts/profile_scorecard.py --json
    python3 scripts/profile_scorecard.py --markdown
    python3 scripts/profile_scorecard.py --json > scorecard.json

Exit codes:
    0  All hard checks pass (warnings may exist)
    1  One or more hard failures detected
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML is required: pip install pyyaml")

REQUIRED_MANIFEST_FIELDS = ["name", "version", "description", "author", "license"]
RECOMMENDED_TOPICS = ["hermes-agent", "ai-agents", "agent-profile"]

Level = Literal["pass", "warn", "fail"]


@dataclass
class Check:
    name: str
    level: Level
    message: str
    hard: bool = False


@dataclass
class Scorecard:
    profile_dir: Path
    checks: list[Check] = field(default_factory=list)

    def add(self, name: str, passed: bool, message: str, hard: bool = False) -> None:
        if passed:
            self.checks.append(Check(name, "pass", message, hard))
        elif hard:
            self.checks.append(Check(name, "fail", message, hard=True))
        else:
            self.checks.append(Check(name, "warn", message, hard=False))

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.level == "pass")

    @property
    def warnings(self) -> int:
        return sum(1 for c in self.checks if c.level == "warn")

    @property
    def failures(self) -> int:
        return sum(1 for c in self.checks if c.level == "fail")

    @property
    def score(self) -> int:
        total = len(self.checks)
        return round((self.passed / total) * 100) if total else 0

    @property
    def hard_failed(self) -> bool:
        return any(c.level == "fail" and c.hard for c in self.checks)


def run_checks(profile_dir: Path) -> Scorecard:
    sc = Scorecard(profile_dir=profile_dir)

    # ── 1. distribution.yaml manifest ────────────────────────────────────────
    dist_file = profile_dir / "distribution.yaml"
    if not dist_file.exists():
        sc.add("manifest-exists", False, "distribution.yaml not found", hard=True)
        return sc

    sc.add("manifest-exists", True, "distribution.yaml found")

    try:
        dist = yaml.safe_load(dist_file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        sc.add("manifest-parseable", False, f"distribution.yaml parse error: {e}", hard=True)
        return sc

    sc.add("manifest-parseable", True, "distribution.yaml is valid YAML")

    for f in REQUIRED_MANIFEST_FIELDS:
        present = bool(dist.get(f, ""))
        sc.add(f"manifest-field-{f}", present,
               f"manifest field '{f}' present" if present else f"manifest missing field '{f}'",
               hard=(f in ("name", "version", "description")))

    # ── 2. README ────────────────────────────────────────────────────────────
    readme = profile_dir / "README.md"
    sc.add("readme-exists", readme.exists(), "README.md found", hard=True)

    if readme.exists():
        readme_text = readme.read_text(encoding="utf-8", errors="replace")
        has_install = "hermes profile install" in readme_text or "pip install" in readme_text
        sc.add("readme-install-command", has_install,
               "README contains install command" if has_install
               else "README missing install command")
        sc.add("readme-non-empty", len(readme_text.strip()) > 100,
               "README has content", hard=True)

    # ── 3. .env.EXAMPLE ──────────────────────────────────────────────────────
    env_example = profile_dir / ".env.EXAMPLE"
    env_requires = dist.get("env_requires", [])
    if env_requires:
        sc.add("env-example-exists", env_example.exists(),
               ".env.EXAMPLE present to document required env vars")
        if env_example.exists():
            env_text = env_example.read_text(encoding="utf-8", errors="replace")
            for req in env_requires:
                name = req.get("name", "") if isinstance(req, dict) else str(req)
                documented = name in env_text
                sc.add(f"env-documented-{name}", documented,
                       f"{name} documented in .env.EXAMPLE" if documented
                       else f"{name} missing from .env.EXAMPLE")
    else:
        sc.add("env-example-optional", True, "No env_requires declared")

    # ── 4. No runtime / secret files ─────────────────────────────────────────
    bad_patterns = [".env", "auth.json", "state.db", "*.pyc", "__pycache__"]
    runtime_files = []
    for pattern in [".env", "auth.json", "state.db"]:
        if (profile_dir / pattern).exists():
            runtime_files.append(pattern)
    sc.add("no-runtime-files", len(runtime_files) == 0,
           "No runtime/secret files found" if not runtime_files
           else f"Runtime files present: {', '.join(runtime_files)}",
           hard=True)

    # ── 5. Skill frontmatter validity ────────────────────────────────────────
    skills_dir = profile_dir / "skills"
    if skills_dir.exists():
        skill_files = list(skills_dir.glob("**/*.md"))
        bad_skills = []
        for sf in skill_files:
            text = sf.read_text(encoding="utf-8", errors="replace")
            if not text.startswith("---"):
                bad_skills.append(sf.name)
        sc.add("skill-frontmatter", len(bad_skills) == 0,
               f"{len(skill_files)} skill(s) have valid frontmatter" if not bad_skills
               else f"Skills missing frontmatter: {', '.join(bad_skills)}")
    else:
        sc.add("skills-dir", False, "skills/ directory not found")

    # ── 6. GitHub topics ─────────────────────────────────────────────────────
    meta_file = profile_dir / "github-repo-metadata.yaml"
    if meta_file.exists():
        try:
            meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
            topics = meta.get("topics", [])
            has_topics = any(t in topics for t in RECOMMENDED_TOPICS)
            sc.add("github-topics", has_topics,
                   f"GitHub topics include recommended tags ({', '.join(t for t in RECOMMENDED_TOPICS if t in topics)})"
                   if has_topics else
                   f"None of the recommended GitHub topics present: {RECOMMENDED_TOPICS}")
        except yaml.YAMLError:
            sc.add("github-topics", False, "github-repo-metadata.yaml parse error")
    else:
        sc.add("github-topics", False,
               "github-repo-metadata.yaml not found — add GitHub topics for discoverability")

    # ── 7. License ───────────────────────────────────────────────────────────
    license_file = next(profile_dir.glob("LICENSE*"), None)
    sc.add("license-file", license_file is not None,
           "LICENSE file present" if license_file else "No LICENSE file found", hard=True)

    # ── 8. CHANGELOG ─────────────────────────────────────────────────────────
    changelog = profile_dir / "CHANGELOG.md"
    sc.add("changelog-exists", changelog.exists(),
           "CHANGELOG.md present" if changelog.exists() else "CHANGELOG.md missing")

    if changelog.exists() and dist.get("version"):
        version = str(dist["version"])
        has_version = version in changelog.read_text(encoding="utf-8", errors="replace")
        sc.add("changelog-version-match", has_version,
               f"CHANGELOG mentions current version {version}" if has_version
               else f"CHANGELOG does not mention version {version}")

    # ── 9. Install smoke command ──────────────────────────────────────────────
    makefile = profile_dir / "Makefile"
    if makefile.exists():
        mk = makefile.read_text(encoding="utf-8", errors="replace")
        has_smoke = "smoke" in mk
        sc.add("makefile-smoke", has_smoke,
               "Makefile has 'smoke' target" if has_smoke
               else "Makefile missing 'smoke' target — add install smoke test")
    else:
        sc.add("makefile-exists", False, "Makefile not found")

    return sc


# ── output formatters ────────────────────────────────────────────────────────

def fmt_terminal(sc: Scorecard) -> str:
    ICONS = {"pass": "✅", "warn": "⚠️ ", "fail": "❌"}
    lines = [
        f"\nProfile Scorecard — {sc.profile_dir.resolve().name}",
        "=" * 52,
    ]
    for c in sc.checks:
        lines.append(f"  {ICONS[c.level]}  {c.message}")
    lines += [
        "=" * 52,
        f"  Score   : {sc.score}/100",
        f"  Passed  : {sc.passed}",
        f"  Warnings: {sc.warnings}",
        f"  Failures: {sc.failures}",
        "",
    ]
    return "\n".join(lines)


def fmt_json(sc: Scorecard) -> str:
    data = {
        "profile": str(sc.profile_dir.resolve()),
        "score": sc.score,
        "passed": sc.passed,
        "warnings": sc.warnings,
        "failures": sc.failures,
        "hard_failed": sc.hard_failed,
        "checks": [
            {"name": c.name, "level": c.level, "message": c.message, "hard": c.hard}
            for c in sc.checks
        ],
    }
    return json.dumps(data, indent=2, sort_keys=False)


def fmt_markdown(sc: Scorecard) -> str:
    ICONS = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
    rows = "\n".join(
        f"| {ICONS[c.level]} | `{c.name}` | {c.message} |"
        for c in sc.checks
    )
    return f"""## Profile Quality Scorecard

**Score: {sc.score}/100** — {sc.passed} passed · {sc.warnings} warnings · {sc.failures} failures

| Status | Check | Detail |
|--------|-------|--------|
{rows}

_Generated by `scripts/profile_scorecard.py`_
"""


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score the quality of a Hermes profile distribution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("profile_dir", nargs="?", default=".",
                        help="Path to the profile distribution root (default: .)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--markdown", action="store_true", help="Output Markdown summary")
    args = parser.parse_args()

    profile_dir = Path(args.profile_dir)
    if not profile_dir.exists():
        print(f"Error: {profile_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    sc = run_checks(profile_dir)

    if args.json:
        print(fmt_json(sc))
    elif args.markdown:
        print(fmt_markdown(sc))
    else:
        print(fmt_terminal(sc))

    sys.exit(1 if sc.hard_failed else 0)


if __name__ == "__main__":
    main()
