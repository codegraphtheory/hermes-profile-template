"""Fixture-backed tests for catalog submission rendering."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://github.com/codegraphtheory/hermes-profile-template"


class CatalogRenderTests(unittest.TestCase):
    def run_renderer(self, fmt: str) -> str:
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/render_catalog_entry.py",
                ".",
                "--source-url",
                SOURCE_URL,
                "--format",
                fmt,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertTrue(proc.stdout.strip(), f"empty output for format={fmt}")
        return proc.stdout

    def test_markdown_contains_install_and_source(self):
        actual = self.run_renderer("markdown")
        self.assertIn("hermes profile install", actual)
        self.assertIn("codegraphtheory/hermes-profile-template", actual)

    def test_yaml_contains_required_fields(self):
        actual = self.run_renderer("yaml")
        data = yaml.safe_load(actual)
        self.assertEqual(data["name"], "hermes-profile-template")
        self.assertEqual(data["source_url"], SOURCE_URL)
        self.assertIn("hermes profile install", data["install"])

    def test_pr_body_and_all_formats_render(self):
        self.assertIn("Profile catalog submission", self.run_renderer("pr-body"))
        all_output = self.run_renderer("all")
        for heading in ("## markdown", "## yaml", "## pr-body"):
            self.assertIn(heading, all_output)


if __name__ == "__main__":
    unittest.main()
