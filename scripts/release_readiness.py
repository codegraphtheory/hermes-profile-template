#!/usr/bin/env python3
"""Release readiness checker for Hermes profile distributions.

Emits a Markdown report suitable for release notes or PR comments.
Checks version discipline, changelog, validation, smoke tests,
install command, and secret leakage before tagging a release.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
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

RUNTIME_FILES = {".env", "auth.json", "state.db", "state.db-shm", "state.db-wal",
                 "memories", "sessions", "logs", "workspace", "plans", "local", "cache"}

RELEASE_RELEVANT = {"distribution.yaml", "CHANGELOG.md", "README.md",
                    "requirements.txt", "Makefile", "scripts/", "templates/",
                    "skills/", "config.yaml", "mcp.json"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check release readiness")
    parser.add_argument("--base", default="origin/main",
                        help="Git base ref to compare against (default: origin/main)")
    parser.add_argument("--repo", default=".",
                        help="Path to the repository root (default: .)")
    return parser.parse_args()


def run_git(cmd: list[str], cwd: str) -> tuple[int, str]:
    """Run a git command and return (returncode, stdout)."""
    try:
        result = subprocess.run(["git"] + cmd, capture_output=True, text=True,
                                cwd=cwd, timeout=30)
        return result.returncode, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return -1, str(e)


def check_version_changed(repo_path: str, base: str) -> tuple[bool, str]:
    """Check if distribution.yaml version changed when release-relevant files changed."""
    dist_file = Path(repo_path) / "distribution.yaml"
    if not dist_file.exists():
        return False, "distribution.yaml not found"

    with open(dist_file) as f:
        dist = yaml.safe_load(f) if yaml else {}
    current_version = dist.get("version", "unknown")

    rc, diff = run_git(["diff", "--name-only", base, "--", "."], repo_path)
    if rc != 0:
        return False, f"Git comparison failed: {diff}"

    changed_files = set(diff.splitlines())
    relevant_changed = changed_files & RELEASE_RELEVANT
    if not relevant_changed:
        return True, f"Version {current_version} (no release-relevant files changed)"

    rc2, version_diff = run_git(
        ["diff", base, "--", "distribution.yaml"], repo_path
    )
    if rc2 == 0 and version_diff:
        for line in version_diff.splitlines():
            if line.startswith("+version:"):
                return True, f"Version updated to {current_version} ✓"
        return False, f"Version {current_version} — release-relevant files changed but version not bumped"
    return True, f"Version {current_version} (new file or no prior version)"


def check_changelog(repo_path: str, version: str) -> tuple[bool, str]:
    """Check that CHANGELOG.md has a matching heading for the version."""
    changelog = Path(repo_path) / "CHANGELOG.md"
    if not changelog.exists():
        return False, "CHANGELOG.md not found"

    content = changelog.read_text()
    heading_pattern = re.compile(r"^##\s+\[" + re.escape(version) + r"\]", re.MULTILINE)
    if heading_pattern.search(content):
        return True, f"CHANGELOG entry for [{version}] found ✓"
    # Also try plain heading
    plain = re.compile(r"^##\s+" + re.escape(version), re.MULTILINE)
    if plain.search(content):
        return True, f"CHANGELOG entry for {version} found ✓"
    return False, f"No CHANGELOG entry found for version {version}"


def check_validation(repo_path: str) -> tuple[bool, str]:
    """Run make validate and check result."""
    rc, output = run_git(["rev-parse", "--show-toplevel"], repo_path)
    if rc != 0:
        return False, "Not a git repository"

    try:
        result = subprocess.run(
            ["make", "validate"], capture_output=True, text=True,
            cwd=repo_path, timeout=60
        )
        if result.returncode == 0:
            return True, "make validate passes ✓"
        else:
            lines = result.stdout.splitlines() + result.stderr.splitlines()
            hint = lines[-1][:100] if lines else "unknown error"
            return False, f"make validate failed: {hint}"
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, f"Could not run make validate: {e}"


def check_smoke(repo_path: str) -> tuple[bool, str]:
    """Run make generate-smoke if the target exists."""
    makefile = Path(repo_path) / "Makefile"
    if not makefile.exists():
        return False, "Makefile not found"

    content = makefile.read_text()
    if "generate-smoke" not in content:
        return True, "No generate-smoke target (skipping)"

    try:
        result = subprocess.run(
            ["make", "generate-smoke"], capture_output=True, text=True,
            cwd=repo_path, timeout=120
        )
        if result.returncode == 0:
            return True, "make generate-smoke passes ✓"
        else:
            return False, "make generate-smoke failed (see CI for details)"
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, f"Could not run generate-smoke: {e}"


def check_install_command(repo_path: str) -> tuple[bool, str]:
    """Check that README includes a current install command."""
    readme = Path(repo_path) / "README.md"
    if not readme.exists():
        return False, "README.md not found"

    content = readme.read_text()
    install_patterns = [
        r"hermes\s+profile\s+install",
        r"pip\s+install",
        r"npm\s+install",
        r"brew\s+install",
        r"curl.*install",
    ]
    for pattern in install_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            match = re.search(pattern, content, re.IGNORECASE)
            return True, f"Install command found: '{match.group()}' ✓"

    return False, "No recognized install command found in README.md"


def check_secrets(repo_path: str) -> tuple[bool, str]:
    """Check for runtime files and secrets that should not be committed."""
    findings = []
    for root, dirs, files in os.walk(repo_path):
        rel = Path(root).relative_to(repo_path)
        if str(rel).startswith(".git"):
            continue
        for f in files:
            fp = Path(root) / f
            if f in RUNTIME_FILES:
                findings.append(f"Runtime file present: {rel / f}")
            try:
                if fp.stat().st_size < 1_000_000:
                    text = fp.read_text(errors="replace")
                    for pattern in SECRET_PATTERNS:
                        if pattern.search(text):
                            findings.append(f"Possible secret in {rel / f}: matches {pattern.pattern[:20]}...")
            except Exception:
                pass

    if findings:
        return False, f"Found {len(findings)} issue(s):\n  " + "\n  ".join(findings[:5])
    return True, "No secrets or runtime files detected ✓"


def get_current_version(repo_path: str) -> str:
    """Read the current version from distribution.yaml."""
    dist_file = Path(repo_path) / "distribution.yaml"
    if dist_file.exists():
        try:
            with open(dist_file) as f:
                dist = yaml.safe_load(f) if yaml else {}
            return dist.get("version", "unknown")
        except Exception:
            return "unknown"
    return "unknown"


def main() -> None:
    args = parse_args()
    repo = os.path.abspath(args.repo)
    version = get_current_version(repo)

    checks = [
        ("Version discipline", check_version_changed(repo, args.base)),
        ("CHANGELOG entry", check_changelog(repo, version)),
        ("Validation", check_validation(repo)),
        ("Profile smoke", check_smoke(repo)),
        ("Install command in README", check_install_command(repo)),
        ("Secrets & runtime files", check_secrets(repo)),
    ]

    passed = 0
    failed = 0
    report_lines = [
        f"# Release Readiness Report",
        f"",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Version:** {version}",
        f"**Base ref:** {args.base}",
        f"",
        f"| Check | Status | Detail |",
        f"|-------|--------|--------|",
    ]

    for name, (ok, detail) in checks:
        status = "✅ Pass" if ok else "❌ Fail"
        if ok:
            passed += 1
        else:
            failed += 1
        detail_short = detail.splitlines()[0][:80] if detail else ""
        report_lines.append(f"| {name} | {status} | {detail_short} |")

    report_lines.extend([
        f"",
        f"## Summary",
        f"",
        f"- **Passed:** {passed}/{len(checks)}",
        f"- **Failed:** {failed}/{len(checks)}",
        f"- **Overall:** {'✅ Ready for release' if failed == 0 else '❌ Issues to resolve'}",
        f"",
        f"### Remediation",
    ])

    if failed > 0:
        report_lines.append("")
        for name, (ok, detail) in checks:
            if not ok:
                report_lines.append(f"- **{name}**: {detail}")
    else:
        report_lines.append("All checks pass. The release is ready.")

    report = "\n".join(report_lines)
    print(report)


if __name__ == "__main__":
    main()
