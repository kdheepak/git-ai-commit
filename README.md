# git-copilot-commit

🤖 AI-powered Git commit assistant that automatically generates conventional commit messages using
GitHub Copilot.

## Features

- **AI-Generated Commit Messages**: Uses GitHub Copilot to analyze your staged changes and generate
  conventional commit messages
- **Message Editing**: Edit generated messages using your git-configured editor or commit directly
- **Conventional Commits**: Follows the [Conventional Commits](https://www.conventionalcommits.org/)
  specification
- **Rich Output**: Beautiful terminal output with syntax highlighting and tables

## Installation

Install using uv (recommended):

```bash
uv tool install git-copilot-commit
# or
uvx git-copilot-commit
```

Or with pip:

```bash
pipx install git-copilot-commit
```

## Prerequisites

1. **GitHub Copilot Access**: You need an active GitHub Copilot subscription
2. **Authentication**: Authenticate with GitHub Copilot before first use

## Quick Start

1. **Authenticate with GitHub Copilot**:

   ```bash
   git-copilot-commit authenticate
   ```

2. **Make some changes** in your git repository

3. **Generate and commit**:

   ```bash
   git-copilot-commit commit
   ```

## Usage

#### `commit`

Automatically commit changes in the current git repository:

```bash
git-copilot-commit commit
```

**Options:**

- `--all, -a`: Stage all files before committing
- `--verbose, -v`: Show verbose output with file details

1. The tool analyzes your changes
2. Prompts you to stage files (if needed)
3. Generates an AI-powered commit message
4. Offers three choices:
   - `(c)ommit`: Commit with the generated message
   - `(e)dit`: Edit the message in your git-configured editor
   - `(q)uit`: Cancel the commit

#### `authenticate`

Set up authentication with GitHub Copilot:

```bash
git-copilot-commit authenticate
```

#### `models`

List available AI models:

```bash
git-copilot-commit models
```

### Examples

**Commit all changes with staging prompts:**

```bash
git-copilot-commit commit --all
```

**Commit with verbose output:**

```bash
git-copilot-commit commit --verbose
```

## Generated Commit Message Format

The tool follows the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>
```

**Supported Types:**

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic changes)
- `refactor`: Code restructuring (no behavior changes)
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (tooling, dependencies, etc.)
- `revert`: Reverting previous changes

**Example Messages:**

- `feat(auth): add user authentication with JWT`
- `fix(database): handle connection retries properly`
- `docs(readme): update installation instructions`
- `refactor(utils): simplify date parsing logic`
