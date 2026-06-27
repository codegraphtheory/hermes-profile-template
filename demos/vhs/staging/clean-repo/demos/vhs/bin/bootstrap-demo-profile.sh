#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../sanitize-recording-env.sh
source "$SCRIPT_DIR/../sanitize-recording-env.sh"

PROFILE="${DEMO_PROFILE:-}"
if [[ -z "$PROFILE" ]] && [[ -f distribution.yaml ]]; then
  PROFILE="$(grep -E '^name:' distribution.yaml | head -1 | sed 's/^name:[[:space:]]*//;s/"//g')"
fi
PROFILE="${PROFILE:-$(basename "$REPO_ROOT")}"

CLEAN="$REPO_ROOT/demos/vhs/staging/clean-repo"
rm -rf "$CLEAN"
mkdir -p "$CLEAN"
rsync -a \
  --exclude .venv \
  --exclude .git \
  --exclude 'demos/vhs/staging' \
  --exclude eval/runs \
  --exclude 'demos/vhs/out' \
  "$REPO_ROOT/" "$CLEAN/"

echo "Installing Hermes profile: $PROFILE"
hermes profile install "$CLEAN" --name "$PROFILE" --force -y
echo "Profile ready: hermes -p $PROFILE chat"