#!/usr/bin/env python3
"""List and explore profile examples - #12 bounty 0.25 SOL"""

import os, json, sys, glob

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")

def list_examples():
    if not os.path.exists(EXAMPLES_DIR):
        print("No examples directory found")
        return []
    
    examples = []
    for item in os.listdir(EXAMPLES_DIR):
        item_path = os.path.join(EXAMPLES_DIR, item)
        if os.path.isdir(item_path) and not item.startswith("."):
            readme = os.path.join(item_path, "README.md")
            desc = ""
            if os.path.exists(readme):
                with open(readme) as f:
                    first_line = f.readline().strip().lstrip("# ")
                    desc = first_line
            examples.append({"name": item, "description": desc})
    
    return sorted(examples, key=lambda x: x["name"])

def show_example(name):
    path = os.path.join(EXAMPLES_DIR, name)
    if not os.path.exists(path):
        print("Example '%s' not found" % name)
        return
    
    print("\n=== %s ===\n" % name)
    readme = os.path.join(path, "README.md")
    if os.path.exists(readme):
        with open(readme) as f:
            print(f.read())

def generate_from_template(name, output_dir):
    src = os.path.join(EXAMPLES_DIR, name)
    if not os.path.exists(src):
        print("Template '%s' not found" % name)
        return False
    
    os.makedirs(output_dir, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        dest = os.path.join(output_dir, rel)
        os.makedirs(dest, exist_ok=True)
        for f in files:
            with open(os.path.join(root, f)) as fh:
                content = fh.read()
            with open(os.path.join(dest, f), "w") as fh:
                fh.write(content)
    print("Generated profile in %s" % output_dir)
    return True

if __name__ == "__main__":
    examples = list_examples()
    print("# Profile Examples Gallery\n")
    print("| Name | Description |")
    print("|------|-------------|")
    for ex in examples:
        print("| %s | %s |" % (ex["name"], ex["description"]))
    
    if "--show" in sys.argv:
        idx = sys.argv.index("--show")
        if idx + 1 < len(sys.argv):
            show_example(sys.argv[idx + 1])
    
    if "--generate" in sys.argv:
        idx = sys.argv.index("--generate")
        if idx + 1 < len(sys.argv):
            name = sys.argv[idx + 1]
            output = "./generated-profile"
            if "--output" in sys.argv:
                oidx = sys.argv.index("--output")
                if oidx + 1 < len(sys.argv):
                    output = sys.argv[oidx + 1]
            generate_from_template(name, output)
