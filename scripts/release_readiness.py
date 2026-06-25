#!/usr/bin/env python3
"""Run release readiness workflow checks and generate a Markdown report."""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python3 -m pip install pyyaml") from exc

# Release relevant prefixes (reused from check_release_version.py)
RELEASE_RELEVANT_PREFIXES = (
    "SOUL.md",
    "AGENTS.md",
    "README.md",
    "config.yaml",
    "distribution.yaml",
    ".env.EXAMPLE",
    "mcp.json",
    "skills/",
    "templates/",
    "scripts/",
    ".github/workflows/",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "github-repo-metadata.yaml",
    "requirements.txt",
    "Makefile",
    "docs/",
)

IGNORED_PATHS = {
    "CHANGELOG.md",
}

# Forbidden directories and files (reused from validate_profile.py)
USER_OWNED = {
    ".env",
    "auth.json",
    "state.db",
    "state.db-shm",
    "state.db-wal",
    "memories",
    "sessions",
    "logs",
    "workspace",
    "plans",
    "local",
    "cache",
}

FORBIDDEN_DIR_NAMES = USER_OWNED | {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    "dist",
    "build",
    "hook-sessions",
}

FORBIDDEN_FILE_NAMES = {
    ".coverage",
    "coverage.xml",
}

FORBIDDEN_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".pyd",
)

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)


def read_current_version(root: Path) -> str:
    data = yaml.safe_load((root / "distribution.yaml").read_text(encoding="utf-8")) or {}
    version = str(data.get("version") or "").strip()
    if not version:
        raise ValueError("distribution.yaml missing version")
    return version


def read_base_version(root: Path, base: str) -> str | None:
    proc = run_git(["show", f"{base}:distribution.yaml"], root)
    if proc.returncode != 0:
        return None
    try:
        data = yaml.safe_load(proc.stdout) or {}
        return str(data.get("version") or "").strip() or None
    except Exception:
        return None


def changed_files(root: Path, base: str) -> list[str] | None:
    proc = run_git(["diff", "--name-only", f"{base}...HEAD"], root)
    if proc.returncode != 0:
        proc = run_git(["diff", "--name-only", base, "HEAD"], root)
    if proc.returncode != 0:
        return None
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def is_release_relevant(path: str) -> bool:
    if path in IGNORED_PATHS:
        return False
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in RELEASE_RELEVANT_PREFIXES)


def iter_validation_paths(root: Path) -> list[Path]:
    if (root / ".git").exists():
        proc = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=root,
            text=False,
            capture_output=True,
        )
        if proc.returncode == 0:
            rels = [item.decode("utf-8") for item in proc.stdout.split(b"\0") if item]
            return [root / rel for rel in rels]
    return [path for path in root.rglob("*") if path.is_file()]


def check_version_discipline(root: Path, base: str, strict: bool) -> dict[str, str]:
    files = changed_files(root, base)
    if files is None:
        message = f"Could not compare against base ref {base}"
        if strict:
            return {
                "name": "Version Discipline",
                "status": "FAIL",
                "description": message,
                "hint": f"Ensure base ref '{base}' is fetched and exists locally. Try running 'git fetch origin'."
            }
        else:
            return {
                "name": "Version Discipline",
                "status": "SKIPPED",
                "description": message,
                "hint": "Run with a valid base ref to enforce version checking."
            }

    relevant = [path for path in files if is_release_relevant(path)]
    if not relevant:
        return {
            "name": "Version Discipline",
            "status": "PASS",
            "description": "No release-relevant changes detected.",
            "hint": ""
        }

    try:
        current_version = read_current_version(root)
    except Exception as exc:
        return {
            "name": "Version Discipline",
            "status": "FAIL",
            "description": f"Failed to read current version: {exc}",
            "hint": "Check that distribution.yaml exists and has a valid version field."
        }

    base_version = read_base_version(root, base)
    if base_version is None:
        message = f"Could not read distribution.yaml from base ref {base}"
        if strict:
            return {
                "name": "Version Discipline",
                "status": "FAIL",
                "description": message,
                "hint": "Ensure distribution.yaml exists in the base branch and contains a valid version."
            }
        else:
            return {
                "name": "Version Discipline",
                "status": "SKIPPED",
                "description": message,
                "hint": "Base branch distribution.yaml is missing or invalid. Check skipped."
            }

    if current_version == base_version:
        return {
            "name": "Version Discipline",
            "status": "FAIL",
            "description": f"distribution.yaml version did not change from {base_version}.",
            "hint": f"Increment the 'version' field in distribution.yaml (currently {current_version})."
        }

    return {
        "name": "Version Discipline",
        "status": "PASS",
        "description": f"Version bumped from {base_version} to {current_version}.",
        "hint": ""
    }


def check_changelog_heading(root: Path) -> dict[str, str]:
    try:
        current_version = read_current_version(root)
    except Exception as exc:
        return {
            "name": "Changelog Heading",
            "status": "FAIL",
            "description": f"Cannot determine current version: {exc}",
            "hint": "Fix distribution.yaml version first."
        }

    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.exists():
        return {
            "name": "Changelog Heading",
            "status": "FAIL",
            "description": "CHANGELOG.md does not exist.",
            "hint": "Create CHANGELOG.md and add release notes."
        }

    text = changelog_path.read_text(encoding="utf-8")
    pattern = rf"^##\s+\[?{re.escape(current_version)}\]?\b"
    if re.search(pattern, text, flags=re.MULTILINE) is not None:
        return {
            "name": "Changelog Heading",
            "status": "PASS",
            "description": f"Found matching entry '## {current_version}' in CHANGELOG.md.",
            "hint": ""
        }

    return {
        "name": "Changelog Heading",
        "status": "FAIL",
        "description": f"Missing entry for version {current_version} in CHANGELOG.md.",
        "hint": f"Add a heading like '## {current_version}' to CHANGELOG.md and document the changes."
    }


def check_profile_validation(root: Path) -> dict[str, str]:
    validator_script = root / "scripts" / "validate_profile.py"
    if not validator_script.exists():
        return {
            "name": "Profile Validation",
            "status": "FAIL",
            "description": "scripts/validate_profile.py does not exist.",
            "hint": "Restore scripts/validate_profile.py in the repository."
        }

    proc = subprocess.run([sys.executable, str(validator_script), str(root)], capture_output=True, text=True)
    if proc.returncode == 0:
        return {
            "name": "Profile Validation",
            "status": "PASS",
            "description": "Profile validation checks passed.",
            "hint": ""
        }

    # Extract errors starting with ERROR:
    errors = [line.strip() for line in proc.stdout.splitlines() if line.startswith("ERROR:")]
    if not errors:
        errors = [proc.stderr.strip() or proc.stdout.strip()]

    return {
        "name": "Profile Validation",
        "status": "FAIL",
        "description": f"Validation failed with {len(errors)} error(s).",
        "hint": "<br>".join(errors) or "Run 'make validate' to see errors."
    }


def check_runtime_files(root: Path) -> dict[str, str]:
    seen_dirs: set[Path] = set()
    forbidden: list[str] = []

    for path in iter_validation_paths(root):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(root)
        for parent in rel.parents:
            if str(parent) == "." or parent in seen_dirs:
                continue
            seen_dirs.add(parent)
            if parent.name in FORBIDDEN_DIR_NAMES:
                forbidden.append(f"Directory '{parent}'")
        if path.name in FORBIDDEN_FILE_NAMES:
            forbidden.append(f"File '{rel}'")
        if path.name in USER_OWNED:
            forbidden.append(f"User-owned file '{rel}'")
        if path.name.endswith(FORBIDDEN_SUFFIXES):
            forbidden.append(f"Cache file '{rel}'")

    if forbidden:
        forbidden = sorted(list(set(forbidden)))
        return {
            "name": "No Runtime Files",
            "status": "FAIL",
            "description": f"Found forbidden runtime files or caches in repository: {', '.join(forbidden[:5])}" + ("..." if len(forbidden) > 5 else ""),
            "hint": "Delete these files or add them to your .gitignore/exclude rules so they are not tracked or committed."
        }

    return {
        "name": "No Runtime Files",
        "status": "PASS",
        "description": "No runtime files, user-owned files, or caches detected.",
        "hint": ""
    }


def check_secrets(root: Path) -> dict[str, str]:
    skip_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__"}
    flagged_files: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file() or any(part in skip_dirs for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                flagged_files.append(str(path.relative_to(root)))
                break

    if flagged_files:
        return {
            "name": "No Secrets",
            "status": "FAIL",
            "description": f"Possible credentials or secrets detected in: {', '.join(flagged_files[:5])}" + ("..." if len(flagged_files) > 5 else ""),
            "hint": "Remove any private keys, passwords, API tokens, or secrets from files in the repository."
        }

    return {
        "name": "No Secrets",
        "status": "PASS",
        "description": "No hardcoded secrets or credentials detected.",
        "hint": ""
    }


def check_generator_smoke(root: Path) -> dict[str, str]:
    gen_script = root / "scripts" / "generate_profile.py"
    params_file = root / "templates" / "profile.params.yaml"

    if not gen_script.exists():
        return {
            "name": "Generator Smoke",
            "status": "FAIL",
            "description": "scripts/generate_profile.py is missing.",
            "hint": "Restore generate_profile.py script."
        }
    if not params_file.exists():
        return {
            "name": "Generator Smoke",
            "status": "FAIL",
            "description": "templates/profile.params.yaml is missing.",
            "hint": "Restore profile.params.yaml starter parameters."
        }

    with tempfile.TemporaryDirectory(prefix="hermes-gen-") as tmpdir:
        output_path = Path(tmpdir) / "generated"

        # Run generator
        gen_proc = subprocess.run([
            sys.executable,
            str(gen_script),
            "--params", str(params_file),
            "--output", str(output_path)
        ], capture_output=True, text=True)

        if gen_proc.returncode != 0:
            return {
                "name": "Generator Smoke",
                "status": "FAIL",
                "description": "Profile generation failed.",
                "hint": f"Error from generate_profile.py:<br>{gen_proc.stderr or gen_proc.stdout}"
            }

        # Run validate_profile.py on generated output
        val_script = output_path / "scripts" / "validate_profile.py"
        if not val_script.exists():
            return {
                "name": "Generator Smoke",
                "status": "FAIL",
                "description": "Generated profile does not contain validate_profile.py.",
                "hint": "Ensure generate_profile.py includes validation script in target."
            }

        val_proc = subprocess.run([
            sys.executable,
            str(val_script),
            str(output_path)
        ], capture_output=True, text=True)

        if val_proc.returncode != 0:
            return {
                "name": "Generator Smoke",
                "status": "FAIL",
                "description": "Generated profile validation failed.",
                "hint": f"Error validating generated profile:<br>{val_proc.stderr or val_proc.stdout}"
            }

    return {
        "name": "Generator Smoke",
        "status": "PASS",
        "description": "Generated profile compiled, output generated, and validated successfully.",
        "hint": ""
    }


def check_install_smoke(root: Path) -> dict[str, str]:
    hermes_cli = shutil.which("hermes")
    if not hermes_cli:
        return {
            "name": "Install Smoke",
            "status": "SKIPPED",
            "description": "Hermes CLI ('hermes') not found in PATH.",
            "hint": "Install Hermes CLI or add it to PATH to enable this check."
        }

    with tempfile.TemporaryDirectory(prefix="hermes-home-") as tmpdir:
        env = os.environ.copy()
        env["HERMES_HOME"] = tmpdir

        # Run hermes profile install
        install_proc = subprocess.run([
            hermes_cli, "profile", "install", str(root),
            "--name", "profile-smoke", "--yes"
        ], env=env, capture_output=True, text=True)

        if install_proc.returncode != 0:
            return {
                "name": "Install Smoke",
                "status": "FAIL",
                "description": "Hermes profile install command failed.",
                "hint": f"Output from hermes command:<br>{install_proc.stderr or install_proc.stdout}"
            }

        # Verify key files are present in the installed destination
        installed_profile = Path(tmpdir) / "profiles" / "profile-smoke"
        required_installed_files = [
            "SOUL.md",
            "distribution.yaml",
            "scripts/generate_profile.py",
            "templates/profile.params.yaml"
        ]

        missing = []
        for rel_file in required_installed_files:
            if not (installed_profile / rel_file).is_file():
                missing.append(rel_file)

        if missing:
            return {
                "name": "Install Smoke",
                "status": "FAIL",
                "description": f"Installed profile is missing files: {', '.join(missing)}.",
                "hint": "Check distribution_owned section in distribution.yaml and ensure these files are listed."
            }

    return {
        "name": "Install Smoke",
        "status": "PASS",
        "description": "Profile successfully installed and key files validated.",
        "hint": ""
    }


def check_install_docs(root: Path) -> dict[str, str]:
    repo_identifier = None
    proc = run_git(["remote", "get-url", "origin"], root)
    if proc.returncode == 0:
        url = proc.stdout.strip()
        match = re.search(r"(?:github\.com[:/])([^/]+/[^/.]+)(?:\.git)?", url)
        if match:
            repo_identifier = f"github.com/{match.group(1)}"

    if not repo_identifier:
        meta_path = root / "github-repo-metadata.yaml"
        if meta_path.exists():
            try:
                meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
                homepage = meta.get("homepage", "")
                if homepage:
                    match = re.search(r"(?:github\.com[:/])([^/]+/[^/.]+)(?:\.git)?", homepage)
                    if match:
                        repo_identifier = f"github.com/{match.group(1)}"
            except Exception:
                pass

    # Gather markdown files to scan
    md_files = [root / "README.md"]
    docs_dir = root / "docs"
    if docs_dir.exists():
        md_files.extend(docs_dir.rglob("*.md"))

    def search_docs(pattern: str) -> bool:
        regex = re.compile(pattern, re.IGNORECASE)
        for md_file in md_files:
            if md_file.is_file():
                try:
                    content = md_file.read_text(encoding="utf-8")
                    if regex.search(content):
                        return True
                except Exception:
                    pass
        return False

    if repo_identifier:
        pattern = rf"hermes\s+profile\s+install\s+(?:https?://)?{re.escape(repo_identifier)}"
        if search_docs(pattern):
            return {
                "name": "Install Documentation",
                "status": "PASS",
                "description": f"Found installation command matching '{repo_identifier}' in documentation.",
                "hint": ""
            }
        else:
            return {
                "name": "Install Documentation",
                "status": "FAIL",
                "description": f"Installation command for '{repo_identifier}' was not found in docs.",
                "hint": f"Add the command `hermes profile install {repo_identifier}` to README.md or other documentation."
            }
    else:
        pattern = r"hermes\s+profile\s+install"
        if search_docs(pattern):
            return {
                "name": "Install Documentation",
                "status": "PASS",
                "description": "Found a generic installation command in documentation, but could not determine git remote.",
                "hint": ""
            }
        else:
            return {
                "name": "Install Documentation",
                "status": "FAIL",
                "description": "No installation command 'hermes profile install' found in documentation.",
                "hint": "Document the installation instructions using `hermes profile install <repository>` in README.md."
            }


def generate_markdown_report(results: list[dict[str, str]], base: str, current_version: str) -> str:
    overall_status = "PASS"
    for r in results:
        if r["status"] == "FAIL":
            overall_status = "FAIL"
            break

    status_emoji = "🟢" if overall_status == "PASS" else "🔴"

    lines = [
        f"# Release Readiness Report",
        f"",
        f"- **Overall Status**: {status_emoji} **{overall_status}**",
        f"- **Current Version**: `{current_version}`",
        f"- **Base Ref**: `{base}`",
        f"",
        f"## Checklist",
        f"",
        f"| Check | Status | Description | Remediation Hint |",
        f"| :--- | :--- | :--- | :--- |",
    ]

    for r in results:
        status_str = r["status"]
        if status_str == "PASS":
            status_cell = "🟢 PASS"
        elif status_str == "FAIL":
            status_cell = "🔴 FAIL"
        elif status_str == "SKIPPED":
            status_cell = "⚪ SKIPPED"
        else:
            status_cell = f"🟡 {status_str}"

        # Clean hint for table markdown formatting
        hint_cell = r["hint"].replace("\n", "<br>")
        lines.append(f"| {r['name']} | {status_cell} | {r['description']} | {hint_cell} |")

    lines.append("")

    if overall_status == "FAIL":
        lines.append("### ⚠️ Action Required")
        lines.append("Please resolve the failed checks highlighted above before publishing or tagging the release.")
        lines.append("")
    else:
        lines.append("### 🎉 Ready for Release")
        lines.append("All checks passed or skipped. This profile template distribution is ready to be tagged and released!")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check release readiness and generate a Markdown report")
    parser.add_argument("--base", default="origin/main", help="Git base ref to compare against")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--strict", action="store_true", help="Fail instead of skip when base ref is unavailable")
    parser.add_argument("--output", help="Write Markdown report to this file")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    try:
        current_version = read_current_version(root)
    except Exception as exc:
        print(f"ERROR: Cannot determine current version from distribution.yaml: {exc}")
        return 1

    results = []

    # Run checks
    results.append(check_version_discipline(root, args.base, args.strict))
    results.append(check_changelog_heading(root))
    results.append(check_profile_validation(root))
    results.append(check_runtime_files(root))
    results.append(check_secrets(root))
    results.append(check_generator_smoke(root))
    results.append(check_install_smoke(root))
    results.append(check_install_docs(root))

    report = generate_markdown_report(results, args.base, current_version)

    print(report)

    if args.output:
        try:
            Path(args.output).write_text(report, encoding="utf-8")
            print(f"Report successfully written to {args.output}")
        except Exception as exc:
            print(f"ERROR: Failed to write report to {args.output}: {exc}")

    # Determine exit code
    for r in results:
        if r["status"] == "FAIL":
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
