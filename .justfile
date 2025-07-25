# Default recipe calls commit
default: commit

# Pass all arguments directly to git-copilot-commit
commit *args:
    uv run git-copilot-commit commit {{args}}

