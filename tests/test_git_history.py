"""Tests for git history extraction."""

import subprocess
from pathlib import Path

import pytest

from generator.git_history import get_file_history


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repo."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Tester"],
        cwd=tmp_path,
        capture_output=True,
    )
    return tmp_path


def _commit_file(repo, rel_path, content, message):
    """Write content to a file and commit it."""
    fpath = repo / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)
    subprocess.run(["git", "add", str(rel_path)], cwd=repo, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message], cwd=repo, capture_output=True, check=True
    )


class TestGetFileHistory:
    def test_returns_empty_for_untracked_file(self, git_repo):
        # Need at least one commit for git to work
        _commit_file(git_repo, "other.md", "x", "init")
        fpath = git_repo / "untracked.md"
        fpath.write_text("hello")
        assert get_file_history(fpath, git_repo) == []

    def test_returns_empty_outside_git(self, tmp_path):
        fpath = tmp_path / "nofile.md"
        fpath.write_text("hello")
        assert get_file_history(fpath, tmp_path) == []

    def test_single_commit(self, git_repo):
        _commit_file(git_repo, "post.md", "# Hello", "first")
        versions = get_file_history(git_repo / "post.md", git_repo)
        assert len(versions) == 1
        assert versions[0].content == "# Hello"
        assert versions[0].message == "first"
        assert versions[0].author == "Tester"

    def test_multiple_commits_oldest_first(self, git_repo):
        _commit_file(git_repo, "post.md", "v1", "first")
        _commit_file(git_repo, "post.md", "v2", "second")
        _commit_file(git_repo, "post.md", "v3", "third")
        versions = get_file_history(git_repo / "post.md", git_repo)
        assert len(versions) == 3
        assert versions[0].content == "v1"
        assert versions[0].message == "first"
        assert versions[1].content == "v2"
        assert versions[2].content == "v3"
        assert versions[2].message == "third"

    def test_dates_are_timezone_aware(self, git_repo):
        _commit_file(git_repo, "post.md", "content", "commit")
        versions = get_file_history(git_repo / "post.md", git_repo)
        assert versions[0].date.tzinfo is not None

    def test_nested_file_path(self, git_repo):
        _commit_file(git_repo, "content/blog/deep.md", "deep content", "nested")
        versions = get_file_history(
            git_repo / "content" / "blog" / "deep.md", git_repo
        )
        assert len(versions) == 1
        assert versions[0].content == "deep content"

    def test_only_returns_history_for_target_file(self, git_repo):
        _commit_file(git_repo, "a.md", "file a", "commit a")
        _commit_file(git_repo, "b.md", "file b", "commit b")
        versions = get_file_history(git_repo / "a.md", git_repo)
        assert len(versions) == 1
        assert versions[0].content == "file a"

    def test_commit_hash_is_full_sha(self, git_repo):
        _commit_file(git_repo, "post.md", "content", "commit")
        versions = get_file_history(git_repo / "post.md", git_repo)
        assert len(versions[0].commit_hash) == 40
