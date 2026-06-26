#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

python3 scripts/validate_profile.py .
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/*.py

gen_root="$(mktemp -d /tmp/hermes-profile-template-gen.XXXXXX)"
python3 scripts/generate_profile.py \
  --params templates/profile.params.yaml \
  --output "$gen_root/generated"
python3 "$gen_root/generated/scripts/validate_profile.py" "$gen_root/generated"

if ! command -v hermes >/dev/null 2>&1; then
  echo "Hermes CLI not found. Skipping install smoke test after validation and generator smoke passed."
  exit 0
fi

home="$(mktemp -d /tmp/hermes-profile-template-home.XXXXXX)"
HERMES_HOME="$home" hermes profile install . --name profile-smoke --yes

test -f "$home/profiles/profile-smoke/SOUL.md"
test -f "$home/profiles/profile-smoke/distribution.yaml"
test -f "$home/profiles/profile-smoke/scripts/generate_profile.py"
test -f "$home/profiles/profile-smoke/templates/profile.params.yaml"

echo "Hermes profile install smoke passed: $home/profiles/profile-smoke"
