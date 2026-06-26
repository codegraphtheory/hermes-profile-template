#!/usr/bin/env bash
set -euo pipefail

# Remove temporary Hermes demo workspaces created by demo_fixture.py
find "${TMPDIR:-/tmp}" -maxdepth 1 -type d -name 'hermes-demo-*' -print -exec rm -rf {} + 2>/dev/null || true
echo "Removed temporary hermes-demo-* workspaces."
