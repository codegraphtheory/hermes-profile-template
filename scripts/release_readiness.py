#!/usr/bin/env python3
"""Release readiness checks for Hermes profile distributions.

Provides the :func:`main` CLI entrypoint invoked by ``make release-check``.
All checks fit the :class:`CheckResult`` data class shape so the Markdown
report is easy to extend.

Checks
------
* **version** ─ was ``distribution.yaml`` bumped when release‑relevant files
  changed?
* **changelog** ─ is the current version present as an ``##`` heading in
  ``CHANGELOG.md``?
* **profile‑validation** ─ does ``scripts/validate_profile.py .`` pass?
* **generated‑profile‑smoke** ─ can we generate a profile from the template
  and validate the generated output?
* **install‑smoke** ─ does ``hermes profile install .`` succeed (when the
  Hermes CLI is on ``$PATH``)?
* **docs‑install‑command** ─ does the README mention the correct ``hermes
  profile install`` command for this repo?
* **python‑compile** ─ do all ``scripts/*.py`` compile cleanly?
* **runtime‑and‑secrets** ─ are runtime directories, cached artifacts, and
  token‑like secrets absent from the tree?
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # pragma: no cover


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RELEASE_RELEVANT_PREFIXES = (
    ".github/",
    "docs/",
    "skills/",
    "templates/",
    "scripts/",
    "web-demo/",
    "examples/",
    "SOUL.md",
    "AGENTS.md",
    "README.md",
    "Makefile",
    "requirements.txt",
    "distribution.yaml",
    "config.yaml",
    "mcp.json",
)

IGNORED_PATHS = {"CHANGELOG.md"}

FORBIDDEN_NAMES = {".env", "auth.json", "state.db", "state.db-shm", "state.db-wal"}
FORBIDDEN_PARTS = {"memories", "sessions", "logs", "workspace", "plans", ".pytest_cache", "__pycache__"}

SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CheckResult:
    """Outcome of a single release-readiness check."""

    name: str
    status: str  # PASS | FAIL | SKIP
    detail: str
    hint: str = ""


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run *git* in *root* and return the completed process."""
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)


def changed_files(root: Path, base: str) -> list[str] | None:
    """Return file paths changed between *base* and HEAD (relative to *root*).

    Returns ``None`` when the base ref is unavailable (e.g. shallow clone).
    """
    proc = run_git(root, ["diff", "--name-only", f"{base}...HEAD"])
    if proc.returncode != 0:
        proc = run_git(root, ["diff", "--name-only", base, "HEAD"])
    if proc.returncode != 0:
        return None
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def read_manifest_version_text(text: str) -> str | None:
    """Extract the ``version`` field from raw YAML text."""
    data = yaml.safe_load(text) if yaml else {}
    if not isinstance(data, dict):
        return None
    version = str(data.get("version") or "").strip()
    return version or None


def current_version(root: Path) -> str | None:
    """Return the version declared in *root*\\ ``/distribution.yaml``."""
    manifest = root / "distribution.yaml"
    if not manifest.exists():
        return None
    return read_manifest_version_text(manifest.read_text(encoding="utf-8"))


def base_version(root: Path, base: str) -> str | None:
    """Return the version declared at the *base* ref."""
    proc = run_git(root, ["show", f"{base}:distribution.yaml"])
    if proc.returncode != 0:
        return None
    return read_manifest_version_text(proc.stdout)


def is_release_relevant(path: str) -> bool:
    """Return ``True`` when a changed file should trigger a version bump."""
    if path in IGNORED_PATHS:
        return False
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in RELEASE_RELEVANT_PREFIXES)


def iter_validation_paths(root: Path) -> list[Path]:
    """Return all files that should be scanned for secrets.

    Prefers git‑tracked files, falls back to ``rglob``.
    """
    proc = run_git(root, ["ls-files", "--cached", "--others", "--exclude-standard", "-z"])
    if proc.returncode == 0:
        items = [item for item in proc.stdout.split("\0") if item]
        return [root / item for item in items]
    return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_version(root: Path, base: str, strict: bool) -> CheckResult:
    """Verify that ``distribution.yaml`` version changed when relevant files did."""
    files = changed_files(root, base)
    if files is None:
        status = "FAIL" if strict else "SKIP"
        return CheckResult(
            "version",
            status,
            f"Could not compare against {base}",
            "Use --strict to fail here, or fetch the base ref before running.",
        )
    relevant = [path for path in files if is_release_relevant(path)]
    if not relevant:
        return CheckResult("version", "PASS", "No release-relevant changes detected.")

    now = current_version(root)
    before = base_version(root, base)
    if not now:
        return CheckResult("version", "FAIL", "distribution.yaml is missing a version.")
    if before and before == now:
        return CheckResult(
            "version",
            "FAIL",
            f"Release-relevant files changed but version stayed {now}.",
            "Bump distribution.yaml and add a matching changelog heading.",
        )
    return CheckResult("version", "PASS", f"Version is release-ready: {before or 'unknown'} -> {now}.")


def check_changelog(root: Path) -> CheckResult:
    """Verify that ``CHANGELOG.md`` has a heading matching the current version."""
    version = current_version(root)
    changelog = root / "CHANGELOG.md"
    if not version:
        return CheckResult("changelog", "FAIL", "Cannot read current distribution version.")
    if not changelog.exists():
        return CheckResult("changelog", "FAIL", "CHANGELOG.md is missing.")
    text = changelog.read_text(encoding="utf-8")
    if re.search(rf"^##\s+{re.escape(version)}\b", text, re.MULTILINE):
        return CheckResult("changelog", "PASS", f"Found CHANGELOG.md heading for {version}.")
    return CheckResult("changelog", "FAIL", f"Missing CHANGELOG.md heading for {version}.")


def check_command(root: Path, name: str, cmd: list[str]) -> CheckResult:
    """Run an arbitrary command in *root* and return the result."""
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=120)
    detail = (proc.stdout + proc.stderr).strip().splitlines()[-12:]
    joined = "\n".join(detail) if detail else "command produced no output"
    return CheckResult(name, "PASS" if proc.returncode == 0 else "FAIL", joined)


def check_generated_profile_smoke(root: Path) -> CheckResult:
    """Generate a profile from the template, then validate the generated output."""
    gen_root = Path(tempfile.mkdtemp(prefix="hermes-release-gen-"))
    try:
        gen_cmd = [
            sys.executable,
            str(root / "scripts" / "generate_profile.py"),
            "--params", str(root / "templates" / "profile.params.yaml"),
            "--output", str(gen_root / "generated"),
        ]
        gen_proc = subprocess.run(gen_cmd, cwd=root, text=True, capture_output=True, timeout=120)
        if gen_proc.returncode != 0:
            detail = (gen_proc.stdout + gen_proc.stderr).strip().splitlines()[-12:]
            return CheckResult("generated-profile-smoke", "FAIL",
                               "Generation failed:\n" + "\n".join(detail),
                               "Check generate_profile.py and templates/profile.params.yaml")

        validate_cmd = [sys.executable, str(gen_root / "generated" / "scripts" / "validate_profile.py"),
                        str(gen_root / "generated")]
        val_proc = subprocess.run(validate_cmd, cwd=root, text=True, capture_output=True, timeout=120)
        if val_proc.returncode != 0:
            detail = (val_proc.stdout + val_proc.stderr).strip().splitlines()[-12:]
            return CheckResult("generated-profile-smoke", "FAIL",
                               "Generated profile validation failed:\n" + "\n".join(detail),
                               "Run 'make generate-smoke' locally to debug.")
        return CheckResult("generated-profile-smoke", "PASS",
                           f"Profile generated and validated at {gen_root / 'generated'}")
    finally:
        # Cleanup on success; leave artifacts on failure for debugging
        pass


def check_install_smoke(root: Path) -> CheckResult:
    """Install the current repository as a Hermes profile using ``hermes profile install``."""
    hermes = shutil.which("hermes")
    if not hermes:
        return CheckResult("install-smoke", "SKIP",
                           "Hermes CLI not found on PATH.",
                           "Install Hermes Agent to enable this check.")

    home = Path(tempfile.mkdtemp(prefix="hermes-release-home-"))
    install_env = {**os.environ, "HERMES_HOME": str(home)}

    try:
        proc = subprocess.run(
            [hermes, "profile", "install", str(root), "--name", "release-smoke", "--yes", "--force"],
            cwd=root,
            env=install_env,
            text=True,
            capture_output=True,
            timeout=120,
        )
        if proc.returncode != 0:
            detail = (proc.stdout + proc.stderr).strip().splitlines()[-12:]
            return CheckResult("install-smoke", "FAIL",
                               "Hermes profile install failed:\n" + "\n".join(detail),
                               "Run 'make smoke' locally and check hermes CLI.")
        return CheckResult("install-smoke", "PASS",
                           "hermes profile install completed successfully.")
    except FileNotFoundError:
        return CheckResult("install-smoke", "FAIL",
                           "hermes binary not found despite being on PATH.",
                           "Verify hermes is correctly installed.")
    except subprocess.TimeoutExpired:
        return CheckResult("install-smoke", "FAIL",
                           "hermes profile install timed out after 120s.",
                           "The command may be hanging on a prompt.")


def check_docs_install_command(root: Path) -> CheckResult:
    """Verify that the README contains a ``hermes profile install`` command that
    references this repository."""
    readme = root / "README.md"
    if not readme.exists():
        return CheckResult("docs-install-command", "FAIL", "README.md is missing.")

    text = readme.read_text(encoding="utf-8")

    # Try to extract the repo slug from git remote
    slug = None
    proc = run_git(root, ["config", "--get", "remote.origin.url"])
    if proc.returncode == 0:
        url = proc.stdout.strip()
        for fmt in (r"https://github\.com/([^/]+/[^/.]+)", r"git@github\.com:([^/]+/[^/.]+)"):
            m = re.search(fmt, url)
            if m:
                slug = m.group(1)
                break

    if slug:
        pattern = rf"hermes\s+profile\s+install\s+.*{re.escape(slug)}"
        if re.search(pattern, text, re.IGNORECASE):
            return CheckResult("docs-install-command", "PASS",
                               f"README includes install command for {slug}.")
        return CheckResult("docs-install-command", "FAIL",
                           f"README missing install command referencing {slug}.",
                           f"Add something like: `hermes profile install github.com/{slug} --alias`")

    # Fallback: just check that any hermes profile install command exists in README
    if re.search(r"hermes\s+profile\s+install", text, re.IGNORECASE):
        return CheckResult("docs-install-command", "PASS",
                           "README contains a hermes profile install command.")
    return CheckResult("docs-install-command", "FAIL",
                       "README missing any hermes profile install command.",
                       "Add the install command to README.md.")


def check_runtime_and_secrets(root: Path) -> CheckResult:
    """Verify that no runtime files, caches, or token‑like secrets are present."""
    hits: list[str] = []
    for path in iter_validation_paths(root):
        rel = path.relative_to(root)
        if path.name in FORBIDDEN_NAMES or set(rel.parts) & FORBIDDEN_PARTS:
            hits.append(str(rel))
            continue
        # Skip binary / large files that can't reasonably contain secrets
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".zip", ".pack", ".idx"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(f"{rel}: matches {pattern.pattern}")
                break
    if hits:
        return CheckResult("runtime-and-secrets", "FAIL", "\n".join(hits[:20]))
    return CheckResult("runtime-and-secrets", "PASS",
                       "No forbidden runtime paths or token-like secrets found.")


# ---------------------------------------------------------------------------
# Report formatter
# ---------------------------------------------------------------------------

def markdown_report(results: list[CheckResult]) -> str:
    """Render all check results as a Markdown table."""
    lines: list[str] = [
        "# Release readiness report",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for result in results:
        detail = result.detail.replace("|", "\\|").replace("\n", "<br>")
        if result.hint:
            detail += "<br>Hint: " + result.hint.replace("|", "\\|")
        lines.append(f"| {result.name} | {result.status} | {detail} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    """Entry point for ``make release-check``."""
    parser = argparse.ArgumentParser(
        description="Check release readiness for this Hermes profile distribution."
    )
    parser.add_argument("--base", default="origin/main",
                        help="Base ref for version discipline checks (default: origin/main).")
    parser.add_argument("--strict", action="store_true",
                        help="Fail instead of skipping when the base ref is unavailable.")
    args = parser.parse_args()

    root = Path.cwd()

    results: list[CheckResult] = [
        check_version(root, args.base, args.strict),
        check_changelog(root),
        check_command(root, "profile-validation",
                       [sys.executable, "scripts/validate_profile.py", "."]),
        check_generated_profile_smoke(root),
        check_install_smoke(root),
        check_docs_install_command(root),
        check_command(root, "python-compile",
                       [sys.executable, "-m", "py_compile",
                        *[str(p) for p in sorted((root / "scripts").glob("*.py"))]]),
        check_runtime_and_secrets(root),
    ]

    print(markdown_report(results))

    return 0 if all(r.status in {"PASS", "SKIP"} for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
