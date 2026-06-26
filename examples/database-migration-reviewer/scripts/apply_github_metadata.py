#!/usr/bin/env python3
"""Apply GitHub repository description, homepage, and topics from YAML metadata."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install pyyaml") from exc


def run(args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, input=input_text, text=True, capture_output=True)


def load_metadata(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("metadata file must contain a YAML mapping")
    topics = data.get("topics") or []
    if not isinstance(topics, list) or not all(isinstance(item, str) for item in topics):
        raise ValueError("topics must be a list of strings")
    clean_topics = []
    for topic in topics:
        topic = topic.strip().lower()
        if topic and topic not in clean_topics:
            clean_topics.append(topic)
    data["topics"] = clean_topics
    if len(clean_topics) > 20:
        raise ValueError("GitHub allows at most 20 repository topics")
    return data


def infer_repo() -> str:
    proc = run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "failed to infer repository")
    repo = proc.stdout.strip()
    if not repo or "/" not in repo:
        raise RuntimeError("could not infer repository. Pass --repo OWNER/REPO")
    return repo


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply GitHub repository metadata")
    parser.add_argument("--metadata", default="github-repo-metadata.yaml", help="Metadata YAML path")
    parser.add_argument("--repo", default="", help="Repository slug, for example OWNER/REPO")
    parser.add_argument("--apply", action="store_true", help="Mutate GitHub. Without this flag, only print the planned change")
    args = parser.parse_args()

    path = Path(args.metadata).resolve()
    metadata = load_metadata(path)
    repo = args.repo.strip() or infer_repo()

    payload = {
        key: metadata[key]
        for key in ["description", "homepage"]
        if metadata.get(key) is not None
    }
    topics = metadata.get("topics") or []

    print(f"Repository: {repo}")
    print(json.dumps({"repo": repo, **payload, "topics": topics}, indent=2, sort_keys=True))

    if not args.apply:
        print("Dry run only. Re-run with --apply to update GitHub.")
        return 0

    if payload:
        proc = run(["gh", "api", f"repos/{repo}", "-X", "PATCH", "--input", "-"], input_text=json.dumps(payload))
        if proc.returncode != 0:
            print(proc.stderr or proc.stdout, file=sys.stderr)
            return proc.returncode
    if topics:
        proc = run(
            [
                "gh",
                "api",
                f"repos/{repo}/topics",
                "-X",
                "PUT",
                "-H",
                "Accept: application/vnd.github+json",
                "--input",
                "-",
            ],
            input_text=json.dumps({"names": topics}),
        )
        if proc.returncode != 0:
            print(proc.stderr or proc.stdout, file=sys.stderr)
            return proc.returncode
    print("GitHub repository metadata updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
