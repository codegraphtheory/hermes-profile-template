#!/usr/bin/env bash
set -euo pipefail

prefix="${HERMES_PROFILE_TEMPLATE_DEMO_PREFIX:-/tmp/hermes-profile-template-demo}"
workspace="$(mktemp -d "${prefix}.workspace.XXXXXX")"
hermes_home="$(mktemp -d "${prefix}.home.XXXXXX")"
manifest="${workspace}/demo-fixture.env"

cat > "$manifest" <<EOF
HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE=$workspace
HERMES_HOME=$hermes_home
EOF

cat <<EOF
# Demo fixture created. Run this in your shell before recording:
export HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE="$workspace"
export HERMES_HOME="$hermes_home"

# Cleanup when done:
scripts/demo_cleanup.sh "$manifest"
EOF
