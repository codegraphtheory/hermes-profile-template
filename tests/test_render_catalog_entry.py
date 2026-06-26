from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "render_catalog_entry.py"
FIXTURES = REPO / "tests" / "fixtures" / "catalog"
SOURCE_URL = "https://github.com/acme/release-manager"


class RenderCatalogEntryTests(unittest.TestCase):
    def make_profile(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "distribution.yaml").write_text(
            """
name: release-manager
version: 0.1.0
description: Reviews release readiness and changelog discipline for Hermes profile repositories.
author: Example Author
license: MIT
template_source:
  name: codegraphtheory/hermes-profile-template
  url: https://github.com/codegraphtheory/hermes-profile-template
env_requires:
  - name: GITHUB_TOKEN
    required: false
    description: Optional GitHub token for issue and PR lookup.
""".strip()
            + "\n",
            encoding="utf-8",
        )
        (root / "github-repo-metadata.yaml").write_text(
            """
description: Release manager profile
topics:
  - hermes-agent
  - release-management
  - profile-distribution
""".strip()
            + "\n",
            encoding="utf-8",
        )
        return root

    def run_script(self, *args: str) -> str:
        result = subprocess.run(
            ["python3", str(SCRIPT), *args],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout

    def assert_matches_fixture(self, fmt: str) -> None:
        root = self.make_profile()
        out = self.run_script(str(root), "--format", fmt, "--source-url", SOURCE_URL)
        expected = (FIXTURES / f"{fmt}.out").read_text(encoding="utf-8")
        self.assertEqual(out, expected)

    def test_markdown_matches_fixture_and_includes_required_notes(self) -> None:
        self.assert_matches_fixture("markdown")
        expected = (FIXTURES / "markdown.out").read_text(encoding="utf-8")
        self.assertIn("hermes profile install https://github.com/acme/release-manager --alias", expected)
        self.assertIn("Does not include runtime state", expected)
        self.assertIn("target catalog's contribution rules", expected)

    def test_yaml_matches_fixture_and_contains_required_fields(self) -> None:
        self.assert_matches_fixture("yaml")
        expected = (FIXTURES / "yaml.out").read_text(encoding="utf-8")
        self.assertIn("name: release-manager", expected)
        self.assertIn("catalog_submission_note:", expected)
        self.assertIn("env_requires:", expected)

    def test_resource_line_matches_fixture(self) -> None:
        self.assert_matches_fixture("resource-line")

    def test_pr_body_matches_fixture(self) -> None:
        self.assert_matches_fixture("pr-body")


if __name__ == "__main__":
    unittest.main()
