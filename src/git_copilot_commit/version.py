import subprocess
import shlex
from importlib import metadata
import os


DIR = os.path.dirname(os.path.realpath(__file__))

VERSION = metadata.version(__package__ or "git-copilot-commit")


def cmd(cmd, kind="") -> str:
    """
    Get git subprocess output
    """
    output = "unknown"
    try:
        output = (
            subprocess.check_output(shlex.split(cmd), cwd=DIR, stderr=subprocess.STDOUT)
            .decode()
            .strip()
        )
    except Exception as _:
        ...
    return f"{kind}{output}"


def last_commit_id() -> str:
    return cmd("git describe --always --dirty --abbrev=7")


def branch() -> str:
    return cmd("git rev-parse --abbrev-ref HEAD")


def get_git_version() -> str:
    return f"{last_commit_id()}-{branch()}"


__version__ = f"v{VERSION}-{get_git_version()}"
