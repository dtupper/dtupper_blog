"""Integration tests for the page diff feature."""

import json
import re
import subprocess
import textwrap

import pytest

from generator.build import SiteBuilder
from generator.config import load_config


@pytest.fixture
def git_project(tmp_path):
    """Create a project directory that is also a git repo."""
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
    # Write site.yaml and commit it
    (tmp_path / "site.yaml").write_text(
        textwrap.dedent("""\
        site:
          title: Test Site
          description: Test
          author: Tester
          url: https://example.com
          language: en
          locale: en-US
    """)
    )
    (tmp_path / "content" / "blog").mkdir(parents=True)
    (tmp_path / "content" / "projects").mkdir(parents=True)
    (tmp_path / "content" / "pages").mkdir(parents=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True
    )
    return tmp_path


def _commit_post(project, filename, content, message):
    """Write a blog post and commit it."""
    fpath = project / "content" / "blog" / filename
    fpath.write_text(content)
    subprocess.run(["git", "add", str(fpath)], cwd=project, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=project,
        capture_output=True,
        check=True,
    )


def _commit_page(project, filename, content, message):
    """Write a page and commit it."""
    fpath = project / "content" / "pages" / filename
    fpath.write_text(content)
    subprocess.run(["git", "add", str(fpath)], cwd=project, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=project,
        capture_output=True,
        check=True,
    )


def _build(project):
    config = load_config(project)
    builder = SiteBuilder(config)
    builder.build()
    return builder


def _find_output(project, slug):
    """Find the output HTML file for a given slug (filename stem, not title)."""
    matches = list((project / "output").rglob(f"**/{slug}/index.html"))
    assert matches, f"No output found for slug '{slug}'"
    return matches[0].read_text()


def _extract_version_json(html):
    """Extract and parse the version data JSON from page HTML."""
    match = re.search(
        r'<script type="application/json" id="diff-version-data">\s*(.*?)\s*</script>',
        html,
        re.DOTALL,
    )
    assert match is not None, "No diff-version-data script tag found"
    return json.loads(match.group(1))


class TestDiffFeatureDisabled:
    def test_no_diff_viewer_without_flag(self, git_project):
        """Posts without enable_diffs should not include the diff viewer."""
        _commit_post(
            git_project,
            "normal.md",
            textwrap.dedent("""\
                ---
                title: Normal Post
                date: 2024-01-01
                ---
                No diffs here.
            """),
            "add post",
        )
        _build(git_project)
        html = _find_output(git_project, "normal")
        assert "diff-version-data" not in html
        assert "diff-viewer-bar" not in html

    def test_single_version_no_viewer(self, git_project):
        """A file with only one commit should not show the diff viewer."""
        _commit_post(
            git_project,
            "single.md",
            textwrap.dedent("""\
                ---
                title: Single Version
                date: 2024-01-01
                enable_diffs: true
                ---
                Only version.
            """),
            "only commit",
        )
        _build(git_project)
        html = _find_output(git_project, "single")
        assert "diff-version-data" not in html


class TestDiffFeatureEnabled:
    def test_diff_viewer_present_with_flag(self, git_project):
        """Posts with enable_diffs and 2+ versions should include the viewer."""
        _commit_post(
            git_project,
            "diffable.md",
            textwrap.dedent("""\
                ---
                title: Diffable Post
                date: 2024-01-01
                enable_diffs: true
                ---
                Version one.
            """),
            "v1",
        )
        _commit_post(
            git_project,
            "diffable.md",
            textwrap.dedent("""\
                ---
                title: Diffable Post
                date: 2024-01-01
                enable_diffs: true
                ---
                Version two with changes.
            """),
            "v2",
        )
        _build(git_project)
        html = _find_output(git_project, "diffable")
        assert "diff-version-data" in html
        assert "diff-viewer-bar" in html
        assert "diff-prev" in html
        assert "diff-next" in html

    def test_version_data_json_is_valid(self, git_project):
        """The embedded JSON should parse and contain expected fields."""
        _commit_post(
            git_project,
            "diffable.md",
            textwrap.dedent("""\
                ---
                title: Diffable Post
                date: 2024-01-01
                enable_diffs: true
                ---
                First version.
            """),
            "v1",
        )
        _commit_post(
            git_project,
            "diffable.md",
            textwrap.dedent("""\
                ---
                title: Diffable Post
                date: 2024-01-01
                enable_diffs: true
                ---
                Second version.
            """),
            "v2",
        )
        _build(git_project)
        html = _find_output(git_project, "diffable")
        data = _extract_version_json(html)

        assert len(data) == 2
        # First version has no diff
        assert data[0]["diff_html"] is None
        assert "html" in data[0]
        assert "date" in data[0]
        assert "commit_hash" in data[0]
        assert "author" in data[0]
        assert "message" in data[0]
        # Second version has diff markers
        assert data[1]["diff_html"] is not None

    def test_three_versions(self, git_project):
        """Three versions should all be present in version data."""
        for i in range(1, 4):
            _commit_post(
                git_project,
                "evolving.md",
                textwrap.dedent(f"""\
                    ---
                    title: Evolving Post
                    date: 2024-01-01
                    enable_diffs: true
                    ---
                    Content version {i}.
                """),
                f"v{i}",
            )
        _build(git_project)
        html = _find_output(git_project, "evolving")
        data = _extract_version_json(html)

        assert len(data) == 3
        assert data[0]["diff_html"] is None
        assert data[1]["diff_html"] is not None
        assert data[2]["diff_html"] is not None

    def test_lazy_loading_on_old_versions(self, git_project):
        """Non-latest versions should have lazy-loaded images."""
        _commit_post(
            git_project,
            "images.md",
            textwrap.dedent("""\
                ---
                title: Image Post
                date: 2024-01-01
                enable_diffs: true
                ---
                ![photo](/img.jpg)
            """),
            "v1 with image",
        )
        _commit_post(
            git_project,
            "images.md",
            textwrap.dedent("""\
                ---
                title: Image Post
                date: 2024-01-01
                enable_diffs: true
                ---
                Updated text, no image.
            """),
            "v2 no image",
        )
        _build(git_project)
        html = _find_output(git_project, "images")
        data = _extract_version_json(html)

        # First (older) version should have lazy image
        assert "data-src" in data[0]["html"]
        # Latest version is NOT lazified (rendered normally on the page)
        assert "data-src" not in data[1]["html"]

    def test_diff_html_contains_change_markers(self, git_project):
        """Diff HTML should contain ins/del markers for changes."""
        _commit_post(
            git_project,
            "markers.md",
            textwrap.dedent("""\
                ---
                title: Marker Post
                date: 2024-01-01
                enable_diffs: true
                ---
                Original content here.
            """),
            "v1",
        )
        _commit_post(
            git_project,
            "markers.md",
            textwrap.dedent("""\
                ---
                title: Marker Post
                date: 2024-01-01
                enable_diffs: true
                ---
                Modified content here.
            """),
            "v2",
        )
        _build(git_project)
        html = _find_output(git_project, "markers")
        data = _extract_version_json(html)

        diff = data[1]["diff_html"]
        assert "diff-ins" in diff
        assert "diff-del" in diff


class TestDiffFeaturePages:
    def test_page_with_diffs(self, git_project):
        """Pages (not just posts) should support enable_diffs."""
        _commit_page(
            git_project,
            "about.md",
            textwrap.dedent("""\
                ---
                title: About
                enable_diffs: true
                ---
                About version one.
            """),
            "about v1",
        )
        _commit_page(
            git_project,
            "about.md",
            textwrap.dedent("""\
                ---
                title: About
                enable_diffs: true
                ---
                About version two.
            """),
            "about v2",
        )
        _build(git_project)
        html = _find_output(git_project, "about")
        assert "diff-version-data" in html
        assert "diff-viewer-bar" in html


class TestDiffNoInterference:
    def test_non_diff_posts_unaffected(self, git_project):
        """Posts without enable_diffs in same build are unaffected."""
        _commit_post(
            git_project,
            "normal.md",
            textwrap.dedent("""\
                ---
                title: Normal Post
                date: 2024-01-01
                ---
                Normal content.
            """),
            "normal post",
        )
        _commit_post(
            git_project,
            "diffable.md",
            textwrap.dedent("""\
                ---
                title: Diffable Post
                date: 2024-01-02
                enable_diffs: true
                ---
                Version one.
            """),
            "diff v1",
        )
        _commit_post(
            git_project,
            "diffable.md",
            textwrap.dedent("""\
                ---
                title: Diffable Post
                date: 2024-01-02
                enable_diffs: true
                ---
                Version two.
            """),
            "diff v2",
        )
        _build(git_project)

        normal_html = _find_output(git_project, "normal")
        diff_html = _find_output(git_project, "diffable")

        assert "diff-version-data" not in normal_html
        assert "diff-version-data" in diff_html
