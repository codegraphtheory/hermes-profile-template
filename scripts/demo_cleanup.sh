#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/demo_cleanup.sh /path/to/demo-fixture.env" >&2
  exit 2
fi

manifest="$1"
if [ ! -f "$manifest" ]; then
  echo "Demo manifest not found: $manifest" >&2
  exit 1
fi

workspace=""
hermes_home=""
while IFS='=' read -r key value; do
  case "$key" in
    HERMES_PROFILE_TEMPLATE_DEMO_WORKSPACE) workspace="$value" ;;
    HERMES_HOME) hermes_home="$value" ;;
  esac
done < "$manifest"

for path in "$workspace" "$hermes_home"; do
  if [ -n "$path" ] && [[ "$path" == /tmp/hermes-profile-template-demo.* ]]; then
    rm -rf "$path"
    echo "Removed $path"
  elif [ -n "$path" ]; then
    echo "Refusing to remove non-demo path: $path" >&2
    exit 1
  fi
done
