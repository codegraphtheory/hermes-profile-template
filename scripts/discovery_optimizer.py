#!/usr/bin/env python3
"""README Discovery Optimizer - #18 bounty 0.25 SOL"""

import os, re, json, sys

REQUIRED_TOPICS = ["hermes-profile", "generated", "template"]

def optimize_readme(readme_path="README.md"):
    if not os.path.exists(readme_path):
        print("README.md not found")
        return False
    
    with open(readme_path) as f:
        content = f.read()
    
    changes = []
    
    # 1. Check description line (first non-frontmatter line)
    lines = content.split("\n")
    desc_line = None
    for i, line in enumerate(lines):
        if line.startswith("# ") and len(line) > 3:
            desc_line = line
            break
    
    if desc_line:
        print("Title: %s" % desc_line)
    
    # 2. Check for install command
    install_patterns = [
        r"pip install",
        r"npm install",
        r"cargo install",
        r"brew install",
        r"git clone",
    ]
    has_install = any(re.search(p, content) for p in install_patterns)
    if not has_install:
        print("WARNING: No install command found in README")
        changes.append("Add install command")
    
    # 3. Check for Topics block in README
    topic_patterns = ["topic", "topics", "keywords"]
    has_topics = any(p in content.lower() for p in topic_patterns)
    if not has_topics:
        print("WARNING: No topics/keywords section in README")
        changes.append("Add topics/keywords section")
    
    # 4. Check for badges
    badge_patterns = ["shield.io", "github.com/.../actions", "github.com/.../workflows"]
    has_badges = any(p in content for p in ["shield.io", "github.com/"])
    if not has_badges:
        print("WARNING: No badges found in README")
        changes.append("Add CI/badge links")
    
    # 5. Check metadata consistency
    metadata_checks = [
        ("description", "description" in content.lower()),
        ("license", "license" in content.lower()),
        ("installation", "install" in content.lower()),
        ("usage", "usage" in content.lower()),
        ("contributing", "contribut" in content.lower()),
    ]
    
    print("\n## Metadata Coverage")
    for name, present in metadata_checks:
        print("- %s: %s" % (name, "PASS" if present else "MISSING"))
        if not present:
            changes.append("Add %s section" % name)
    
    # 6. Generate optimized metadata block
    print("\n## Optimized Topics Suggestion")
    suggested_topics = ["hermes-profile", "profile-generator", "github-profile", "readme", "template"]
    print("Suggested GitHub topics: %s" % ", ".join(suggested_topics))
    
    print("\n## Optimization Summary")
    print("Checks passed: %d/5" % (5 - len([c for c in ["install", "topics", "badges", "description", "license"] 
                                               if c not in content.lower()])))
    if changes:
        print("Suggested improvements:")
        for c in changes:
            print("- %s" % c)
    
    return len(changes) == 0

if __name__ == "__main__":
    optimize_readme()
