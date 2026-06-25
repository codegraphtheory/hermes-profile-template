#!/usr/bin/env python3
"""Run the profile validation checks expected in GitHub Actions."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


def run_step(name: str, args: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> CheckResult:
    print(f"::group::{name}")
    print("$ " + " ".join(args))
    proc = subprocess.run(args, cwd=cwd, text=True, env=env)
    print("::endgroup::")
    if proc.returncode != 0:
        raise RuntimeError(f"{name} failed with exit code {proc.returncode}")
    return CheckResult(name, "passed", "Command completed successfully.")


def compile_scripts(root: Path) -> CheckResult:
    scripts = sorted(str(path) for path in (root / "scripts").glob("*.py"))
    if not scripts:
        raise RuntimeError("No Python scripts found under scripts/")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    return run_step("Compile Python scripts", [sys.executable, "-m", "py_compile", *scripts], cwd=root, env=env)


def validate_profile(root: Path) -> CheckResult:
    return run_step("Validate profile distribution", [sys.executable, "scripts/validate_profile.py", "."], cwd=root)


def generator_smoke(root: Path) -> CheckResult:
    params = root / "templates" / "profile.params.yaml"
    if not params.exists():
        return CheckResult("Generator smoke", "skipped", "templates/profile.params.yaml is not present.")
    with tempfile.TemporaryDirectory(prefix="hermes-profile-ci-") as temp_dir:
        output = Path(temp_dir) / "generated"
        run_step(
            "Generate profile from params",
            [sys.executable, "scripts/generate_profile.py", "--params", str(params), "--output", str(output)],
            cwd=root,
        )
        return run_step(
            "Validate generated profile",
            [sys.executable, str(output / "scripts" / "validate_profile.py"), str(output)],
            cwd=root,
        )


def install_smoke(root: Path, *, require_hermes: bool) -> CheckResult:
    hermes = shutil.which("hermes")
    if not hermes:
        if require_hermes:
            raise RuntimeError("Hermes CLI is required but was not found on PATH.")
        return CheckResult("Hermes install smoke", "skipped", "Hermes CLI not found; validation and generator smoke still ran.")
    with tempfile.TemporaryDirectory(prefix="hermes-profile-home-") as temp_dir:
        env = {**os.environ, "HERMES_HOME": temp_dir}
        run_step(
            "Install profile with Hermes CLI",
            [hermes, "profile", "install", ".", "--name", "profile-smoke", "--yes"],
            cwd=root,
            env=env,
        )
        installed = Path(temp_dir) / "profiles" / "profile-smoke"
        required = [
            installed / "SOUL.md",
            installed / "distribution.yaml",
            installed / "scripts" / "validate_profile.py",
        ]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise RuntimeError("Hermes install smoke missing expected files: " + ", ".join(missing))
        return CheckResult("Hermes install smoke", "passed", f"Installed profile at {installed}")


def print_summary(results: list[CheckResult]) -> None:
    print("\nProfile CI summary")
    print("| Check | Status | Detail |")
    print("| --- | --- | --- |")
    for result in results:
        print(f"| {result.name} | {result.status} | {result.detail} |")


def run_checks(root: Path, *, skip_install_smoke: bool, require_hermes: bool) -> list[CheckResult]:
    results = [
        compile_scripts(root),
        validate_profile(root),
        generator_smoke(root),
    ]
    if skip_install_smoke:
        results.append(CheckResult("Hermes install smoke", "skipped", "Skipped by --skip-install-smoke."))
    else:
        results.append(install_smoke(root, require_hermes=require_hermes))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Hermes profile GitHub Actions validation checks")
    parser.add_argument("path", nargs="?", default=".", help="Profile repository path")
    parser.add_argument("--skip-install-smoke", action="store_true", help="Skip Hermes CLI install smoke")
    parser.add_argument("--require-hermes", action="store_true", help="Fail when Hermes CLI is unavailable")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 2
    try:
        results = run_checks(root, skip_install_smoke=args.skip_install_smoke, require_hermes=args.require_hermes)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print_summary(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
