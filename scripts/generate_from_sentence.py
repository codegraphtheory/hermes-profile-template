#!/usr/bin/env python3
"""Generate an installable Hermes profile repo from one sentence.

This is the deterministic backend entrypoint for local and web demos. It expands
one short idea into a mature profile prompt, writes params YAML, invokes the
profile generator, adds a focused starter skill, renders a playable static demo,
renders an SVG contents diagram, validates the profile, and optionally packages
safe downloadable artifacts.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import textwrap
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

MAX_SENTENCE_CHARS = 1000
SECRET_HINTS = re.compile(
    r"(sk-[A-Za-z0-9]{12,}|gh[pousr]_[A-Za-z0-9_]{12,}|xox[baprs]-|AKIA[0-9A-Z]{12,}|-----BEGIN [A-Z ]+PRIVATE KEY-----)",
    re.IGNORECASE,
)

STOPWORDS = {
    "a", "an", "the", "for", "with", "that", "this", "into", "agent", "profile", "hermes",
    "make", "build", "create", "turn", "to", "of", "and", "or", "my", "our", "me", "it",
}

@dataclass
class BuildResult:
    slug: str
    display_name: str
    profile_dir: Path
    params_path: Path
    prompt_path: Path
    diagram_path: Path
    demo_md_path: Path
    demo_html_path: Path
    validation_report_path: Path
    zip_path: Path | None
    validation_stdout: str


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        return "generated-profile"
    parts = [part for part in value.split("-") if part not in STOPWORDS]
    slug = "-".join(parts[:5]) or value
    return slug[:63].strip("-") or "generated-profile"


def titleize(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-"))


def sanitize_sentence(sentence: str) -> str:
    cleaned = " ".join(sentence.strip().split())
    if not cleaned:
        raise ValueError("sentence is required")
    if len(cleaned) > MAX_SENTENCE_CHARS:
        raise ValueError(f"sentence must be {MAX_SENTENCE_CHARS} characters or less")
    if SECRET_HINTS.search(cleaned):
        raise ValueError("sentence appears to contain a secret or credential. Remove it and try again")
    return cleaned


def infer_domain(sentence: str) -> dict[str, Any]:
    low = sentence.lower()
    if any(term in low for term in ["ticket", "support", "helpdesk", "customer"]):
        return {
            "noun": "support ticket",
            "skill": "ticket-triage-workflow",
            "skill_title": "Ticket Triage Workflow",
            "description": "Triage customer support tickets into priority, ownership, response guidance, and safe next actions while protecting customer data.",
            "topics": ["support", "helpdesk", "ticket-triage", "customer-success"],
            "scope": [
                "Classify support tickets by priority, category, sentiment, customer impact, and likely owning team.",
                "Extract concise summaries, missing information, evidence, and recommended next actions.",
                "Draft safe customer replies and internal escalation notes.",
                "Flag security, privacy, billing, legal, outage, SLA, VIP, and customer-health risks for human review.",
            ],
            "outputs": [
                "Triage result with priority, category, owner, status recommendation, and confidence.",
                "Evidence from the ticket and inspected sources, with assumptions labeled.",
                "Missing information and recommended next actions.",
                "Customer-facing draft reply and internal escalation note when useful.",
            ],
            "refusals": [
                "Exfiltrating customer data, credentials, payment information, or internal-only records.",
                "Fabricating ticket history, SLA commitments, outage status, refunds, or root causes.",
                "Closing, deleting, suppressing, or downgrading tickets to hide incidents.",
            ],
            "env": [
                {"name": "SUPPORT_HELPDESK_BASE_URL", "description": "Optional helpdesk base URL.", "required": False},
                {"name": "SUPPORT_KB_BASE_URL", "description": "Optional support knowledge-base URL.", "required": False},
            ],
        }
    if any(term in low for term in ["migration", "sql", "database", "postgres", "mysql"]):
        return {
            "noun": "database migration",
            "skill": "migration-review-workflow",
            "skill_title": "Migration Review Workflow",
            "description": "Review database migration changes for destructive operations, lock risk, data integrity risk, and rollback readiness.",
            "topics": ["database", "sql", "migrations", "devops"],
            "scope": [
                "Review SQL, ORM, and schema migration diffs before deployment.",
                "Flag destructive changes, table rewrites, unsafe locks, missing rollback plans, and irreversible data changes.",
                "Produce deploy risk summaries and rollback checklists.",
                "Ask for database engine and version only when semantics depend on it.",
            ],
            "outputs": [
                "Risk verdict with one-sentence rationale.",
                "Findings grouped by destructive change, lock risk, rollback gap, and data integrity risk.",
                "Required fixes before deploy.",
                "Rollback checklist and evidence reviewed.",
            ],
            "refusals": [
                "Running destructive SQL against production without explicit approval and a named target.",
                "Claiming a migration is safe without reviewing the actual diff or migration content.",
                "Storing database credentials in repository files.",
            ],
            "env": [],
        }
    if any(term in low for term in ["security", "audit", "vulnerability", "threat", "risk"]):
        return {
            "noun": "security review",
            "skill": "security-review-workflow",
            "skill_title": "Security Review Workflow",
            "description": "Review code, architecture, and operational changes for security risk with evidence-backed findings and mitigations.",
            "topics": ["security", "code-review", "threat-modeling", "appsec"],
            "scope": [
                "Inspect code, configs, diffs, and architecture notes for security weaknesses.",
                "Prioritize issues by exploitability, blast radius, and likelihood.",
                "Recommend concrete mitigations and verification steps.",
                "Separate confirmed vulnerabilities from assumptions and follow-up questions.",
            ],
            "outputs": [
                "Severity-ranked findings with evidence.",
                "Threat model summary.",
                "Mitigation checklist.",
                "Verification commands or review steps.",
            ],
            "refusals": [
                "Weaponizing vulnerabilities against third-party systems.",
                "Stealing credentials, secrets, sessions, or private data.",
                "Concealing backdoors or bypasses in code.",
            ],
            "env": [],
        }
    return {
        "noun": "workflow",
        "skill": "focused-workflow",
        "skill_title": "Focused Workflow",
        "description": f"Help users with {sentence.rstrip('.')} through a focused, safe, evidence-backed Hermes profile.",
        "topics": ["workflow-automation", "ai-agent", "productivity"],
        "scope": [
            f"Handle user requests related to {sentence.rstrip('.')}.",
            "Clarify missing inputs only when they materially affect the result.",
            "Produce durable, actionable outputs with evidence when relevant.",
            "Run validation or checks after creating or modifying files.",
        ],
        "outputs": [
            "Concise result.",
            "Evidence, files inspected, or commands run when relevant.",
            "Risks, assumptions, and blockers.",
            "Recommended next action.",
        ],
        "refusals": [
            "Credential theft or secret exposure.",
            "Hidden persistence, backdoors, or deceptive automation.",
            "Fabricated facts, links, audits, or affiliations.",
        ],
        "env": [],
    }


def mature_prompt(sentence: str, slug: str, display_name: str, domain: dict[str, Any], output: Path) -> str:
    workflows = "\n".join(f"{i}. {item}" for i, item in enumerate(domain["scope"], 1))
    outputs = "\n".join(f"- {item}" for item in domain["outputs"])
    refusals = "\n".join(f"- {item}" for item in domain["refusals"])
    env_lines = domain.get("env") or []
    env_text = "\n".join(f"- {item['name']}: {item['description']}" for item in env_lines) or "- None required for the default local workflow."
    return f"""## Simple sentence

{sentence}

## Mature Profile Prompt

### Profile name and slug

- Display name: {display_name}
- Slug: {slug}

### Mission

{domain['description']}

### Target users

- Builders, operators, reviewers, and teams who need repeatable assistance for {domain['noun']} work.

### Primary workflows

{workflows}

### Trigger patterns

Use this profile when the user asks to analyze, review, triage, generate, summarize, validate, or prepare outputs related to {domain['noun']} work.

### Inputs expected

- Pasted text, local files, repository paths, diffs, exported data, links, or user-provided context.
- The user's taxonomy, policy, rubric, or success criteria when available.
- Constraints such as risk tolerance, audience, deadline, or required output format.

### Outputs required

{outputs}

### Tool-use policy

- Inspect real files, repositories, or docs before making factual claims about them.
- Use validation, smoke tests, or syntax checks after changing files.
- Report exact command output for verification-critical work.
- State assumptions and blockers clearly instead of inventing results.

### Safety boundaries and refusals

{refusals}

### Required bundled skills

- {domain['skill']}: a focused procedure for the profile's core workflow.
- prompt-engineering: preserves the simple-sentence to mature-prompt workflow for future regeneration.
- profile-craft: validates and maintains installable Hermes profile distribution structure.

### Environment variables

{env_text}

### Verification and smoke-test expectations

- `python3 scripts/validate_profile.py .`
- `hermes profile install . --name {slug}-local --yes --force`

### Repository output requirements

- Write the generated profile under `{output}`.
- Include `SOUL.md`, `distribution.yaml`, `README.md`, `config.yaml`, `.env.EXAMPLE`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`, scripts, docs, and required bundled skills.
- Preserve this mature prompt in `docs/profile-prompt.md`.
- Include a playable demo and an SVG diagram explaining the output contents.
"""


def params_for(sentence: str, output: Path, profile_prompt_override: str | None = None) -> dict[str, Any]:
    slug = slugify(sentence)
    display = titleize(slug)
    domain = infer_domain(sentence)
    prompt = profile_prompt_override or mature_prompt(sentence, slug, display, domain, output)
    topics = ["hermes-agent", "ai-agents", "agent-profile", "profile-distribution"] + domain["topics"]
    return {
        "name": slug,
        "display_name": display,
        "description": domain["description"],
        "author": "Hermes profile author",
        "version": "0.1.0",
        "license": "MIT",
        "model_provider": "openrouter",
        "model_default": "anthropic/claude-sonnet-4",
        "template_source": {
            "name": "codegraphtheory/hermes-profile-template",
            "url": "https://github.com/codegraphtheory/hermes-profile-template",
            "relationship": "generated-from-template",
        },
        "toolsets": ["file", "terminal", "skills", "web", "session_search", "clarify"],
        "env_requires": domain.get("env") or [],
        "principles": [
            "Be evidence-backed before being confident.",
            "Protect user data and never expose secrets.",
            "Ask only for missing information that materially changes the result.",
            "Produce concise outputs that a human can act on immediately.",
            "Run validation or checks when creating or changing artifacts.",
        ],
        "scope": domain["scope"],
        "refusals": domain["refusals"],
        "output_contract": domain["outputs"],
        "profile_prompt": prompt,
        "github_topics": topics[:20],
    }


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install with: python3 -m pip install pyyaml")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, default_flow_style=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def render_skill(path: Path, slug: str, title: str, domain: dict[str, Any]) -> None:
    scope = "\n".join(f"{i}. {item}" for i, item in enumerate(domain["scope"], 1))
    outputs = "\n".join(f"- {item}" for item in domain["outputs"])
    text = f"""---
name: {slug}
description: "Reusable workflow for {domain['noun']} tasks."
version: 0.1.0
author: Hermes profile author
license: MIT
---

# {title}

Use this skill when the user asks for help with {domain['noun']} work.

## Workflow

{scope}

## Output contract

{outputs}

## Verification

- Cite files, inputs, or commands used as evidence.
- Label assumptions and missing information.
- Run validators, tests, or smoke checks when files are created or changed.
- Never invent command output or external facts.
"""
    write_text(path, text)


def render_playable_demo(profile_dir: Path, params: dict[str, Any]) -> tuple[Path, Path]:
    slug = params["name"]
    display = params["display_name"]
    demo_prompt = f"Help me with {params['description'].rstrip('.').lower()}."
    assistant_reply = "\n".join([
        f"I am {display}. I will handle this with a focused workflow.",
        "",
        "1. I will inspect the provided context before making factual claims.",
        "2. I will apply the bundled workflow skill for this profile.",
        "3. I will return the required output contract with evidence, risks, and next steps.",
        "4. If files change, I will run validation before calling the task complete.",
    ])
    md = f"""# Playable Demo

This is a static demo transcript for the generated `{slug}` profile. It is safe to publish and does not require credentials.

## Demo conversation

**User**

```text
{demo_prompt}
```

**{display}**

```text
{assistant_reply}
```

## Try it locally

```bash
hermes profile install . --name {slug}-local --yes --force
hermes -p {slug}-local chat
```
"""
    md_path = profile_dir / "docs" / "playable-demo.md"
    write_text(md_path, md)
    html_doc = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(display)} demo</title>
  <style>
    body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; background: #0b1020; color: #f8fafc; }}
    main {{ max-width: 840px; margin: 0 auto; padding: 48px 20px; }}
    .card {{ background: #121a33; border: 1px solid #26324f; border-radius: 18px; padding: 24px; box-shadow: 0 20px 60px rgba(0,0,0,.28); }}
    .bubble {{ padding: 16px 18px; border-radius: 16px; margin: 16px 0; line-height: 1.55; white-space: pre-wrap; }}
    .user {{ background: #2563eb; margin-left: 10%; }}
    .agent {{ background: #18243f; margin-right: 10%; border: 1px solid #31405f; }}
    code {{ color: #93c5fd; }}
  </style>
</head>
<body>
  <main>
    <p><code>{html.escape(slug)}</code></p>
    <h1>{html.escape(display)} playable demo</h1>
    <div class=\"card\">
      <div class=\"bubble user\">{html.escape(demo_prompt)}</div>
      <div class=\"bubble agent\">{html.escape(assistant_reply)}</div>
    </div>
  </main>
</body>
</html>
"""
    html_path = profile_dir / "demo" / "index.html"
    write_text(html_path, html_doc)
    return md_path, html_path


def render_diagram(profile_dir: Path, params: dict[str, Any]) -> Path:
    display = html.escape(params["display_name"])
    slug = html.escape(params["name"])
    boxes = [
        ("User sentence", "One short idea typed into the web form"),
        ("Mature profile prompt", "docs/profile-prompt.md preserves the expanded design"),
        ("Params YAML", "templates/profile.params.yaml captures generation inputs"),
        ("Installable repo", "SOUL, manifest, config, docs, scripts, skills"),
        ("Playable demo", "demo/index.html and docs/playable-demo.md"),
        ("Validation", "scripts/validate_profile.py proves the repo shape"),
    ]
    width, height = 980, 720
    parts = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"]
    parts.append("<defs><linearGradient id='g' x1='0' x2='1'><stop stop-color='#2563eb'/><stop offset='1' stop-color='#7c3aed'/></linearGradient></defs>")
    parts.append("<rect width='980' height='720' rx='28' fill='#0b1020'/>")
    parts.append(f"<text x='48' y='60' fill='#f8fafc' font-family='Inter, Arial' font-size='30' font-weight='700'>{display}</text>")
    parts.append(f"<text x='48' y='92' fill='#93c5fd' font-family='Inter, Arial' font-size='16'>{slug} profile generation map</text>")
    y = 130
    for i, (title, body) in enumerate(boxes):
        fill = "url(#g)" if i == 0 else "#121a33"
        stroke = "#60a5fa" if i == 0 else "#334155"
        parts.append(f"<rect x='90' y='{y}' width='800' height='72' rx='16' fill='{fill}' stroke='{stroke}'/>")
        parts.append(f"<text x='120' y='{y+30}' fill='#f8fafc' font-family='Inter, Arial' font-size='18' font-weight='700'>{html.escape(title)}</text>")
        parts.append(f"<text x='120' y='{y+54}' fill='#dbeafe' font-family='Inter, Arial' font-size='14'>{html.escape(body)}</text>")
        if i < len(boxes) - 1:
            parts.append(f"<path d='M490 {y+76} L490 {y+104}' stroke='#60a5fa' stroke-width='3' marker-end='url(#arrow)'/>")
        y += 94
    parts.insert(2, "<defs><marker id='arrow' viewBox='0 0 10 10' refX='5' refY='5' markerWidth='6' markerHeight='6' orient='auto-start-reverse'><path d='M 0 0 L 10 5 L 0 10 z' fill='#60a5fa'/></marker></defs>")
    parts.append("</svg>")
    path = profile_dir / "docs" / "output-diagram.svg"
    write_text(path, "\n".join(parts))
    return path


def safe_zip(profile_dir: Path, artifact_dir: Path, slug: str) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    zip_path = artifact_dir / f"{slug}.zip"
    forbidden_parts = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "sessions", "memories", "logs", "cache", "local"}
    forbidden_names = {".env", "auth.json", "state.db", "state.db-shm", "state.db-wal"}
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(profile_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(profile_dir)
            if any(part in forbidden_parts for part in rel.parts) or path.name in forbidden_names:
                continue
            zf.write(path, Path(slug) / rel)
    return zip_path


def run_validation(profile_dir: Path) -> str:
    cmd = [sys.executable, str(profile_dir / "scripts" / "validate_profile.py"), str(profile_dir)]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    output = proc.stdout + proc.stderr
    if proc.returncode != 0:
        raise RuntimeError(output)
    return output


def build(sentence: str, output: Path, force: bool, artifact_dir: Path | None, package: bool, profile_prompt_file: Path | None = None) -> BuildResult:
    sentence = sanitize_sentence(sentence)
    output = output.resolve()
    template_root = Path(__file__).resolve().parents[1]
    profile_prompt_override = profile_prompt_file.read_text(encoding="utf-8") if profile_prompt_file else None
    params = params_for(sentence, output, profile_prompt_override)
    slug = params["name"]
    display = params["display_name"]
    if output.exists() and force:
        shutil.rmtree(output)
    elif output.exists():
        raise FileExistsError(f"output exists. Pass --force to overwrite: {output}")
    params_path = output.parent / f"{slug}.params.yaml"
    write_yaml(params_path, params)
    generator = template_root / "scripts" / "generate_profile.py"
    subprocess.run([sys.executable, str(generator), "--params", str(params_path), "--output", str(output)], check=True)
    domain = infer_domain(sentence)
    render_skill(output / "skills" / domain["skill"] / "SKILL.md", domain["skill"], domain["skill_title"], domain)
    demo_md_path, demo_html_path = render_playable_demo(output, params)
    diagram_path = render_diagram(output, params)
    validation_stdout = run_validation(output)
    validation_report_path = output / "docs" / "validation-report.md"
    write_text(validation_report_path, f"# Validation Report\n\nGenerated at: {datetime.now(timezone.utc).isoformat()}\n\n```text\n{validation_stdout}\n```\n")
    validation_stdout = run_validation(output)
    zip_path = safe_zip(output, artifact_dir or output.parent / "artifacts", slug) if package else None
    manifest = {
        "slug": slug,
        "display_name": display,
        "sentence": sentence,
        "profile_dir": str(output),
        "params_path": str(params_path),
        "prompt_path": str(output / "docs" / "profile-prompt.md"),
        "diagram_path": str(diagram_path),
        "demo_html_path": str(demo_html_path),
        "demo_md_path": str(demo_md_path),
        "validation_report_path": str(validation_report_path),
        "zip_path": str(zip_path) if zip_path else None,
    }
    write_text((artifact_dir or output.parent / "artifacts") / f"{slug}.manifest.json", json.dumps(manifest, indent=2) + "\n")
    return BuildResult(slug, display, output, params_path, output / "docs" / "profile-prompt.md", diagram_path, demo_md_path, demo_html_path, validation_report_path, zip_path, validation_stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Turn one sentence into an installable Hermes profile repo")
    parser.add_argument("--sentence", required=True, help="Simple profile idea")
    parser.add_argument("--output", required=True, help="Output profile directory")
    parser.add_argument("--force", action="store_true", help="Overwrite output if it exists")
    parser.add_argument("--artifact-dir", help="Directory for zip and manifest artifacts")
    parser.add_argument("--no-package", action="store_true", help="Skip zip packaging")
    parser.add_argument("--profile-prompt-file", help="Optional mature prompt markdown produced by Hermes/LLM refinement")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()
    try:
        result = build(
            args.sentence,
            Path(args.output),
            args.force,
            Path(args.artifact_dir).resolve() if args.artifact_dir else None,
            not args.no_package,
            Path(args.profile_prompt_file).resolve() if args.profile_prompt_file else None,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    payload = {
        "ok": True,
        "slug": result.slug,
        "display_name": result.display_name,
        "profile_dir": str(result.profile_dir),
        "params_path": str(result.params_path),
        "prompt_path": str(result.prompt_path),
        "diagram_path": str(result.diagram_path),
        "demo_md_path": str(result.demo_md_path),
        "demo_html_path": str(result.demo_html_path),
        "validation_report_path": str(result.validation_report_path),
        "zip_path": str(result.zip_path) if result.zip_path else None,
        "validation_stdout": result.validation_stdout,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Created installable Hermes profile repo: {result.profile_dir}")
        print(f"Mature prompt: {result.prompt_path}")
        print(f"Playable demo: {result.demo_html_path}")
        print(f"Diagram: {result.diagram_path}")
        if result.zip_path:
            print(f"Download zip: {result.zip_path}")
        print(result.validation_stdout, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
