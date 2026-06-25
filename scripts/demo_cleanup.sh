#!/usr/bin/env bash
# Removes the temporary demo workspace created by demo_fixture.sh.
# Source this file after a recording session:
#   source scripts/demo_cleanup.sh

set -euo pipefail

DEMO_ROOT="${DEMO_ROOT:-/tmp/hermes-profile-builder-demo}"

if [ -d "${DEMO_ROOT}" ]; then
    rm -rf "${DEMO_ROOT}"
    echo "Demo workspace removed: ${DEMO_ROOT}"
else
    echo "Nothing to clean — ${DEMO_ROOT} does not exist."
fi

# Unset demo variables if they were set by demo_fixture.sh
unset HERMES_HOME OPENROUTER_API_KEY GITHUB_TOKEN 2>/dev/null || true
echo "Demo environment variables cleared."
