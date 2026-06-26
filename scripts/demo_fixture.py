#!/usr/bin/env python3
"""Create safe temporary demo workspaces for Hermes profile recordings."""
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
class DemoResult:
    name: str
    status: str
    workspace: str
    note: str


def redact_command(args: list[str]) -> str:
    temp_root = tempfile.gettempdir()
    redacted = [
        "$TMPDIR" if str(arg).startswith(temp_root) else str(arg)
        for arg in args
    ]
    return " ".join(redacted)


def assert_no_runtime_state(root: Path) -> None:
    forbidden = {".env", "auth.json", "state.db", "sessions", "memories", "logs"}
    hits = [path for path in root.rglob("*") if path.name in forbidden]
    if hits:
        names = ", ".join(str(path.relative_to(root)) for path in hits)
        raise RuntimeError(f"Generated profile includes runtime state: {names}")


def run(args: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    print("$ " + redact_command(args))
    subprocess.run(args, cwd=cwd, env=env, check=True)


def generate_profile_demo(root: Path, workspace: Path) -> DemoResult:
    output = workspace / "generated-profile"
    run(
        [
            sys.executable,
            "scripts/generate_profile.py",
            "--params",
            "templates/profile.params.yaml",
            "--output",
            str(output),
        ],
        cwd=root,
    )
    run([sys.executable, str(output / "scripts" / "validate_profile.py"), str(output)], cwd=root)
    assert_no_runtime_state(output)
    return DemoResult(
        "generate-and-validate",
        "passed",
        str(workspace),
        "Generated profile was created in a temporary workspace and validated.",
    )


def install_architect_demo(root: Path, workspace: Path, *, require_hermes: bool) -> DemoResult:
    hermes = shutil.which("hermes")
    if not hermes:
        if require_hermes:
            raise RuntimeError("Hermes CLI is required for this demo but was not found on PATH.")
        return DemoResult(
            "profile-architect-install",
            "skipped",
            str(workspace),
            "Hermes CLI was not found; install demo commands remain documented but were not executed.",
        )
    hermes_home = workspace / "hermes-home"
    hermes_home.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "HERMES_HOME": str(hermes_home),
        "HERMES_NO_UPDATE_CHECK": "1",
    }
    run(
        [hermes, "profile", "install", ".", "--name", "profile-architect-demo", "--yes", "--force"],
        cwd=root,
        env=env,
    )
    expected = hermes_home / "profiles" / "profile-architect-demo" / "SOUL.md"
    if not expected.exists():
        raise RuntimeError(f"Expected installed profile file missing: {expected}")
    return DemoResult(
        "profile-architect-install",
        "passed",
        str(workspace),
        f"Profile installed into temporary HERMES_HOME: {hermes_home}",
    )


def print_summary(results: list[DemoResult]) -> None:
    print("\nDemo fixture summary")
    print("| Demo | Status | Workspace | Note |")
    print("| --- | --- | --- | --- |")
    for result in results:
        print(f"| {result.name} | {result.status} | {result.workspace} | {result.note} |")
    print("\nRedaction reminder: record only the temporary workspace, never `.env`, auth files, memories, sessions, or local private paths.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe Hermes profile demo fixtures")
    parser.add_argument("path", nargs="?", default=".", help="Template repository root")
    parser.add_argument("--demo", choices=["all", "generate", "install"], default="generate")
    parser.add_argument("--keep", action="store_true", help="Keep the temporary workspace for manual recording")
    parser.add_argument("--require-hermes", action="store_true", help="Fail install demo when Hermes CLI is unavailable")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 2

    temp_context = tempfile.TemporaryDirectory(prefix="hermes-demo-")
    workspace = Path(temp_context.name)
    if args.keep:
        temp_context.cleanup()
        workspace.mkdir(parents=True, exist_ok=True)

    try:
        results: list[DemoResult] = []
        if args.demo in {"all", "generate"}:
            results.append(generate_profile_demo(root, workspace))
        if args.demo in {"all", "install"}:
            results.append(install_architect_demo(root, workspace, require_hermes=args.require_hermes))
        print_summary(results)
        return 0
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if not args.keep:
            temp_context.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
