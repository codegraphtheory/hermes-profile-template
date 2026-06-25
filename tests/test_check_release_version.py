from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_release_version


class ReleaseVersionCheckTest(unittest.TestCase):
    def test_examples_are_release_relevant_distribution_content(self) -> None:
        self.assertTrue(check_release_version.is_release_relevant("examples/gallery.json"))
        self.assertTrue(check_release_version.is_release_relevant("examples/security-reviewer/README.md"))


if __name__ == "__main__":
    unittest.main()
