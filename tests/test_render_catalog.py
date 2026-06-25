import tempfile
from pathlib import Path
import pytest
import yaml

from scripts.render_catalog_entry import (
    infer_org,
    render_template,
    get_markdown_card,
    get_yaml_manifest,
    get_readme_line,
    get_pr_body,
    get_flat_md,
)


@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_placeholder_replacement():
    template = "This is " + "{{" + "profile_slug" + "}}" + " owned by " + "{{" + "org" + "}}" + " and does " + "{{" + "description" + "}}" + "."
    replacements = {
        "profile_slug": "database-cleaner",
        "org": "saitama-corp",
        "description": "cleaning old DB records",
    }
    rendered = render_template(template, replacements)
    assert rendered == "This is database-cleaner owned by saitama-corp and does cleaning old DB records."


def test_snippet_rendering_formats(temp_repo):
    replacements = {
        "profile_slug": "rust-linter",
        "display_name": "Rust Linter",
        "description": "Lints Rust projects.",
        "org": "therealsaitama0",
    }

    # 1. Test Markdown card
    card = get_markdown_card(replacements)
    assert "### Rust Linter" in card
    assert "hermes profile install github.com/therealsaitama0/rust-linter" in card

    # 2. Test README line
    readme_line = get_readme_line(replacements)
    assert "[Rust Linter](https://github.com/therealsaitama0/rust-linter)" in readme_line
    assert "Lints Rust projects." in readme_line

    # 3. Test PR body
    pr_body = get_pr_body(replacements)
    assert "Hello! I would like to submit my custom Hermes Agent profile" in pr_body
    assert "Rust Linter" in pr_body

    # 4. Test YAML manifest (without template file)
    yaml_snippet = get_yaml_manifest(temp_repo, replacements)
    assert "name: rust-linter" in yaml_snippet
    assert "role: Lints Rust projects." in yaml_snippet

    # 5. Test YAML manifest (with template file)
    templates_dir = temp_repo / "templates" / "catalog"
    templates_dir.mkdir(parents=True)
    (templates_dir / "manifest-profile.yaml.tmpl").write_text(
        "name: " + "{{" + "profile_slug" + "}}" + "\ndescription: " + "{{" + "description" + "}}" + "\n", encoding="utf-8"
    )
    yaml_snippet_with_tmpl = get_yaml_manifest(temp_repo, replacements)
    assert yaml_snippet_with_tmpl == "name: rust-linter\ndescription: Lints Rust projects.\n"


def test_infer_org_fallback(temp_repo):
    # Without git remote or github-repo-metadata.yaml, should fallback to YOUR_ORG
    assert infer_org(temp_repo) == "YOUR_ORG"

    # With github-repo-metadata.yaml homepage
    (temp_repo / "github-repo-metadata.yaml").write_text(
        "homepage: https://github.com/test-org/test-repo\n", encoding="utf-8"
    )
    assert infer_org(temp_repo) == "test-org"
