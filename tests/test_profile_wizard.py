"""Tests for scripts/profile_wizard.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from profile_wizard import collect_params_from_args, write_params, build_parser


def _make_args(**kwargs):
    defaults = dict(
        name="test-agent",
        display_name="Test Agent",
        description="A test agent profile.",
        author="Tester",
        version="0.1.0",
        license="MIT",
        params_out="profile.params.yaml",
        output_dir=None,
        no_generate=True,
    )
    defaults.update(kwargs)

    class NS:
        pass

    ns = NS()
    for k, v in defaults.items():
        setattr(ns, k, v)
    return ns


class TestCollectParamsFromArgs:
    def test_basic_fields(self):
        params = collect_params_from_args(_make_args())
        assert params["name"] == "test-agent"
        assert params["display_name"] == "Test Agent"
        assert params["description"] == "A test agent profile."
        assert params["author"] == "Tester"
        assert params["version"] == "0.1.0"
        assert params["license"] == "MIT"

    def test_name_normalised_to_kebab(self):
        params = collect_params_from_args(_make_args(name="My Cool Agent!"))
        assert params["name"] == "my-cool-agent"

    def test_name_normalised_lowercase(self):
        params = collect_params_from_args(_make_args(name="MyAgent"))
        assert params["name"] == "myagent"

    def test_required_keys_present(self):
        params = collect_params_from_args(_make_args())
        for key in ("name", "display_name", "description", "toolsets",
                    "env_requires", "principles", "scope", "refusals",
                    "output_contract", "github_topics", "template_source"):
            assert key in params, f"Missing key: {key}"

    def test_toolsets_are_list(self):
        params = collect_params_from_args(_make_args())
        assert isinstance(params["toolsets"], list)
        assert len(params["toolsets"]) > 0

    def test_env_requires_empty_by_default(self):
        params = collect_params_from_args(_make_args())
        assert params["env_requires"] == []

    def test_template_source_present(self):
        params = collect_params_from_args(_make_args())
        ts = params["template_source"]
        assert "name" in ts and "url" in ts and "relationship" in ts


class TestWriteParams:
    def test_writes_yaml_file(self, tmp_path):
        params = collect_params_from_args(_make_args())
        out = tmp_path / "out.yaml"
        write_params(params, out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_output_is_valid_yaml(self, tmp_path):
        pytest.importorskip("yaml")
        import yaml
        params = collect_params_from_args(_make_args())
        out = tmp_path / "out.yaml"
        write_params(params, out)
        loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
        assert isinstance(loaded, dict)
        assert loaded["name"] == "test-agent"

    def test_output_is_deterministic(self, tmp_path):
        params = collect_params_from_args(_make_args())
        out1 = tmp_path / "a.yaml"
        out2 = tmp_path / "b.yaml"
        write_params(params, out1)
        write_params(params, out2)
        assert out1.read_text() == out2.read_text()

    def test_creates_parent_dirs(self, tmp_path):
        params = collect_params_from_args(_make_args())
        out = tmp_path / "nested" / "dir" / "params.yaml"
        write_params(params, out)
        assert out.exists()


class TestCLINonInteractive:
    def _run(self, *extra_args):
        script = Path(__file__).parent.parent / "scripts" / "profile_wizard.py"
        return subprocess.run(
            [sys.executable, str(script), "--no-generate", *extra_args],
            capture_output=True, text=True,
        )

    def test_basic_invocation(self, tmp_path):
        out = tmp_path / "params.yaml"
        result = self._run("--name", "ci-agent", "--params-out", str(out))
        assert result.returncode == 0, result.stderr
        assert out.exists()

    def test_params_file_content(self, tmp_path):
        pytest.importorskip("yaml")
        import yaml
        out = tmp_path / "params.yaml"
        self._run(
            "--name", "ci-agent",
            "--description", "CI smoke test agent.",
            "--author", "CI",
            "--params-out", str(out),
        )
        loaded = yaml.safe_load(out.read_text())
        assert loaded["name"] == "ci-agent"
        assert loaded["description"] == "CI smoke test agent."
        assert loaded["author"] == "CI"

    def test_next_step_printed(self, tmp_path):
        out = tmp_path / "params.yaml"
        result = self._run("--name", "smoke-agent", "--params-out", str(out))
        assert "generate_profile.py" in result.stdout or "generate" in result.stdout.lower()

    def test_missing_name_exits_nonzero(self, tmp_path):
        # Non-interactive but no --name → parser doesn't error, runs interactive
        # which will hit EOF and exit 1.
        script = Path(__file__).parent.parent / "scripts" / "profile_wizard.py"
        result = subprocess.run(
            [sys.executable, str(script), "--no-generate"],
            capture_output=True, text=True, input="",
        )
        assert result.returncode != 0
