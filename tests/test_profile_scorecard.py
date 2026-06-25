import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Import the Scorecard class from scripts.profile_scorecard
# We add scripts to path so we can import it easily
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from profile_scorecard import Scorecard


class TestProfileScorecard(unittest.TestCase):
    def test_perfect_score(self):
        """Test scorecard returns 100.0/100.0 for a perfect profile configuration."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create required manifest
            distribution_content = """
name: test-profile
version: 1.0.0
description: "A perfect test profile"
env_requires:
  - name: API_KEY
    description: "Your api key"
"""
            (root / "distribution.yaml").write_text(distribution_content, encoding="utf-8")

            # Create required documentation files
            (root / "README.md").write_text(
                "# Test Profile\nTo install, run: `hermes profile install github.com/test/test-profile`",
                encoding="utf-8"
            )
            (root / "SOUL.md").write_text("# Soul of the Agent", encoding="utf-8")
            (root / "AGENTS.md").write_text("# Instructions for AI Agents", encoding="utf-8")

            # Create configuration and optional files
            (root / "config.yaml").write_text("model: gemini-2.5", encoding="utf-8")
            (root / ".env.EXAMPLE").write_text("API_KEY=your_key_here\n", encoding="utf-8")
            (root / "mcp.json").write_text("{}", encoding="utf-8")

            # Run checks
            scorecard = Scorecard(root)
            scorecard.run_checks()

            self.assertEqual(scorecard.get_total_score(), 100.0)
            self.assertEqual(scorecard.get_max_score(), 100.0)

            # Check categories exist
            self.assertIn("Manifest Integrity", scorecard.scores)
            self.assertIn("Documentation", scorecard.scores)
            self.assertIn("Security & Privacy", scorecard.scores)
            self.assertIn("Configuration & Extendability", scorecard.scores)

    def test_missing_manifest_and_docs(self):
        """Test scorecard checks when distribution.yaml and required docs are missing."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            scorecard = Scorecard(root)
            scorecard.run_checks()

            # distribution.yaml missing means 0 in Manifest Integrity
            self.assertEqual(scorecard.scores.get("Manifest Integrity", 0.0), 0.0)
            # README, SOUL, AGENTS missing means 0 in Documentation
            self.assertEqual(scorecard.scores.get("Documentation", 0.0), 0.0)
            # No forbidden files or secrets means 20 in Security
            self.assertEqual(scorecard.scores.get("Security & Privacy", 0.0), 20.0)
            # config.yaml, .env.EXAMPLE missing means 10 in Config (mcp and skills not present default to pass)
            self.assertEqual(scorecard.scores.get("Configuration & Extendability", 0.0), 10.0)

            self.assertEqual(scorecard.get_total_score(), 30.0)

    def test_invalid_manifest_fields(self):
        """Test handling of invalid name (not kebab-case) and invalid version (not semver)."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            distribution_content = """
name: test_profile_invalid
version: v1.0
description: ""
"""
            (root / "distribution.yaml").write_text(distribution_content, encoding="utf-8")
            (root / "README.md").write_text("# Test Profile", encoding="utf-8")

            scorecard = Scorecard(root)
            scorecard.run_checks()

            # Check that kebab-case name check failed (0 points)
            # Check that semver check failed (0 points)
            # Check that missing description failed (0 points)
            manifest_details = scorecard.details["Manifest Integrity"]
            has_kebab_error = any("Name is lowercase kebab-case (0.0/" in d for d in manifest_details)
            has_semver_error = any("Version matches semantic versioning format (0.0/" in d for d in manifest_details)
            has_description_error = any("has required field: description (0.0/" in d for d in manifest_details)

            self.assertTrue(has_kebab_error)
            self.assertTrue(has_semver_error)
            self.assertTrue(has_description_error)

    def test_security_violation_forbidden_files(self):
        """Test that committing forbidden files (like .env) reduces the security score."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create a forbidden file (.env)
            (root / ".env").write_text("SECRET=mysecret", encoding="utf-8")

            scorecard = Scorecard(root)
            scorecard.run_checks()

            security_details = scorecard.details["Security & Privacy"]
            self.assertEqual(scorecard.scores.get("Security & Privacy", 0.0), 10.0) # Deducted 10 points
            has_forbidden_error = any("Forbidden/user-owned runtime files found:" in d for d in security_details)
            self.assertTrue(has_forbidden_error)

    def test_security_violation_secrets(self):
        """Test that committing plain-text secrets reduces the security score."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create a file with a secret (GitHub token pattern)
            (root / "secrets.txt").write_text("token = " + "ghp_" + "abc123XYZabc123XYZabc", encoding="utf-8")

            scorecard = Scorecard(root)
            scorecard.run_checks()

            self.assertEqual(scorecard.scores.get("Security & Privacy", 0.0), 10.0) # Deducted 10 points
            security_details = scorecard.details["Security & Privacy"]
            has_secret_error = any("Potential secret pattern found in:" in d for d in security_details)
            self.assertTrue(has_secret_error)

    def test_report_formats(self):
        """Test report serialization formats (JSON, Markdown, and Text)."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scorecard = Scorecard(root)
            scorecard.run_checks()

            # JSON
            js = scorecard.to_json()
            data = json.loads(js)
            self.assertIn("score", data)
            self.assertIn("categories", data)

            # Markdown
            md = scorecard.to_markdown()
            self.assertIn("# Hermes Profile Quality Scorecard", md)
            self.assertIn("## Score by Category", md)

            # Text
            txt = scorecard.to_text()
            self.assertIn("HERMES PROFILE QUALITY SCORECARD", txt)


if __name__ == "__main__":
    unittest.main()
