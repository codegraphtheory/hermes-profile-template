"""Tests for scripts/profile_scorecard.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORECARD = [sys.executable, str(ROOT / "scripts" / "profile_scorecard.py")]
FIXTURES = Path(__file__).parent / "fixtures" / "scorecard"


def run(args: list[str], fixture: str = "good") -> subprocess.CompletedProcess:
    return subprocess.run(
        SCORECARD + [str(FIXTURES / fixture)] + args,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def run_in(path: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        SCORECARD + [str(path)] + args,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


class TestGoodFixture(unittest.TestCase):
    """Full-featured fixture — all required and optional files present."""

    def test_exit_zero(self):
        r = run([])
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def test_text_shows_pass(self):
        r = run([])
        self.assertIn("[PASS]", r.stdout)
        self.assertNotIn("[FAIL]", r.stdout)

    def test_json_schema(self):
        r = run(["--json"])
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertIn("score", data)
        self.assertIn("points", data)
        self.assertIn("max_points", data)
        self.assertIn("hard_failures", data)
        self.assertIn("items", data)
        self.assertFalse(data["hard_failures"])

    def test_json_score_above_threshold(self):
        r = run(["--json"])
        data = json.loads(r.stdout)
        self.assertGreater(data["score"], 50)

    def test_markdown_output(self):
        r = run(["--markdown"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("# Hermes profile scorecard", r.stdout)
        self.assertIn("PASS", r.stdout)

    def test_threshold_pass(self):
        r = run(["--threshold", "1"])
        self.assertEqual(r.returncode, 0)


class TestMinimalFixture(unittest.TestCase):
    """Minimal fixture — distribution.yaml + README only; optional docs absent."""

    def test_exit_zero_no_hard_fails(self):
        r = run([], fixture="minimal")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def test_warns_on_missing_optional_docs(self):
        r = run([], fixture="minimal")
        self.assertIn("[WARN]", r.stdout)

    def test_json_no_hard_failures(self):
        r = run(["--json"], fixture="minimal")
        data = json.loads(r.stdout)
        self.assertFalse(data["hard_failures"])

    def test_threshold_fail_on_low_score(self):
        r = run(["--threshold", "99"], fixture="minimal")
        self.assertEqual(r.returncode, 1)

    def test_markdown_shows_warn(self):
        r = run(["--markdown"], fixture="minimal")
        self.assertIn("WARN", r.stdout)


class TestNoManifest(unittest.TestCase):
    """No distribution.yaml — hard failure expected."""

    def test_exit_nonzero(self):
        r = run([], fixture="no_manifest")
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_json_hard_failures_true(self):
        r = run(["--json"], fixture="no_manifest")
        data = json.loads(r.stdout)
        self.assertTrue(data["hard_failures"])

    def test_fail_label_in_text(self):
        r = run([], fixture="no_manifest")
        self.assertIn("[FAIL]", r.stdout)

    def test_markdown_notes_hard_failure(self):
        r = run(["--markdown"], fixture="no_manifest")
        self.assertIn("FAIL", r.stdout)


class TestSecretFixture(unittest.TestCase):
    """Dynamically created fixture with a token-like pattern — secrets hard failure."""

    def _make_secret_repo(self) -> tempfile.TemporaryDirectory:
        tmp = tempfile.TemporaryDirectory()
        p = Path(tmp.name)
        (p / "distribution.yaml").write_text(
            "name: secret-profile\nversion: 0.1.0\ndescription: "
            "'Fixture for secret detection test.'\nhermes_requires: '>=0.12.0'\n"
        )
        # intentional fake token pattern — NOT a real credential
        (p / "config.yaml").write_text("api_key: ghp_" + "A" * 40 + "\n")
        return tmp

    def test_exit_nonzero(self):
        with self._make_secret_repo() as d:
            r = run_in(Path(d), [])
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_json_hard_failures_true(self):
        with self._make_secret_repo() as d:
            r = run_in(Path(d), ["--json"])
        data = json.loads(r.stdout)
        self.assertTrue(data["hard_failures"])

    def test_fail_label_in_text(self):
        with self._make_secret_repo() as d:
            r = run_in(Path(d), [])
        self.assertIn("[FAIL]", r.stdout)


class TestLiveRepo(unittest.TestCase):
    """Scorecard on the actual template repo should score ≥ 80%."""

    def test_live_repo_json(self):
        r = subprocess.run(
            SCORECARD + [".", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertGreaterEqual(data["score"], 80)


if __name__ == "__main__":
    unittest.main()
