import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class CommunityToolsTest(unittest.TestCase):
    def test_profile_wizard_noninteractive_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            params = Path(tmp) / "profile.params.yaml"
            proc = subprocess.run(
                [sys.executable, "scripts/profile_wizard.py", "--class", "engineer", "--bundle", "open-source", "--output", str(params)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            data = yaml.safe_load(params.read_text())
            self.assertEqual(data["name"], "engineering-reviewer")
            self.assertIn("github", data["toolsets"])

    def test_scorecard_json(self):
        proc = subprocess.run(
            [sys.executable, "scripts/profile_scorecard.py", ".", "--format", "json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        data = json.loads(proc.stdout)
        self.assertGreaterEqual(data["score"], 80)

    def test_catalog_renderer(self):
        proc = subprocess.run(
            [sys.executable, "scripts/render_catalog_entry.py", ".", "--source-url", "https://github.com/codegraphtheory/hermes-profile-template", "--format", "yaml"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        data = yaml.safe_load(proc.stdout)
        self.assertEqual(data["name"], "hermes-profile-template")
        self.assertIn("hermes profile install", data["install"])


if __name__ == "__main__":
    unittest.main()
