"""Tests for scripts/render_catalog_entry.py."""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from render_catalog_entry import (
    load_distribution,
    render_markdown,
    render_yaml,
    render_readme_line,
    render_pr_body,
    _field,
    _env_names,
    _source_url,
    _install_cmd,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_DIST = {
    "name": "my-agent",
    "version": "1.0.0",
    "description": "Does useful things for developers.",
    "author": "Alice",
    "license": "MIT",
}

FULL_DIST = {
    **MINIMAL_DIST,
    "display_name": "My Agent",
    "hermes_requires": ">=0.12.0",
    "env_requires": [
        {"name": "MY_API_KEY", "description": "Required key.", "required": True},
        {"name": "OPTIONAL_KEY", "description": "Optional key.", "required": False},
    ],
}

SOURCE_URL = "https://github.com/alice/my-agent"


def _write_dist(tmp_path: Path, data: dict) -> Path:
    pytest.importorskip("yaml")
    import yaml
    dist = tmp_path / "distribution.yaml"
    dist.write_text(yaml.dump(data), encoding="utf-8")
    return dist


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_field_returns_value(self):
        assert _field({"name": "foo"}, "name") == "foo"

    def test_field_returns_fallback(self):
        assert _field({}, "name", "default") == "default"

    def test_field_strips_whitespace(self):
        assert _field({"name": "  foo  "}, "name") == "foo"

    def test_env_names_empty(self):
        assert _env_names({}) == []

    def test_env_names_list(self):
        data = {"env_requires": [
            {"name": "KEY_A"}, {"name": "KEY_B"}
        ]}
        assert _env_names(data) == ["KEY_A", "KEY_B"]

    def test_env_names_skips_malformed(self):
        data = {"env_requires": [{"name": "KEY_A"}, "not-a-dict", {}]}
        assert _env_names(data) == ["KEY_A"]

    def test_install_cmd_format(self):
        cmd = _install_cmd({}, "https://github.com/alice/my-agent")
        assert cmd == "hermes profile install alice/my-agent"


# ---------------------------------------------------------------------------
# Renderer tests
# ---------------------------------------------------------------------------

class TestRenderMarkdown:
    def test_contains_display_name(self):
        out = render_markdown(FULL_DIST, SOURCE_URL)
        assert "My Agent" in out

    def test_contains_description(self):
        out = render_markdown(FULL_DIST, SOURCE_URL)
        assert "Does useful things" in out

    def test_contains_install_command(self):
        out = render_markdown(FULL_DIST, SOURCE_URL)
        assert "hermes profile install" in out

    def test_contains_source_url(self):
        out = render_markdown(FULL_DIST, SOURCE_URL)
        assert SOURCE_URL in out

    def test_contains_safety_constraints(self):
        out = render_markdown(FULL_DIST, SOURCE_URL)
        assert "Safety" in out or "safety" in out
        assert "fabricate" in out

    def test_contains_catalog_reminder(self):
        out = render_markdown(FULL_DIST, SOURCE_URL)
        assert "REMINDER" in out

    def test_lists_env_vars(self):
        out = render_markdown(FULL_DIST, SOURCE_URL)
        assert "MY_API_KEY" in out

    def test_minimal_dist_no_crash(self):
        out = render_markdown(MINIMAL_DIST, SOURCE_URL)
        assert "my-agent" in out.lower() or "My Agent" in out

    def test_no_marketing_fluff(self):
        out = render_markdown(FULL_DIST, SOURCE_URL)
        fluff = ["best", "revolutionary", "groundbreaking", "amazing", "powerful"]
        for word in fluff:
            assert word not in out.lower(), f"Marketing fluff found: {word}"


class TestRenderYaml:
    def test_is_valid_yaml(self):
        yaml = pytest.importorskip("yaml")
        out = render_yaml(FULL_DIST, SOURCE_URL)
        # Strip comment line before parsing
        content = "\n".join(l for l in out.splitlines() if not l.startswith("#"))
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict)

    def test_contains_name(self):
        out = render_yaml(FULL_DIST, SOURCE_URL)
        assert "my-agent" in out

    def test_contains_source_url(self):
        out = render_yaml(FULL_DIST, SOURCE_URL)
        assert SOURCE_URL in out

    def test_contains_install(self):
        out = render_yaml(FULL_DIST, SOURCE_URL)
        assert "hermes profile install" in out

    def test_optional_tokens_include_env_vars(self):
        out = render_yaml(FULL_DIST, SOURCE_URL)
        assert "MY_API_KEY" in out


class TestRenderReadmeLine:
    def test_is_single_line(self):
        out = render_readme_line(FULL_DIST, SOURCE_URL)
        assert "\n" not in out.strip()

    def test_contains_link(self):
        out = render_readme_line(FULL_DIST, SOURCE_URL)
        assert f"[My Agent]({SOURCE_URL})" in out

    def test_contains_description(self):
        out = render_readme_line(FULL_DIST, SOURCE_URL)
        assert "Does useful things" in out

    def test_contains_install(self):
        out = render_readme_line(FULL_DIST, SOURCE_URL)
        assert "hermes profile install" in out


class TestRenderPrBody:
    def test_contains_heading(self):
        out = render_pr_body(FULL_DIST, SOURCE_URL)
        assert "## Add" in out

    def test_contains_install_block(self):
        out = render_pr_body(FULL_DIST, SOURCE_URL)
        assert "hermes profile install" in out

    def test_contains_checklist(self):
        out = render_pr_body(FULL_DIST, SOURCE_URL)
        assert "- [ ]" in out

    def test_contains_contribution_reminder(self):
        out = render_pr_body(FULL_DIST, SOURCE_URL)
        assert "contribution guidelines" in out

    def test_contains_safety_constraints(self):
        out = render_pr_body(FULL_DIST, SOURCE_URL)
        assert "fabricate" in out

    def test_lists_env_vars(self):
        out = render_pr_body(FULL_DIST, SOURCE_URL)
        assert "MY_API_KEY" in out


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

class TestCLI:
    def _run(self, *args):
        script = Path(__file__).parent.parent / "scripts" / "render_catalog_entry.py"
        return subprocess.run(
            [sys.executable, str(script), *args],
            capture_output=True, text=True,
        )

    def test_default_format_markdown(self, tmp_path):
        _write_dist(tmp_path, FULL_DIST)
        r = self._run(str(tmp_path))
        assert r.returncode == 0
        assert "hermes profile install" in r.stdout

    def test_yaml_format(self, tmp_path):
        _write_dist(tmp_path, FULL_DIST)
        r = self._run(str(tmp_path), "--format", "yaml")
        assert r.returncode == 0
        assert "name:" in r.stdout

    def test_readme_line_format(self, tmp_path):
        _write_dist(tmp_path, FULL_DIST)
        r = self._run(str(tmp_path), "--format", "readme-line")
        assert r.returncode == 0
        assert "\n" not in r.stdout.strip()

    def test_pr_body_format(self, tmp_path):
        _write_dist(tmp_path, FULL_DIST)
        r = self._run(str(tmp_path), "--format", "pr-body")
        assert r.returncode == 0
        assert "checklist" in r.stdout.lower() or "- [ ]" in r.stdout

    def test_all_format(self, tmp_path):
        _write_dist(tmp_path, FULL_DIST)
        r = self._run(str(tmp_path), "--format", "all")
        assert r.returncode == 0
        assert "hermes profile install" in r.stdout
        assert "name:" in r.stdout

    def test_direct_dist_flag(self, tmp_path):
        dist = _write_dist(tmp_path, FULL_DIST)
        r = self._run("--dist", str(dist))
        assert r.returncode == 0

    def test_missing_dist_exits_nonzero(self, tmp_path):
        r = self._run(str(tmp_path / "nonexistent"))
        assert r.returncode != 0
