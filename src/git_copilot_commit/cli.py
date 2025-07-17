"""
git-copilot-commit - AI-powered Git commit assistant
"""

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from rich.table import Table

from pycopilot.copilot import Copilot
from pycopilot.auth import Authentication
from .git import GitRepository, GitError, NotAGitRepositoryError, GitStatus
from .settings import Settings
from . import __version__

console = Console()
app = typer.Typer(help=__doc__, add_completion=False)


def version_callback(value: bool):
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", callback=version_callback, help="Show version and exit"
    ),
):
    """
    Automatically commit changes in the current git repository.
    """
    if ctx.invoked_subcommand is None:
        # Show help when no command is provided
        print(ctx.get_help())
        raise typer.Exit()


def display_file_status(status: GitStatus) -> None:
    """Display file status in a rich table."""
    if not status.files:
        return

    table = Table(title="Git Status")
    table.add_column("Status", style="yellow", width=8)
    table.add_column("File", style="white")

    # Group files by status
    staged = status.staged_files
    unstaged = status.unstaged_files
    untracked = status.untracked_files

    if staged:
        table.add_row("[green]Staged[/green]", "", style="dim")
        for file in staged:
            table.add_row(f"  {file.staged_status}", file.path)

    if unstaged:
        table.add_row("[yellow]Unstaged[/yellow]", "", style="dim")
        for file in unstaged:
            table.add_row(f"  {file.status}", file.path)

    if untracked:
        table.add_row("[red]Untracked[/red]", "", style="dim")
        for file in untracked:
            table.add_row("  ?", file.path)

    console.print(table)


def generate_commit_message(
    repo: GitRepository, status: GitStatus, model: str | None = None
) -> str:
    """Generate a conventional commit message using Copilot API."""

    # Get recent commits for context
    recent_commits = repo.get_recent_commits(limit=5)
    recent_commits_text = "\n".join([f"- {msg}" for _, msg in recent_commits])

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

Avoid wrapping the whole response in triple backticks or single backticks.
Return the commit message as the output without any additional text, explanations, or formatting markers.
"""
    )

    prompt = f"""Recent commits:
{recent_commits_text}

`git status`:

```
{status.get_porcelain_output()}
```

`git diff --staged`:

```
{status.staged_diff}
```

Generate a conventional commit message:"""

    response = client.ask(prompt, model=model) if model else client.ask(prompt)
    return response.content


@app.command()
def commit(
    all_files: bool = typer.Option(
        False, "--all", "-a", help="Stage all files before committing"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
    model: str | None = typer.Option(
        None, "--model", "-m", help="Model to use for generating commit message"
    ),
):
    """
    Automatically commit changes in the current git repository.
    """
    try:
        repo = GitRepository()
    except NotAGitRepositoryError:
        console.print("[red]Error: Not in a git repository[/red]")
        raise typer.Exit(1)

    # Load settings and use default model if none provided
    settings = Settings()
    if model is None:
        model = settings.default_model

    # Get initial status
    status = repo.get_status()

    if not status.files:
        console.print("[yellow]No changes to commit.[/yellow]")
        raise typer.Exit()

    # Display current status
    if verbose:
        display_file_status(status)

    # Handle staging based on options
    if all_files:
        repo.stage_files()  # Stage all files
        console.print("[green]Staged all files.[/green]")
    else:
        # Show git status once if there are unstaged or untracked files to prompt about
        if status.has_unstaged_changes or status.has_untracked_files:
            git_status_output = repo._run_git_command(["status"])
            console.print(git_status_output.stdout)

        if status.has_unstaged_changes:
            if Confirm.ask(
                "Modified files found. Add [bold yellow]all unstaged changes[/] to staging?",
                default=True,
            ):
                repo.stage_modified()
                console.print("[green]Staged modified files.[/green]")
        if status.has_untracked_files:
            if Confirm.ask(
                "Untracked files found. Add [bold yellow]all untracked files and unstaged changes[/] to staging?",
                default=True,
            ):
                repo.stage_files()
                console.print("[green]Staged untracked files.[/green]")

    # Refresh status after staging
    status = repo.get_status()

    if not status.has_staged_changes:
        console.print("[yellow]No staged changes to commit.[/yellow]")
        raise typer.Exit()

    # Generate or use provided commit message
    with console.status("[cyan]Generating commit message...[/cyan]"):
        commit_message = generate_commit_message(repo, status, model)

    console.print("[cyan]Generated commit message...[/cyan]")

    # Display commit message
    console.print(Panel(commit_message, title="Commit Message", border_style="green"))

    # Show what will be committed in verbose mode
    if verbose:
        console.print("\n[bold]Changes to be committed:[/bold]")
        for file in status.staged_files:
            console.print(f"  {file.staged_status} {file.path}")

    # Confirm commit or edit message
    choice = typer.prompt(
        "Choose action: (c)ommit, (e)dit message, (q)uit",
        default="c",
        show_default=True,
    ).lower()

    if choice == "q":
        console.print("Commit cancelled.")
        raise typer.Exit()
    elif choice == "e":
        # Use git's built-in editor with generated message as template
        console.print("[cyan]Opening git editor...[/cyan]")
        try:
            commit_sha = repo.commit(commit_message, use_editor=True)
        except GitError as e:
            console.print(f"[red]Commit failed: {e}[/red]")
            raise typer.Exit(1)
    elif choice == "c":
        # Commit with generated message
        try:
            commit_sha = repo.commit(commit_message)
        except GitError as e:
            console.print(f"[red]Commit failed: {e}[/red]")
            raise typer.Exit(1)
    else:
        console.print("Invalid choice. Commit cancelled.")
        raise typer.Exit()

    # Show success message
    console.print(f"[green]✓ Successfully committed: {commit_sha[:8]}[/green]")


@app.command()
def authenticate():
    """Autheticate with GitHub Copilot."""
    Authentication().auth()


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


@app.command()
def config(
    set_default_model: str | None = typer.Option(
        None, "--set-default-model", help="Set default model for commit messages"
    ),
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
):
    """Manage application configuration."""
    settings = Settings()

    if set_default_model:
        settings.default_model = set_default_model
        console.print(f"[green]✓ Default model set to: {set_default_model}[/green]")

    if show or (not set_default_model):
        console.print("\n[bold]Current Configuration:[/bold]")
        default_model = settings.default_model
        if default_model:
            console.print(f"Default model: [cyan]{default_model}[/cyan]")
        else:
            console.print("Default model: [dim]not set[/dim]")

        console.print(f"Config file: [dim]{settings.config_file}[/dim]")


if __name__ == "__main__":
    app()
