#!/usr/bin/env python3
"""Generate a Markdown release readiness report for a Hermes profile distribution."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    from check_release_version import (
        changed_files,
        changelog_has_version,
        is_release_relevant,
        read_base_version,
        read_current_version,
    )
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"Could not import release helpers: {exc}") from exc


@dataclass
class Check:
    name: str
    status: str
    detail: str
    remediation: str = ""


def run(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=root, text=True, capture_output=True)


def summarize_output(proc: subprocess.CompletedProcess[str]) -> str:
    output = "\n".join(part.strip() for part in [proc.stdout, proc.stderr] if part.strip())
    if not output:
        return "Command completed successfully."
    lines = output.splitlines()
    if len(lines) > 4:
        lines = [*lines[:3], f"... {len(output.splitlines()) - 3} more lines"]
    return " ".join(line.strip() for line in lines if line.strip())


def check_release_version(root: Path, base: str, *, strict: bool) -> Check:
    files = changed_files(root, base)
    if files is None:
        status = "fail" if strict else "skip"
        return Check(
            "release-version",
            status,
            f"Could not compare against base ref `{base}`.",
            "Fetch the base ref or pass --base with an available ref.",
        )
    for diff_args in (["diff", "--name-only"], ["diff", "--name-only", "--cached"]):
        proc = run(["git", *diff_args], root)
        if proc.returncode == 0:
            files.extend(line.strip() for line in proc.stdout.splitlines() if line.strip())
    files = sorted(set(files))
    relevant = [path for path in files if is_release_relevant(path)]
    if not relevant:
        return Check("release-version", "pass", "No release-relevant changes detected.")

    current = read_current_version(root)
    base_version = read_base_version(root, base)
    if base_version is None:
        status = "fail" if strict else "skip"
        return Check(
            "release-version",
            status,
            f"Could not read `distribution.yaml` from `{base}`.",
            "Fetch the base ref or pass --base with an available ref.",
        )
    if current == base_version:
        return Check(
            "release-version",
            "fail",
            f"Release-relevant files changed but version stayed `{current}`.",
            "Bump `distribution.yaml` version.",
        )
    if not changelog_has_version(root, current):
        return Check(
            "release-version",
            "fail",
            f"`CHANGELOG.md` is missing a `## {current}` entry.",
            "Add a matching changelog section.",
        )
    return Check("release-version", "pass", f"Version advanced from `{base_version}` to `{current}`.")


def check_profile_validation(root: Path) -> Check:
    proc = run([sys.executable, "scripts/validate_profile.py", "."], root)
    if proc.returncode == 0:
        return Check("profile-validation", "pass", summarize_output(proc))
    return Check("profile-validation", "fail", summarize_output(proc), "Fix validation errors.")


def check_generated_profile(root: Path) -> Check:
    params = root / "templates" / "profile.params.yaml"
    if not params.exists():
        return Check("generated-profile-smoke", "skip", "`templates/profile.params.yaml` is not present.")
    with tempfile.TemporaryDirectory(prefix="hermes-release-readiness-") as temp_dir:
        output = Path(temp_dir) / "generated"
        generate = run(
            [
                sys.executable,
                "scripts/generate_profile.py",
                "--params",
                str(params),
                "--output",
                str(output),
                "--force",
            ],
            root,
        )
        if generate.returncode != 0:
            return Check(
                "generated-profile-smoke",
                "fail",
                summarize_output(generate),
                "Fix deterministic generation from `templates/profile.params.yaml`.",
            )
        validate = subprocess.run(
            [sys.executable, str(output / "scripts" / "validate_profile.py"), str(output)],
            cwd=root,
            text=True,
            capture_output=True,
        )
        if validate.returncode != 0:
            return Check(
                "generated-profile-smoke",
                "fail",
                summarize_output(validate),
                "Fix generated profile validation errors.",
            )
    return Check("generated-profile-smoke", "pass", "Generated profile was created and validated.")


def check_install_smoke(root: Path) -> Check:
    hermes = shutil.which("hermes")
    if not hermes:
        return Check(
            "install-smoke",
            "skip",
            "Hermes CLI was not found; install smoke was not executed.",
            "Install Hermes CLI and rerun before tagging when possible.",
        )
    with tempfile.TemporaryDirectory(prefix="hermes-release-install-") as temp_dir:
        env = {"HERMES_HOME": str(Path(temp_dir) / "hermes-home")}
        proc = subprocess.run(
            [hermes, "profile", "install", str(root), "--name", "release-readiness-demo", "--yes", "--force"],
            cwd=root,
            env={**os.environ, **env},
            text=True,
            capture_output=True,
        )
    if proc.returncode == 0:
        return Check("install-smoke", "pass", summarize_output(proc))
    return Check("install-smoke", "fail", summarize_output(proc), "Fix local Hermes install smoke failure.")


def check_readme_install(root: Path) -> Check:
    readme = root / "README.md"
    if not readme.exists():
        return Check("readme-install-command", "fail", "`README.md` is missing.", "Add README install guidance.")
    text = readme.read_text(encoding="utf-8")
    if "hermes profile install" in text:
        return Check("readme-install-command", "pass", "README includes a Hermes install command.")
    return Check(
        "readme-install-command",
        "fail",
        "README does not include `hermes profile install`.",
        "Document the current install command.",
    )


def render_report(root: Path, base: str, checks: list[Check]) -> str:
    current_version = read_current_version(root)
    lines = [
        "# Release Readiness Report",
        "",
        f"- Root: `{root}`",
        f"- Base ref: `{base}`",
        f"- Version: `{current_version}`",
        "",
        "| Check | Status | Detail | Remediation |",
        "| --- | --- | --- | --- |",
    ]
    for check in checks:
        detail = check.detail.replace("|", "\\|")
        remediation = check.remediation.replace("|", "\\|")
        lines.append(f"| {check.name} | {check.status} | {detail} | {remediation} |")
    failures = [check for check in checks if check.status == "fail"]
    skipped = [check for check in checks if check.status == "skip"]
    lines.extend(
        [
            "",
            f"Summary: {len(failures)} failed, {len(skipped)} skipped, {len(checks) - len(failures) - len(skipped)} passed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a release readiness Markdown report")
    parser.add_argument("--base", default="origin/main", help="Git base ref to compare against")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--output", help="Optional file path for the Markdown report")
    parser.add_argument("--strict-base", action="store_true", help="Fail when the base ref is unavailable")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    checks = [
        check_release_version(root, args.base, strict=args.strict_base),
        check_profile_validation(root),
        check_generated_profile(root),
        check_install_smoke(root),
        check_readme_install(root),
    ]
    report = render_report(root, args.base, checks)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    print(report, end="")
    return 1 if any(check.status == "fail" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
