#!/usr/bin/env python3
"""Check and optionally fix profile repository discovery metadata."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

RECOMMENDED_TOPICS = ["hermes-agent", "ai-agents", "agent-profile", "profile-distribution"]


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def infer_origin(root: Path) -> str | None:
    proc = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, text=True, capture_output=True)
    if proc.returncode != 0:
        return None
    url = proc.stdout.strip()
    if url.endswith(".git"):
        url = url[:-4]
    return url


def check(root: Path, fix: bool) -> tuple[list[str], list[str]]:
    recs: list[str] = []
    fixes: list[str] = []
    dist = load_yaml(root / "distribution.yaml")
    meta_path = root / "github-repo-metadata.yaml"
    meta = load_yaml(meta_path)
    desc = str(dist.get("description") or "").strip()
    if not desc:
        recs.append("distribution.yaml should include a concise description.")
    elif len(desc) > 180:
        recs.append("distribution.yaml description should be 180 characters or less for GitHub search.")
    if "hermes profile install" not in (root / "README.md").read_text(encoding="utf-8", errors="ignore") if (root / "README.md").exists() else "":
        recs.append("README.md should include a visible `hermes profile install` command.")
    if not meta:
        if fix:
            meta = {"description": desc, "homepage": infer_origin(root) or "", "topics": list(RECOMMENDED_TOPICS)}
            meta_path.write_text(yaml.safe_dump(meta, sort_keys=False), encoding="utf-8")
            fixes.append("Created github-repo-metadata.yaml.")
        else:
            recs.append("github-repo-metadata.yaml is missing.")
    if meta:
        topics = [str(t).lower() for t in meta.get("topics") or []]
        missing = [topic for topic in RECOMMENDED_TOPICS if topic not in topics]
        if missing:
            if fix:
                meta["topics"] = topics + missing
                meta_path.write_text(yaml.safe_dump(meta, sort_keys=False), encoding="utf-8")
                fixes.append("Added missing recommended topics: " + ", ".join(missing))
            else:
                recs.append("Missing recommended topics: " + ", ".join(missing))
        if desc and meta.get("description") != desc:
            recs.append("github-repo-metadata.yaml description should match distribution.yaml description.")
    if not (root / "SECURITY.md").exists():
        recs.append("SECURITY.md is missing.")
    if not (root / "LICENSE").exists():
        recs.append("LICENSE is missing.")
    return recs, fixes


def main() -> int:
    parser = argparse.ArgumentParser(description="Check profile discovery readiness.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args()
    recs, fixes = check(Path(args.path), args.fix)
    for item in fixes:
        print("FIX: " + item)
    if recs:
        for item in recs:
            print("RECOMMEND: " + item)
        return 1
    print("Discovery readiness passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
