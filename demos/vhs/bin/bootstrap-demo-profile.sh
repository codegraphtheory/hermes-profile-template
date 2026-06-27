#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../sanitize-recording-env.sh"

PROFILE="${DEMO_PROFILE:-}"
if [[ -z "$PROFILE" ]] && [[ -f distribution.yaml ]]; then
  PROFILE="$(grep -E '^name:' distribution.yaml | head -1 | sed 's/^name:[[:space:]]*//;s/"//g')"
fi
PROFILE="${PROFILE:-$(basename "$REPO_ROOT")}"

ORG="${DEMO_GITHUB_ORG:-codegraphtheory}"
SOURCE="${DEMO_INSTALL_SOURCE:-github}"

if [[ "$SOURCE" == "github" ]]; then
  echo "Installing Hermes profile from github.com/$ORG/$PROFILE"
  hermes profile install "github.com/$ORG/$PROFILE" --name "$PROFILE" --force -y
else
  CLEAN="$REPO_ROOT/demos/vhs/staging/clean-repo"
  rm -rf "$CLEAN"
  mkdir -p "$CLEAN"
  rsync -a --exclude .venv --exclude .git --exclude 'demos/vhs/staging' --exclude eval/runs "$REPO_ROOT/" "$CLEAN/"
  echo "Installing Hermes profile: $PROFILE (local staging)"
  hermes profile install "$CLEAN" --name "$PROFILE" --force -y
fi
echo "Profile ready: hermes -p $PROFILE chat"