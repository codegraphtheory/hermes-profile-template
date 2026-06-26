#!/usr/bin/env python3
"""Tests for scripts/readme_discovery_optimizer.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from readme_discovery_optimizer import run_checks, apply_fix, Level  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "readme_discovery"
GOOD = FIXTURES / "good"
MINIMAL = FIXTURES / "minimal"


def findings_by_name(profile_dir: Path) -> dict[str, Level]:
    rpt = run_checks(profile_dir)
    return {f.name: f.level for f in rpt.findings}


class TestGoodFixture:
    def test_readme_exists(self):
        assert findings_by_name(GOOD)["readme-exists"] == "pass"

    def test_install_command_near_top(self):
        assert findings_by_name(GOOD)["install-command-near-top"] == "pass"

    def test_github_topics(self):
        assert findings_by_name(GOOD)["github-topics"] == "pass"

    def test_template_lineage(self):
        assert findings_by_name(GOOD)["template-lineage"] == "pass"

    def test_validation_command(self):
        assert findings_by_name(GOOD)["validation-command"] == "pass"

    def test_license_file(self):
        assert findings_by_name(GOOD)["license-file"] == "pass"

    def test_social_preview(self):
        assert findings_by_name(GOOD)["social-preview"] == "pass"

    def test_no_required_failures(self):
        rpt = run_checks(GOOD)
        assert not rpt.has_required_failures


class TestMinimalFixture:
    def test_readme_exists(self):
        assert findings_by_name(MINIMAL)["readme-exists"] == "pass"

    def test_install_missing(self):
        assert findings_by_name(MINIMAL)["install-command-near-top"] == "required"

    def test_no_github_topics(self):
        assert findings_by_name(MINIMAL)["github-topics"] == "warn"

    def test_no_template_lineage(self):
        assert findings_by_name(MINIMAL)["template-lineage"] == "warn"

    def test_no_license(self):
        assert findings_by_name(MINIMAL)["license-file"] == "required"

    def test_has_required_failures(self):
        rpt = run_checks(MINIMAL)
        assert rpt.has_required_failures


class TestFixCommand:
    def test_fix_appends_lineage(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Test\n\nHello world.\n\nhermes profile install foo/bar\n")
        dist = tmp_path / "distribution.yaml"
        dist.write_text("name: test\nversion: 0.1.0\ndescription: A test profile.\nauthor: Me\nlicense: MIT\n")
        (tmp_path / "LICENSE").touch()

        actions = apply_fix(tmp_path, run_checks(tmp_path))
        assert any("lineage" in a.lower() for a in actions)
        assert "hermes-profile-template" in readme.read_text()

    def test_fix_adds_missing_topics(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Test\n\nhermes profile install foo/bar\n\nhermes-profile-template\n")
        dist = tmp_path / "distribution.yaml"
        dist.write_text("name: test\nversion: 0.1.0\ndescription: A test profile.\nauthor: Me\nlicense: MIT\n")
        meta = tmp_path / "github-repo-metadata.yaml"
        meta.write_text("topics:\n  - python\n")
        (tmp_path / "LICENSE").touch()

        actions = apply_fix(tmp_path, run_checks(tmp_path))
        assert any("topics" in a.lower() for a in actions)

        import yaml
        updated = yaml.safe_load(meta.read_text()) or {}
        for topic in ["hermes-agent", "ai-agents", "agent-profile"]:
            assert topic in updated.get("topics", [])

    def test_fix_idempotent(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Test\n\nhermes profile install foo/bar\n\nhermes-profile-template\n")
        dist = tmp_path / "distribution.yaml"
        dist.write_text("name: test\nversion: 0.1.0\ndescription: A test profile.\nauthor: Me\nlicense: MIT\n")
        meta = tmp_path / "github-repo-metadata.yaml"
        meta.write_text("topics:\n  - hermes-agent\n  - ai-agents\n  - agent-profile\n")
        (tmp_path / "LICENSE").touch()

        rpt = run_checks(tmp_path)
        actions1 = apply_fix(tmp_path, rpt)
        rpt2 = run_checks(tmp_path)
        actions2 = apply_fix(tmp_path, rpt2)
        assert actions2 == [], f"Fix was not idempotent: {actions2}"
