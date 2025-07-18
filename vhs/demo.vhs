# VHS script to showcase git-copilot-commit
# Run with: vhs < demo.vhs

# Set up the terminal
Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 600
Set PlaybackSpeed 1.0
Set TypingSpeed 50ms
Set Theme "Catppuccin Mocha"

# Show the title
Type "# git-copilot-commit demo"
Enter
Enter
Sleep 2s

# Demonstrate the tool
Type "uv run git-copilot-commit commit"
Enter
Sleep 5s

Enter # Yes to stage files
Sleep 5s

Enter # Yes to commit
Sleep 5s

Type "git log --oneline --graph --all -n 5"
Enter

Sleep 10s

Output demo.gif
