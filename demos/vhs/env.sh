#!/usr/bin/env bash
# Minimal env for VHS (repos without heavy-coder src/).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
if [[ "${VHS_RECORDING:-}" != "1" ]]; then
  cd "$REPO_ROOT"
fi