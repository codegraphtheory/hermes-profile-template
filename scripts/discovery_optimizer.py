#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import json
import re
from pathlib import Path
import yaml

RECOMMENDED_TOPICS = ["hermes-agent", "ai-agents", "agent-profile", "profile-distribution"]


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def infer_origin(root: Path) -> str | None:
    proc = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, text=True, capture_output=True)
    if proc.returncode != 0:
        return None
    url = proc.stdout.strip()
    if url.endswith(".git"):
        url = url[:-4]
    return url


def run_checks(root: Path, fix: bool) -> tuple[dict[str, dict[str, str]], list[str]]:
    report = {
        "one_sentence_desc": {"status": "FAIL", "hint": "Add a clear description (<= 180 chars) in distribution.yaml."},
        "install_command": {"status": "FAIL", "hint": "Include a visible `hermes profile install` command near the top of README.md."},
        "github_topics": {"status": "FAIL", "hint": "Add all recommended topics to github-repo-metadata.yaml."},
        "domain_keywords": {"status": "FAIL", "hint": "Enhance README.md headings with context keywords like Security or Use Case."},
        "template_lineage": {"status": "FAIL", "hint": "Mention source template lineage (hermes-profile-template) in README.md."},
        "validation_commands": {"status": "FAIL", "hint": "Document explicit verification runbooks like `make validate` in README.md."},
        "license_security": {"status": "FAIL", "hint": "Verify both LICENSE and SECURITY.md exist in the repository root."},
        "social_preview": {"status": "FAIL", "hint": "Provide configurations or guides for social previews / sharing snippets."}
    }
    
    fixes: list[str] = []
    dist = load_yaml(root / "distribution.yaml")
    meta_path = root / "github-repo-metadata.yaml"
    meta = load_yaml(meta_path)
    
    desc = str(dist.get("description") or "").strip()
    if desc and len(desc) <= 180:
        report["one_sentence_desc"]["status"] = "PASS"
        report["one_sentence_desc"]["hint"] = "Valid core distribution description verified."
        
    readme_path = root / "README.md"
    readme_content = ""
    readme_lines = []
    if readme_path.exists():
        readme_content = readme_path.read_text(encoding="utf-8", errors="ignore")
        readme_lines = readme_content.splitlines()
        
    if "hermes profile install" in readme_content:
        report["install_command"]["status"] = "PASS"
        report["install_command"]["hint"] = "Installation command block located dynamically."
        
    if not meta and fix and desc:
        meta = {"description": desc, "homepage": infer_origin(root) or "", "topics": list(RECOMMENDED_TOPICS)}
        meta_path.write_text(yaml.safe_dump(meta, sort_keys=False), encoding="utf-8")
        fixes.append("Created github-repo-metadata.yaml configuration.")
        meta = load_yaml(meta_path)
        
    if meta:
        topics = [str(t).lower() for t in meta.get("topics") or []]
        missing = [t for t in RECOMMENDED_TOPICS if t not in topics]
        if not missing:
            report["github_topics"]["status"] = "PASS"
            report["github_topics"]["hint"] = "All recommended discovery topics are active."
        elif fix:
            meta["topics"] = topics + missing
            meta_path.write_text(yaml.safe_dump(meta, sort_keys=False), encoding="utf-8")
            fixes.append("Injected missing infrastructure topics.")
            report["github_topics"]["status"] = "PASS"
            report["github_topics"]["hint"] = "All recommended discovery topics are active."
            
    matched_headings = 0
    keyword_patterns = [r"security", r"discovery", r"use\s*case", r"profile", r"optimization", r"deployment"]
    for line in readme_lines:
        if line.strip().startswith("#"):
            if any(re.search(pat, line, re.IGNORECASE) for pat in keyword_patterns):
                matched_headings += 1
                
    if matched_headings >= 2:
        report["domain_keywords"]["status"] = "PASS"
        report["domain_keywords"]["hint"] = f"Validated {matched_headings} enriched domain search anchors."
        
    if "hermes-profile-template" in readme_content:
        report["template_lineage"]["status"] = "PASS"
        report["template_lineage"]["hint"] = "Upstream tracking lineage confirmed."
        
    val_patterns = [r"make validate", r"validate_profile\.py", r"make smoke"]
    if any(re.search(pat, readme_content, re.IGNORECASE) for pat in val_patterns):
        report["validation_commands"]["status"] = "PASS"
        report["validation_commands"]["hint"] = "Testing matrix runbooks mapped out."
        
    if (root / "SECURITY.md").exists() and (root / "LICENSE").exists():
        report["license_security"]["status"] = "PASS"
        report["license_security"]["hint"] = "Compliance gates (LICENSE + SECURITY.md) satisfied."
        
    if any(re.search(pat, readme_content, re.IGNORECASE) for pat in [r"social", r"preview", r"share", r"og:image", r"meta"]):
        report["social_preview"]["status"] = "PASS"
        report["social_preview"]["hint"] = "Social link index configuration guidelines covered."
        
    if fix and report["template_lineage"]["status"] == "FAIL" and readme_path.exists():
        lineage_node = "\n\n---\n*Generated via [hermes-profile-template](https://github.com/codegraphtheory/hermes-profile-template).*\n"
        readme_path.write_text(readme_content + lineage_node, encoding="utf-8")
        fixes.append("Appended lineage tracking data to README.md.")
        report["template_lineage"]["status"] = "PASS"
        report["template_lineage"]["hint"] = "Upstream tracking lineage confirmed."
        
    return report, fixes


def generate_markdown(report: dict) -> str:
    lines = ["# README Discovery Optimization Report\n"]
    lines.append("| Metric Domain | Pipeline Status | Recommendation Notes |")
    lines.append("| :--- | :---: | :--- |")
    for k, v in report.items():
        sym = "✅ PASS" if v["status"] == "PASS" else "❌ FAIL"
        lines.append(f"| **{k.replace('_', ' ').title()}** | {sym} | {v['hint']} |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check and optimize profile repository discovery.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    
    root = Path(args.path)
    report, fixes = run_checks(root, args.fix)
    
    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    elif args.markdown:
        print(generate_markdown(report))
        return 0
        
    for item in fixes:
        print("FIX: " + item)
        
    all_passed = True
    print("Discovery Diagnostics Summary:")
    for k, v in report.items():
        print(f"[{v['status']}] {k.replace('_', ' ').title()}: {v['hint']}")
        if v["status"] == "FAIL":
            all_passed = False
            
    if not all_passed and not args.fix:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
    
