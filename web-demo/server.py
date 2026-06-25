#!/usr/bin/env python3
"""Local web demo for prompt-to-profile generation.

Run:
  python3 web-demo/server.py
Then open http://127.0.0.1:8765
"""
from __future__ import annotations

import json
import mimetypes
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


def run_job(job_id: str, sentence: str) -> None:
    job_dir = JOBS_ROOT / job_id
    output = job_dir / "profile"
    artifacts = job_dir / "artifacts"
    job_dir.mkdir(parents=True, exist_ok=True)
    set_job(
        job_id,
        status="running",
        stage_index=0,
        progress=["Expanding sentence into a mature profile prompt"],
    )
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
    try:
        set_job(
            job_id,
            stage_index=2,
            progress=[
                "Generating profile repository",
                "Rendering playable demo and contents diagram",
                "Running validation and packaging download",
            ],
        )
        proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=180)
        raw = proc.stdout.strip()
        payload = json.loads(raw[raw.find("{"):]) if "{" in raw else {}
        if proc.returncode != 0 or not payload.get("ok"):
            error = payload.get("error") or proc.stderr or proc.stdout or "generation failed"
            set_job(job_id, status="failed", error=error, stdout=proc.stdout, stderr=proc.stderr)
            return
        zip_path = Path(payload["zip_path"]) if payload.get("zip_path") else None
        demo_path = Path(payload["demo_html_path"])
        diagram_path = Path(payload["diagram_path"])
        prompt_path = Path(payload["prompt_path"])
        validation_report_path = Path(payload["validation_report_path"])
        result = {
            "slug": payload["slug"],
            "display_name": payload["display_name"],
            "profile_dir": payload["profile_dir"],
            "zip_url": f"/api/jobs/{job_id}/artifact/zip" if zip_path else None,
            "demo_url": f"/api/jobs/{job_id}/artifact/demo",
            "diagram_url": f"/api/jobs/{job_id}/artifact/diagram",
            "prompt_url": f"/api/jobs/{job_id}/artifact/prompt",
            "validation_url": f"/api/jobs/{job_id}/artifact/validation",
            "install_command": f"unzip {payload['slug']}.zip && cd {payload['slug']} && hermes profile install . --name {payload['slug']}-local --yes",
        }
        set_job(
            job_id,
            status="complete",
            progress=["Complete"],
            result=result,
            paths={
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
