#!/usr/bin/env python3
"""Tests for the profile quality scorecard."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scorecard import run_scorecard, Scorecard  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestScorecardPass(unittest.TestCase):
    """Fixtures that should pass all checks."""

    @classmethod
    def setUpClass(cls):
        cls.root = FIXTURES / "pass-profile"
        cls.scorecard = run_scorecard(cls.root)

    def test_passes(self):
        self.assertTrue(self.scorecard.passed())

    def test_no_failures(self):
        self.assertEqual(self.scorecard.summary.get("fail", 0), 0)

    def test_manifest_fields_pass(self):
        checks = {c["name"]: c for c in self.scorecard.checks}
        self.assertEqual(checks["manifest:name"]["status"], "pass")
        self.assertEqual(checks["manifest:version"]["status"], "pass")
        self.assertEqual(checks["manifest:description"]["status"], "pass")

    def test_readme_install_pass(self):
        checks = {c["name"]: c for c in self.scorecard.checks}
        self.assertEqual(checks["readme:install_command"]["status"], "pass")

    def test_license_pass(self):
        checks = {c["name"]: c for c in self.scorecard.checks}
        self.assertEqual(checks["license:exists"]["status"], "pass")

    def test_changelog_pass(self):
        checks = {c["name"]: c for c in self.scorecard.checks}
        self.assertEqual(checks["changelog:version_entry"]["status"], "pass")

    def test_github_topics_pass(self):
        checks = {c["name"]: c for c in self.scorecard.checks}
        self.assertEqual(checks["github:topics"]["status"], "pass")

    def test_json_output(self):
        data = self.scorecard.to_dict()
        self.assertIn("distribution", data)
        self.assertIn("version", data)
        self.assertIn("summary", data)
        self.assertIn("checks", data)
        self.assertIsInstance(data["checks"], list)

    def test_json_serializable(self):
        data = self.scorecard.to_dict()
        json.dumps(data)  # should not raise


class TestScorecardWarn(unittest.TestCase):
    """Fixtures that should produce warnings but no failures."""

    @classmethod
    def setUpClass(cls):
        cls.root = FIXTURES / "warn-profile"
        cls.scorecard = run_scorecard(cls.root)

    def test_no_failures(self):
        self.assertEqual(self.scorecard.summary.get("fail", 0), 0)

    def test_has_warnings(self):
        self.assertGreater(self.scorecard.summary.get("warn", 0), 0)

    def test_missing_install_warn(self):
        checks = {c["name"]: c for c in self.scorecard.checks}
        self.assertEqual(checks["readme:install_command"]["status"], "warn")

    def test_no_github_topics_warn(self):
        checks = {c["name"]: c for c in self.scorecard.checks}
        self.assertEqual(checks["github:topics"]["status"], "warn")

    def test_non_semver_version_warn(self):
        checks = {c["name"]: c for c in self.scorecard.checks}
        self.assertEqual(checks["manifest:version_format"]["status"], "warn")


class TestScorecardFail(unittest.TestCase):
    """Fixtures that should produce failures."""

    @classmethod
    def setUpClass(cls):
        cls.root = FIXTURES / "fail-profile"
        cls.scorecard = run_scorecard(cls.root)

    def test_has_failures(self):
        self.assertGreater(self.scorecard.summary.get("fail", 0), 0)

    def test_not_passed(self):
        self.assertFalse(self.scorecard.passed())

    def test_missing_env_in_example_fail(self):
        checks = {c["name"]: c for c in self.scorecard.checks}
        self.assertEqual(checks["env:declared_in_example"]["status"], "fail")

    def test_missing_license_warn(self):
        checks = {c["name"]: c for c in self.scorecard.checks}
        self.assertEqual(checks["license:exists"]["status"], "warn")

    def test_missing_security_warn(self):
        checks = {c["name"]: c for c in self.scorecard.checks}
        self.assertEqual(checks["security:policy"]["status"], "warn")


class TestScorecardCLI(unittest.TestCase):
    """Test CLI entry point behavior."""

    def test_terminal_output(self):
        from scorecard import format_terminal
        s = Scorecard(distribution="test", version="1.0.0", timestamp="2026-01-01T00:00:00Z")
        output = format_terminal(s)
        self.assertIn("Profile Scorecard", output)

    def test_markdown_output(self):
        from scorecard import format_markdown
        s = Scorecard(distribution="test", version="1.0.0", timestamp="2026-01-01T00:00:00Z")
        output = format_markdown(s)
        self.assertIn("Profile Scorecard", output)
        self.assertIn("## Summary", output)

    def test_json_output(self):
        from scorecard import format_terminal
        s = Scorecard(distribution="test", version="1.0.0", timestamp="2026-01-01T00:00:00Z")
        data = s.to_dict()
        self.assertEqual(data["distribution"], "test")
        self.assertEqual(data["version"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
