from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.render_catalog_entry import build_profile, render


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "catalog"


class RenderCatalogEntryTests(unittest.TestCase):
    def test_markdown_entry_includes_install_use_case_and_rules(self) -> None:
        profile = build_profile(FIXTURES / "complete-profile", "https://github.com/acme/security-reviewer")

        output = render(profile, "markdown")

        self.assertIn("Security Reviewer", output)
        self.assertIn("hermes profile install https://github.com/acme/security-reviewer --alias", output)
        self.assertIn("Follow catalog contribution rules", output)

    def test_yaml_entry_is_catalog_native(self) -> None:
        profile = build_profile(FIXTURES / "complete-profile", "https://github.com/acme/security-reviewer")

        output = render(profile, "yaml")

        self.assertIn("name: security-reviewer", output)
        self.assertIn("source: https://github.com/acme/security-reviewer", output)
        self.assertIn("safety:", output)

    def test_minimal_profile_uses_safe_placeholders(self) -> None:
        profile = build_profile(FIXTURES / "minimal-profile", None)

        output = render(profile, "resource-line")

        self.assertIn("https://github.com/YOUR_ORG/release-helper", output)
        self.assertIn("Follow the target catalog's contribution rules", output)

    def test_all_format_contains_every_section(self) -> None:
        profile = build_profile(FIXTURES / "complete-profile", "https://github.com/acme/security-reviewer")

        output = render(profile, "all")

        self.assertIn("--- markdown ---", output)
        self.assertIn("--- yaml ---", output)
        self.assertIn("--- resource-line ---", output)
        self.assertIn("--- pr-body ---", output)


if __name__ == "__main__":
    unittest.main()
