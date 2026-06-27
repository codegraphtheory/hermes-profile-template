Output demos/demo.gif
Set Shell "bash"
Set FontSize 16
Set Width 1280
Set Height 720
Set Theme "Builtin Dark"
Set TypingSpeed 55ms

Hide
Type "source demos/vhs/sanitize-recording-env.sh" Enter
Type "bash demos/vhs/bin/bootstrap-demo-profile.sh" Enter
Sleep 8s
Show

Type "# Skinned Hermes TUI (/help + profile skin)" Enter
Sleep 800ms

Hide
Type "source demos/vhs/sanitize-recording-env.sh" Enter
Sleep 200ms
Type "bash demos/vhs/bin/hermes-tui-skin-demo.sh" Enter
Sleep 22s
Show
