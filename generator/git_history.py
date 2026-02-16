"""Extract file version history from git."""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class FileVersion:
    """A single committed version of a file."""

    commit_hash: str
    date: datetime  # UTC-aware
    author: str
    message: str
    content: str  # raw file content at this commit


def get_file_history(
    file_path: Path,
    repo_dir: Path | None = None,
) -> list[FileVersion]:
    """Get all committed versions of a file, sorted oldest-first.

    Args:
        file_path: Absolute path to the file.
        repo_dir: Git repo root. If None, uses file_path.parent.

    Returns:
        List of FileVersion, oldest first. Empty list if file is not
        tracked or git is unavailable.
    """
    if repo_dir is None:
        repo_dir = file_path.parent

    # Get the git repo root and compute relative path
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=repo_dir,
        )
        if result.returncode != 0:
            return []
        git_root = Path(result.stdout.strip())
        rel_path = file_path.resolve().relative_to(git_root)
    except (FileNotFoundError, ValueError):
        return []

    # Get commit log for this file
    # Format: hash<US>ISO-date<US>author<US>subject
    SEP = "\x1f"  # unit separator
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--follow",
                f"--format=format:%H{SEP}%aI{SEP}%an{SEP}%s",
                "--",
                str(rel_path),
            ],
            capture_output=True,
            text=True,
            cwd=git_root,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
    except FileNotFoundError:
        return []

    versions: list[FileVersion] = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split(SEP, 3)
        if len(parts) != 4:
            continue
        commit_hash, date_str, author, message = parts

        # Get file content at this commit
        try:
            content_result = subprocess.run(
                ["git", "show", f"{commit_hash}:{rel_path}"],
                capture_output=True,
                text=True,
                cwd=git_root,
            )
            if content_result.returncode != 0:
                continue
        except FileNotFoundError:
            continue

        versions.append(
            FileVersion(
                commit_hash=commit_hash,
                date=datetime.fromisoformat(date_str),
                author=author,
                message=message,
                content=content_result.stdout,
            )
        )

    # Reverse so oldest is first (git log returns newest first)
    versions.reverse()
    return versions
