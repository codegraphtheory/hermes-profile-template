import shutil
import tempfile
from pathlib import Path
import pytest
import yaml

from scripts.check_discovery import (
    check_description,
    check_install_command,
    check_topics,
    check_domain_keywords,
    check_lineage,
    check_validation_commands,
    check_license_security,
    check_catalog_guidance,
)


@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_shape_a_template_repo(temp_repo):
    """Shape A: Mimics the template repository itself.

    Should have no template lineage requirements by default, but should verify
    presence of general files.
    """
    # Create distribution.yaml without template_source (as in the template root)
    dist_data = {
        "name": "hermes-profile-template",
        "version": "0.3.0",
        "description": "Starter distribution for building custom Hermes Agent profiles with AI assistance.",
    }
    (temp_repo / "distribution.yaml").write_text(yaml.safe_dump(dist_data), encoding="utf-8")

    # Create README.md
    readme_content = """# Hermes Profile Template
This is a starter template.

## Option 1: Installation
hermes profile install github.com/codegraphtheory/hermes-profile-template
"""
    (temp_repo / "README.md").write_text(readme_content, encoding="utf-8")

    # Create github-repo-metadata.yaml with mismatched description (which is warning/rec)
    meta_data = {
        "description": "A different description for GitHub search.",
        "topics": ["hermes-agent", "ai-agents", "agent-profile", "profile-distribution"],
    }
    (temp_repo / "github-repo-metadata.yaml").write_text(yaml.safe_dump(meta_data), encoding="utf-8")

    # Run checks
    recs, fixes = check_description(temp_repo, fix=False)
    assert len(recs) == 1
    assert "description does not match" in recs[0]

    recs, _ = check_install_command(temp_repo)
    assert len(recs) == 0  # install command is in line 5 (near the top)

    recs, _ = check_topics(temp_repo, fix=False)
    # Warns because there's no domain-specific topic other than the recommended ones
    assert any("domain-specific search topic" in r for r in recs)

    recs, _ = check_domain_keywords(temp_repo)
    assert len(recs) == 0  # Skipped because name is hermes-profile-template


def test_shape_b_generated_profile_repo(temp_repo):
    """Shape B: Mimics a generated profile repository.

    Must contain template_source, have matching metadata description, custom
    domain keywords in headings, install commands, license, and security.
    """
    # Create distribution.yaml with template_source
    dist_data = {
        "name": "database-migration-reviewer",
        "version": "1.0.0",
        "description": "Reviews SQL migration diffs for breaking changes.",
        "template_source": {
            "url": "https://github.com/codegraphtheory/hermes-profile-template",
            "ref": "main",
        },
    }
    (temp_repo / "distribution.yaml").write_text(yaml.safe_dump(dist_data), encoding="utf-8")

    # Create github-repo-metadata.yaml with matching description and domain topic
    meta_data = {
        "description": "Reviews SQL migration diffs for breaking changes.",
        "topics": [
            "hermes-agent",
            "ai-agents",
            "agent-profile",
            "profile-distribution",
            "database",
            "sql",
        ],
    }
    (temp_repo / "github-repo-metadata.yaml").write_text(yaml.safe_dump(meta_data), encoding="utf-8")

    # Create .github/template-source.yml
    github_dir = temp_repo / ".github"
    github_dir.mkdir()
    template_source_data = {
        "template": {
            "url": "https://github.com/codegraphtheory/hermes-profile-template",
            "ref": "main",
        }
    }
    (github_dir / "template-source.yml").write_text(yaml.safe_dump(template_source_data), encoding="utf-8")

    # Create README.md with matching keyword in heading (SQL)
    readme_content = """# Database Migration Reviewer
This profile reviews database migrations.

hermes profile install github.com/user/database-migration-reviewer

## SQL Migration Best Practices
Documenting quality check.

To validate changes:
Run `make validate` or `make smoke` to check.
"""
    (temp_repo / "README.md").write_text(readme_content, encoding="utf-8")

    # Create LICENSE and SECURITY.md
    (temp_repo / "LICENSE").write_text("MIT License...", encoding="utf-8")
    (temp_repo / "SECURITY.md").write_text("Security reporting info...", encoding="utf-8")

    # Run checks
    recs, _ = check_description(temp_repo, fix=False)
    assert len(recs) == 0

    recs, _ = check_install_command(temp_repo)
    assert len(recs) == 0

    recs, _ = check_topics(temp_repo, fix=False)
    # The recommended topics are present, and there's custom domain topics ('database', 'sql')
    assert len(recs) == 0

    recs, _ = check_domain_keywords(temp_repo)
    # README contains heading "## SQL Migration Best Practices" matching keyword "sql" or "database"
    assert len(recs) == 0

    recs, _ = check_lineage(temp_repo, fix=False)
    assert len(recs) == 0

    recs, _ = check_license_security(temp_repo, fix=False)
    assert len(recs) == 0


def test_fix_behavior(temp_repo):
    """Test that check_discovery applies --fix successfully to clean up issues."""
    # Create incomplete distribution.yaml with template_source
    dist_data = {
        "name": "database-migration-reviewer",
        "version": "1.0.0",
        "description": "Reviews SQL migration diffs for breaking changes.",
        "template_source": {
            "url": "https://github.com/codegraphtheory/hermes-profile-template",
        },
    }
    (temp_repo / "distribution.yaml").write_text(yaml.safe_dump(dist_data), encoding="utf-8")

    # No github-repo-metadata.yaml, .github/template-source.yml, or SECURITY.md present.

    # 1. Run fix on description (creates github-repo-metadata.yaml)
    recs, fixes = check_description(temp_repo, fix=True)
    assert len(fixes) == 1
    assert (temp_repo / "github-repo-metadata.yaml").exists()

    # 2. Run fix on lineage (creates .github/template-source.yml)
    recs, fixes = check_lineage(temp_repo, fix=True)
    assert len(fixes) == 1
    assert (temp_repo / ".github" / "template-source.yml").exists()

    # 3. Run fix on security docs (creates SECURITY.md)
    recs, fixes = check_license_security(temp_repo, fix=True)
    assert len(fixes) == 1
    assert (temp_repo / "SECURITY.md").exists()
