import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum


class GitError(Exception):
    """Base exception for git-related errors."""

    pass


class NotAGitRepositoryError(GitError):
    """Raised when not in a git repository."""

    pass


class GitCommandError(GitError):
    """Raised when a git command fails."""

    pass


class FileStatus(Enum):
    """Git file status codes."""

    MODIFIED = "M"
    ADDED = "A"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNMERGED = "U"
    UNTRACKED = "?"
    IGNORED = "!"


@dataclass
class GitFile:
    """Represents a file in git status."""

    path: str
    status: str
    staged_status: str

    @property
    def is_staged(self) -> bool:
        """Check if file has staged changes."""
        return self.staged_status != " " and self.staged_status != "?"

    @property
    def is_modified(self) -> bool:
        """Check if file is modified."""
        return self.status == "M" or self.staged_status == "M"

    @property
    def is_untracked(self) -> bool:
        """Check if file is untracked."""
        return self.staged_status == "?" and self.status == "?"


@dataclass
class GitStatus:
    """Structured representation of git status."""

    files: List[GitFile]
    staged_diff: str
    unstaged_diff: str

    @property
    def has_staged_changes(self) -> bool:
        """Check if there are any staged changes."""
        return bool(self.staged_diff.strip())

    @property
    def has_unstaged_changes(self) -> bool:
        """Check if there are any unstaged changes."""
        return bool(self.unstaged_diff.strip())

    @property
    def has_untracked_files(self) -> bool:
        """Check if there are any untracked files."""
        return any(f.is_untracked for f in self.files)

    @property
    def staged_files(self) -> List[GitFile]:
        """Get list of files with staged changes."""
        return [f for f in self.files if f.is_staged]

    @property
    def unstaged_files(self) -> List[GitFile]:
        """Get list of files with unstaged changes."""
        return [f for f in self.files if not f.is_staged and not f.is_untracked]

    @property
    def untracked_files(self) -> List[GitFile]:
        """Get list of untracked files."""
        return [f for f in self.files if f.is_untracked]

    def get_porcelain_output(self) -> str:
        """Get the original porcelain output format."""
        lines = []
        for file in self.files:
            lines.append(f"{file.staged_status}{file.status} {file.path}")
        return "\n".join(lines)


class GitRepository:
    """Encapsulates git repository operations."""

    def __init__(self, repo_path: Optional[Path] = None, timeout: int = 30):
        """
        Initialize GitRepository.

        Args:
            repo_path: Path to git repository. Defaults to current directory.
            timeout: Timeout for git commands in seconds.

        Raises:
            NotAGitRepositoryError: If the path is not a git repository.
        """
        self.repo_path = repo_path or Path.cwd()
        self.timeout = timeout
        self._validate_git_repo()

    def _validate_git_repo(self) -> None:
        """Ensure we're in a git repository."""
        try:
            self._run_git_command(["rev-parse", "--git-dir"])
        except GitCommandError:
            raise NotAGitRepositoryError(f"{self.repo_path} is not a git repository")

    def _run_git_command(
        self, args: List[str], check: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run a git command and return the result.

        Args:
            args: Git command arguments (without 'git' prefix).
            check: Whether to raise exception on non-zero exit code.

        Returns:
            CompletedProcess instance.

        Raises:
            GitCommandError: If command fails and check=True.
        """
        cmd = ["git"] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=check,
            )
            return result
        except subprocess.CalledProcessError as e:
            raise GitCommandError(f"Git command failed: {' '.join(cmd)}\n{e.stderr}")
        except subprocess.TimeoutExpired:
            raise GitCommandError(f"Git command timed out: {' '.join(cmd)}")

    def get_status(self) -> GitStatus:
        """
        Get comprehensive git status information.

        Returns:
            GitStatus object with all status information.
        """
        # Get porcelain status
        status_result = self._run_git_command(["status", "--porcelain"])

        # Get staged diff
        staged_diff_result = self._run_git_command(["diff", "--staged"])

        # Get unstaged diff
        unstaged_diff_result = self._run_git_command(["diff"])

        # Parse status output into GitFile objects
        files = self._parse_status_output(status_result.stdout)

        return GitStatus(
            files=files,
            staged_diff=staged_diff_result.stdout,
            unstaged_diff=unstaged_diff_result.stdout,
        )

    def _parse_status_output(self, status_output: str) -> List[GitFile]:
        """Parse git status --porcelain output into GitFile objects."""
        files = []
        for line in status_output.strip().split("\n"):
            if not line:
                continue

            # Git status format: XY filename
            # X = staged status, Y = unstaged status
            if len(line) < 3:
                continue

            staged_status = line[0]
            unstaged_status = line[1]
            filename = line[3:]  # Skip the space

            files.append(
                GitFile(
                    path=filename, status=unstaged_status, staged_status=staged_status
                )
            )

        return files

    def stage_files(self, paths: Optional[List[str]] = None) -> None:
        """
        Stage files for commit.

        Args:
            paths: List of file paths to stage. If None, stages all files (git add .).
        """
        if paths is None:
            self._run_git_command(["add", "."])
        else:
            # Stage files in batches to avoid command line length limits
            batch_size = 100
            for i in range(0, len(paths), batch_size):
                batch = paths[i : i + batch_size]
                self._run_git_command(["add"] + batch)

    def stage_modified(self) -> None:
        """Stage all modified files (git add -u)."""
        self._run_git_command(["add", "-u"])

    def unstage_files(self, paths: Optional[List[str]] = None) -> None:
        """
        Unstage files.

        Args:
            paths: List of file paths to unstage. If None, unstages all files.
        """
        if paths is None:
            self._run_git_command(["reset", "HEAD"])
        else:
            self._run_git_command(["reset", "HEAD"] + paths)

    def commit(self, message: Optional[str] = None, use_editor: bool = False) -> str:
        """
        Create a commit with the given message or using git's editor.

        Args:
            message: Commit message. Used as template if use_editor is True.
            use_editor: Whether to use git's configured editor.

        Returns:
            Commit SHA.

        Raises:
            GitCommandError: If commit fails.
        """
        if use_editor:
            import tempfile
            import os
            
            # Create temp file with message as starting point
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                if message:
                    f.write(message)
                temp_file = f.name
            
            try:
                args = ["commit", "-e", "-F", temp_file]
                
                # Run interactively without capturing output
                cmd = ["git"] + args
                subprocess.run(
                    cmd,
                    cwd=self.repo_path,
                    timeout=self.timeout,
                    check=True,
                )
            except subprocess.CalledProcessError:
                raise GitCommandError(f"Git commit failed: {' '.join(cmd)}")
            except subprocess.TimeoutExpired:
                raise GitCommandError(f"Git commit timed out: {' '.join(cmd)}")
            finally:
                # Clean up temp file
                os.unlink(temp_file)
        else:
            if message is None:
                raise ValueError("message is required when use_editor is False")
            args = ["commit", "-m", message]

            self._run_git_command(args)

        # Extract commit SHA from output
        sha_result = self._run_git_command(["rev-parse", "HEAD"])
        return sha_result.stdout.strip()

    def get_recent_commits(self, limit: int = 10) -> List[Tuple[str, str]]:
        """
        Get recent commit history.

        Args:
            limit: Number of commits to retrieve.

        Returns:
            List of tuples (sha, message).
        """
        result = self._run_git_command(
            ["log", f"--max-count={limit}", "--pretty=format:%H|%s"]
        )

        commits = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                sha, message = line.split("|", 1)
                commits.append((sha, message))

        return commits

    def get_current_branch(self) -> str:
        """Get the name of the current branch."""
        result = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        return result.stdout.strip()

    def has_changes(self) -> bool:
        """Check if there are any changes (staged, unstaged, or untracked)."""
        status = self.get_status()
        return (
            status.has_staged_changes
            or status.has_unstaged_changes
            or status.has_untracked_files
        )

    def get_diff(self, staged: bool = False, paths: Optional[List[str]] = None) -> str:
        """
        Get diff output.

        Args:
            staged: Whether to get staged diff (--staged flag).
            paths: Specific paths to diff.

        Returns:
            Diff output as string.
        """
        args = ["diff"]
        if staged:
            args.append("--staged")
        if paths:
            args.extend(["--"] + paths)

        result = self._run_git_command(args)
        return result.stdout

    def get_file_content(self, path: str, revision: str = "HEAD") -> str:
        """
        Get content of a file at a specific revision.

        Args:
            path: File path.
            revision: Git revision (default: HEAD).

        Returns:
            File content as string.
        """
        result = self._run_git_command(["show", f"{revision}:{path}"])
        return result.stdout
