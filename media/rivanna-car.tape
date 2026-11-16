Output media/rivanna-car.gif
Set Shell zsh
Set FontSize 15
Set Width 1280
Set Height 740
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms
Env PS1 "$ "
Hide
Type 'cd "$(git rev-parse --show-toplevel)" && clear' Enter
Show
Type "sim run --scenario sim/scenario.yaml --timeout 10 --ascii 2>&1 \" Enter
Type "    | grep --line-buffered -E 'initialized|Precharge disabled|\[bps\]' \" Enter
Type "    | sed -u -E 's#^.*/Rivanna3S/##'" Enter
Sleep 35s
Sleep 4s
