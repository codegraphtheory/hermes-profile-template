#!/usr/bin/env python3
"""Build complete generated profile examples for the examples gallery."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


EXAMPLES = [
    "security-reviewer",
    "database-migration-reviewer",
    "release-manager",
    "research-assistant",
]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    generate = root / "scripts" / "generate_profile.py"
    params_dir = root / "examples" / "params"

    for slug in EXAMPLES:
        params = params_dir / f"{slug}.yaml"
        output = root / "examples" / slug
        if not params.exists():
            raise SystemExit(f"missing params file: {params}")
        cmd = [
            sys.executable,
            str(generate),
            "--params",
            str(params),
            "--output",
            str(output),
            "--force",
        ]
        print(f"Generating {slug}...")
        result = subprocess.run(cmd, cwd=root)
        if result.returncode != 0:
            return result.returncode

        validate = subprocess.run(
            [sys.executable, str(output / "scripts" / "validate_profile.py"), str(output)],
            cwd=root,
        )
        if validate.returncode != 0:
            return validate.returncode

    print("All examples generated and validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
