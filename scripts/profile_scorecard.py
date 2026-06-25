#!/usr/bin/env python3
"""Compute a quality scorecard for a Hermes profile repository."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]

FORBIDDEN_FILES = {
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a quality scorecard for a Hermes profile repo."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the Hermes profile directory (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output",
        help="Path to write the scorecard report (optional)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        help="Exit with code 1 if the overall score is below this threshold",
    )
    return parser.parse_args()


class Scorecard:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.scores: dict[str, float] = {}
        self.max_scores: dict[str, float] = {}
        self.details: dict[str, list[str]] = {}

    def add_points(self, category: str, points: float, max_points: float, detail: str) -> None:
        self.scores[category] = self.scores.get(category, 0.0) + points
        self.max_scores[category] = self.max_scores.get(category, 0.0) + max_points
        status = "[x]" if points == max_points else "[ ]" if points == 0 else "[-]"
        self.details.setdefault(category, []).append(f"{status} {detail} ({points:.1f}/{max_points:.1f} pts)")

    def run_checks(self) -> None:
        self._check_manifest()
        self._check_documentation()
        self._check_security()
        self._check_config_mcp_skills()

    def _check_manifest(self) -> None:
        category = "Manifest Integrity"
        manifest_path = self.root / "distribution.yaml"

        if not manifest_path.is_file():
            self.add_points(category, 0.0, 30.0, "distribution.yaml exists")
            return

        self.add_points(category, 5.0, 5.0, "distribution.yaml exists")

        if yaml is None:
            self.add_points(category, 0.0, 25.0, "PyYAML loaded (cannot validate content without PyYAML)")
            return

        try:
            data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            self.add_points(category, 0.0, 25.0, f"distribution.yaml is valid YAML: {exc}")
            return

        self.add_points(category, 5.0, 5.0, "distribution.yaml is valid YAML")

        if not isinstance(data, dict):
            self.add_points(category, 0.0, 20.0, "distribution.yaml is a mapping dictionary")
            return

        # Check required fields name, version, description (total 9 points)
        required_fields = ["name", "version", "description"]
        for field in required_fields:
            val = str(data.get(field, "")).strip()
            if val:
                self.add_points(category, 3.0, 3.0, f"distribution.yaml has required field: {field}")
            else:
                self.add_points(category, 0.0, 3.0, f"distribution.yaml has required field: {field}")

        # Check kebab case
        name = str(data.get("name", ""))
        if name and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", name):
            self.add_points(category, 3.0, 3.0, "Name is lowercase kebab-case")
        else:
            self.add_points(category, 0.0, 3.0, "Name is lowercase kebab-case")

        # Check semver version
        version = str(data.get("version", ""))
        semver_pattern = re.compile(
            r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+)?$"
        )
        if version and semver_pattern.match(version):
            self.add_points(category, 4.0, 4.0, "Version matches semantic versioning format")
        else:
            self.add_points(category, 0.0, 4.0, "Version matches semantic versioning format")

        # Check env_requires against .env.EXAMPLE
        env_requires = data.get("env_requires", [])
        env_example_path = self.root / ".env.EXAMPLE"
        if not env_requires:
            self.add_points(category, 4.0, 4.0, "env_requires is empty (no env validation needed)")
        elif not env_example_path.is_file():
            self.add_points(category, 0.0, 4.0, "env_requires declared but .env.EXAMPLE is missing")
        else:
            try:
                example_content = env_example_path.read_text(encoding="utf-8")
                all_match = True
                missing_vars = []
                for item in env_requires:
                    if isinstance(item, dict) and item.get("name"):
                        var_name = item["name"]
                        if var_name not in example_content:
                            all_match = False
                            missing_vars.append(var_name)
                    else:
                        all_match = False
                if all_match:
                    self.add_points(category, 4.0, 4.0, "All env_requires variables documented in .env.EXAMPLE")
                else:
                    self.add_points(
                        category,
                        0.0,
                        4.0,
                        f"Some env_requires variables not in .env.EXAMPLE: {', '.join(missing_vars)}",
                    )
            except Exception as exc:
                self.add_points(category, 0.0, 4.0, f"Failed to check env vars: {exc}")

    def _check_documentation(self) -> None:
        category = "Documentation"
        readme_path = self.root / "README.md"
        soul_path = self.root / "SOUL.md"
        agents_path = self.root / "AGENTS.md"

        # README.md existence
        if readme_path.is_file():
            self.add_points(category, 10.0, 10.0, "README.md exists")
            # Verify installation instructions
            try:
                content = readme_path.read_text(encoding="utf-8")
                # Look for hermes profile install or hermes install
                pattern = re.compile(r"hermes\s+(?:profile\s+)?install", re.IGNORECASE)
                if pattern.search(content):
                    self.add_points(category, 10.0, 10.0, "README.md contains installation instructions")
                else:
                    self.add_points(category, 0.0, 10.0, "README.md contains installation instructions")
            except Exception as exc:
                self.add_points(category, 0.0, 10.0, f"README.md readable: {exc}")
        else:
            self.add_points(category, 0.0, 10.0, "README.md exists")
            self.add_points(category, 0.0, 10.0, "README.md contains installation instructions")

        # SOUL.md existence
        if soul_path.is_file():
            self.add_points(category, 5.0, 5.0, "SOUL.md exists")
        else:
            self.add_points(category, 0.0, 5.0, "SOUL.md exists")

        # AGENTS.md existence
        if agents_path.is_file():
            self.add_points(category, 5.0, 5.0, "AGENTS.md exists")
        else:
            self.add_points(category, 0.0, 5.0, "AGENTS.md exists")

    def _check_security(self) -> None:
        category = "Security & Privacy"

        # Forbidden files check
        found_forbidden = []
        for forbidden in FORBIDDEN_FILES:
            path = self.root / forbidden
            if path.exists():
                found_forbidden.append(forbidden)

        if not found_forbidden:
            self.add_points(category, 10.0, 10.0, "No forbidden/user-owned runtime files committed")
        else:
            self.add_points(
                category,
                0.0,
                10.0,
                f"Forbidden/user-owned runtime files found: {', '.join(found_forbidden)}",
            )

        # Secrets check
        found_secret = False
        secret_file = ""
        skip_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__"}

        for r, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                filepath = Path(r) / file
                if filepath.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar", ".gz"}:
                    continue
                try:
                    text = filepath.read_text(encoding="utf-8")
                    for pattern in SECRET_PATTERNS:
                        if pattern.search(text):
                            found_secret = True
                            secret_file = str(filepath.relative_to(self.root))
                            break
                except (UnicodeDecodeError, PermissionError):
                    continue
                if found_secret:
                    break
            if found_secret:
                break

        if not found_secret:
            self.add_points(category, 10.0, 10.0, "No plain-text credentials or secrets detected")
        else:
            self.add_points(category, 0.0, 10.0, f"Potential secret pattern found in: {secret_file}")

    def _check_config_mcp_skills(self) -> None:
        category = "Configuration & Extendability"

        # config.yaml existence
        config_path = self.root / "config.yaml"
        if config_path.is_file():
            if yaml is None:
                self.add_points(category, 2.5, 5.0, "config.yaml exists (PyYAML not loaded to check format)")
            else:
                try:
                    yaml.safe_load(config_path.read_text(encoding="utf-8"))
                    self.add_points(category, 5.0, 5.0, "config.yaml exists and is valid YAML")
                except Exception as exc:
                    self.add_points(category, 0.0, 5.0, f"config.yaml is valid YAML: {exc}")
        else:
            self.add_points(category, 0.0, 5.0, "config.yaml exists")

        # .env.EXAMPLE existence
        env_example_path = self.root / ".env.EXAMPLE"
        if env_example_path.is_file():
            self.add_points(category, 5.0, 5.0, ".env.EXAMPLE exists")
        else:
            self.add_points(category, 0.0, 5.0, ".env.EXAMPLE exists")

        # mcp.json checks
        mcp_path = self.root / "mcp.json"
        if mcp_path.is_file():
            try:
                json.loads(mcp_path.read_text(encoding="utf-8"))
                self.add_points(category, 5.0, 5.0, "mcp.json is valid JSON")
            except Exception as exc:
                self.add_points(category, 0.0, 5.0, f"mcp.json is valid JSON: {exc}")
        else:
            self.add_points(category, 5.0, 5.0, "mcp.json not present (optional, default full score)")

        # skills check
        skills_dir = self.root / "skills"
        if not skills_dir.is_dir():
            self.add_points(category, 5.0, 5.0, "No custom skills folder (optional, default full score)")
        else:
            skill_mds = list(skills_dir.rglob("SKILL.md"))
            if not skill_mds:
                self.add_points(category, 5.0, 5.0, "skills folder empty (default full score)")
            else:
                invalid_skills = []
                for skill_md in skill_mds:
                    rel_path = skill_md.relative_to(self.root)
                    try:
                        text = skill_md.read_text(encoding="utf-8")
                        if not text.startswith("---\n"):
                            invalid_skills.append(f"{rel_path} (missing frontmatter)")
                            continue
                        parts = text.split("---", 2)
                        if len(parts) < 3:
                            invalid_skills.append(f"{rel_path} (unclosed frontmatter)")
                            continue
                        if yaml is not None:
                            meta = yaml.safe_load(parts[1]) or {}
                            if not meta.get("name") or not meta.get("description"):
                                invalid_skills.append(f"{rel_path} (missing name/description)")
                    except Exception as exc:
                        invalid_skills.append(f"{rel_path} ({exc})")

                if not invalid_skills:
                    self.add_points(category, 5.0, 5.0, "All skills have valid YAML frontmatter metadata")
                else:
                    self.add_points(category, 0.0, 5.0, f"Some invalid skills: {', '.join(invalid_skills)}")

    def get_total_score(self) -> float:
        return sum(self.scores.values())

    def get_max_score(self) -> float:
        return sum(self.max_scores.values())

    def to_json(self) -> str:
        report = {
            "root_path": str(self.root),
            "score": round(self.get_total_score(), 1),
            "max_score": round(self.get_max_score(), 1),
            "percentage": round((self.get_total_score() / self.get_max_score()) * 100, 1) if self.get_max_score() > 0 else 0,
            "categories": {},
        }
        for cat in self.scores.keys():
            report["categories"][cat] = {
                "score": round(self.scores[cat], 1),
                "max_score": round(self.max_scores[cat], 1),
                "details": self.details[cat],
            }
        return json.dumps(report, indent=2)

    def to_markdown(self) -> str:
        total = self.get_total_score()
        max_val = self.get_max_score()
        pct = (total / max_val * 100) if max_val > 0 else 0
        bars = int(pct / 10)
        progress_bar = "█" * bars + "░" * (10 - bars)

        lines = [
            "# Hermes Profile Quality Scorecard",
            "",
            f"**Overall Score: {total:.1f}/{max_val:.1f} ({pct:.1f}%)**",
            f"`[{progress_bar}]`",
            "",
            "## Score by Category",
            "",
            "| Category | Score | Max Score | Percentage | Status |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]

        for cat in self.scores.keys():
            c_tot = self.scores[cat]
            c_max = self.max_scores[cat]
            c_pct = (c_tot / c_max * 100) if c_max > 0 else 0
            status = "Pass" if c_pct >= 80 else "Needs Work"
            lines.append(f"| {cat} | {c_tot:.1f} | {c_max:.1f} | {c_pct:.1f}% | {status} |")

        lines.append("")
        lines.append("## Detailed Checklist")
        lines.append("")

        for cat, items in self.details.items():
            lines.append(f"### {cat} ({self.scores[cat]:.1f}/{self.max_scores[cat]:.1f})")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

        return "\n".join(lines)

    def to_text(self) -> str:
        total = self.get_total_score()
        max_val = self.get_max_score()
        pct = (total / max_val * 100) if max_val > 0 else 0
        bars = int(pct / 10)
        progress_bar = "█" * bars + "░" * (10 - bars)

        lines = [
            "==================================================",
            "        HERMES PROFILE QUALITY SCORECARD          ",
            "==================================================",
            f"Target: {self.root}",
            f"Score:  {total:.1f}/{max_val:.1f} ({pct:.1f}%)",
            f"Progress: [{progress_bar}]",
            "--------------------------------------------------",
        ]

        for cat in self.scores.keys():
            c_tot = self.scores[cat]
            c_max = self.max_scores[cat]
            lines.append(f"{cat:<30} {c_tot:>5.1f} / {c_max:<5.1f}")

        lines.append("--------------------------------------------------")
        lines.append("Details:")
        for cat, items in self.details.items():
            lines.append(f"\n* {cat}:")
            for item in items:
                lines.append(f"  {item}")

        lines.append("==================================================")
        return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root_path = Path(args.path)

    if not root_path.exists():
        print(f"Error: Target path does not exist: {args.path}", file=sys.stderr)
        return 2

    scorecard = Scorecard(root_path)
    scorecard.run_checks()

    # Get formatted report
    if args.format == "json":
        report_content = scorecard.to_json()
    elif args.format == "markdown":
        report_content = scorecard.to_markdown()
    else:
        report_content = scorecard.to_text()

    # Output to stdout
    print(report_content)

    # Save to file if output is specified
    if args.output:
        try:
            out_path = Path(args.output).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(report_content, encoding="utf-8")
            print(f"\n[Scorecard] Saved report to {out_path}", file=sys.stderr)
        except Exception as exc:
            print(f"Error writing report to file {args.output}: {exc}", file=sys.stderr)
            return 3

    # Check threshold
    if args.threshold is not None:
        total = scorecard.get_total_score()
        if total < args.threshold:
            print(
                f"\nError: Score {total:.1f} is below threshold {args.threshold:.1f}",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
