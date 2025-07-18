# `git-copilot-commit`

AI-powered Git commit assistant that generates conventional commit messages using GitHub Copilot.

![](https://github.com/user-attachments/assets/6a6d70a6-6060-44e6-8cf4-a6532e9e9142)

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
$ uvx git-copilot-commit commit --help
Usage: git-copilot-commit commit [OPTIONS]

  Automatically commit changes in the current git repository.

Options:
  -a, --all         Stage all files before committing
  -v, --verbose     Show verbose output
  -m, --model TEXT  Model to use for generating commit message
  --help            Show this message and exit.
```

### Authenticate

```bash
$ uvx git-copilot-commit authenticate --help
Usage: git-copilot-commit authenticate [OPTIONS]

  Autheticate with GitHub Copilot.

Options:
  --help  Show this message and exit.
```

### List models

```bash
$ uvx git-copilot-commit models --help
Usage: git-copilot-commit models [OPTIONS]

  List models available for chat in a table.

Options:
  --help  Show this message and exit.
```

### Configure

```bash
$ uvx git-copilot-commit config --help
Usage: git-copilot-commit config [OPTIONS]

  Manage application configuration.

Options:
  --set-default-model TEXT  Set default model for commit messages
  --show                    Show current configuration
  --help                    Show this message and exit.
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
git ai-commit --all --verbose
git ai-commit --model claude-3.5-sonnet
```

Additionally, show more context in diffs by running the following command:

```bash
git config --global diff.context 3
```
