import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path to allow importing scorecard
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import scorecard


class TestProfileScorecard(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the test workspace
        self.test_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.test_dir.name)
        
    def tearDown(self):
        # Clean up temporary directory
        self.test_dir.cleanup()

    def create_minimal_valid_structure(self):
        """Helper to create a minimal passing structure."""
        # Required files
        (self.root / "SOUL.md").write_text("Mission description", encoding="utf-8")
        (self.root / "README.md").write_text(
            "Install: `hermes profile install` \nSmoke test: `make smoke`", encoding="utf-8"
        )
        (self.root / "AGENTS.md").write_text("Agent rules", encoding="utf-8")
        (self.root / "config.yaml").write_text("model: default", encoding="utf-8")
        (self.root / ".env.EXAMPLE").write_text("API_KEY=\nDATABASE_URL=", encoding="utf-8")
        
        # Manifest
        (self.root / "distribution.yaml").write_text(
            "name: test-profile\nversion: 0.1.0\ndescription: A test profile\n", encoding="utf-8"
        )
        
        # License
        (self.root / "LICENSE").write_text("MIT License", encoding="utf-8")
        
        # GitHub topics
        (self.root / "github-repo-metadata.yaml").write_text("topics:\n  - hermes-agent\n", encoding="utf-8")
        
        # Changelog
        (self.root / "CHANGELOG.md").write_text("## 0.1.0\n- Initial release", encoding="utf-8")
        
        # Create clean scripts dir
        os.makedirs(self.root / "scripts", exist_ok=True)
        (self.root / "scripts" / "helper.py").write_text("print('hello')", encoding="utf-8")

    def test_perfect_scorecard_passes(self):
        """Test a pristine profile distribution gets a score of 100 and overall PASS."""
        self.create_minimal_valid_structure()
        res = scorecard.run_scorecard(self.root)
        
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["score"], 100)
        self.assertEqual(res["passed_count"], 12)
        self.assertEqual(res["failed_count"], 0)
        self.assertEqual(res["warning_count"], 0)

    def test_advisory_warning_only(self):
        """Test that advisory warnings (e.g. missing LICENSE, missing docs) deduct points but PASS."""
        self.create_minimal_valid_structure()
        # Remove LICENSE file and github topics file to trigger warnings
        os.remove(self.root / "LICENSE")
        os.remove(self.root / "github-repo-metadata.yaml")
        
        res = scorecard.run_scorecard(self.root)
        
        # Scorecard should still pass but with a reduced score
        self.assertEqual(res["status"], "PASS")
        self.assertTrue(res["score"] < 100)
        self.assertEqual(res["warning_count"], 2)
        self.assertEqual(res["failed_count"], 0)

    def test_critical_failure_exit_code(self):
        """Test that a critical failure (e.g. missing SOUL.md) yields FAIL status."""
        self.create_minimal_valid_structure()
        # Remove required file SOUL.md
        os.remove(self.root / "SOUL.md")
        
        res = scorecard.run_scorecard(self.root)
        
        self.assertEqual(res["status"], "FAIL")
        self.assertEqual(res["failed_count"], 1)
        self.assertTrue(res["score"] < 100)

    def test_malformed_manifest(self):
        """Test that a malformed manifest (invalid YAML) yields FAIL status."""
        self.create_minimal_valid_structure()
        # Write invalid YAML to manifest
        (self.root / "distribution.yaml").write_text("name: : : : invalid", encoding="utf-8")
        
        res = scorecard.run_scorecard(self.root)
        
        self.assertEqual(res["status"], "FAIL")
        # Manifest field failure should occur
        manifest_check = next(c for c in res["checks"] if c["id"] == "manifest-fields")
        self.assertEqual(manifest_check["status"], "FAIL")

    def test_skill_frontmatter_errors(self):
        """Test skill markdown frontmatter parsing validation."""
        self.create_minimal_valid_structure()
        skills_dir = self.root / "skills" / "test_skill"
        os.makedirs(skills_dir, exist_ok=True)
        
        # Write malformed skill frontmatter (missing closing marker)
        (skills_dir / "SKILL.md").write_text("---\nname: Test Skill\nDescription: Missing closing", encoding="utf-8")
        
        res = scorecard.run_scorecard(self.root)
        self.assertEqual(res["status"], "FAIL")
        
        # Now fix frontmatter format but omit name/description
        (skills_dir / "SKILL.md").write_text("---\nauthor: Saitama\n---\nContent", encoding="utf-8")
        res = scorecard.run_scorecard(self.root)
        # Missing fields should only warn (advisory), so overall status remains PASS
        self.assertEqual(res["status"], "PASS")
        skill_check = next(c for c in res["checks"] if c["id"] == "skill-frontmatter")
        self.assertEqual(skill_check["status"], "WARN")

    def test_json_and_markdown_output(self):
        """Test json and markdown output flags in CLI mode."""
        self.create_minimal_valid_structure()
        
        # Test JSON CLI output
        with patch("sys.argv", ["scorecard.py", str(self.root), "--json"]):
            out = StringIO()
            with patch("sys.stdout", out):
                try:
                    scorecard.main()
                except SystemExit as exc:
                    self.assertEqual(exc.code, 0)
            
            data = json.loads(out.getvalue())
            self.assertEqual(data["status"], "PASS")
            self.assertEqual(data["score"], 100)
            
        # Test Markdown CLI output
        with patch("sys.argv", ["scorecard.py", str(self.root), "--markdown"]):
            out = StringIO()
            with patch("sys.stdout", out):
                try:
                    scorecard.main()
                except SystemExit as exc:
                    self.assertEqual(exc.code, 0)
            
            md_content = out.getvalue()
            self.assertIn("# Hermes Profile Quality Scorecard", md_content)
            self.assertIn("## Checklist Details", md_content)


if __name__ == "__main__":
    unittest.main()
