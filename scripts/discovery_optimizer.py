#!/usr/bin/env python3
"""Report discovery readiness recommendations for generated Hermes profiles."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


BASE_TOPICS = [
    "hermes-agent",
    "agent-profile",
    "profile-distribution",
]

STOPWORDS = {
    "about",
    "agent",
    "build",
    "custom",
    "description",
    "developer",
    "distribution",
    "hermes",
    "install",
    "profile",
    "profiles",
    "quickly",
    "repository",
    "starter",
    "template",
    "with",
}


@dataclass(frozen=True)
class Finding:
    check: str
    status: str
    message: str
    recommendation: str = ""


@dataclass(frozen=True)
class DiscoveryReport:
    path: str
    score: int
    findings: list[Finding]
    recommended_topics: list[str]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install with: python3 -m pip install -r requirements.txt")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def clean_topic(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")[:50]


def keyword_candidates(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", text.lower())
    topics: list[str] = []
    for word in words:
        topic = clean_topic(word)
        if topic and topic not in STOPWORDS and topic not in topics:
            topics.append(topic)
    return topics


def recommended_topics(manifest: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
    seeds = BASE_TOPICS.copy()
    description = " ".join(
        str(item)
        for item in [
            manifest.get("name", ""),
            manifest.get("description", ""),
            metadata.get("description", ""),
        ]
        if item
    )
    for topic in keyword_candidates(description):
        if topic not in seeds:
            seeds.append(topic)
    return seeds[:8]


def has_near_top_install(readme: str) -> bool:
    near_top = "\n".join(readme.splitlines()[:90]).lower()
    return "hermes profile install" in near_top or (
        "git clone" in near_top and "validate_profile.py" in near_top
    )


def heading_keywords(readme: str) -> set[str]:
    headings = re.findall(r"^#+\s+(.+)$", readme, flags=re.MULTILINE)
    return set(keyword_candidates(" ".join(headings)))


def add_finding(
    findings: list[Finding],
    check: str,
    passed: bool,
    pass_message: str,
    fail_message: str,
    recommendation: str,
    *,
    warn: bool = True,
) -> None:
    if passed:
        findings.append(Finding(check, "pass", pass_message))
    else:
        findings.append(Finding(check, "warning" if warn else "missing", fail_message, recommendation))


def analyze_repository(root: Path) -> DiscoveryReport:
    root = root.resolve()
    readme_path = root / "README.md"
    manifest_path = root / "distribution.yaml"
    metadata_path = root / "github-repo-metadata.yaml"
    readme = read_text(readme_path)
    manifest = load_yaml(manifest_path)
    metadata = load_yaml(metadata_path)
    topics = [clean_topic(str(item)) for item in metadata.get("topics", []) if clean_topic(str(item))]
    suggested_topics = recommended_topics(manifest, metadata)
    missing_core_topics = [topic for topic in BASE_TOPICS if topic not in topics]

    findings: list[Finding] = []
    description = str(metadata.get("description") or manifest.get("description") or "").strip()
    add_finding(
        findings,
        "description",
        bool(description and len(description) <= 180),
        "Repository description is concise and available in metadata or manifest.",
        "Repository description is missing or too long for quick search snippets.",
        "Add a one-sentence description under 180 characters to github-repo-metadata.yaml or distribution.yaml.",
    )
    add_finding(
        findings,
        "install-command",
        has_near_top_install(readme),
        "README shows an install or clone-and-validate path near the top.",
        "README does not show an install path near the top.",
        "Add a short `hermes profile install ...` or clone-and-validate command in the first sections.",
    )
    add_finding(
        findings,
        "github-topics",
        bool(topics) and not missing_core_topics,
        "GitHub metadata topics cover Hermes and profile discovery.",
        "GitHub metadata topics are missing useful discovery terms.",
        "Add topics: " + ", ".join(missing_core_topics or suggested_topics),
    )
    heading_terms = heading_keywords(readme)
    add_finding(
        findings,
        "readme-headings",
        bool(heading_terms.intersection(set(suggested_topics))),
        "README headings include searchable domain or profile keywords.",
        "README headings do not expose clear search-friendly domain keywords.",
        "Use concrete domain terms in section headings instead of hiding them only in prose.",
    )
    lineage_file = root / ".github" / "template-source.yml"
    lineage_text = bool(
        re.search(r"(template[_ -]?source|generated from|source template|template lineage)", readme, re.I)
    )
    add_finding(
        findings,
        "template-lineage",
        bool(manifest.get("template_source") or lineage_file.exists() or lineage_text),
        "Template lineage is declared in manifest, metadata, or README.",
        "Template lineage is not discoverable.",
        "Record source template lineage in distribution.yaml, .github/template-source.yml, or README.",
    )
    add_finding(
        findings,
        "validation-commands",
        "make validate" in readme and ("make smoke" in readme or "validate_profile.py" in readme),
        "README shows validation and smoke commands.",
        "README does not clearly show validation and smoke commands.",
        "Document `make validate` and `make smoke` before the publishing section.",
    )
    add_finding(
        findings,
        "license-security",
        (root / "LICENSE").exists() and (root / "SECURITY.md").exists(),
        "License and security policy files are present.",
        "License or security policy file is missing.",
        "Add LICENSE and SECURITY.md before publishing.",
        warn=False,
    )
    add_finding(
        findings,
        "share-snippet",
        bool(re.search(r"(social preview|share snippet|catalog|homepage|topics)", readme, re.I)),
        "README gives catalog, topic, or sharing guidance.",
        "README does not include catalog, topic, or sharing guidance.",
        "Add a short publishing snippet with homepage, topics, and social preview guidance.",
    )

    earned = sum(1 for finding in findings if finding.status == "pass")
    score = round((earned / len(findings)) * 100) if findings else 0
    return DiscoveryReport(str(root), score, findings, suggested_topics)


def apply_safe_fixes(root: Path, report: DiscoveryReport) -> list[str]:
    if yaml is None:
        raise SystemExit("PyYAML is required for --fix")
    metadata_path = root / "github-repo-metadata.yaml"
    metadata = load_yaml(metadata_path)
    existing = [clean_topic(str(item)) for item in metadata.get("topics", []) if clean_topic(str(item))]
    changed = False
    for topic in report.recommended_topics:
        if topic not in existing:
            existing.append(topic)
            changed = True
    if not changed:
        return []
    metadata["topics"] = existing[:20]
    metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")
    return [f"Updated {metadata_path.relative_to(root)} topics."]


def to_json(report: DiscoveryReport) -> str:
    data = asdict(report)
    data["findings"] = [asdict(finding) for finding in report.findings]
    return json.dumps(data, indent=2, sort_keys=True)


def to_markdown(report: DiscoveryReport) -> str:
    lines = [
        "# Discovery Readiness Report",
        "",
        f"Score: **{report.score}/100**",
        "",
        "| Check | Status | Recommendation |",
        "| --- | --- | --- |",
    ]
    for finding in report.findings:
        recommendation = finding.recommendation or finding.message
        lines.append(f"| {finding.check} | {finding.status} | {recommendation} |")
    lines.extend(["", "Recommended topics:", ""])
    lines.extend(f"- `{topic}`" for topic in report.recommended_topics)
    return "\n".join(lines) + "\n"


def to_text(report: DiscoveryReport) -> str:
    lines = [f"Discovery readiness score: {report.score}/100", ""]
    for finding in report.findings:
        lines.append(f"[{finding.status}] {finding.check}: {finding.message}")
        if finding.recommendation:
            lines.append(f"  recommendation: {finding.recommendation}")
    lines.extend(["", "Recommended topics: " + ", ".join(report.recommended_topics)])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Report discovery readiness for a Hermes profile repository")
    parser.add_argument("path", nargs="?", default=".", help="Profile repository path")
    parser.add_argument("--json", action="store_true", help="Print deterministic JSON")
    parser.add_argument("--markdown", action="store_true", help="Print a Markdown report")
    parser.add_argument("--fix", action="store_true", help="Apply safe mechanical metadata fixes")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 2

    try:
        report = analyze_repository(root)
        if args.fix:
            for message in apply_safe_fixes(root, report):
                print(message, file=sys.stderr)
            report = analyze_repository(root)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(to_json(report))
    elif args.markdown:
        print(to_markdown(report), end="")
    else:
        print(to_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
