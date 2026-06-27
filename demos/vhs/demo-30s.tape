Output demos/demo.gif
Set Shell "bash"
Set FontSize 20
Set Width 1280
Set Height 720
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms

Type "# Hermes Profile Template · prompt to repo" Enter
Sleep 600ms

Hide
Type "python3 scripts/validate_profile.py ." Enter
Sleep 5s
Type "python3 scripts/profile_scorecard.py . | head -14" Enter
Sleep 6s
Type "head -8 distribution.yaml" Enter
Sleep 4s
Show

Type "hermes profile install github.com/codegraphtheory/hermes-profile-template --name profile-architect --yes" Enter
Sleep 4s
Type "# One sentence in · installable profile distribution out" Enter
Sleep 3s