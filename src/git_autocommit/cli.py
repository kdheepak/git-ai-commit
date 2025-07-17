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
    """Get git status and staged changes."""
    try:
        status_result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )

        diff_result = subprocess.run(
            ["git", "diff", "--staged"], capture_output=True, text=True, check=True
        )

        return status_result.stdout.strip(), diff_result.stdout.strip()
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Git command failed: {e}[/red]")
        raise typer.Exit(1)


def generate_commit_message(status_output, diff_output):
    """Generate a conventional commit message using Copilot API."""

    client = Copilot(
        system_prompt="""You are a git commit message generator. Generate concise conventional commit messages.

Use these conventional commit types:
- feat: new feature
- fix: bug fix
- docs: documentation changes
- style: formatting, missing semicolons, etc
- refactor: code restructuring
- test: adding tests
- chore: maintenance tasks

Format: type(scope): description

Keep messages under 50 characters for the subject line.
Only return the commit message, nothing else."""
    )

    prompt = "Git status:\n```\n{status_output}\n```\n\nGit diff --staged:\n```\n{diff_output}\n```\n\nGenerate a conventional commit message:"
    response = client.ask(
        prompt.format(status_output=status_output, diff_output=diff_output),
        model="gemini-2.5-pro",
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
    status_output, diff_output = get_git_status()

    if not status_output:
        console.print("[yellow]No changes to commit.[/yellow]")
        raise typer.Exit()

    # Check for untracked files
    has_untracked = any(line.startswith("??") for line in status_output.split("\n"))

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
        status_output, diff_output = get_git_status()

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
                status_output, diff_output = get_git_status()
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Failed to add untracked files: {e}[/red]")
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
