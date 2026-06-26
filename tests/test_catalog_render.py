"""Fixture-backed tests for catalog submission generators."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "catalog"


class CatalogRenderTests(unittest.TestCase):
    def run_renderer(self, fmt: str) -> str:
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/render_catalog_entry.py",
                ".",
                "--source-url",
                "https://github.com/codegraphtheory/hermes-profile-template",
                "--format",
                fmt,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        return proc.stdout

    def test_markdown_contains_install_and_source(self):
        actual = self.run_renderer("markdown")
        self.assertIn("hermes profile install", actual)
        self.assertIn("codegraphtheory/hermes-profile-template", actual)

    def test_yaml_contains_required_fields(self):
        actual = self.run_renderer("yaml")
        self.assertIn("name: hermes-profile-template", actual)
        self.assertIn("install:", actual)
        self.assertIn("source_url:", actual)

    def test_all_formats_render(self):
        for fmt in ("markdown", "yaml", "readme-line", "pr-body"):
            output = self.run_renderer(fmt)
            self.assertTrue(output.strip(), f"empty output for format={fmt}")


if __name__ == "__main__":
    unittest.main()
