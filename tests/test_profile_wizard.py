import unittest
from pathlib import Path

import yaml  # type: ignore

from scripts.profile_wizard import build_params

FIXTURES = Path("tests/fixtures/wizard")


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


class TestBuildParams(unittest.TestCase):
    def test_engineer_defaults(self):
        classes = _yaml(FIXTURES / "classes.yaml")
        engineer = next(item for item in classes["classes"] if item["slug"] == "engineer")
        params = build_params(engineer, None)
        self.assertEqual(params["name"], "engineering-generalist")
        self.assertIn("terminal", params["toolsets"])

    def test_bundle_extends_toolsets(self):
        classes = _yaml(FIXTURES / "classes.yaml")
        bundles = _yaml(FIXTURES / "bundles.yaml")
        engineer = next(item for item in classes["classes"] if item["slug"] == "engineer")
        bundle = next(item for item in bundles["bundles"] if item["name"] == "Open Forge")
        params = build_params(engineer, bundle)
        self.assertIn("browser", params["toolsets"])
        self.assertIn("terminal", params["toolsets"])

    def test_bundle_overrides_name(self):
        classes = _yaml(FIXTURES / "classes.yaml")
        bundles = _yaml(FIXTURES / "bundles.yaml")
        artisan = next(item for item in classes["classes"] if item["slug"] == "artisan")
        bundle = next(item for item in bundles["bundles"] if item["name"] == "Open Forge")
        params = build_params(artisan, bundle)
        self.assertEqual(params["name"], "open-forge-artisan")

    def test_principle_unique_preservation(self):
        classes = _yaml(FIXTURES / "classes.yaml")
        bundles = _yaml(FIXTURES / "bundles.yaml")
        scout = next(item for item in classes["classes"] if item["slug"] == "scout")
        bundle = next(item for item in bundles["bundles"] if item["name"] == "Bound Scanner")
        params = build_params(scout, bundle)
        self.assertEqual(len(params["principles"]), len(set(params["principles"])))
