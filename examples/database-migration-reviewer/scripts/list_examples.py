#!/usr/bin/env python3
"""List Hermes profile examples with validation status."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def validate_example(path: Path) -> tuple[bool, str]:
    script = path / "scripts" / "validate_profile.py"
    if not script.exists():
        return False, "missing validate_profile.py"
    result = subprocess.run(
        [sys.executable, str(script), str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True, "valid"
    message = (result.stdout + result.stderr).strip().splitlines()
    return False, message[-1] if message else "validation failed"


def main() -> int:
    parser = argparse.ArgumentParser(description="List Hermes profile examples")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    examples_root = root / "examples"
    gallery_path = examples_root / "gallery.json"
    gallery = json.loads(gallery_path.read_text(encoding="utf-8")) if gallery_path.exists() else {"examples": []}
    metadata = {item["name"]: item for item in gallery.get("examples", [])}

    rows: list[dict[str, str]] = []
    for child in sorted(examples_root.iterdir()):
        if not child.is_dir() or child.name in {"params"}:
            continue
        if not (child / "distribution.yaml").exists():
            continue
        ok, status = validate_example(child)
        meta = metadata.get(child.name, {})
        rows.append(
            {
                "name": child.name,
                "use_case": meta.get("use_case", ""),
                "install_command": meta.get("install_command", ""),
                "validation": status if ok else f"FAILED: {status}",
            }
        )

    if args.json:
        print(json.dumps(rows, indent=2))
        return 0

    for row in rows:
        print(f"- {row['name']}: {row['use_case']} [{row['validation']}]")
        print(f"  install: {row['install_command']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
