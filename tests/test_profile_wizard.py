"""Tests for scripts/profile_wizard.py."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from profile_wizard import BUNDLES, CLASSES, build_params, merge_unique, write_params


class TestMergeUnique(unittest.TestCase):
    def test_no_duplicates(self):
        self.assertEqual(merge_unique(["a", "b"], ["b", "c"]), ["a", "b", "c"])

    def test_empty_extra(self):
        self.assertEqual(merge_unique(["a"], []), ["a"])

    def test_empty_base(self):
        self.assertEqual(merge_unique([], ["x", "y"]), ["x", "y"])

    def test_preserves_order(self):
        result = merge_unique(["z", "a"], ["b", "a"])
        self.assertEqual(result, ["z", "a", "b"])


class TestBuildParams(unittest.TestCase):
    def test_all_classes_produce_valid_params(self):
        required_keys = {
            "name", "display_name", "description", "version", "author",
            "toolsets", "env_requires", "principles", "scope",
            "refusals", "output_contract", "github_topics", "template_source",
        }
        for cls in CLASSES:
            with self.subTest(cls=cls):
                params = build_params(cls, [])
                self.assertTrue(required_keys.issubset(params.keys()))

    def test_name_override(self):
        params = build_params("engineer", [], name="my-reviewer")
        self.assertEqual(params["name"], "my-reviewer")

    def test_display_name_override(self):
        params = build_params("engineer", [], display_name="My Reviewer")
        self.assertEqual(params["display_name"], "My Reviewer")

    def test_description_override(self):
        params = build_params("engineer", [], description="Custom description.")
        self.assertEqual(params["description"], "Custom description.")

    def test_version_override(self):
        params = build_params("engineer", [], version="1.2.3")
        self.assertEqual(params["version"], "1.2.3")

    def test_author_override(self):
        params = build_params("researcher", [], author="Alice")
        self.assertEqual(params["author"], "Alice")

    def test_env_requires_passed_through(self):
        params = build_params("engineer", [], env_requires=["GITHUB_TOKEN", "MY_KEY"])
        self.assertEqual(params["env_requires"], ["GITHUB_TOKEN", "MY_KEY"])

    def test_extra_topics_merged(self):
        params = build_params("engineer", [], extra_topics=["rust", "wasm"])
        self.assertIn("rust", params["github_topics"])
        self.assertIn("wasm", params["github_topics"])

    def test_unknown_class_raises(self):
        with self.assertRaises(ValueError):
            build_params("unicorn", [])

    def test_unknown_bundle_raises(self):
        with self.assertRaises(ValueError):
            build_params("engineer", ["unicorn-bundle"])

    def test_template_source_always_present(self):
        params = build_params("operator", [])
        self.assertIn("url", params["template_source"])
        self.assertIn("relationship", params["template_source"])

    def test_hermes_url_in_template_source(self):
        params = build_params("data", [])
        self.assertIn("hermes-profile-template", params["template_source"]["url"])


class TestBundles(unittest.TestCase):
    def test_open_source_bundle_adds_github_toolset(self):
        params = build_params("researcher", ["open-source"])
        self.assertIn("github", params["toolsets"])

    def test_database_bundle_adds_scope(self):
        params = build_params("engineer", ["database"])
        combined = " ".join(params["scope"])
        self.assertIn("production data", combined)

    def test_api_integration_bundle_adds_web(self):
        params = build_params("data", ["api-integration"])
        self.assertIn("web", params["toolsets"])

    def test_multiple_bundles_merged(self):
        params = build_params("engineer", ["open-source", "safe-demo"])
        self.assertIn("github", params["toolsets"])
        self.assertIn("open-source", params["github_topics"])
        self.assertIn("demo", params["github_topics"])

    def test_all_bundles_produce_valid_output(self):
        for bundle in BUNDLES:
            with self.subTest(bundle=bundle):
                params = build_params("operator", [bundle])
                self.assertIsInstance(params["toolsets"], list)


class TestWriteParams(unittest.TestCase):
    def _sample_params(self) -> dict:
        return build_params("engineer", [])

    def test_writes_yaml_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "params.yaml"
            write_params(out, self._sample_params(), force=False)
            self.assertTrue(out.exists())
            data = yaml.safe_load(out.read_text())
            self.assertEqual(data["name"], "engineering-reviewer")

    def test_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "params.yaml"
            out.write_text("existing")
            with self.assertRaises(SystemExit):
                write_params(out, self._sample_params(), force=False)

    def test_force_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "params.yaml"
            out.write_text("old content")
            write_params(out, self._sample_params(), force=True)
            data = yaml.safe_load(out.read_text())
            self.assertIn("name", data)

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "nested" / "deep" / "params.yaml"
            write_params(out, self._sample_params(), force=False)
            self.assertTrue(out.exists())

    def test_output_is_valid_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "params.yaml"
            write_params(out, self._sample_params(), force=False)
            parsed = yaml.safe_load(out.read_text())
            self.assertIsInstance(parsed, dict)


class TestCLI(unittest.TestCase):
    def _run(self, args: list[str]) -> int:
        with patch("sys.argv", ["profile_wizard.py"] + args):
            from profile_wizard import main
            return main()

    def test_noninteractive_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "params.yaml"
            rc = self._run(["--class", "engineer", "--output", str(out), "--force"])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())

    def test_all_classes_noninteractive(self):
        for cls in CLASSES:
            with self.subTest(cls=cls):
                with tempfile.TemporaryDirectory() as tmp:
                    out = Path(tmp) / "params.yaml"
                    rc = self._run(["--class", cls, "--output", str(out), "--force"])
                    self.assertEqual(rc, 0)

    def test_name_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "params.yaml"
            self._run(["--class", "engineer", "--name", "custom-slug", "--output", str(out), "--force"])
            data = yaml.safe_load(out.read_text())
            self.assertEqual(data["name"], "custom-slug")

    def test_bundle_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "params.yaml"
            self._run(["--class", "engineer", "--bundle", "open-source", "--output", str(out), "--force"])
            data = yaml.safe_load(out.read_text())
            self.assertIn("github", data["toolsets"])

    def test_env_requires_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "params.yaml"
            self._run([
                "--class", "researcher",
                "--env-requires", "OPENAI_API_KEY",
                "--env-requires", "GITHUB_TOKEN",
                "--output", str(out), "--force",
            ])
            data = yaml.safe_load(out.read_text())
            self.assertIn("OPENAI_API_KEY", data["env_requires"])
            self.assertIn("GITHUB_TOKEN", data["env_requires"])

    def test_topic_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "params.yaml"
            self._run(["--class", "data", "--topic", "rust", "--output", str(out), "--force"])
            data = yaml.safe_load(out.read_text())
            self.assertIn("rust", data["github_topics"])

    def test_generate_requires_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "params.yaml"
            rc = self._run(["--class", "engineer", "--generate", "--output", str(out), "--force"])
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
