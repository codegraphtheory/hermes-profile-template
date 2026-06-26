#!/usr/bin/env python3
"""Run safe temporary demo fixtures without exposing local Hermes state."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

FORBIDDEN_NAMES = {".env", "auth.json", "state.db"}
FORBIDDEN_PARTS = {"memories", "sessions", "logs"}


@dataclass(frozen=True)
class DemoResult:
    name: str
    status: str
    workspace: Path
    note: str


def redacted(path: Path, workspace: Path) -> str:
    text = str(path)
    return text.replace(str(workspace), "$DEMO_WORKSPACE")


def run(args: list[str], cwd: Path, workspace: Path, env: dict[str, str] | None = None) -> None:
    printable = [redacted(Path(arg), workspace) if str(arg).startswith(str(workspace)) else str(arg) for arg in args]
    print("$ " + " ".join(printable))
    subprocess.run(args, cwd=cwd, env=env, check=True)


def assert_no_runtime_state(root: Path) -> None:
    hits = []
    for path in root.rglob("*"):
        if path.name in FORBIDDEN_NAMES or set(path.relative_to(root).parts) & FORBIDDEN_PARTS:
            hits.append(str(path.relative_to(root)))
    if hits:
        raise RuntimeError("Runtime state leaked into demo output: " + ", ".join(hits))


def generate_demo(root: Path, workspace: Path) -> DemoResult:
    output = workspace / "generated-profile"
    run([sys.executable, "scripts/generate_profile.py", "--params", "templates/profile.params.yaml", "--output", str(output)], root, workspace)
    run([sys.executable, str(output / "scripts" / "validate_profile.py"), str(output)], root, workspace)
    assert_no_runtime_state(output)
    return DemoResult("generate-and-validate", "passed", workspace, "Generated profile validated in a temporary workspace.")


def install_demo(root: Path, workspace: Path, require_hermes: bool) -> DemoResult:
    hermes = shutil.which("hermes")
    if not hermes:
        if require_hermes:
            raise RuntimeError("Hermes CLI was not found on PATH.")
        return DemoResult("install-profile", "skipped", workspace, "Hermes CLI not found.")
    hermes_home = workspace / "hermes-home"
    env = {**os.environ, "HERMES_HOME": str(hermes_home)}
    run([hermes, "profile", "install", ".", "--name", "profile-architect-demo", "--yes", "--force"], root, workspace, env=env)
    expected = hermes_home / "profiles" / "profile-architect-demo" / "SOUL.md"
    if not expected.exists():
        raise RuntimeError(f"Expected installed file missing: {expected}")
    return DemoResult("install-profile", "passed", workspace, "Installed into temporary HERMES_HOME.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe Hermes profile demo fixtures.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--demo", choices=["generate", "install", "all"], default="generate")
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--require-hermes", action="store_true")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    workspace = Path(tempfile.mkdtemp(prefix="hermes-demo-"))
    results: list[DemoResult] = []
    try:
        if args.demo in {"generate", "all"}:
            results.append(generate_demo(root, workspace))
        if args.demo in {"install", "all"}:
            results.append(install_demo(root, workspace, args.require_hermes))
        print("\n| Demo | Status | Note |")
        print("| --- | --- | --- |")
        for result in results:
            print(f"| {result.name} | {result.status} | {result.note} |")
        print("\nRedaction reminder: record only the temporary workspace, never secrets, auth files, memories, sessions, or logs.")
        return 0
    finally:
        if args.keep:
            print(f"Kept workspace: {workspace}")
        else:
            shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
