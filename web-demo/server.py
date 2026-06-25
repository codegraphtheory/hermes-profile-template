#!/usr/bin/env python3
"""Local web demo for prompt-to-profile generation.

Run:
  python3 web-demo/server.py
Then open http://127.0.0.1:8765
"""
from __future__ import annotations

import json
import mimetypes
import os
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

HOST = "127.0.0.1"
PORT = 8765
MAX_BODY = 12_000
MAX_FILE_PREVIEW = 80_000
HERMES_LLM_ENABLED = os.getenv("HERMES_WEB_DEMO_USE_LLM", "1").lower() not in {"0", "false", "no"}
DEMO_STEP_DELAY = float(os.getenv("HERMES_WEB_DEMO_STEP_DELAY", "0.75"))
ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"
JOBS_ROOT = Path("/tmp/hermes-profile-web-demo-jobs")
JOBS_ROOT.mkdir(parents=True, exist_ok=True)

JOBS: dict[str, dict] = {}
LOCK = threading.Lock()


def safe_job(job_id: str) -> dict | None:
    with LOCK:
        job = JOBS.get(job_id)
        return dict(job) if job else None


def set_job(job_id: str, **updates) -> None:
    with LOCK:
        job = JOBS.setdefault(job_id, {})
        job.update(updates)
        job["updated_at"] = time.time()



def pace() -> None:
    if DEMO_STEP_DELAY > 0:
        time.sleep(DEMO_STEP_DELAY)


def append_progress(job_id: str, stage_index: int, message: str) -> None:
    with LOCK:
        job = JOBS.setdefault(job_id, {})
        progress = list(job.get("progress") or [])
        progress.append(message)
        job.update(status="running", stage_index=stage_index, progress=progress, updated_at=time.time())


def run_hermes_llm(job_id: str, stage_index: int, title: str, prompt: str, timeout: int = 120) -> tuple[bool, str]:
    """Run a real Hermes one-shot LLM call for web-demo generation steps."""
    if not HERMES_LLM_ENABLED:
        append_progress(job_id, stage_index, f"Skipped Hermes LLM call: {title}")
        return False, "Hermes LLM calls disabled by HERMES_WEB_DEMO_USE_LLM=0."
    append_progress(job_id, stage_index, f"Hermes LLM call: {title}")
    cmd = ["hermes", "chat", "-Q", "-q", prompt]
    try:
        proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    except FileNotFoundError:
        return False, "Hermes CLI was not found on PATH."
    except subprocess.TimeoutExpired as exc:
        return False, f"Hermes LLM call timed out after {timeout}s. Partial output: {exc.stdout or ''}"
    output = (proc.stdout or "").strip()
    if proc.returncode != 0 or not output:
        return False, (proc.stderr or proc.stdout or "Hermes LLM call failed").strip()
    return True, output


def hermes_expand_prompt(job_id: str, sentence: str, job_dir: Path) -> tuple[Path | None, str]:
    prompt = f"""You are improving a Hermes Agent profile generation request.

User sentence:
{sentence}

Return only a mature Hermes profile prompt in Markdown. Do not include preamble.
Make it specific, operational, and demoable. Include these sections:

## Simple sentence
## Mature Profile Prompt
### Mission
### Target users
### Primary workflows
### Required outputs
### Safety boundaries
### Tool and data policy
### Skills to include
### Demo behavior
### Validation expectations

The output should be suitable for docs/profile-prompt.md in an installable Hermes profile repository.
"""
    ok, output = run_hermes_llm(job_id, 0, "expand one sentence into mature profile prompt", prompt, timeout=150)
    path = job_dir / "enhanced-profile-prompt.md"
    if ok:
        path.write_text(output + "\n", encoding="utf-8")
        return path, "Hermes expanded the sentence into a mature profile prompt."
    path.write_text(f"# Hermes prompt expansion unavailable\n\n```text\n{output}\n```\n", encoding="utf-8")
    return None, f"Hermes prompt expansion unavailable. Used deterministic fallback. Reason: {output[:240]}"


def hermes_review_generated_profile(job_id: str, sentence: str, output: Path) -> tuple[Path | None, str]:
    snippets: list[str] = []
    for rel in ["docs/profile-prompt.md", "SOUL.md", "skills/focused-workflow/SKILL.md", "docs/playable-demo.md", "docs/validation-report.md"]:
        path = output / rel
        if path.exists() and path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")[:5000]
            snippets.append(f"## {rel}\n\n{text}")
    prompt = f"""Review this generated Hermes profile for demo quality.

Original user sentence:
{sentence}

Generated profile snippets:
{chr(10).join(snippets)}

Return only Markdown with:
## Verdict
A one-paragraph quality verdict.

## What is good
- concise bullets

## What still feels half baked
- concise bullets

## How to demo it
- concrete talk track bullets

Do not invent external claims. Be honest and useful.
"""
    ok, output_text = run_hermes_llm(job_id, 5, "review generated profile quality", prompt, timeout=150)
    path = output / "docs" / "llm-quality-review.md"
    if ok:
        path.write_text(output_text + "\n", encoding="utf-8")
        return path, "Hermes reviewed generated profile quality."
    path.write_text(f"# LLM Quality Review\n\nHermes review unavailable.\n\n```text\n{output_text}\n```\n", encoding="utf-8")
    return path, f"Hermes quality review unavailable. Reason: {output_text[:240]}"


def safe_profile_file(profile_dir: Path, rel: str) -> Path:
    rel_path = Path(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        raise ValueError("invalid file path")
    path = (profile_dir / rel_path).resolve()
    root = profile_dir.resolve()
    if not str(path).startswith(str(root)) or not path.is_file():
        raise ValueError("file not found")
    if path.name in {".env", "auth.json", "state.db"}:
        raise ValueError("file is not previewable")
    return path

def generated_file_summary(profile_dir: Path) -> list[dict[str, str]]:
    """Return the most important generated files for the web UI."""
    candidates = [
        ("SOUL.md", "agent identity"),
        ("distribution.yaml", "install manifest"),
        ("README.md", "usage guide"),
        ("config.yaml", "runtime defaults"),
        ("templates/profile.params.yaml", "generation params"),
        ("docs/profile-prompt.md", "mature prompt"),
        ("skills", "bundled skills"),
        ("scripts/validate_profile.py", "validator"),
        ("demo/index.html", "playable demo"),
        ("docs/output-diagram.svg", "contents diagram"),
        ("docs/validation-report.md", "quality report"),
        ("docs/llm-quality-review.md", "Hermes review"),
    ]
    summary: list[dict[str, str]] = []
    for rel, role in candidates:
        path = profile_dir / rel
        if rel == "skills" and path.exists():
            for skill_file in sorted(path.glob("*/SKILL.md"))[:4]:
                summary.append({"path": str(skill_file.relative_to(profile_dir)), "role": "bundled skill"})
            continue
        if path.exists() and path.is_file():
            summary.append({"path": rel, "role": role})
    return summary


def run_job(job_id: str, sentence: str) -> None:
    job_dir = JOBS_ROOT / job_id
    output = job_dir / "profile"
    artifacts = job_dir / "artifacts"
    job_dir.mkdir(parents=True, exist_ok=True)
    set_job(
        job_id,
        status="running",
        stage_index=0,
        progress=["Starting Hermes prompt engineering pass"],
    )
    try:
        enhanced_prompt_path, prompt_status = hermes_expand_prompt(job_id, sentence, job_dir)
        append_progress(job_id, 1, prompt_status)
        pace()
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "generate_from_sentence.py"),
            "--sentence",
            sentence,
            "--output",
            str(output),
            "--artifact-dir",
            str(artifacts),
            "--force",
            "--json",
        ]
        if enhanced_prompt_path:
            cmd.extend(["--profile-prompt-file", str(enhanced_prompt_path)])
        append_progress(job_id, 2, "Generating profile repository from refined prompt")
        pace()
        proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=180)
        raw = proc.stdout.strip()
        payload = json.loads(raw[raw.find("{"):]) if "{" in raw else {}
        if proc.returncode != 0 or not payload.get("ok"):
            error = payload.get("error") or proc.stderr or proc.stdout or "generation failed"
            set_job(job_id, status="failed", error=error, stdout=proc.stdout, stderr=proc.stderr)
            return
        append_progress(job_id, 3, "Rendered playable demo and contents diagram")
        pace()
        append_progress(job_id, 4, "Validation passed and download zip was packaged")
        pace()
        zip_path = Path(payload["zip_path"]) if payload.get("zip_path") else None
        demo_path = Path(payload["demo_html_path"])
        diagram_path = Path(payload["diagram_path"])
        prompt_path = Path(payload["prompt_path"])
        validation_report_path = Path(payload["validation_report_path"])
        review_path, review_status = hermes_review_generated_profile(job_id, sentence, output)
        append_progress(job_id, 5, review_status)
        generated_files = generated_file_summary(output)
        for item in generated_files:
            item["url"] = f"/api/jobs/{job_id}/file/{item['path']}"
        result = {
            "slug": payload["slug"],
            "display_name": payload["display_name"],
            "profile_dir": payload["profile_dir"],
            "quality_summary": "Validated profile repo",
            "quality_checks": [
                prompt_status,
                "Hermes profile validation passed.",
                "Mature prompt was preserved for review.",
                "Playable demo and contents diagram were generated.",
                review_status,
                "Download zip was packaged from allowlisted profile files.",
            ],
            "generated_files": generated_files,
            "zip_url": f"/api/jobs/{job_id}/artifact/zip" if zip_path else None,
            "demo_url": f"/api/jobs/{job_id}/artifact/demo",
            "diagram_url": f"/api/jobs/{job_id}/artifact/diagram",
            "prompt_url": f"/api/jobs/{job_id}/artifact/prompt",
            "validation_url": f"/api/jobs/{job_id}/artifact/validation",
            "install_command": f"unzip {payload['slug']}.zip && cd {payload['slug']} && hermes profile install . --name {payload['slug']}-local --yes",
        }
        final_progress = list((safe_job(job_id) or {}).get("progress") or []) + ["Complete"]
        set_job(
            job_id,
            status="complete",
            progress=final_progress,
            result=result,
            paths={
                "profile": str(output),
                "zip": str(zip_path) if zip_path else None,
                "demo": str(demo_path),
                "diagram": str(diagram_path),
                "prompt": str(prompt_path),
                "validation": str(validation_report_path),
            },
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    except Exception as exc:
        set_job(job_id, status="failed", error=str(exc))


class Handler(BaseHTTPRequestHandler):
    server_version = "HermesProfileDemo/0.1"

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, download_name: str | None = None) -> None:
        if not path.exists() or not path.is_file():
            self.send_json({"error": "artifact not found"}, 404)
            return
        data = path.read_bytes()
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if download_name:
            self.send_header("Content-Disposition", f"attachment; filename=\"{download_name}\"")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/jobs":
            self.send_json({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            self.send_json({"error": "request too large"}, 413)
            return
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            sentence = str(data.get("sentence") or "").strip()
            if not sentence:
                raise ValueError("sentence is required")
        except Exception as exc:
            self.send_json({"error": str(exc)}, 400)
            return
        job_id = uuid.uuid4().hex[:12]
        set_job(job_id, status="queued", progress=["Queued"], created_at=time.time(), sentence=sentence)
        thread = threading.Thread(target=run_job, args=(job_id, sentence), daemon=True)
        thread.start()
        self.send_json({"job_id": job_id, "status_url": f"/api/jobs/{job_id}"}, 202)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path.startswith("/api/jobs/"):
            parts = path.strip("/").split("/")
            job_id = parts[2] if len(parts) >= 3 else ""
            job = safe_job(job_id)
            if not job:
                self.send_json({"error": "job not found"}, 404)
                return
            if len(parts) == 3:
                public = {k: v for k, v in job.items() if k not in {"paths"}}
                public["job_id"] = job_id
                self.send_json(public)
                return
            if len(parts) >= 5 and parts[3] == "file":
                paths = job.get("paths") or {}
                profile = paths.get("profile")
                if not profile:
                    self.send_json({"error": "profile files are not available yet"}, 404)
                    return
                rel = "/".join(parts[4:])
                try:
                    file_path = safe_profile_file(Path(profile), rel)
                    data = file_path.read_text(encoding="utf-8", errors="replace")
                except Exception as exc:
                    self.send_json({"error": str(exc)}, 404)
                    return
                truncated = len(data) > MAX_FILE_PREVIEW
                if truncated:
                    data = data[:MAX_FILE_PREVIEW] + "\n\n[truncated]"
                self.send_json({"path": rel, "content": data, "truncated": truncated})
                return
            if len(parts) == 5 and parts[3] == "artifact":
                kind = parts[4]
                paths = job.get("paths") or {}
                artifact = paths.get(kind)
                if not artifact:
                    self.send_json({"error": "artifact not available"}, 404)
                    return
                download = None
                if kind == "zip":
                    slug = (job.get("result") or {}).get("slug", "generated-profile")
                    download = f"{slug}.zip"
                self.send_file(Path(artifact), download)
                return
            self.send_json({"error": "not found"}, 404)
            return
        if path in {"/", ""}:
            path = "/index.html"
        candidate = (STATIC / path.lstrip("/")).resolve()
        if not str(candidate).startswith(str(STATIC.resolve())):
            self.send_json({"error": "not found"}, 404)
            return
        self.send_file(candidate)


def main() -> int:
    print(f"Hermes profile web demo: http://{HOST}:{PORT}")
    print(f"Jobs directory: {JOBS_ROOT}")
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
