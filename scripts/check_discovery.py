#!/usr/bin/env python3
"""Check a Hermes profile distribution repository for search/discovery readiness."""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install pyyaml") from exc

RECOMMENDED_TOPICS = ["hermes-agent", "ai-agents", "agent-profile", "profile-distribution"]


def check_description(root: Path, fix: bool) -> tuple[list[str], list[str]]:
    recs = []
    fixes = []

    dist_yaml = root / "distribution.yaml"
    meta_yaml = root / "github-repo-metadata.yaml"

    dist_desc = ""
    dist_name = ""

    if dist_yaml.exists():
        try:
            data = yaml.safe_load(dist_yaml.read_text(encoding="utf-8")) or {}
            dist_desc = str(data.get("description") or "").strip()
            dist_name = str(data.get("name") or "").strip()
        except Exception as exc:
            recs.append(f"distribution.yaml exists but cannot be parsed: {exc}")
            return recs, fixes
    else:
        recs.append("Missing distribution.yaml in repository root.")
        return recs, fixes

    if not dist_desc:
        recs.append("distribution.yaml description is empty or missing.")
    else:
        # Check for one-sentence description
        sentences = [s for s in re.split(r'\. |\? |\! ', dist_desc) if s.strip()]
        if len(sentences) > 1 or not dist_desc.strip().endswith((".", "!", "?")):
            recs.append("distribution.yaml description should be a single, concise sentence ending with a period.")

    meta_desc = ""
    meta_exists = meta_yaml.exists()

    if meta_exists:
        try:
            data = yaml.safe_load(meta_yaml.read_text(encoding="utf-8")) or {}
            meta_desc = str(data.get("description") or "").strip()
        except Exception as exc:
            recs.append(f"github-repo-metadata.yaml exists but cannot be parsed: {exc}")

    if dist_desc:
        if not meta_exists:
            if fix:
                try:
                    payload = {
                        "description": dist_desc,
                        "homepage": f"https://github.com/YOUR_ORG/{dist_name or 'YOUR_REPO_NAME'}",
                        "topics": RECOMMENDED_TOPICS
                    }
                    meta_yaml.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
                    fixes.append("Created github-repo-metadata.yaml with description and recommended topics.")
                except Exception as exc:
                    recs.append(f"Failed to fix: could not write github-repo-metadata.yaml: {exc}")
            else:
                recs.append("Missing github-repo-metadata.yaml. Run with --fix to automatically generate one.")
        else:
            if meta_desc != dist_desc:
                if fix:
                    try:
                        content = yaml.safe_load(meta_yaml.read_text(encoding="utf-8")) or {}
                        content["description"] = dist_desc
                        meta_yaml.write_text(yaml.safe_dump(content, sort_keys=False), encoding="utf-8")
                        fixes.append("Updated github-repo-metadata.yaml description to match distribution.yaml.")
                    except Exception as exc:
                        recs.append(f"Failed to fix: could not update github-repo-metadata.yaml: {exc}")
                else:
                    recs.append("github-repo-metadata.yaml description does not match distribution.yaml description.")

    return recs, fixes


def check_install_command(root: Path) -> tuple[list[str], list[str]]:
    recs = []
    readme = root / "README.md"
    if not readme.exists():
        recs.append("Missing README.md in repository root.")
        return recs, []

    lines = readme.read_text(encoding="utf-8").splitlines()
    found = -1
    for idx, line in enumerate(lines[:80]):
        if "hermes profile install" in line.lower():
            found = idx
            break

    if found == -1:
        found_later = any("hermes profile install" in line.lower() for line in lines[80:])
        if found_later:
            recs.append("Installation command 'hermes profile install' is in README.md but not near the top (first 80 lines).")
        else:
            recs.append("Missing installation command ('hermes profile install') in README.md.")

    return recs, []


def check_topics(root: Path, fix: bool) -> tuple[list[str], list[str]]:
    recs = []
    fixes = []

    meta_yaml = root / "github-repo-metadata.yaml"
    if not meta_yaml.exists():
        return recs, fixes

    try:
        data = yaml.safe_load(meta_yaml.read_text(encoding="utf-8")) or {}
    except Exception:
        return recs, fixes

    topics = data.get("topics") or []
    if not isinstance(topics, list):
        recs.append("github-repo-metadata.yaml 'topics' field must be a list of strings.")
        return recs, fixes

    clean_topics = [t.strip().lower() for t in topics if isinstance(t, str)]
    missing = [t for t in RECOMMENDED_TOPICS if t not in clean_topics]

    if missing:
        if fix:
            try:
                data["topics"] = clean_topics + missing
                meta_yaml.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
                fixes.append(f"Added missing recommended topics to github-repo-metadata.yaml: {', '.join(missing)}")
            except Exception as exc:
                recs.append(f"Failed to fix: could not write topics to github-repo-metadata.yaml: {exc}")
        else:
            recs.append(f"github-repo-metadata.yaml is missing recommended topics: {', '.join(missing)}")

    domain_topics = [t for t in clean_topics if t not in RECOMMENDED_TOPICS]
    if not domain_topics:
        recs.append("Add at least one domain-specific search topic (e.g., database, security, analytics) to github-repo-metadata.yaml.")

    return recs, fixes


def check_domain_keywords(root: Path) -> tuple[list[str], list[str]]:
    recs = []
    dist_yaml = root / "distribution.yaml"
    readme_path = root / "README.md"

    if not dist_yaml.exists() or not readme_path.exists():
        return recs, []

    try:
        data = yaml.safe_load(dist_yaml.read_text(encoding="utf-8")) or {}
        name = str(data.get("name") or "").strip()
        desc = str(data.get("description") or "").strip()
    except Exception:
        return recs, []

    # Skip check for the template repository itself
    if name == "hermes-profile-template":
        return recs, []

    keywords = set()
    if name:
        for word in name.split("-"):
            if len(word) > 2 and word.lower() not in {"profile", "template", "agent", "hermes"}:
                keywords.add(word.lower())
    if desc:
        for word in re.findall(r"\b[a-zA-Z]{3,}\b", desc):
            if word.lower() not in {"profile", "template", "agent", "hermes", "with", "for", "custom", "building", "assistance", "starter", "distribution", "reusable", "authoring"}:
                keywords.add(word.lower())

    if not keywords:
        return recs, []

    readme_text = readme_path.read_text(encoding="utf-8")
    headings = []
    for line in readme_text.splitlines():
        if line.startswith("#"):
            headings.append(line.lstrip("#").strip().lower())

    matched_keywords = set()
    for heading in headings:
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", heading):
                matched_keywords.add(kw)

    if not matched_keywords:
        recs.append(f"README headings do not contain domain keywords (keywords found: {', '.join(sorted(list(keywords))[:5])}). Add domain-specific keywords to README headings.")

    return recs, []


def check_lineage(root: Path, fix: bool) -> tuple[list[str], list[str]]:
    recs = []
    fixes = []

    dist_yaml = root / "distribution.yaml"
    template_source_yml = root / ".github" / "template-source.yml"

    template_source = None
    if dist_yaml.exists():
        try:
            data = yaml.safe_load(dist_yaml.read_text(encoding="utf-8")) or {}
            template_source = data.get("template_source")
        except Exception:
            pass

    if not template_source:
        recs.append("template_source metadata is not defined in distribution.yaml.")
    else:
        if not isinstance(template_source, dict) or not template_source.get("url"):
            recs.append("template_source in distribution.yaml must be a mapping with a 'url' key.")
        elif not template_source_yml.exists():
            if fix:
                try:
                    template_source_yml.parent.mkdir(parents=True, exist_ok=True)
                    payload = {
                        "template": {
                            "url": template_source["url"],
                            "ref": template_source.get("ref", "main")
                        }
                    }
                    template_source_yml.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
                    fixes.append("Created .github/template-source.yml based on distribution.yaml lineage.")
                except Exception as exc:
                    recs.append(f"Failed to fix: could not create .github/template-source.yml: {exc}")
            else:
                recs.append("Missing .github/template-source.yml lineage descriptor. Run with --fix to generate it.")

    return recs, fixes


def check_validation_commands(root: Path) -> tuple[list[str], list[str]]:
    recs = []
    readme_path = root / "README.md"
    if not readme_path.exists():
        return recs, []

    readme_text = readme_path.read_text(encoding="utf-8").lower()

    has_validate = "make validate" in readme_text or "validate_profile.py" in readme_text
    has_smoke = "make smoke" in readme_text or "smoke_install.sh" in readme_text

    if not has_validate:
        recs.append("Document how to run profile validation (e.g., 'make validate' or 'validate_profile.py') in README.md.")
    if not has_smoke:
        recs.append("Document how to run local smoke tests (e.g., 'make smoke' or 'smoke_install.sh') in README.md.")

    return recs, []


def check_license_security(root: Path, fix: bool) -> tuple[list[str], list[str]]:
    recs = []
    fixes = []

    license_exists = any((root / f).exists() for f in ["LICENSE", "LICENSE.md", "LICENSE.txt"])
    security_exists = any((root / f).exists() for f in ["SECURITY.md", "SECURITY.txt"])

    if not license_exists:
        recs.append("Missing LICENSE file in repository root.")

    if not security_exists:
        if fix:
            try:
                security_content = """# Security Policy

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues. Instead, email security reports to [security@example.com](mailto:security@example.com).

We will acknowledge receipt of your report within 48 hours and coordinate a fix and release timeline with you.
"""
                (root / "SECURITY.md").write_text(security_content, encoding="utf-8")
                fixes.append("Created default SECURITY.md file.")
            except Exception as exc:
                recs.append(f"Failed to fix: could not create SECURITY.md: {exc}")
        else:
            recs.append("Missing SECURITY.md file in repository root. Run with --fix to generate a default one.")

    return recs, fixes


def check_catalog_guidance(root: Path) -> tuple[list[str], list[str]]:
    recs = []
    readme_path = root / "README.md"
    if not readme_path.exists():
        return recs, []

    readme_text = readme_path.read_text(encoding="utf-8").lower()

    has_catalog = "catalog" in readme_text or "snippet" in readme_text or "templates/catalog" in readme_text

    if not has_catalog:
        recs.append("Add catalog snippets or documentation guidance for submitting to profile catalogs in README.md.")

    return recs, []


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Hermes profile distribution repository for discovery readiness")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--fix", action="store_true", help="Apply safe mechanical fixes automatically")
    parser.add_argument("--strict", action="store_true", help="Fail with exit code 1 if any recommendations remain")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    if not root.exists():
        print(f"ERROR: Root path does not exist: {root}", file=sys.stderr)
        return 2

    recs: list[str] = []
    fixes: list[str] = []

    # Run checks
    for check_fn in [
        lambda r, f: check_description(r, f),
        lambda r, f: ([], []) if not r.exists() else check_install_command(r),
        lambda r, f: check_topics(r, f),
        lambda r, f: ([], []) if not r.exists() else check_domain_keywords(r),
        lambda r, f: check_lineage(r, f),
        lambda r, f: ([], []) if not r.exists() else check_validation_commands(r),
        lambda r, f: check_license_security(r, f),
        lambda r, f: ([], []) if not r.exists() else check_catalog_guidance(r),
    ]:
        r_list, f_list = check_fn(root, args.fix)
        recs.extend(r_list)
        fixes.extend(f_list)

    if fixes:
        print("Applied mechanical fixes:")
        for fix_msg in fixes:
            print(f" - {fix_msg}")
        print()

    # Re-run checks if fixed to see what remains
    if fixes and args.fix:
        recs = []
        for check_fn in [
            lambda r, f: check_description(r, False),
            lambda r, f: ([], []) if not r.exists() else check_install_command(r),
            lambda r, f: check_topics(r, False),
            lambda r, f: ([], []) if not r.exists() else check_domain_keywords(r),
            lambda r, f: check_lineage(r, False),
            lambda r, f: ([], []) if not r.exists() else check_validation_commands(r),
            lambda r, f: check_license_security(r, False),
            lambda r, f: ([], []) if not r.exists() else check_catalog_guidance(r),
        ]:
            r_list, _ = check_fn(root, False)
            recs.extend(r_list)

    if recs:
        print("Organic Discovery Recommendations:")
        for rec_msg in recs:
            print(f" * {rec_msg}")
        if args.strict:
            return 1
    else:
        print("All organic discovery checks passed successfully!")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
