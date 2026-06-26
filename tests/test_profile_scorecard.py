import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "profile_scorecard.py"
FIXTURES = ROOT / "tests" / "fixtures" / "scorecard"


def run_scorecard(profile: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(profile), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


class ProfileScorecardTests(unittest.TestCase):
    def test_complete_profile_outputs_deterministic_json_and_exits_zero(self):
        result = run_scorecard(FIXTURES / "complete", "--json")

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        data = json.loads(result.stdout)
        self.assertEqual(list(data.keys()), ["profile", "summary", "checks"])
        self.assertEqual(data["summary"]["hard_failures"], 0)
        self.assertEqual(data["summary"]["advisory_warnings"], 0)
        self.assertGreaterEqual(data["summary"]["score"], 90)
        self.assertEqual([check["id"] for check in data["checks"]], sorted(check["id"] for check in data["checks"]))

    def test_advisory_warnings_do_not_fail_process(self):
        result = run_scorecard(FIXTURES / "advisory-warnings", "--json")

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        data = json.loads(result.stdout)
        self.assertEqual(data["summary"]["hard_failures"], 0)
        self.assertGreater(data["summary"]["advisory_warnings"], 0)
        warning_ids = {check["id"] for check in data["checks"] if check["status"] == "warn"}
        self.assertIn("license.present", warning_ids)
        self.assertIn("readme.install_command", warning_ids)

    def test_hard_failures_exit_nonzero_and_include_validator_details(self):
        result = run_scorecard(FIXTURES / "hard-failure-missing-env-doc", "--json")

        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        data = json.loads(result.stdout)
        self.assertGreater(data["summary"]["hard_failures"], 0)
        failed = {check["id"]: check for check in data["checks"] if check["status"] == "fail"}
        self.assertIn("validator.required", failed)
        self.assertIn("REQUIRED_TOKEN", "\n".join(failed["validator.required"]["details"]))

    def test_runtime_file_is_a_hard_failure_but_docs_cache_policy_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "profile"
            shutil.copytree(FIXTURES / "complete", profile)
            (profile / "docs").mkdir()
            (profile / "docs" / "cache-policy.md").write_text("# Cache policy\n", encoding="utf-8")
            ok = run_scorecard(profile, "--json")
            self.assertEqual(ok.returncode, 0, ok.stderr + ok.stdout)

            shutil.copytree(FIXTURES / "runtime-file" / "_runtime_cache", profile / "cache")
            bad = run_scorecard(profile, "--json")
            self.assertEqual(bad.returncode, 1, bad.stderr + bad.stdout)
            data = json.loads(bad.stdout)
            failed_details = "\n".join(
                detail
                for check in data["checks"] if check["status"] == "fail"
                for detail in check["details"]
            )
            self.assertIn("cache", failed_details)
            self.assertNotIn("docs/cache-policy.md", failed_details)

    def test_markdown_output_is_pr_comment_ready(self):
        result = run_scorecard(FIXTURES / "advisory-warnings", "--markdown")

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("## Hermes profile quality scorecard", result.stdout)
        self.assertIn("Advisory warnings", result.stdout)
        self.assertIn("readme.install_command", result.stdout)

    def test_invalid_yaml_is_reported_as_hard_failure(self):
        result = run_scorecard(FIXTURES / "invalid-yaml", "--json")

        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        data = json.loads(result.stdout)
        self.assertGreater(data["summary"]["hard_failures"], 0)
        self.assertIn("Invalid YAML", "\n".join(
            detail
            for check in data["checks"] if check["status"] == "fail"
            for detail in check["details"]
        ))


if __name__ == "__main__":
    unittest.main()
