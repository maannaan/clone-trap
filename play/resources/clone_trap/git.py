"""Read-only Git invocation for inventory only."""

from __future__ import annotations

import os
import subprocess
from typing import Sequence

from clone_trap.errors import CloneTrapError

READ_ONLY_GIT_COMMANDS = frozenset(
    {"rev-parse", "ls-files", "check-ignore", "submodule"}
)

NOT_A_REPO_MESSAGE = "clone-trap must be run against a Git repository."
MISSING_GIT_MESSAGE = "Git is not installed or not on PATH. Install Git and try again."


def run_git(
    repo: str,
    args: Sequence[str],
    *,
    check: bool = True,
) -> str:
    """Run a read-only git command in repo and return stdout."""
    return _run_git(repo, args, check=check)[1]


def _run_git(
    repo: str,
    args: Sequence[str],
    *,
    check: bool = True,
) -> tuple[int, str, str]:
    if not args or args[0] not in READ_ONLY_GIT_COMMANDS:
        raise CloneTrapError(
            "Internal error: refused to run a non-read-only git command."
        )

    try:
        completed = subprocess.run(
            ["git", "-C", repo, *args],
            shell=False,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise CloneTrapError(MISSING_GIT_MESSAGE) from exc

    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise CloneTrapError(f"Git command failed: {detail or 'unknown error'}")
    return completed.returncode, completed.stdout, completed.stderr


def find_repository(start: str) -> str:
    """Return the Git work-tree root, or raise if not a repository."""
    start_path = os.path.abspath(os.path.expanduser(start))
    if not os.path.isdir(start_path):
        raise CloneTrapError(f"Path is not a directory: {start_path}")

    try:
        inside = run_git(start_path, ["rev-parse", "--is-inside-work-tree"]).strip()
    except CloneTrapError as exc:
        message = str(exc).lower()
        if "git is not installed" in message:
            raise
        raise CloneTrapError(NOT_A_REPO_MESSAGE) from exc

    if inside != "true":
        raise CloneTrapError(NOT_A_REPO_MESSAGE)

    toplevel = run_git(start_path, ["rev-parse", "--show-toplevel"]).strip()
    return os.path.abspath(toplevel)


def list_tracked_files(repo: str) -> set[str]:
    """Return repository-relative tracked paths."""
    output = run_git(repo, ["ls-files", "-z"], check=False)
    if not output:
        return set()
    return {part for part in output.split("\0") if part}


def is_ignored(repo: str, path: str) -> bool:
    """Return True if git check-ignore considers the path ignored."""
    code, _, _ = _run_git(
        repo,
        ["check-ignore", "-q", "--", path],
        check=False,
    )
    return code == 0


def list_submodules(repo: str) -> list[dict[str, str]]:
    """Parse `git submodule status` into path/sha/state records."""
    code, stdout, _ = _run_git(repo, ["submodule", "status"], check=False)
    if code != 0 or not stdout.strip():
        return []
    records: list[dict[str, str]] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        state = "initialized"
        body = line
        if line[0] in {"-", "+", " "}:
            if line[0] == "-":
                state = "uninitialized"
            elif line[0] == "+":
                state = "out_of_sync"
            body = line[1:]
        parts = body.split()
        if len(parts) < 2:
            continue
        records.append(
            {
                "sha": parts[0],
                "path": parts[1],
                "state": state,
            }
        )
    return records
