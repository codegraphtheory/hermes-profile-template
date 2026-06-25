#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

fixture_output="$(scripts/demo_fixture.sh)"
eval "$(printf '%s\n' "$fixture_output" | awk '/^export / { print }')"
manifest="$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/demo-fixture.env"
trap 'scripts/demo_cleanup.sh "$manifest" >/dev/null 2>&1 || true' EXIT

python3 scripts/new_profile.py \
  --name security-reviewer \
  --display-name "Security Reviewer" \
  --description "Reviews code and architecture changes for security risk" \
  --output "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/security-reviewer"

python3 "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/security-reviewer/scripts/validate_profile.py" \
  "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/security-reviewer"

test -f "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/security-reviewer/README.md"
test -f "$HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE/security-reviewer/distribution.yaml"

if command -v hermes >/dev/null 2>&1; then
  HERMES_HOME="$HERMES_HOME" hermes profile install "$root" --name profile-architect-demo --yes
  test -f "$HERMES_HOME/profiles/profile-architect-demo/SOUL.md"
fi

echo "Demo smoke passed"
