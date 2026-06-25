#!/usr/bin/env bash
set -euo pipefail

# Resolve script root
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

echo "Running smoke test for Demo 1 (flags-based scaffolding)..."

# 1. Setup temporary directories
DEMO_WORK="/tmp/hermes-demo-smoke-work"
rm -rf "$DEMO_WORK"
mkdir -p "$DEMO_WORK"

# 2. Run new_profile.py
python3 scripts/new_profile.py \
  --name code-cleaner \
  --display-name "Code Cleaner" \
  --description "Reviews codebase files to remove unused imports and dead code." \
  --output "$DEMO_WORK/code-cleaner"

# 3. Validate the output directory
python3 "$DEMO_WORK/code-cleaner/scripts/validate_profile.py" "$DEMO_WORK/code-cleaner"

# 4. Clean up
rm -rf "$DEMO_WORK"

echo "Demo smoke test passed successfully!"
