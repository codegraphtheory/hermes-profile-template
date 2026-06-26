#!/usr/bin/env python3
"""Interactive Profile Design Wizard - #13 bounty 0.25 SOL"""

import os, sys, json, datetime

QUESTIONS = [
    {
        "id": "profile_type",
        "question": "What type of profile are you creating?",
        "options": ["Developer", "Open Source Maintainer", "Data Scientist", "DevOps Engineer", "Technical Writer"]
    },
    {
        "id": "experience_level",
        "question": "What is your experience level?",
        "options": ["Junior (1-2 years)", "Mid-level (3-5 years)", "Senior (6-10 years)", "Lead/Principal (10+ years)"]
    },
    {
        "id": "include_projects",
        "question": "Include project showcase?",
        "options": ["Yes, top 3 projects", "Yes, top 5 projects", "Yes, all projects", "No, skip projects"]
    },
    {
        "id": "include_skills",
        "question": "Include skills section?",
        "options": ["Yes, with rating bars", "Yes, simple list", "No, skip skills"]
    },
    {
        "id": "theme",
        "question": "Preferred color theme?",
        "options": ["Dark (default)", "Light", "Auto (system preference)"]
    }
]

def run_wizard():
    """Run the interactive wizard and return answers."""
    print("=" * 50)
    print("🤖 Hermes Profile Design Wizard")
    print("=" * 50)
    print()
    
    answers = {}
    
    for q in QUESTIONS:
        print("Q: %s" % q["question"])
        for i, opt in enumerate(q["options"], 1):
            print("  %d. %s" % (i, opt))
        
        while True:
            try:
                choice = input("Choice (1-%d): " % len(q["options"]))
                idx = int(choice) - 1
                if 0 <= idx < len(q["options"]):
                    answers[q["id"]] = q["options"][idx]
                    break
            except:
                pass
            print("Invalid choice, try again.")
        
        print()
    
    return answers

def generate_config(answers, output_path="hermes-config.json"):
    """Generate configuration from wizard answers."""
    config = {
        "profile": {
            "type": answers.get("profile_type", "Developer").lower().replace(" ", "-"),
            "experience": answers.get("experience_level", "Mid-level"),
            "include_projects": "projects" in answers.get("include_projects", "Yes, top 3 projects").lower(),
            "include_skills": "skills" in answers.get("include_skills", "Yes, simple list").lower(),
            "project_count": 3,
            "skills_format": "bars" if "bars" in answers.get("include_skills", "Yes, simple list") else "list",
            "theme": answers.get("theme", "Dark").lower(),
        },
        "generated_at": datetime.datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    # Parse project count
    if "5" in answers.get("include_projects", ""):
        config["profile"]["project_count"] = 5
    elif "all" in answers.get("include_projects", ""):
        config["profile"]["project_count"] = -1  # signal for all
    
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
    
    print("Configuration saved to %s" % output_path)
    return config

def generate_profile(config, output_dir="generated-profile"):
    """Generate profile from config."""
    os.makedirs(output_dir, exist_ok=True)
    
    profile_type = config["profile"]["type"]
    theme = config["profile"]["theme"]
    
    # Generate README.md
    readme = []
    readme.append("# My %s Profile\n" % profile_type.replace("-", " ").title())
    readme.append("Generated with Hermes Profile Template\n")
    readme.append("## About Me")
    readme.append("A %s professional leveraging technology to solve problems." % 
                  config["profile"]["experience"])
    readme.append("")
    
    if config["profile"]["include_skills"]:
        readme.append("## Skills")
        readme.append("| Category | Skills |")
        readme.append("|----------|--------|")
        skills_data = {
            "Languages": "Python, JavaScript, TypeScript",
            "Frameworks": "React, Node.js, FastAPI",
            "Tools": "Git, Docker, CI/CD",
        }
        for cat, skills in skills_data.items():
            readme.append("| %s | %s |" % (cat, skills))
        readme.append("")
    
    if config["profile"]["include_projects"]:
        readme.append("## Projects")
        for i in range(min(config["profile"]["project_count"], 5)):
            readme.append("### Project %d" % (i + 1))
            readme.append("A showcase project demonstrating skills and expertise.")
            readme.append("")
    
    with open(os.path.join(output_dir, "README.md"), "w") as f:
        f.write("\n".join(readme))
    
    # Generate distribution.yaml
    dist = {
        "name": profile_type.replace("-", " ").title() + " Profile",
        "version": "1.0.0",
        "description": "A professional profile generated with Hermes",
        "author": "",
        "license": "MIT",
        "generated_by": "hermes-profile-template"
    }
    with open(os.path.join(output_dir, "distribution.yaml"), "w") as f:
        import yaml
        yaml.dump(dist, f)
    
    print("Profile generated in %s/" % output_dir)
    return output_dir

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Interactive Profile Design Wizard")
    parser.add_argument("--interactive", action="store_true", help="Run interactive wizard")
    parser.add_argument("--config", help="Path to config file (skip wizard)")
    parser.add_argument("--output", default="generated-profile", help="Output directory")
    
    args = parser.parse_args()
    
    if args.config:
        with open(args.config) as f:
            config = json.load(f)
    else:
        answers = run_wizard()
        config = generate_config(answers)
    
    generate_profile(config, args.output)
