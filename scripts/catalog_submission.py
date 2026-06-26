#!/usr/bin/env python3
"""Catalog Submission Generator - #17 bounty 0.25 SOL"""

import os, json, sys, datetime, re

def generate_submission(profile_path="."):
    """Generate catalog submission metadata for a profile."""
    
    metadata = {}
    
    # Read profile info
    readme_path = os.path.join(profile_path, "README.md")
    dist_path = os.path.join(profile_path, "distribution.yaml")
    
    if os.path.exists(readme_path):
        with open(readme_path) as f:
            content = f.read()
        # Extract name
        m = re.search(r"^# (.+)", content)
        metadata["name"] = m.group(1).strip() if m else os.path.basename(os.path.abspath(profile_path))
        # Extract description
        lines = content.split("\n")
        for line in lines[1:5]:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("!"):
                metadata["description"] = line[:200]
                break
    
    if os.path.exists(dist_path):
        with open(dist_path) as f:
            import yaml
            try:
                dist = yaml.safe_load(f)
                metadata["version"] = dist.get("version", "0.1.0")
                metadata["author"] = dist.get("author", "")
                metadata["license"] = dist.get("license", "MIT")
            except:
                metadata["version"] = "0.1.0"
    
    metadata["generated_at"] = datetime.datetime.now().isoformat()
    
    return metadata

def generate_awesome_list_entry(metadata):
    """Generate an awesome-list compatible entry."""
    name = metadata.get("name", "My Profile")
    desc = metadata.get("description", "A generated profile")
    url = metadata.get("url", "https://github.com/username/repo")
    return "- [%s](%s) - %s" % (name, url, desc)

def generate_topics(metadata):
    """Generate GitHub topics for the profile repo."""
    topics = ["hermes-profile", "generated-profile", "profile"]
    desc = metadata.get("description", "").lower()
    if "developer" in desc: topics.append("developer")
    if "portfolio" in desc: topics.append("portfolio")
    if "open-source" in desc or "maintainer" in desc: topics.append("open-source")
    return list(set(topics))

if __name__ == "__main__":
    profile_path = sys.argv[1] if len(sys.argv) > 1 else "."
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    metadata = generate_submission(profile_path)
    
    report = []
    report.append("# Catalog Submission\n")
    report.append("## Profile Metadata")
    report.append("```json")
    report.append(json.dumps(metadata, indent=2))
    report.append("```\n")
    report.append("## Awesome List Entry")
    report.append(generate_awesome_list_entry(metadata))
    report.append("\n")
    report.append("## Suggested GitHub Topics")
    report.append(", ".join(generate_topics(metadata)))
    report.append("\n")
    report.append("## Submission Quality Checklist")
    checks = [
        ("Name present", "name" in metadata),
        ("Description present", "description" in metadata),
        ("Version defined", "version" in metadata),
        ("License specified", "license" in metadata),
    ]
    for check, ok in checks:
        report.append("- [%s] %s" % ("x" if ok else " ", check))
    
    output = "\n".join(report)
    print(output)
    
    if output_path:
        with open(output_path, "w") as f:
            f.write(output)
