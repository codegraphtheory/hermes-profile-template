#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../sanitize-recording-env.sh"

PROFILE="${DEMO_PROFILE:-}"
if [[ -z "$PROFILE" ]] && [[ -f distribution.yaml ]]; then
  PROFILE="$(grep -E '^name:' distribution.yaml | head -1 | sed 's/^name:[[:space:]]*//;s/"//g')"
fi
PROFILE="${PROFILE:-$(basename "$REPO_ROOT")}"

command -v expect >/dev/null || { echo "expect required" >&2; exit 1; }
command -v hermes >/dev/null || { echo "hermes CLI required" >&2; exit 1; }

export TERM=xterm-256color
stty cols 120 rows 36 2>/dev/null || true

export HOME HERMES_HOME PROFILE
expect <<'EXPECT_EOF'
set timeout 28
set profile $env(PROFILE)
log_user 1
spawn env HOME=$env(HOME) HERMES_HOME=$env(HERMES_HOME) TERM=xterm-256color HERMES_TUI_FAST_ECHO=0 hermes -p $profile chat
sleep 5
send "/help\r"
sleep 4
send "/skin\r"
sleep 3
send "\x03"
expect eof
EXPECT_EOF