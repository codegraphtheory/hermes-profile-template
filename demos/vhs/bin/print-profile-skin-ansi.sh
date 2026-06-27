#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../sanitize-recording-env.sh"

PROFILE="${DEMO_PROFILE:-}"
if [[ -z "$PROFILE" ]] && [[ -f distribution.yaml ]]; then
  PROFILE="$(grep -E '^name:' distribution.yaml | head -1 | sed 's/^name:[[:space:]]*//;s/"//g')"
fi
PROFILE="${PROFILE:-$(basename "$REPO_ROOT")}"

SKIN_DIR="$HERMES_HOME/profiles/$PROFILE/skins"
SKIN_FILE="$SKIN_DIR/${PROFILE}.yaml"
[[ -f "$SKIN_FILE" ]] || SKIN_FILE="$(find "$SKIN_DIR" -maxdepth 1 -name '*.yaml' | head -1)"

CYAN='\033[38;2;86;212;232m'
MAG='\033[38;2;198;120;221m'
GOLD='\033[38;2;255;215;0m'
DIM='\033[38;2;136;146;155m'
RST='\033[0m'

echo -e "${MAG}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}"
echo -e "${GOLD}  Hermes profile${RST} ${CYAN}$PROFILE${RST} ${DIM}· skinned terminal preview${RST}"
if [[ -f "$SKIN_FILE" ]]; then
  echo -e "${DIM}  skin file:${RST} $(basename "$SKIN_FILE")"
fi
echo -e "${MAG}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}"
if command -v pyfiglet >/dev/null 2>&1; then
  pyfiglet -f slant "$PROFILE" 2>/dev/null | head -8 | while IFS= read -r line; do echo -e "${CYAN}${line}${RST}"; done
else
  echo -e "${CYAN}  $(echo "$PROFILE" | tr 'a-z' 'A-Z')${RST}"
fi
echo -e "${DIM}  display.skin from config.yaml · hooks · skills · SOUL${RST}"
if [[ -f SOUL.md ]]; then
  echo -e "${GOLD}── SOUL ──${RST}"
  sed -n '1,8p' SOUL.md | sed 's/^/  /'
fi
if [[ -d skills ]]; then
  echo -e "${GOLD}── skills ($(ls skills | wc -l | tr -d ' ')) ──${RST}"
  ls skills | head -8 | sed 's/^/  · /'
fi
echo -e "${MAG}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}"