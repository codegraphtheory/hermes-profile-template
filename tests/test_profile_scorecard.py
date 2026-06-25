from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import profile_scorecard


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def make_profile(root: Path, *, readme_install: bool = True, topics: bool = True, env_mismatch: bool = False) -> None:
    env_requires = """
env_requires:
  - name: DEMO_API_KEY
    description: Optional demo key.
    required: false
"""
    write(
        root / "distribution.yaml",
        f"""name: test-profile
version: 0.1.0
description: Test profile for scorecard fixtures.
hermes_requires: ">=0.12.0"
author: Test Author
license: MIT
{env_requires}
""",
    )
    write(root / "SOUL.md", "# Test Profile\n\nMission.")
    write(root / "AGENTS.md", "# Agent Instructions\n\nRun validation.")
    write(root / "config.yaml", "model:\n  default: test\n")
    env_name = "OTHER_KEY" if env_mismatch else "DEMO_API_KEY"
    write(
        root / ".env.EXAMPLE",
        f"""# Optional demo key.
# optional
{env_name}=
""",
    )
    install = "hermes profile install github.com/example/test-profile --alias" if readme_install else ""
    write(
        root / "README.md",
        f"""# Test Profile

{install}

```bash
make validate
make smoke
```
""",
    )
    write(root / "LICENSE", "MIT")
    write(root / "CHANGELOG.md", "# Changelog\n\n## 0.1.0\n\n- Initial fixture.")
    topic_block = """
topics:
  - hermes-agent
  - ai-agents
  - agent-profile
  - profile-distribution
""" if topics else "topics:\n  - python\n"
    write(root / "github-repo-metadata.yaml", f"description: Fixture\nhomepage: ''\n{topic_block}")
    write(root / "scripts" / "smoke_install.sh", "#!/usr/bin/env bash\necho smoke")
    write(
        root / "skills" / "fixture" / "SKILL.md",
        """---
name: fixture
description: Fixture skill.
---

# Fixture
""",
    )


class ProfileScorecardTest(unittest.TestCase):
    def test_complete_profile_passes_without_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_profile(root)
            scorecard = profile_scorecard.build_scorecard(root)
        self.assertEqual(scorecard["summary"]["status"], "pass")
        self.assertEqual(scorecard["summary"]["score"], 100)
        self.assertEqual(scorecard["summary"]["hard_failures"], 0)
        self.assertEqual(scorecard["summary"]["warnings"], 0)
        self.assertEqual(profile_scorecard.exit_code(scorecard), 0)

    def test_warning_only_scorecard_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_profile(root, readme_install=False)
            scorecard = profile_scorecard.build_scorecard(root)
        self.assertEqual(scorecard["summary"]["status"], "pass")
        self.assertLess(scorecard["summary"]["score"], 100)
        self.assertEqual(scorecard["summary"]["hard_failures"], 0)
        self.assertGreaterEqual(scorecard["summary"]["warnings"], 1)
        self.assertEqual(profile_scorecard.exit_code(scorecard), 0)

    def test_missing_required_file_is_hard_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_profile(root)
            (root / "SOUL.md").unlink()
            scorecard = profile_scorecard.build_scorecard(root)
        self.assertEqual(scorecard["summary"]["status"], "fail")
        self.assertLess(scorecard["summary"]["score"], 100)
        self.assertEqual(profile_scorecard.exit_code(scorecard), 1)
        self.assertIn("Missing required file: SOUL.md", scorecard["checks"][0]["details"])

    def test_env_requires_missing_from_env_example_is_hard_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_profile(root, env_mismatch=True)
            scorecard = profile_scorecard.build_scorecard(root)
        self.assertEqual(scorecard["summary"]["status"], "fail")
        self.assertEqual(profile_scorecard.exit_code(scorecard), 1)
        self.assertIn("Env var DEMO_API_KEY is declared but missing from .env.EXAMPLE", scorecard["checks"][0]["details"])

    def test_missing_recommended_topics_is_advisory_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_profile(root, topics=False)
            scorecard = profile_scorecard.build_scorecard(root)
        check = next(item for item in scorecard["checks"] if item["id"] == "metadata.github_topics")
        self.assertEqual(check["status"], "warning")
        self.assertEqual(profile_scorecard.exit_code(scorecard), 0)

    def test_invalid_manifest_yaml_reports_hard_failure_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_profile(root)
            write(root / "distribution.yaml", "name: [broken")
            scorecard = profile_scorecard.build_scorecard(root)
            rendered = profile_scorecard.render_json(scorecard)
        self.assertEqual(scorecard["summary"]["status"], "fail")
        self.assertEqual(profile_scorecard.exit_code(scorecard), 1)
        self.assertIn("Invalid YAML in", rendered)

    def test_invalid_github_metadata_yaml_reports_warning_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_profile(root)
            write(root / "github-repo-metadata.yaml", "topics: [broken")
            scorecard = profile_scorecard.build_scorecard(root)
            rendered = profile_scorecard.render_markdown(scorecard)
        check = next(item for item in scorecard["checks"] if item["id"] == "metadata.github_topics")
        self.assertEqual(check["status"], "warning")
        self.assertEqual(profile_scorecard.exit_code(scorecard), 0)
        self.assertIn("GitHub metadata YAML could not be parsed", rendered)

    def test_json_output_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_profile(root)
            scorecard = profile_scorecard.build_scorecard(root)
            first = profile_scorecard.render_json(scorecard)
            second = profile_scorecard.render_json(scorecard)
        self.assertEqual(first, second)
        data = json.loads(first)
        self.assertEqual(data["schema_version"], profile_scorecard.SCHEMA_VERSION)
        self.assertEqual(data["summary"]["score"], 100)

    def test_markdown_output_contains_summary_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_profile(root, readme_install=False)
            markdown = profile_scorecard.render_markdown(profile_scorecard.build_scorecard(root))
        self.assertIn("# Hermes Profile Scorecard", markdown)
        self.assertIn("- Score:", markdown)
        self.assertIn("| warning | advisory | README install command |", markdown)


if __name__ == "__main__":
    unittest.main()
