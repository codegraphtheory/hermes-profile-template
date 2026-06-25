#!/usr/bin/env python3
"""Hermes Profile Quality Scorecard.

Evaluates a Hermes profile repository for release and organic discovery readiness,
producing human-readable, JSON, and Markdown outputs.

Score calculation:
- Starts at 100.
- Deducts 15 points for each failed check of severity 'FAIL' (hard failure).
- Deducts 5 points for each failed check of severity 'WARN' (advisory warning).
- Minimum score is 0.

Exit codes:
- 0: All checks passed, or only advisory warnings (WARN) failed.
- 1: One or more critical checks (FAIL) failed.
- 2: CLI error (e.g. invalid path).
"""
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

USER_OWNED = {
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

FORBIDDEN_DIR_NAMES = USER_OWNED | {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    "dist",
    "build",
    "hook-sessions",
}

FORBIDDEN_FILE_NAMES = {
    ".coverage",
    "coverage.xml",
}

FORBIDDEN_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".pyd",
)

REQUIRED_ROOT = ["distribution.yaml", "SOUL.md", "README.md", "AGENTS.md", "config.yaml", ".env.EXAMPLE"]


def get_git_files(root: Path) -> list[Path] | None:
    """Get tracked and unignored files using git ls-files if it is a git repository."""
    if (root / ".git").exists():
        import subprocess
        proc = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=root,
            text=False,
            capture_output=True,
        )
        if proc.returncode == 0:
            rels = [item.decode("utf-8") for item in proc.stdout.split(b"\0") if item]
            return [root / rel for rel in rels]
    return None


def get_all_files(root: Path) -> list[Path]:
    """Get all files recursively from path, excluding hidden dot directories like .git."""
    files = []
    for p in root.rglob("*"):
        if p.is_file():
            # Exclude files inside dot folders (like .git, .pytest_cache)
            if any(part.startswith(".") and part != "." for part in p.relative_to(root).parts[:-1]):
                continue
            files.append(p)
    return files


def check_required_files(root: Path) -> tuple[str, str]:
    missing = [f for f in REQUIRED_ROOT if not (root / f).is_file()]
    if missing:
        return "FAIL", f"Missing required root files: {', '.join(missing)}"
    return "PASS", "All required root files are present."


def check_manifest_fields(root: Path) -> tuple[str, str]:
    manifest_path = root / "distribution.yaml"
    if not manifest_path.is_file():
        return "FAIL", "distribution.yaml is missing."
    if yaml is None:
        return "FAIL", "PyYAML is required but not installed."
    try:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return "FAIL", f"Invalid YAML in distribution.yaml: {exc}"
    if not isinstance(data, dict):
        return "FAIL", "distribution.yaml must be a YAML mapping."
    
    missing_fields = [f for f in ["name", "version", "description"] if not str(data.get(f, "")).strip()]
    if missing_fields:
        return "FAIL", f"distribution.yaml missing required field(s): {', '.join(missing_fields)}"
    
    name = str(data.get("name", ""))
    if name and not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", name):
        return "FAIL", f"distribution.yaml name '{name}' must be lowercase kebab-case."
    
    return "PASS", f"Manifest has valid required fields (name: {name}, version: {data.get('version')})."


def check_env_vars(root: Path) -> tuple[str, str]:
    manifest_path = root / "distribution.yaml"
    if not manifest_path.is_file():
        return "FAIL", "distribution.yaml is missing."
    if yaml is None:
        return "FAIL", "PyYAML is required but not installed."
    try:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return "FAIL", "Invalid distribution.yaml."
    env_requires = data.get("env_requires", [])
    if not env_requires:
        return "PASS", "No environment variables are required by this profile."
    if not isinstance(env_requires, list):
        return "FAIL", "distribution.yaml env_requires must be a list."
    
    env_example_path = root / ".env.EXAMPLE"
    if not env_example_path.is_file():
        return "FAIL", ".env.EXAMPLE file is missing."
    
    try:
        example_content = env_example_path.read_text(encoding="utf-8")
    except Exception as exc:
        return "FAIL", f"Could not read .env.EXAMPLE: {exc}"
        
    missing_vars = []
    for item in env_requires:
        if isinstance(item, dict) and item.get("name"):
            name = item["name"]
            if name not in example_content:
                missing_vars.append(name)
        elif isinstance(item, str):
            if item not in example_content:
                missing_vars.append(item)
                
    if missing_vars:
        return "FAIL", f"Required env vars are missing from .env.EXAMPLE: {', '.join(missing_vars)}"
    
    return "PASS", "All required environment variables are documented in .env.EXAMPLE."


def check_no_runtime_files(root: Path) -> tuple[str, str]:
    forbidden_dirs = FORBIDDEN_DIR_NAMES
    forbidden_files = FORBIDDEN_FILE_NAMES | USER_OWNED
    
    committed_forbidden = []
    seen_dirs = set()
    
    paths = get_git_files(root)
    if paths is None:
        paths = get_all_files(root)
        
    for path in paths:
        if ".git" in path.parts:
            continue
        rel = path.relative_to(root)
        for parent in rel.parents:
            if str(parent) == "." or parent in seen_dirs:
                continue
            seen_dirs.add(parent)
            if parent.name in forbidden_dirs:
                committed_forbidden.append(f"directory '{parent}'")
        if path.name in forbidden_files:
            committed_forbidden.append(f"file '{rel}'")
        if path.name.endswith(FORBIDDEN_SUFFIXES):
            committed_forbidden.append(f"compiled artifact '{rel}'")
            
    if committed_forbidden:
        return "FAIL", f"Committed forbidden runtime or cache paths found: {', '.join(committed_forbidden)}"
    return "PASS", "No runtime, cache, or user-owned files are tracked in the repository."


def check_no_secrets(root: Path) -> tuple[str, str]:
    skip_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__"}
    paths = get_git_files(root)
    if paths is None:
        paths = get_all_files(root)
        
    exposed = []
    for path in paths:
        if not path.is_file() or any(part in skip_dirs for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                exposed.append(str(path.relative_to(root)))
                break
    if exposed:
        return "FAIL", f"Exposed secret patterns found in files: {', '.join(exposed)}"
    return "PASS", "No exposed credentials or secret keys detected."


def check_skill_frontmatter(root: Path) -> tuple[str, str]:
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return "PASS", "No skills directory present."
    
    skill_files = list(skills_dir.rglob("SKILL.md"))
    if not skill_files:
        return "PASS", "No SKILL.md files found."
        
    failures = []
    warnings = []
    
    for skill_md in skill_files:
        rel = skill_md.relative_to(root)
        try:
            text = skill_md.read_text(encoding="utf-8")
        except Exception as exc:
            failures.append(f"Could not read {rel}: {exc}")
            continue
            
        if not text.startswith("---\n"):
            failures.append(f"{rel} missing frontmatter marker '---'")
            continue
            
        parts = text.split("---", 2)
        if len(parts) < 3:
            failures.append(f"{rel} frontmatter not closed")
            continue
            
        if yaml is None:
            failures.append(f"PyYAML is required to parse frontmatter of {rel}")
            continue
            
        try:
            meta = yaml.safe_load(parts[1]) or {}
        except Exception as exc:
            failures.append(f"Invalid YAML in frontmatter of {rel}: {exc}")
            continue
            
        if not isinstance(meta, dict):
            failures.append(f"Frontmatter in {rel} must be a YAML mapping")
            continue
            
        for key in ["name", "description"]:
            if not meta.get(key):
                warnings.append(f"Skill {rel} missing frontmatter field: {key}")
                
    if failures:
        return "FAIL", f"Critical frontmatter errors: {'; '.join(failures)}"
    if warnings:
        return "WARN", f"Advisory frontmatter warnings: {'; '.join(warnings)}"
    return "PASS", "All skills contain valid name and description metadata in frontmatter."


def check_script_compilation(root: Path) -> tuple[str, str]:
    scripts_dir = root / "scripts"
    if not scripts_dir.is_dir():
        return "PASS", "No scripts directory to compile."
    python_files = [p for p in scripts_dir.glob("*.py")]
    if not python_files:
        return "PASS", "No Python scripts found to compile."
    errors = []
    for f in python_files:
        try:
            content = f.read_text(encoding="utf-8")
            compile(content, str(f), "exec")
        except Exception as exc:
            errors.append(f"{f.name}: {exc}")
    if errors:
        return "FAIL", f"Python script compilation errors: {', '.join(errors)}"
    return "PASS", "All python scripts compile successfully."


def check_license_presence(root: Path) -> tuple[str, str]:
    license_files = []
    if root.exists():
        license_files = [f for f in os.listdir(root) if f.upper() in ["LICENSE", "LICENSE.TXT", "LICENSE.MD"] if (root / f).is_file()]
    if license_files:
        return "PASS", f"License file '{license_files[0]}' found."
    
    manifest_path = root / "distribution.yaml"
    if manifest_path.is_file() and yaml is not None:
        try:
            data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
            if str(data.get("license", "")).strip():
                return "PASS", f"License '{data['license']}' specified in distribution.yaml."
        except Exception:
            pass
            
    return "WARN", "No LICENSE file found in repository root."


def check_install_command(root: Path) -> tuple[str, str]:
    readme_path = root / "README.md"
    if not readme_path.is_file():
        return "WARN", "README.md is missing."
    try:
        content = readme_path.read_text(encoding="utf-8")
    except Exception as exc:
        return "WARN", f"Could not read README.md: {exc}"
        
    if re.search(r"hermes\s+profile\s+install", content):
        return "PASS", "Installation command documented in README.md."
    return "WARN", "No 'hermes profile install' command found in README.md."


def check_github_topics(root: Path) -> tuple[str, str]:
    meta_path = root / "github-repo-metadata.yaml"
    if not meta_path.is_file():
        return "WARN", "github-repo-metadata.yaml is missing."
    if yaml is None:
        return "WARN", "PyYAML missing, cannot check github-repo-metadata.yaml."
    try:
        data = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return "WARN", f"Invalid YAML in github-repo-metadata.yaml: {exc}"
        
    if isinstance(data, dict) and data.get("topics") and isinstance(data["topics"], list) and len(data["topics"]) > 0:
        return "PASS", f"GitHub topic recommendations found: {', '.join(data['topics'])}."
        
    return "WARN", "No topic recommendations found in github-repo-metadata.yaml."


def check_changelog_consistency(root: Path) -> tuple[str, str]:
    manifest_path = root / "distribution.yaml"
    if not manifest_path.is_file():
        return "WARN", "distribution.yaml missing."
    if yaml is None:
        return "WARN", "PyYAML missing, cannot check version."
    try:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        version = str(data.get("version", "")).strip()
    except Exception:
        return "WARN", "Could not parse version from distribution.yaml."
        
    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.is_file():
        return "WARN", "CHANGELOG.md is missing."
        
    try:
        content = changelog_path.read_text(encoding="utf-8")
    except Exception as exc:
        return "WARN", f"Could not read CHANGELOG.md: {exc}"
        
    if not version:
        return "WARN", "Version in distribution.yaml is empty."
        
    escaped_version = re.escape(version)
    pattern = rf"(?m)^#+\s+(?:v|\[)?{escaped_version}(?:\])?\b"
    if re.search(pattern, content, re.IGNORECASE):
        return "PASS", f"Changelog contains matching entry for version '{version}'."
        
    return "WARN", f"Changelog is missing an entry for the current version '{version}'."


def check_smoke_command(root: Path) -> tuple[str, str]:
    readme_path = root / "README.md"
    if not readme_path.is_file():
        return "WARN", "README.md is missing."
    try:
        content = readme_path.read_text(encoding="utf-8")
    except Exception as exc:
        return "WARN", f"Could not read README.md: {exc}"
        
    if "make smoke" in content or "smoke_install.sh" in content:
        return "PASS", "Smoke test commands/instructions found in README.md."
        
    return "WARN", "README.md does not document how to run smoke tests ('make smoke' or 'smoke_install.sh')."


def run_scorecard(root: Path) -> dict:
    checks_config = [
        ("required-files", "Required Root Files Presence", "FAIL", check_required_files),
        ("manifest-fields", "Manifest Structure & Mandatory Fields", "FAIL", check_manifest_fields),
        ("env-vars", "Environment Variables in .env.EXAMPLE", "FAIL", check_env_vars),
        ("no-runtime-files", "No Committed Runtime or Cache Files", "FAIL", check_no_runtime_files),
        ("no-secrets", "No Exposed API Keys or Secrets", "FAIL", check_no_secrets),
        ("skill-frontmatter", "Skill Markdown Frontmatter Validity", "FAIL", check_skill_frontmatter),
        ("script-compilation", "Python Script Syntax Verification", "FAIL", check_script_compilation),
        ("license-presence", "License File Presence", "WARN", check_license_presence),
        ("install-command", "Install Command in Documentation", "WARN", check_install_command),
        ("github-topics", "GitHub Topic Metadata Recommendations", "WARN", check_github_topics),
        ("changelog-consistency", "Changelog Version Consistency", "WARN", check_changelog_consistency),
        ("smoke-command", "Smoke Testing Commands in Documentation", "WARN", check_smoke_command),
    ]
    
    score = 100
    failed_count = 0
    warning_count = 0
    passed_count = 0
    checks_results = []
    
    for cid, cname, severity, func in checks_config:
        try:
            status, message = func(root)
        except Exception as exc:
            status, message = "FAIL", f"Internal check runner error: {exc}"
            
        if status == "FAIL":
            failed_count += 1
            if severity == "FAIL":
                score -= 15
            else:
                score -= 5
        elif status == "WARN":
            warning_count += 1
            # A WARN status means it failed an advisory check
            score -= 5
        else:
            passed_count += 1
            
        checks_results.append({
            "id": cid,
            "name": cname,
            "severity": severity,
            "status": status,
            "message": message
        })
        
    score = max(0, score)
    status = "FAIL" if any(r["status"] == "FAIL" and r["severity"] == "FAIL" for r in checks_results) else "PASS"
    
    return {
        "scorecard_version": "1.0",
        "status": status,
        "score": score,
        "passed_count": passed_count,
        "warning_count": warning_count,
        "failed_count": failed_count,
        "checks": checks_results
    }


def print_console(res: dict) -> None:
    # Use color escapes only if outputting to a TTY
    use_color = sys.stdout.isatty()
    
    GREEN = "\033[92m" if use_color else ""
    YELLOW = "\033[93m" if use_color else ""
    RED = "\033[91m" if use_color else ""
    RESET = "\033[0m" if use_color else ""
    BOLD = "\033[1m" if use_color else ""
    
    status_color = GREEN if res["status"] == "PASS" else RED
    
    print("=" * 60)
    print(f"{BOLD}HERMES PROFILE QUALITY SCORECARD{RESET}")
    print("=" * 60)
    print(f"Overall Status : {status_color}{res['status']}{RESET}")
    print(f"Quality Score  : {BOLD}{res['score']}/100{RESET}")
    print(f"Summary        : {GREEN}{res['passed_count']} Passed{RESET}, {YELLOW}{res['warning_count']} Warnings{RESET}, {RED}{res['failed_count']} Failed{RESET}")
    print("-" * 60)
    
    for r in res["checks"]:
        if r["status"] == "PASS":
            status_str = f"{GREEN}PASS{RESET}"
        elif r["status"] == "WARN":
            status_str = f"{YELLOW}WARN{RESET}"
        else:
            status_str = f"{RED}FAIL{RESET}"
            
        # Highlight checks that caused hard failure vs advisory warnings
        severity_label = f" ({r['severity']})" if r["status"] != "PASS" else ""
        print(f"[{status_str}]{severity_label} {r['name']}")
        print(f"      {r['message']}")
    print("=" * 60)


def print_markdown(res: dict) -> None:
    status_emoji = "🟢 PASS" if res["status"] == "PASS" else "🔴 FAIL"
    print("# Hermes Profile Quality Scorecard")
    print()
    print(f"- **Overall Status**: {status_emoji}")
    print(f"- **Quality Score**: `{res['score']}/100`")
    print(f"- **Summary**: 🟢 `{res['passed_count']}` Passed | 🟡 `{res['warning_count']}` Warnings | 🔴 `{res['failed_count']}` Failed")
    print()
    print("## Checklist Details")
    print()
    print("| Status | Severity | Check | Details / Remediation |")
    print("| :--- | :--- | :--- | :--- |")
    for r in res["checks"]:
        if r["status"] == "PASS":
            status_cell = "🟢 PASS"
        elif r["status"] == "WARN":
            status_cell = "🟡 WARN"
        else:
            status_cell = "🔴 FAIL"
        print(f"| {status_cell} | `{r['severity']}` | {r['name']} | {r['message']} |")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a quality scorecard for a Hermes profile")
    parser.add_argument("path", nargs="?", default=".", help="Path to the repository root")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--markdown", action="store_true", help="Output results in Markdown format")
    args = parser.parse_args()
    
    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 2
        
    res = run_scorecard(root)
    
    if args.json:
        print(json.dumps(res, indent=2))
    elif args.markdown:
        print_markdown(res)
    else:
        print_console(res)
        
    # Return 1 if there is a hard failure (overall status FAIL)
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
