from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.discovery_optimizer import analyze_repository, to_json, to_markdown


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "discovery"


class DiscoveryOptimizerTests(unittest.TestCase):
    def test_complete_profile_passes_core_discovery_checks(self) -> None:
        report = analyze_repository(FIXTURES / "complete-profile")

        self.assertGreaterEqual(report.score, 85)
        statuses = {finding.check: finding.status for finding in report.findings}
        self.assertEqual(statuses["description"], "pass")
        self.assertEqual(statuses["install-command"], "pass")
        self.assertEqual(statuses["license-security"], "pass")

    def test_sparse_profile_reports_actionable_recommendations(self) -> None:
        report = analyze_repository(FIXTURES / "sparse-profile")

        self.assertLess(report.score, 70)
        recommendations = "\n".join(finding.recommendation for finding in report.findings)
        self.assertIn("LICENSE", recommendations)
        self.assertIn("hermes profile install", recommendations)

    def test_serialized_reports_are_stable(self) -> None:
        report = analyze_repository(FIXTURES / "sparse-profile")

        data = json.loads(to_json(report))
        self.assertEqual(data["score"], report.score)
        markdown = to_markdown(report)
        self.assertIn("| Check | Status | Recommendation |", markdown)


if __name__ == "__main__":
    unittest.main()
