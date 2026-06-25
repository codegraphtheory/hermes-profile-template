#!/usr/bin/env bash
# Sets up a clean, isolated demo workspace with a temporary HERMES_HOME.
# Source this file before recording a demo:
#   source scripts/demo_fixture.sh
# All paths and secrets are sandboxed — nothing from your real environment leaks.

set -euo pipefail

DEMO_ROOT="${DEMO_ROOT:-/tmp/hermes-profile-builder-demo}"
export HERMES_HOME="${DEMO_ROOT}/hermes-home"

rm -rf "${DEMO_ROOT}"
mkdir -p "${DEMO_ROOT}" "${HERMES_HOME}"

# Provide safe placeholder credentials so demos work without real keys.
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-demo-key-not-real}"
export GITHUB_TOKEN="${GITHUB_TOKEN:-demo-token-not-real}"

# Mask real home directory in shell prompt so it does not appear in recordings.
export HOME="${DEMO_ROOT}"
export PS1="[hermes-demo] \W \$ "

echo "Demo workspace ready at: ${DEMO_ROOT}"
echo "HERMES_HOME             : ${HERMES_HOME}"
echo "Run 'source scripts/demo_cleanup.sh' when finished."
