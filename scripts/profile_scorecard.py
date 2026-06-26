#!/usr/bin/env python3
"""Compute a quality scorecard for a Hermes profile repository."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import yaml

SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]
RUNTIME_NAMES = {".env", "auth.json", "state.db", "state.db-shm", "state.db-wal"}
RUNTIME_PARTS = {"memories", "sessions", "logs", "workspace", "plans"}


@dataclass(frozen=True)
class Item:
    name: str
    points: int
    max_points: int
    detail: str


class Scorecard:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.items: list[Item] = []

    def add(self, name: str, points: int, max_points: int, detail: str) -> None:
        self.items.append(Item(name, points, max_points, detail))

    def run(self) -> None:
        self.check_manifest()
        self.check_docs()
        self.check_security()
        self.check_quality_gates()
        self.check_discovery()

    def manifest(self) -> dict:
        path = self.root / "distribution.yaml"
        if not path.exists():
            return {}
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}

    def check_manifest(self) -> None:
        data = self.manifest()
        self.add("distribution.yaml exists", 10 if data else 0, 10, "Installable profiles need a manifest.")
        name = str(data.get("name") or "")
        version = str(data.get("version") or "")
        desc = str(data.get("description") or "")
        self.add("manifest name is kebab-case", 8 if re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) else 0, 8, name or "missing")
        self.add("manifest version is semver", 8 if re.fullmatch(r"\d+\.\d+\.\d+", version) else 0, 8, version or "missing")
        self.add("manifest description is useful", 8 if 20 <= len(desc) <= 180 else 0, 8, desc or "missing")
        env = data.get("env_requires") or []
        documented = all(isinstance(item, dict) and item.get("name") and item.get("description") for item in env)
        self.add("env vars are documented", 6 if documented else 0, 6, f"{len(env)} env var entries")

    def check_docs(self) -> None:
        for filename, points in {"README.md": 8, "SOUL.md": 6, "AGENTS.md": 4, "SECURITY.md": 4, "CHANGELOG.md": 4}.items():
            self.add(f"{filename} exists", points if (self.root / filename).exists() else 0, points, filename)
        readme = (self.root / "README.md").read_text(encoding="utf-8") if (self.root / "README.md").exists() else ""
        self.add("README includes install command", 8 if "hermes profile install" in readme else 0, 8, "install command visible")
        self.add("README includes validation command", 4 if "validate_profile.py" in readme or "make validate" in readme else 0, 4, "validation command visible")

    def check_security(self) -> None:
        hits: list[str] = []
        for path in self.root.rglob("*"):
            if ".git" in path.parts or not path.is_file():
                continue
            rel = path.relative_to(self.root)
            if path.name in RUNTIME_NAMES or set(rel.parts) & RUNTIME_PARTS:
                hits.append(str(rel))
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".zip"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if any(pattern.search(text) for pattern in SECRET_PATTERNS):
                hits.append(str(rel))
        self.add("no runtime state or token-like secrets", 14 if not hits else 0, 14, ", ".join(hits[:8]) if hits else "clean")

    def check_quality_gates(self) -> None:
        self.add("validator script exists", 5 if (self.root / "scripts" / "validate_profile.py").exists() else 0, 5, "scripts/validate_profile.py")
        makefile = (self.root / "Makefile").read_text(encoding="utf-8") if (self.root / "Makefile").exists() else ""
        self.add("Makefile exposes validate", 4 if "validate:" in makefile else 0, 4, "make validate")
        self.add("Makefile exposes smoke", 4 if "smoke:" in makefile else 0, 4, "make smoke")

    def check_discovery(self) -> None:
        meta_path = self.root / "github-repo-metadata.yaml"
        if not meta_path.exists():
            self.add("GitHub metadata exists", 0, 5, "github-repo-metadata.yaml missing")
            self.add("GitHub topics are useful", 0, 4, "metadata missing")
            return
        data = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        topics = data.get("topics") or []
        self.add("GitHub metadata exists", 5, 5, "github-repo-metadata.yaml")
        useful = isinstance(topics, list) and {"hermes-agent", "profile-distribution"}.issubset(set(map(str, topics)))
        self.add("GitHub topics are useful", 4 if useful else 0, 4, ", ".join(map(str, topics)) if isinstance(topics, list) else "invalid")

    @property
    def total(self) -> int:
        return sum(item.points for item in self.items)

    @property
    def maximum(self) -> int:
        return sum(item.max_points for item in self.items)

    @property
    def percent(self) -> float:
        return round((self.total / self.maximum) * 100, 1) if self.maximum else 0.0

    def as_dict(self) -> dict:
        return {"score": self.percent, "points": self.total, "max_points": self.maximum, "items": [asdict(item) for item in self.items]}


def render_markdown(card: Scorecard) -> str:
    lines = ["# Hermes profile scorecard", "", f"Score: {card.percent}% ({card.total}/{card.maximum})", "", "| Check | Points | Detail |", "| --- | --- | --- |"]
    for item in card.items:
        lines.append(f"| {item.name} | {item.points}/{item.max_points} | {item.detail.replace('|', '/')} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a Hermes profile distribution repository.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    parser.add_argument("--threshold", type=int)
    args = parser.parse_args()
    if args.threshold is not None and not 0 <= args.threshold <= 100:
        parser.error("--threshold must be between 0 and 100")
    card = Scorecard(Path(args.path))
    card.run()
    if args.format == "json":
        print(json.dumps(card.as_dict(), indent=2, sort_keys=True))
    elif args.format == "markdown":
        print(render_markdown(card), end="")
    else:
        print(f"Hermes profile scorecard: {card.percent}% ({card.total}/{card.maximum})")
        for item in card.items:
            status = "PASS" if item.points == item.max_points else "WARN" if item.points else "FAIL"
            print(f"[{status}] {item.name}: {item.points}/{item.max_points} - {item.detail}")
    return 1 if args.threshold is not None and card.percent < args.threshold else 0


if __name__ == "__main__":
    raise SystemExit(main())
