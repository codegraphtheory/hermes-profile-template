from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.profile_scorecard import analyze, to_json, to_markdown


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "scorecard"


class ProfileScorecardTests(unittest.TestCase):
    def test_complete_profile_scores_without_failures(self) -> None:
        scorecard = analyze(FIXTURES / "complete")

        self.assertEqual(scorecard.hard_failures, 0)
        self.assertGreaterEqual(scorecard.score, 85)

    def test_missing_manifest_field_is_hard_failure(self) -> None:
        scorecard = analyze(FIXTURES / "missing-manifest-field")

        self.assertGreater(scorecard.hard_failures, 0)
        self.assertIn("manifest-fields", [item.name for item in scorecard.checks if item.status == "fail"])

    def test_missing_install_command_is_warning_only(self) -> None:
        scorecard = analyze(FIXTURES / "missing-install")

        self.assertEqual(scorecard.hard_failures, 0)
        self.assertIn("readme-install", [item.name for item in scorecard.checks if item.status == "warning"])

    def test_missing_env_documentation_is_hard_failure(self) -> None:
        scorecard = analyze(FIXTURES / "missing-env-doc")

        self.assertGreater(scorecard.hard_failures, 0)
        self.assertIn("env-example", [item.name for item in scorecard.checks if item.status == "fail"])

    def test_json_and_markdown_outputs_are_stable(self) -> None:
        scorecard = analyze(FIXTURES / "complete")

        data = json.loads(to_json(scorecard))
        self.assertEqual(data["score"], scorecard.score)
        markdown = to_markdown(scorecard)
        self.assertIn("| Check | Status | Points | Detail | Remediation |", markdown)


if __name__ == "__main__":
    unittest.main()
