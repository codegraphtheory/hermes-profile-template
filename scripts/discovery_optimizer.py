#!/usr/bin/env python3
"""README discovery optimizer for Hermes profile repositories.

Checks a generated profile repo for GitHub discovery readiness:
- Clear one-sentence description
- Install command near the top
- GitHub topic recommendations
- Domain keywords in README headings
- Structured badges or shields
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


class Issue:
    def __init__(self, level: str, check: str, message: str):
        self.level = level  # error, warning, info
        self.check = check
        self.message = message

    def to_dict(self) -> dict:
        return {"level": self.level, "check": self.check, "message": self.message}


def check_description(root: Path) -> list[Issue]:
    issues = []
    readme = root / "README.md"
    if not readme.exists():
        issues.append(Issue("error", "description", "No README.md found"))
        return issues
    text = readme.read_text(errors="replace")
    lines = [l.strip() for l in text.split("\n") if l.strip() and not l.strip().startswith("#")]
    first_line = lines[0] if lines else ""
    if len(first_line) < 20:
        issues.append(Issue("warning", "description", "First non-heading line is very short — add a clear one-sentence description"))
    elif len(first_line) > 200:
        issues.append(Issue("warning", "description", "First description line is very long — keep it under 200 chars"))
    else:
        issues.append(Issue("info", "description", f"Description OK ({len(first_line)} chars)"))
    return issues


def check_install_near_top(root: Path) -> list[Issue]:
    issues = []
    readme = root / "README.md"
    if not readme.exists():
        return issues
    lines = readme.read_text(errors="replace").split("\n")
    install_patterns = ["pip install", "npm install", "cargo install", "git clone", "setup.py", "make install"]
    found_at = None
    for i, line in enumerate(lines[:40], 1):
        lower = line.lower()
        if any(p in lower for p in install_patterns):
            found_at = i
            break
    if found_at:
        issues.append(Issue("info", "install_position", f"Install command found at line {found_at}"))
    else:
        issues.append(Issue("warning", "install_position", "No install command in first 40 lines — add one near the top"))
    return issues


def check_github_topics(root: Path) -> list[Issue]:
    issues = []
    meta = root / "github-repo-metadata.yaml"
    if not meta.exists():
        issues.append(Issue("warning", "topics", "No github-repo-metadata.yaml — add topic recommendations"))
        return issues
    if yaml is None:
        issues.append(Issue("info", "topics", "PyYAML not installed — cannot check topics"))
        return issues
    data = yaml.safe_load(meta.read_text()) or {}
    topics = data.get("topics", [])
    if len(topics) >= 5:
        issues.append(Issue("info", "topics", f"{len(topics)} topics defined — excellent"))
    elif len(topics) >= 3:
        issues.append(Issue("info", "topics", f"{len(topics)} topics defined — consider adding more"))
    else:
        issues.append(Issue("warning", "topics", f"Only {len(topics)} topics — aim for 5+"))
    return issues


def check_keywords_in_headings(root: Path) -> list[Issue]:
    issues = []
    readme = root / "README.md"
    if not readme.exists():
        return issues
    text = readme.read_text(errors="replace").lower()
    headings = re.findall(r"^#+\s+(.+)$", readme.read_text(errors="replace"), re.MULTILINE)
    domain_keywords = ["install", "usage", "getting started", "quickstart", "configuration", "features", "overview"]
    found = [kw for kw in domain_keywords if kw in text]
    missing = [kw for kw in domain_keywords if kw not in text]
    if len(found) >= 4:
        issues.append(Issue("info", "keywords", f"Found {len(found)}/{len(domain_keywords)} domain keywords"))
    else:
        issues.append(Issue("warning", "keywords", f"Only {len(found)}/{len(domain_keywords)} domain keywords — missing: {', '.join(missing[:3])}"))
    return issues


def check_badges(root: Path) -> list[Issue]:
    issues = []
    readme = root / "README.md"
    if not readme.exists():
        return issues
    text = readme.read_text(errors="replace")
    badge_pattern = re.compile(r"!\[.*?\]\(https://img\.shields\.io|!\[.*?\]\(https://github\.com.*?/actions/workflows)")
    badges = badge_pattern.findall(text)
    if len(badges) >= 2:
        issues.append(Issue("info", "badges", f"{len(badges)} badges found"))
    elif len(badges) == 1:
        issues.append(Issue("info", "badges", "1 badge found — consider adding more (CI, version, license)"))
    else:
        issues.append(Issue("warning", "badges", "No badges — add CI status, version, and license badges"))
    return issues


def check_heading_structure(root: Path) -> list[Issue]:
    issues = []
    readme = root / "README.md"
    if not readme.exists():
        return issues
    text = readme.read_text(errors="replace")
    headings = re.findall(r"^(#{1,6})\s+(.+)$", text, re.MULTILINE)
    if not headings:
        issues.append(Issue("warning", "headings", "No headings found in README"))
        return issues
    h1_count = sum(1 for h in headings if len(h[0]) == 1)
    if h1_count == 0:
        issues.append(Issue("warning", "headings", "No H1 heading — add a title"))
    elif h1_count > 1:
        issues.append(Issue("warning", "headings", f"{h1_count} H1 headings — should have exactly 1"))
    else:
        issues.append(Issue("info", "headings", f"Heading structure OK ({len(headings)} headings)"))
    return issues


def format_terminal(issues: list[Issue], score: float) -> str:
    lines = [f"\n{'='*55}", f"  README Discovery Optimizer", f"{'='*55}\n"]
    by_level = {"error": [], "warning": [], "info": []}
    for iss in issues:
        by_level[iss.level].append(iss)
    for level, label in [("error", "ERRORS"), ("warning", "WARNINGS"), ("info", "INFO")]:
        items = by_level[level]
        if items:
            lines.append(f"  {label}:")
            for iss in items:
                lines.append(f"    [{iss.check}] {iss.message}")
            lines.append("")
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
    lines.append(f"{'='*55}")
    lines.append(f"  DISCOVERY SCORE: {score}/100 ({grade})")
    lines.append(f"{'='*55}\n")
    return "\n".join(lines)


def format_json(issues: list[Issue], score: float) -> str:
    return json.dumps({
        "score": score,
        "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F",
        "issues": [i.to_dict() for i in issues],
    }, indent=2)


def format_markdown(issues: list[Issue], score: float) -> str:
    lines = ["## README Discovery Optimizer\n", "| Check | Level | Message |", "|-------|-------|---------|"]
    for iss in issues:
        lines.append(f"| {iss.check} | {iss.level.upper()} | {iss.message} |")
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
    lines.append(f"\n**Discovery Score: {score}/100 ({grade})**\n")
    return "\n".join(lines)


def compute_score(issues: list[Issue]) -> float:
    errors = sum(1 for i in issues if i.level == "error")
    warnings = sum(1 for i in issues if i.level == "warning")
    infos = sum(1 for i in issues if i.level == "info")
    total = errors + warnings + infos
    if total == 0:
        return 100.0
    penalty = errors * 20 + warnings * 10
    return max(0.0, round(100.0 - penalty, 1))


def main() -> int:
    parser = argparse.ArgumentParser(description="README discovery optimizer")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 2
    issues = []
    issues.extend(check_description(root))
    issues.extend(check_install_near_top(root))
    issues.extend(check_github_topics(root))
    issues.extend(check_keywords_in_headings(root))
    issues.extend(check_badges(root))
    issues.extend(check_heading_structure(root))
    score = compute_score(issues)
    if args.json:
        print(format_json(issues, score))
    elif args.markdown:
        print(format_markdown(issues, score))
    else:
        print(format_terminal(issues, score))
    return 0 if score >= 60 else 1


if __name__ == "__main__":
    raise SystemExit(main())
