# `git-copilot-commit`

AI-powered Git commit assistant that generates conventional commit messages using GitHub Copilot.

## Features

- Generates commit messages based on your staged changes
- Supports multiple AI models: GPT-4, Claude, Gemini, and more
- Allows editing of generated messages before committing
- Follows the [Conventional Commits](https://www.conventionalcommits.org/) standard

## Installation

Install with [`uv`] (recommended):

```bash
uv tool install git-copilot-commit
```

Or with `pipx`:

```bash
pipx install git-copilot-commit
```

Or run directly with [`uv`]:

```bash
uvx git-copilot-commit --help
```

[`uv`]: https://github.com/astral-sh/uv

## Prerequisites

- Active GitHub Copilot subscription

## Quick Start

1. Authenticate with GitHub Copilot:

```bash
git-copilot-commit authenticate
```

2. Make changes in your repository.

3. Generate and commit:

```bash
git-copilot-commit commit
```

## Usage

### Commit changes

```bash
git-copilot-commit commit
```

**Options:**

- `--all, -a`: Stage all files
- `--verbose, -v`: Show detailed output
- `--model, -m`: Choose an AI model

Workflow:

1. Analyze changes
2. Prompt to stage files
3. Generate a commit message
4. Choose to commit, edit, or cancel

### Authenticate

```bash
git-copilot-commit authenticate
```

### List models

```bash
git-copilot-commit models
```

### Configure

```bash
git-copilot-commit config --show
git-copilot-commit config --set-default-model gpt-4o
```

## Examples

Commit all changes:

```bash
git-copilot-commit commit --all
```

Verbose output:

```bash
git-copilot-commit commit --verbose
```

Use a specific model:

```bash
git-copilot-commit commit --model claude-3.5-sonnet
```

Set and use a default model:

```bash
git-copilot-commit config --set-default-model gpt-4o
git-copilot-commit commit
git-copilot-commit commit --model claude-3.5-sonnet
```

## Commit Message Format

Follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting only
- `refactor`: Code restructure
- `perf`: Performance
- `test`: Tests
- `chore`: Maintenance
- `revert`: Revert changes

**Examples:**

- `feat(auth): add JWT authentication`
- `fix(db): retry connection on failure`
- `docs(readme): update install steps`
- `refactor(utils): simplify date parsing`

## Git Configuration

Add a git alias by adding the following to your `~/.gitconfig`:

```ini
[alias]
    ai-commit = "!f() { git-copilot-commit commit $@; }; f"
```

Now you can run:

```bash
git ai-commit
git ai-commit --model claude-3.5-sonnet
git ai-commit --all --verbose
```

Show more context in diffs:

```bash
git config --global diff.context 3
```
