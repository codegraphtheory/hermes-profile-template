# Sourced to set up an isolated recording environment. Do not run directly.
# Usage: source scripts/demo_fixture.sh

DEMO_WORK="/tmp/hermes-demo-workspace"
DEMO_HOME="/tmp/hermes-demo-home"

echo "Setting up clean isolated demo environment..."

# Reset directories
rm -rf "$DEMO_WORK" "$DEMO_HOME"
mkdir -p "$DEMO_WORK" "$DEMO_HOME"

# Export environments for isolation
export HERMES_HOME="$DEMO_HOME"
export PS1="[demo] \$ "
unset HISTFILE

# Resolve script root and copy repo template structure
# We identify the location of this script to copy dependencies
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cp -r "$REPO_ROOT/scripts" "$DEMO_WORK/"
cp -r "$REPO_ROOT/templates" "$DEMO_WORK/"
cp "$REPO_ROOT/distribution.yaml" "$DEMO_WORK/"
cp "$REPO_ROOT/config.yaml" "$DEMO_WORK/"
cp "$REPO_ROOT/README.md" "$DEMO_WORK/"

cd "$DEMO_WORK"

echo "Workspace initialized at: $DEMO_WORK"
echo "HERMES_HOME configured to: $HERMES_HOME"
echo "History file unset. Prompt simplified."
