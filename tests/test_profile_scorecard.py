"""Tests for scripts/profile_scorecard.py."""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from profile_scorecard import (
    FAIL,
    PASS,
    WARN,
    Scorecard,
    check_changelog,
    check_env_example_documented,
    check_github_topics,
    check_license,
    check_manifest_fields,
    check_no_runtime_files,
    check_readme_install_command,
    check_required_files,
    check_skill_frontmatter,
    check_smoke_command,
    render_markdown,
    render_terminal,
    run_scorecard,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_valid_profile(tmp_path: Path) -> Path:
    """Write a minimal valid profile directory."""
    dist = textwrap.dedent("""\
        name: test-profile
        version: 1.0.0
        description: A test profile
        author: Tester
        license: MIT
        env_requires:
          - name: MY_KEY
            description: A test key
            required: false
    """)
    (tmp_path / "distribution.yaml").write_text(dist)
    (tmp_path / "SOUL.md").write_text("# Soul\n")
    (tmp_path / "README.md").write_text(
        "# Test\n\n```\nhermes profile install github.com/test/test-profile\n```\n"
        "\nRun `make smoke` to verify install.\n"
    )
    (tmp_path / "AGENTS.md").write_text("# Agents\n")
    (tmp_path / "config.yaml").write_text("model: default\n")
    (tmp_path / ".env.EXAMPLE").write_text("MY_KEY=\n")
    (tmp_path / "LICENSE").write_text("MIT License\n")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## 1.0.0\n\n- Initial release.\n")
    (tmp_path / "Makefile").write_text(".PHONY: smoke\nsmoke:\n\tscripts/smoke_install.sh\n")
    meta = "topics:\n  - hermes\n  - agent\n"
    (tmp_path / "github-repo-metadata.yaml").write_text(meta)
    return tmp_path


# ---------------------------------------------------------------------------
# Individual check tests
# ---------------------------------------------------------------------------

class TestRequiredFiles:
    def test_pass_all_present(self, tmp_path):
        _make_valid_profile(tmp_path)
        sc = Scorecard(tmp_path)
        check_required_files(sc)
        assert sc.checks[0].status == PASS

    def test_fail_missing_file(self, tmp_path):
        _make_valid_profile(tmp_path)
        (tmp_path / "SOUL.md").unlink()
        sc = Scorecard(tmp_path)
        check_required_files(sc)
        assert sc.checks[0].status == FAIL
        assert "SOUL.md" in sc.checks[0].detail


class TestManifestFields:
    def test_pass_all_fields(self, tmp_path):
        _make_valid_profile(tmp_path)
        sc = Scorecard(tmp_path)
        check_manifest_fields(sc)
        statuses = [c.status for c in sc.checks]
        assert FAIL not in statuses

    def test_fail_missing_version(self, tmp_path):
        _make_valid_profile(tmp_path)
        (tmp_path / "distribution.yaml").write_text("name: test-profile\ndescription: x\n")
        sc = Scorecard(tmp_path)
        check_manifest_fields(sc)
        failed = [c for c in sc.checks if c.status == FAIL]
        assert any("version" in c.detail for c in failed)

    def test_warn_missing_author(self, tmp_path):
        _make_valid_profile(tmp_path)
        (tmp_path / "distribution.yaml").write_text(
            "name: test-profile\nversion: 1.0.0\ndescription: x\n"
        )
        sc = Scorecard(tmp_path)
        check_manifest_fields(sc)
        warned = [c for c in sc.checks if c.status == WARN]
        assert any("author" in c.detail for c in warned)


class TestReadmeInstall:
    def test_pass_has_install(self, tmp_path):
        _make_valid_profile(tmp_path)
        sc = Scorecard(tmp_path)
        check_readme_install_command(sc)
        assert sc.checks[0].status == PASS

    def test_warn_no_install(self, tmp_path):
        _make_valid_profile(tmp_path)
        (tmp_path / "README.md").write_text("# Test profile\n\nNo install info here.\n")
        sc = Scorecard(tmp_path)
        check_readme_install_command(sc)
        assert sc.checks[0].status == WARN


class TestEnvDocumented:
    def test_pass_documented(self, tmp_path):
        _make_valid_profile(tmp_path)
        sc = Scorecard(tmp_path)
        check_env_example_documented(sc)
        assert sc.checks[0].status == PASS

    def test_fail_undocumented(self, tmp_path):
        _make_valid_profile(tmp_path)
        (tmp_path / ".env.EXAMPLE").write_text("OTHER_KEY=\n")
        sc = Scorecard(tmp_path)
        check_env_example_documented(sc)
        assert sc.checks[0].status == FAIL
        assert "MY_KEY" in sc.checks[0].detail


class TestNoRuntimeFiles:
    def test_pass_clean(self, tmp_path):
        _make_valid_profile(tmp_path)
        sc = Scorecard(tmp_path)
        check_no_runtime_files(sc)
        assert sc.checks[0].status == PASS

    def test_fail_pyc_present(self, tmp_path):
        _make_valid_profile(tmp_path)
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "foo.pyc").write_bytes(b"")
        sc = Scorecard(tmp_path)
        check_no_runtime_files(sc)
        assert sc.checks[0].status == FAIL


class TestSkillFrontmatter:
    def test_pass_no_skills_dir(self, tmp_path):
        _make_valid_profile(tmp_path)
        sc = Scorecard(tmp_path)
        check_skill_frontmatter(sc)
        assert sc.checks[0].status == PASS

    def test_pass_valid_skill(self, tmp_path):
        _make_valid_profile(tmp_path)
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: Does things.\n---\n\n# My Skill\n"
        )
        sc = Scorecard(tmp_path)
        check_skill_frontmatter(sc)
        assert sc.checks[0].status == PASS

    def test_fail_missing_frontmatter(self, tmp_path):
        _make_valid_profile(tmp_path)
        skill_dir = tmp_path / "skills" / "bad-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# No frontmatter here\n")
        sc = Scorecard(tmp_path)
        check_skill_frontmatter(sc)
        assert sc.checks[0].status == FAIL


# ---------------------------------------------------------------------------
# Integration / full scorecard tests
# ---------------------------------------------------------------------------

class TestRunScorecard:
    def test_valid_profile_passes(self, tmp_path):
        _make_valid_profile(tmp_path)
        sc = run_scorecard(tmp_path)
        assert not sc.has_failures
        assert sc.score > 0

    def test_missing_required_file_fails(self, tmp_path):
        _make_valid_profile(tmp_path)
        (tmp_path / "distribution.yaml").unlink()
        sc = run_scorecard(tmp_path)
        assert sc.has_failures

    def test_json_output_is_deterministic(self, tmp_path):
        _make_valid_profile(tmp_path)
        sc1 = run_scorecard(tmp_path)
        sc2 = run_scorecard(tmp_path)
        assert sc1.to_dict() == sc2.to_dict()

    def test_json_schema(self, tmp_path):
        _make_valid_profile(tmp_path)
        sc = run_scorecard(tmp_path)
        d = sc.to_dict()
        for key in ("root", "score", "total", "passed", "warned", "failed", "checks"):
            assert key in d
        for check in d["checks"]:
            assert "key" in check
            assert "label" in check
            assert check["status"] in (PASS, WARN, FAIL)

    def test_markdown_render(self, tmp_path):
        _make_valid_profile(tmp_path)
        sc = run_scorecard(tmp_path)
        md = render_markdown(sc)
        assert "## Hermes Profile Scorecard" in md
        assert "Score:" in md
        assert "|" in md  # table present

    def test_terminal_render(self, tmp_path):
        _make_valid_profile(tmp_path)
        sc = run_scorecard(tmp_path)
        out = render_terminal(sc, color=False)
        assert "Scorecard" in out
        assert "Score:" in out
        assert "Verdict:" in out
