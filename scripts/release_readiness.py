import subprocess
import os

def run_checks():
    report = []
    report.append("## 🚀 Release Readiness Smoke Report\n")
    report.append("| Check | Status | Notes |")
    report.append("| :--- | :--- | :--- |")
    
    
    try:
        diff = subprocess.check_output(["git", "diff", "--name-only", "origin/main"]).decode("utf-8")
        if "distribution.yaml" in diff:
            report.append("| Version Bump | ✅ Passed | distribution.yaml has been updated. |")
        else:
            report.append("| Version Bump | ❌ Failed | distribution.yaml was not changed compared to main. |")
    except Exception as e:
        report.append(f"| Version Bump | ⚠️ Warning | Could not run git diff ({str(e)}). |")

    
    if os.path.exists("CHANGELOG.md"):
        report.append("| Changelog Presence | ✅ Passed | CHANGELOG.md exists. |")
    else:
        report.append("| Changelog Presence | ❌ Failed | CHANGELOG.md is missing. |")

    # 
    print("\n".join(report))

if __name__ == "__main__":
    run_checks()
  
