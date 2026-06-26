#!/usr/bin/env python3
"""Remove a marked Hermes demo workspace and refuse unsafe paths."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

MARKER_NAME = ".hermes-demo-fixture"


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean up a marked Hermes demo fixture workspace.")
    parser.add_argument("workspace", help="Path created by scripts/demo_fixture.py --keep")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    marker = workspace / MARKER_NAME
    if not marker.is_file():
        raise SystemExit(f"Refusing to remove {workspace}: missing {MARKER_NAME} marker.")
    if workspace.parent == workspace:
        raise SystemExit("Refusing to remove a filesystem root.")

    shutil.rmtree(workspace)
    print(f"Removed demo workspace: {workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
