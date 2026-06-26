#!/usr/bin/env python3
"""
README discovery optimizer for Hermes profile distributions.

Reviews a generated profile repo for discovery-readiness — descriptions,
install commands, GitHub topics, template lineage, and more — and reports
actionable recommendations without overwriting user content by default.

Usage:
    python3 scripts/readme_discovery_optimizer.py [PROFILE_DIR]
    python3 scripts/readme_discovery_optimizer.py --json
    python3 scripts/readme_discovery_optimizer.py --markdown
    python3 scripts/readme_discovery_optimizer.py --fix     # safe mechanical patches only

Exit codes:
    0  All checks pass (warnings may exist)
    1  One or more required recommendations remain unaddressed
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML is required: pip install pyyaml")

RECOMMENDED_TOPICS = ["hermes-agent", "ai-agents", "agent-profile"]
INSTALL_PATTERNS = [
    r"hermes profile install",
    r"hermes install",
]
TEMPLATE_LINEAGE_PATTERNS = [
    r"hermes-profile-template",
    r"codegraphtheory/hermes-profile-template",
    r"generated.{0,30}template",
    r"template.{0,30}generated",
]
VALIDATION_PATTERNS = [
    r"make validate",
    r"validate_profile\.py",
    r"python3? scripts/validate",
]
SMOKE_PATTERNS = [
    r"make smoke",
    r"smoke_install\.sh",
]

Level = Literal["pass", "warn", "required"]


@dataclass
class Finding:
    name: str
    level: Level
    message: str
    fix_hint: str = ""


@dataclass
class Report:
    profile_dir: Path
    findings: list[Finding] = field(default_factory=list)

    def add(self, name: str, passed: bool, message: str,
            required: bool = False, fix_hint: str = "") -> None:
        if passed:
            self.findings.append(Finding(name, "pass", message))
        elif required:
            self.findings.append(Finding(name, "required", message, fix_hint))
        else:
            self.findings.append(Finding(name, "warn", message, fix_hint))

    @property
    def passes(self) -> int:
        return sum(1 for f in self.findings if f.level == "pass")

    @property
    def warnings(self) -> int:
        return sum(1 for f in self.findings if f.level == "warn")

    @property
    def required_failures(self) -> int:
        return sum(1 for f in self.findings if f.level == "required")

    @property
    def has_required_failures(self) -> bool:
        return self.required_failures > 0


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _first_n_lines(text: str, n: int) -> str:
    return "\n".join(text.splitlines()[:n])


def run_checks(profile_dir: Path) -> Report:
    rpt = Report(profile_dir=profile_dir)

    # ── README exists ─────────────────────────────────────────────────────────
    readme_path = profile_dir / "README.md"
    if not readme_path.exists():
        rpt.add("readme-exists", False, "README.md not found",
                required=True, fix_hint="Create README.md with a one-sentence description and install command.")
        return rpt

    rpt.add("readme-exists", True, "README.md found")
    readme = readme_path.read_text(encoding="utf-8", errors="replace")
    readme_top = _first_n_lines(readme, 60)

    # ── Clear one-sentence description ───────────────────────────────────────
    non_empty = [ln.strip() for ln in readme.splitlines()
                 if ln.strip() and not ln.strip().startswith("#")]
    first_prose = non_empty[0] if non_empty else ""
    is_short_sentence = (
        len(first_prose) >= 15
        and len(first_prose) <= 280
        and first_prose.count(".") <= 3
    )
    rpt.add(
        "readme-description",
        is_short_sentence,
        "README opens with a clear one-sentence description"
        if is_short_sentence
        else "README is missing a clear one-sentence description near the top",
        fix_hint="Add a short paragraph (≤ 1–2 sentences) right after the title heading.",
    )

    # ── Install command near the top ─────────────────────────────────────────
    install_in_top = _matches_any(readme_top, INSTALL_PATTERNS)
    rpt.add(
        "install-command-near-top",
        install_in_top,
        "Install command appears near the top of README"
        if install_in_top
        else "Install command not found in the first 60 lines",
        required=True,
        fix_hint=(
            "Add a code block near the top:\n"
            "```bash\n"
            "hermes profile install github.com/YOUR_ORG/YOUR_REPO\n"
            "```"
        ),
    )

    # ── GitHub topics ─────────────────────────────────────────────────────────
    meta_path = profile_dir / "github-repo-metadata.yaml"
    if meta_path.exists():
        try:
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
            topics = meta.get("topics", [])
            missing = [t for t in RECOMMENDED_TOPICS if t not in topics]
            rpt.add(
                "github-topics",
                not missing,
                f"GitHub topics include recommended tags: {', '.join(RECOMMENDED_TOPICS)}"
                if not missing
                else f"github-repo-metadata.yaml is missing recommended topics: {', '.join(missing)}",
                fix_hint=f"Add to topics list: {', '.join(missing)}",
            )
        except yaml.YAMLError as exc:
            rpt.add("github-topics", False,
                    f"github-repo-metadata.yaml parse error: {exc}",
                    fix_hint="Fix YAML syntax in github-repo-metadata.yaml.")
    else:
        rpt.add(
            "github-topics",
            False,
            "github-repo-metadata.yaml not found — GitHub topics will not be set on publish",
            fix_hint=(
                "Create github-repo-metadata.yaml with:\n"
                "topics:\n"
                "  - hermes-agent\n"
                "  - ai-agents\n"
                "  - agent-profile"
            ),
        )

    # ── Domain keywords in headings ───────────────────────────────────────────
    dist_path = profile_dir / "distribution.yaml"
    if dist_path.exists():
        try:
            dist = yaml.safe_load(dist_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            dist = {}
        description = str(dist.get("description", ""))
        stop_words = {"a", "an", "the", "and", "or", "for", "to", "in", "of",
                      "on", "at", "is", "are", "with", "that", "this", "from"}
        keywords = [
            w.lower() for w in re.split(r"\W+", description)
            if len(w) > 3 and w.lower() not in stop_words
        ]
        headings = " ".join(
            ln for ln in readme.splitlines() if ln.startswith("#")
        ).lower()
        matched = [kw for kw in keywords if kw in headings]
        coverage = len(matched) / len(keywords) if keywords else 1.0
        rpt.add(
            "domain-keywords-in-headings",
            coverage >= 0.25,
            f"README headings reflect domain ({', '.join(matched[:4])})"
            if coverage >= 0.25
            else "README headings don't reflect the profile domain (consider adding a relevant ## section)",
            fix_hint=(
                f"Add headings that mention keywords from the description: "
                f"{', '.join(keywords[:5])}"
            ),
        )
    else:
        rpt.add("domain-keywords-in-headings", False,
                "distribution.yaml not found — cannot check domain keywords",
                required=True,
                fix_hint="Create distribution.yaml with name, version, description, author, license.")

    # ── Template lineage ──────────────────────────────────────────────────────
    lineage_present = _matches_any(readme, TEMPLATE_LINEAGE_PATTERNS)
    rpt.add(
        "template-lineage",
        lineage_present,
        "README acknowledges source template lineage"
        if lineage_present
        else "README doesn't mention the source template (hermes-profile-template)",
        fix_hint=(
            "Add a line such as:\n"
            "> Generated from [hermes-profile-template]"
            "(https://github.com/codegraphtheory/hermes-profile-template)"
        ),
    )

    # ── Validation and smoke commands ─────────────────────────────────────────
    has_validate = _matches_any(readme, VALIDATION_PATTERNS)
    rpt.add(
        "validation-command",
        has_validate,
        "README shows how to run validation"
        if has_validate
        else "README doesn't show a validation command",
        fix_hint="Add `make validate` or `python3 scripts/validate_profile.py .` to your README.",
    )

    has_smoke = _matches_any(readme, SMOKE_PATTERNS)
    rpt.add(
        "smoke-command",
        has_smoke,
        "README shows how to run smoke test"
        if has_smoke
        else "README doesn't show a smoke test command",
        fix_hint="Add `make smoke` to your README install verification steps.",
    )

    # ── License docs ──────────────────────────────────────────────────────────
    license_file = next(profile_dir.glob("LICENSE*"), None)
    rpt.add(
        "license-file",
        license_file is not None,
        "LICENSE file present"
        if license_file
        else "No LICENSE file found",
        required=True,
        fix_hint="Add a LICENSE file (e.g. MIT). GitHub surfaces this on the repo sidebar.",
    )

    # ── Security docs ─────────────────────────────────────────────────────────
    security_file = profile_dir / "SECURITY.md"
    rpt.add(
        "security-docs",
        security_file.exists(),
        "SECURITY.md present"
        if security_file.exists()
        else "SECURITY.md not found — GitHub uses this to route vulnerability reports",
        fix_hint="Create SECURITY.md describing how to report security issues.",
    )

    # ── Social share / one-liner snippet ─────────────────────────────────────
    share_patterns = [
        r"badge",
        r"shields\.io",
        r"!\[",
        r"one.{0,20}liner",
        r"quick.{0,20}start",
        r"tldr",
        r"in.one.{0,10}line",
    ]
    has_share = _matches_any(readme, share_patterns)
    rpt.add(
        "social-preview",
        has_share,
        "README has a badge or quick-start snippet for social sharing"
        if has_share
        else "README lacks a shareable one-liner or badge (add a version or CI badge)",
        fix_hint=(
            "Add a badge or a ≤ 2-line quick-start block near the top so previews "
            "render cleanly when the repo is shared on social media."
        ),
    )

    return rpt


# ── --fix: safe mechanical patches ───────────────────────────────────────────

def apply_fix(profile_dir: Path, rpt: Report) -> list[str]:
    """Apply safe mechanical fixes. Returns list of actions taken."""
    actions: list[str] = []

    readme_path = profile_dir / "README.md"
    if not readme_path.exists():
        return actions

    readme = readme_path.read_text(encoding="utf-8", errors="replace")

    # Fix 1: append missing topics to github-repo-metadata.yaml
    meta_path = profile_dir / "github-repo-metadata.yaml"
    if meta_path.exists():
        try:
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
            topics: list[str] = meta.get("topics", [])
            missing = [t for t in RECOMMENDED_TOPICS if t not in topics]
            if missing:
                meta["topics"] = topics + missing
                meta_path.write_text(
                    yaml.dump(meta, default_flow_style=False, sort_keys=False),
                    encoding="utf-8",
                )
                actions.append(
                    f"Added missing topics to github-repo-metadata.yaml: {', '.join(missing)}"
                )
        except (yaml.YAMLError, OSError):
            pass

    # Fix 2: append lineage footer if missing
    lineage_present = _matches_any(readme, TEMPLATE_LINEAGE_PATTERNS)
    if not lineage_present:
        footer = (
            "\n\n---\n\n"
            "_Generated from [hermes-profile-template]"
            "(https://github.com/codegraphtheory/hermes-profile-template)_\n"
        )
        readme_path.write_text(readme + footer, encoding="utf-8")
        readme = readme_path.read_text(encoding="utf-8", errors="replace")
        actions.append("Appended template lineage footer to README.md")

    return actions


# ── output formatters ─────────────────────────────────────────────────────────

def fmt_terminal(rpt: Report) -> str:
    ICONS = {"pass": "✅", "warn": "⚠️ ", "required": "❌"}
    lines = [
        f"\nREADME Discovery Report — {rpt.profile_dir.resolve().name}",
        "=" * 56,
    ]
    for f in rpt.findings:
        lines.append(f"  {ICONS[f.level]}  {f.message}")
        if f.level != "pass" and f.fix_hint:
            for hint_line in f.fix_hint.splitlines():
                lines.append(f"       {hint_line}")
    lines += [
        "=" * 56,
        f"  Passed   : {rpt.passes}",
        f"  Warnings : {rpt.warnings}",
        f"  Required : {rpt.required_failures}",
        "",
    ]
    if rpt.has_required_failures:
        lines.append("  Run with --fix to apply safe mechanical patches.\n")
    else:
        lines.append("  Discovery checks passed. Run --fix to apply optional enhancements.\n")
    return "\n".join(lines)


def fmt_json(rpt: Report) -> str:
    return json.dumps(
        {
            "profile": str(rpt.profile_dir.resolve()),
            "passes": rpt.passes,
            "warnings": rpt.warnings,
            "required_failures": rpt.required_failures,
            "has_required_failures": rpt.has_required_failures,
            "findings": [
                {
                    "name": f.name,
                    "level": f.level,
                    "message": f.message,
                    "fix_hint": f.fix_hint,
                }
                for f in rpt.findings
            ],
        },
        indent=2,
        sort_keys=False,
    )


def fmt_markdown(rpt: Report) -> str:
    ICONS = {"pass": "✅", "warn": "⚠️", "required": "❌"}
    rows = "\n".join(
        f"| {ICONS[f.level]} | `{f.name}` | {f.message} |"
        for f in rpt.findings
    )
    return f"""## README Discovery Report

**{rpt.passes} passed · {rpt.warnings} warnings · {rpt.required_failures} required**

| Status | Check | Detail |
|--------|-------|--------|
{rows}

_Generated by `scripts/readme_discovery_optimizer.py`_
"""


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check README discovery readiness for a Hermes profile distribution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("profile_dir", nargs="?", default=".",
                        help="Path to profile distribution root (default: .)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--markdown", action="store_true", help="Output Markdown")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply safe mechanical fixes (topic additions, lineage footer) without overwriting prose",
    )
    args = parser.parse_args()

    profile_dir = Path(args.profile_dir)
    if not profile_dir.exists():
        print(f"Error: {profile_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    if args.fix:
        rpt_before = run_checks(profile_dir)
        actions = apply_fix(profile_dir, rpt_before)
        if actions:
            print("Applied fixes:")
            for a in actions:
                print(f"  • {a}")
        else:
            print("Nothing to fix — all mechanical patches already in place.")
        rpt = run_checks(profile_dir)
    else:
        rpt = run_checks(profile_dir)

    if args.json:
        print(fmt_json(rpt))
    elif args.markdown:
        print(fmt_markdown(rpt))
    else:
        print(fmt_terminal(rpt))

    sys.exit(1 if rpt.has_required_failures else 0)


if __name__ == "__main__":
    main()
