#!/usr/bin/env bash
# One-shot demo for VHS (always run from repo root).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
source demos/vhs/sanitize-recording-env.sh
bash demos/vhs/bin/bootstrap-demo-profile.sh
bash demos/vhs/bin/hermes-tui-skin-demo.sh