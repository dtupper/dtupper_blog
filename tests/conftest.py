"""Shared test fixtures and helpers for the site generator test suite."""

import textwrap
from pathlib import Path

import pytest

from generator.config import load_config
from generator.build import SiteBuilder


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal project directory with site.yaml and content dirs."""
    (tmp_path / "site.yaml").write_text(textwrap.dedent("""\
        site:
          title: Test Site
          description: A test site
          author: Tester
          url: https://example.com
          language: en
          locale: en-US
          nav:
            - label: Home
              url: /
            - label: Blog
              url: /blog/
    """))
    (tmp_path / "content" / "blog").mkdir(parents=True)
    (tmp_path / "content" / "projects").mkdir(parents=True)
    (tmp_path / "content" / "pages").mkdir(parents=True)
    return tmp_path


def write_post(project_dir, filename, title, date_str, **extra_frontmatter):
    """Write a blog post markdown file."""
    lines = [f"title: {title}", f"date: {date_str}"]
    for key, val in extra_frontmatter.items():
        lines.append(f"{key}: {val}")
    frontmatter = "\n".join(lines)
    content = f"---\n{frontmatter}\n---\n\nSome content for {title}.\n"
    (project_dir / "content" / "blog" / filename).write_text(content)


def write_project(project_dir, filename, title, date_str, **extra_frontmatter):
    """Write a project markdown file."""
    lines = [f"title: {title}", f"date: {date_str}"]
    for key, val in extra_frontmatter.items():
        lines.append(f"{key}: {val}")
    frontmatter = "\n".join(lines)
    content = f"---\n{frontmatter}\n---\n\nSome content for {title}.\n"
    (project_dir / "content" / "projects" / filename).write_text(content)


def write_page(project_dir, filename, title, **extra_frontmatter):
    """Write a page markdown file."""
    lines = [f"title: {title}"]
    for key, val in extra_frontmatter.items():
        lines.append(f"{key}: {val}")
    frontmatter = "\n".join(lines)
    content = f"---\n{frontmatter}\n---\n\nContent for {title}.\n"
    (project_dir / "content" / "pages" / filename).write_text(content)


def build(project_dir):
    """Load config and run a build, returning the SiteBuilder."""
    config = load_config(project_dir)
    builder = SiteBuilder(config)
    builder.build()
    return builder
