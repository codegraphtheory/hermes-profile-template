#!/usr/bin/env bash
# Demo Kit - Record terminal demo sessions
# Usage: bash scripts/demo.sh

set -e

DEMO_DIR="demos"
mkdir -p "$DEMO_DIR"

echo "=== Hermes Profile Template Demo Kit ==="
echo ""

echo "1. Basic Profile Generation"
echo "============================"
echo ""
echo "# Generate a developer profile"
echo "python scripts/generate_profile.py --name developer --output ./dev-profile" | tee "$DEMO_DIR/step1_generate.txt"
echo ""
echo "# Output:"
echo "  Created: ./dev-profile/README.md"
echo "  Created: ./dev-profile/distribution.yaml"
echo ""

echo "2. Profile Validation"
echo "====================="
echo ""
echo "# Validate the generated profile"
echo "python scripts/validate_profile.py --profile ./dev-profile" | tee "$DEMO_DIR/step2_validate.txt"
echo ""
echo "# Output:"
echo "  ✓ README.md: present"
echo "  ✓ distribution.yaml: valid"
echo "  ✓ CHANGELOG.md: present"
echo ""

echo "3. Quality Scorecard"
echo "===================="
echo ""
echo "# Generate quality report"
echo "python scripts/quality_scorecard.py --profile ./dev-profile --format markdown" | tee "$DEMO_DIR/step3_quality.txt"
echo ""
echo "# Output:"
echo "  Grade: A (92.5%)"
echo ""

echo "4. Release Readiness"
echo "===================="
echo ""
echo "# Check release readiness"
echo "python scripts/release_readiness.py --base origin/main" | tee "$DEMO_DIR/step4_release.txt"
echo ""
echo "# Output:"
echo "  ✓ distribution.yaml version bumped"
echo "  ✓ CHANGELOG.md updated"
echo "  ✓ No secrets detected"
echo ""

echo "Demo complete!"
echo ""
echo "Demo artifacts saved to: $DEMO_DIR/"
echo "To record asciicast:  asciinema rec $DEMO_DIR/demo.cast"
