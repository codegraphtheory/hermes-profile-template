#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
source demos/vhs/sanitize-recording-env.sh
bash demos/vhs/bin/bootstrap-demo-profile.sh
sleep 2
bash demos/vhs/bin/print-profile-skin-ansi.sh
sleep 3
PROFILE="${DEMO_PROFILE:-$(grep -E '^name:' distribution.yaml | head -1 | sed 's/^name:[[:space:]]*//;s/"//g')}"
PROFILE="${PROFILE:-$(basename "$REPO_ROOT")}"
echo ""
echo "hermes -p $PROFILE chat --cli"
hermes -p "$PROFILE" chat --cli -q "Name three skills this profile provides." 2>&1 | head -20 || true
sleep 2