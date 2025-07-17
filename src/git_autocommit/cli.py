import os
import subprocess
from pathlib import Path
import tempfile

import typer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
)
from rich.table import Table
from rich.prompt import Confirm
from rich.panel import Panel

from pycopilot.copilot import Copilot
from pycopilot.auth import Authentication

# Configure console
console = Console()

app = typer.Typer(name=__name__, help=__doc__, add_completion=False)


SCRIPT_NAME = f"./{Path(__file__).name}"


def get_git_status():
    """Get git status, staged changes, and unstaged changes."""
    try:
        status_result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )

        diff_result = subprocess.run(
            ["git", "diff", "--staged"], capture_output=True, text=True, check=True
        )

        unstaged_diff = subprocess.run(
            ["git", "diff"], capture_output=True, text=True, check=True
        )

        untracked_files = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=True,
        )

        return (
            status_result.stdout.strip(),
            diff_result.stdout.strip(),
            unstaged_diff.stdout.strip(),
            untracked_files.stdout.strip(),
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Git command failed: {e}[/red]")
        raise typer.Exit(1)


def generate_commit_message(status_output, diff_output):
    """Generate a conventional commit message using Copilot API."""

    client = Copilot(
        system_prompt="""
You are a Git commit message assistant trained to write a single clear, structured, and informative commit message following the Conventional Commits specification based on the provided `git diff --staged` output.

Output format: Provide only the commit message without any additional text, explanations, or formatting markers.

The guidelines for the commit messages are as follows:

1. Format

  ```
  <type>[optional scope]: <description>
  ```

  - The first line (title) should be at most 72 characters long.
  - If the natural description exceeds 72 characters, prioritize the most important aspect.
  - Use abbreviations when appropriate: `config` not `configuration`.
  - The body (if present) should be wrapped at 100 characters per line.

2. Valid Commit Types:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic changes)
- `refactor`: Code restructuring (no behavior changes)
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (e.g., tooling, CI/CD, dependencies)
- `revert`: Reverting previous changes

3. Scope (Optional but encouraged):

- Enclose in parentheses, e.g., feat(auth): add login endpoint.
- Use the affected module, component, or area: `auth`, `api`, `ui`, `database`, `config`.
- For multiple files in same area, use the broader scope: `feat(auth): add login and logout endpoints`.
- For single files, you may use filename: `fix(user-service): handle null email validation`.
- Scope should be a single word or hyphenated phrase describing the affected module.

4. Description:

- Use imperative mood (e.g., "add feature" instead of "added" or "adds").
- Be concise yet informative.
- Focus on the primary change, not all details.
- Do not make assumptions about why the change was made or how it works.
- Do not say "improving code readability" or similar; focus on just the change itself.

5. Analyzing Git Diffs:

- Focus on the logical change, not individual line modifications.
- Group related file changes under one logical scope.
- Identify the primary purpose of the change set.
- If changes span multiple unrelated areas, focus on the most significant one.

Examples:

✅ Good Commit Messages:

- feat(api): add user authentication with JWT
- fix(database): handle connection retries properly
- docs(readme): update installation instructions
- refactor(utils): simplify date parsing logic
- chore(deps): update dependencies to latest versions
- feat(auth): implement OAuth2 integration
- fix(payments): resolve double-charging bug in subscription renewal
- refactor(database): extract query builder into separate module
- chore(ci): add automated security scanning to pipeline
- docs(api): add OpenAPI specifications for user endpoints

❌ Strongly Avoid:

- Vague descriptions: "fixed bug", "updated code", "made changes"
- Past tense: "added feature", "fixed issue"
- Explanations of why: "to improve performance", "because users requested"
- Implementation details: "using React hooks", "with try-catch blocks"
- Not in imperative mood: "new feature", "updates stuff"

Given a Git diff, a list of modified files, or a short description of changes,
generate a single clear and structured Conventional Commit message following the above rules.
If multiple changes are detected, prioritize the most important changes in a single commit message.
Do not add any body or footer.
You can only give one reply for each conversation turn.

Avoid wrapping the whole response in triple backticks.
"""
    )

    prompt = "`git status`:\n```\n\n{status_output}\n```\n\n`git diff --staged`:\n\n```\n{diff_output}\n```\n\nGenerate a conventional commit message:"
    response = client.ask(
        prompt.format(status_output=status_output, diff_output=diff_output),
    )
    return response.content


@app.command()
def authenticate():
    """Autheticate with GitHub Copilot."""
    Authentication().auth()


@app.command()
def commit():
    """
    Automatically commit changes in the current git repository.
    """
    status_output, diff_output, unstaged_output, untracked_output = get_git_status()

    if not status_output:
        console.print("[yellow]No changes to commit.[/yellow]")
        raise typer.Exit()

    # Check for untracked files and unstaged changes
    has_untracked = bool(untracked_output.strip())
    has_unstaged = bool(unstaged_output.strip())

    # If no staged changes, prompt to stage modified files
    if not diff_output:
        console.print("[yellow]No staged changes found.[/yellow]")

        # Check if there are untracked files and prompt to add them
        if has_untracked:
            if Confirm.ask(
                "There are untracked files. Do you want to add all files (git add .)?"
            ):
                try:
                    subprocess.run(["git", "add", "."], check=True)
                    console.print("[green]Added all files.[/green]")
                except subprocess.CalledProcessError as e:
                    console.print(f"[red]Failed to add files: {e}[/red]")
                    raise typer.Exit(1)
            else:
                console.print("No files added.")
                raise typer.Exit()
        else:
            # Only modified files, prompt to stage them
            if Confirm.ask("Do you want to stage modified files (git add -u)?"):
                try:
                    subprocess.run(["git", "add", "-u"], check=True)
                    console.print("[green]Staged modified files.[/green]")
                except subprocess.CalledProcessError as e:
                    console.print(f"[red]Failed to stage files: {e}[/red]")
                    raise typer.Exit(1)
            else:
                console.print("No files staged.")
                raise typer.Exit()

        # Get updated status and diff after staging
        status_output, diff_output, unstaged_output, untracked_output = get_git_status()

        if not diff_output:
            console.print("[yellow]Still no staged changes to commit.[/yellow]")
            raise typer.Exit()
    elif has_untracked:
        # There are staged changes but also untracked files
        if Confirm.ask(
            "There are untracked files. Do you want to add them too (git add .)?"
        ):
            try:
                subprocess.run(["git", "add", "."], check=True)
                console.print("[green]Added untracked files.[/green]")
                # Get updated status and diff after adding untracked files
                status_output, diff_output, unstaged_output, untracked_output = (
                    get_git_status()
                )
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Failed to add untracked files: {e}[/red]")
                # Continue with existing staged changes

    # Check for unstaged changes and prompt to stage them
    if has_unstaged:
        if Confirm.ask(
            "There are unstaged changes. Do you want to stage modified files (git add -u)?"
        ):
            try:
                subprocess.run(["git", "add", "-u"], check=True)
                console.print("[green]Staged modified files.[/green]")
                # Get updated status and diff after staging
                status_output, diff_output, unstaged_output, untracked_output = (
                    get_git_status()
                )
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Failed to stage files: {e}[/red]")
                # Continue with existing staged changes

    console.print("[cyan]Generating commit message...[/cyan]")

    with console.status("[cyan]Generating commit message using Copilot API...[/cyan]"):
        commit_message = generate_commit_message(status_output, diff_output)

    console.print(
        Panel(commit_message, title="Generated Commit Message", border_style="green")
    )

    if not Confirm.ask("Do you want to commit with this message?"):
        console.print("Autocommit cancelled.")
        raise typer.Exit()

    try:
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        console.print(
            f"[green]Successfully committed with message: {commit_message}[/green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Commit failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def models():
    """List models available for chat in a Rich table."""
    models = Copilot().models

    console = Console()
    table = Table(title="Available Models")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Vendor", style="green")
    table.add_column("Version", style="yellow")
    table.add_column("Family", style="white")
    table.add_column("Max Tokens", style="white")
    table.add_column("Streaming", style="white")

    for model in models:
        capabilities = model.get("capabilities", {})
        family = capabilities.get("family", "N/A")
        max_tokens = capabilities.get("limits", {}).get("max_output_tokens", "N/A")
        streaming = capabilities.get("supports", {}).get("streaming", False)

        table.add_row(
            model.get("id", "N/A"),
            model.get("name", "N/A"),
            model.get("vendor", "N/A"),
            model.get("version", "N/A"),
            family,
            str(max_tokens),
            str(streaming),
        )

    console.print(table)


if __name__ == "__main__":
    app()
