#!/usr/bin/env python3
"""Create a new Hermes profile distribution from templates."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("name must contain at least one alphanumeric character")
    return value


def render(text: str, context: dict[str, str]) -> str:
    for key, value in context.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Hermes profile distribution")
    parser.add_argument("--name", required=True, help="Profile slug or display name")
    parser.add_argument("--display-name", default="", help="Human-readable profile name")
    parser.add_argument("--description", required=True, help="One sentence profile purpose")
    parser.add_argument("--author", default="Hermes profile author")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--force", action="store_true", help="Overwrite output directory if it exists")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    template_dir = root / "templates" / "profile"
    output = Path(args.output).resolve()
    slug = slugify(args.name)
    display_name = args.display_name or args.name.replace("-", " ").title()
    context = {
        "profile_slug": slug,
        "display_name": display_name,
        "description": args.description,
        "author": args.author,
    }

    if output.exists():
        if not args.force:
            print(f"ERROR: output exists. Pass --force to overwrite: {output}")
            return 1
        shutil.rmtree(output)
    output.mkdir(parents=True)

    for template in template_dir.rglob("*.tmpl"):
        rel = template.relative_to(template_dir)
        out_rel = Path(str(rel)[:-5])
        target = output / out_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(template.read_text(encoding="utf-8"), context), encoding="utf-8")

    shutil.copytree(root / "scripts", output / "scripts")
    shutil.copytree(root / "skills", output / "skills")
    shutil.copytree(root / ".github", output / ".github")
    shutil.copy2(root / "LICENSE", output / "LICENSE")
    gitignore = output / ".gitignore"
    gitignore.write_text(".env\n*.db\n*.db-shm\n*.db-wal\nlogs/\nsessions/\nmemories/\nworkspace/\nplans/\nlocal/\ncache/\n", encoding="utf-8")

    result = subprocess.run(["python3", str(output / "scripts" / "validate_profile.py"), str(output)], text=True, capture_output=True)
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    if result.returncode != 0:
        return result.returncode
    print(f"Created Hermes profile distribution: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
