"""Tests for generator/build.py — ContentItem, SiteBuilder, and build pipeline."""

import textwrap
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from generator.build import ContentItem, SiteBuilder
from generator.config import load_config

from conftest import build, write_post, write_project, write_page


class TestContentItemLoad:

    def _make_item(self, tmp_path, section, filename, frontmatter_lines, body="Some body."):
        """Helper to create and load a ContentItem."""
        content_dir = tmp_path / "content" / section
        content_dir.mkdir(parents=True, exist_ok=True)
        fm = "\n".join(frontmatter_lines)
        (content_dir / filename).write_text(f"---\n{fm}\n---\n\n{body}\n")
        item = ContentItem(content_dir / filename, section)
        config = load_config(tmp_path)
        item.load(config.sections[section])
        return item

    def test_slug_from_filename(self, tmp_project):
        item = self._make_item(tmp_project, "blog", "my-post.md", ["title: My Post", "date: 2024-01-15"])
        assert item.slug == "my-post"

    def test_slug_from_frontmatter(self, tmp_project):
        item = self._make_item(tmp_project, "blog", "my-post.md", ["title: My Post", "date: 2024-01-15", "slug: custom-slug"])
        assert item.slug == "custom-slug"

    def test_slug_slugified(self, tmp_project):
        item = self._make_item(tmp_project, "blog", "My Weird Post!.md", ["title: My Post", "date: 2024-01-15"])
        assert " " not in item.slug
        assert "!" not in item.slug

    def test_default_title_from_filename(self, tmp_project):
        item = self._make_item(tmp_project, "pages", "about-us.md", [])
        assert item.metadata["title"] == "About Us"

    def test_default_status_published(self, tmp_project):
        item = self._make_item(tmp_project, "pages", "test.md", ["title: T"])
        assert item.metadata["status"] == "published"

    def test_default_tags_empty(self, tmp_project):
        item = self._make_item(tmp_project, "pages", "test.md", ["title: T"])
        assert item.metadata["tags"] == []

    def test_date_in_url(self, tmp_project):
        item = self._make_item(tmp_project, "blog", "test.md", ["title: T", "date: 2024-03-15"])
        assert "2024/03" in item.url

    def test_simple_url_pattern(self, tmp_project):
        item = self._make_item(tmp_project, "projects", "my-proj.md", ["title: P", "date: 2024-01-01"])
        assert item.url == "projects/my-proj"

    def test_last_updated_string_normalized(self, tmp_project):
        item = self._make_item(tmp_project, "blog", "test.md", ["title: T", "date: 2024-01-01", "last_updated: 2024-06-15"])
        assert isinstance(item.metadata["last_updated"], datetime)

    def test_last_updated_date_normalized(self, tmp_project):
        """YAML date values (parsed as date objects) should become datetime."""
        content_dir = tmp_project / "content" / "blog"
        # YAML automatically parses bare dates to date objects
        (content_dir / "test.md").write_text("---\ntitle: T\ndate: 2024-01-01\nlast_updated: 2024-06-15\n---\n\nBody.\n")
        item = ContentItem(content_dir / "test.md", "blog")
        config = load_config(tmp_project)
        item.load(config.sections["blog"])
        assert isinstance(item.metadata["last_updated"], datetime)


class TestContentItemProperties:

    def _load_item(self, tmp_project, frontmatter_lines, body="word " * 100):
        content_dir = tmp_project / "content" / "blog"
        fm = "\n".join(frontmatter_lines)
        (content_dir / "test.md").write_text(f"---\n{fm}\n---\n\n{body}\n")
        item = ContentItem(content_dir / "test.md", "blog")
        config = load_config(tmp_project)
        item.load(config.sections["blog"])
        return item

    def test_is_published_true(self, tmp_project):
        item = self._load_item(tmp_project, ["title: T", "date: 2024-01-15", "status: published"])
        assert item.is_published is True

    def test_is_published_default(self, tmp_project):
        item = self._load_item(tmp_project, ["title: T", "date: 2024-01-15"])
        assert item.is_published is True

    def test_is_draft(self, tmp_project):
        item = self._load_item(tmp_project, ["title: T", "date: 2024-01-15", "status: draft"])
        assert item.is_published is False

    def test_date_property_datetime(self, tmp_project):
        item = self._load_item(tmp_project, ["title: T", "date: 2024-03-15"])
        assert isinstance(item.date, datetime)
        assert item.date.year == 2024
        assert item.date.month == 3

    def test_reading_time_short_content(self, tmp_project):
        item = self._load_item(tmp_project, ["title: T", "date: 2024-01-01"], body="Short.")
        assert item.reading_time >= 1

    def test_reading_time_long_content(self, tmp_project):
        item = self._load_item(tmp_project, ["title: T", "date: 2024-01-01"], body="word " * 1000)
        assert item.reading_time >= 4


class TestSiteBuilderStaticAssets:

    def test_default_assets_copied(self, tmp_project):
        config = load_config(tmp_project)
        builder = SiteBuilder(config)
        builder.clean_output()
        builder.copy_static_assets()
        assert (tmp_project / "output" / "static" / "css" / "style.css").exists()

    def test_user_static_overrides(self, tmp_project):
        # Create user static file
        user_css = tmp_project / "static" / "css" / "custom.css"
        user_css.parent.mkdir(parents=True)
        user_css.write_text("body { color: red; }")

        config = load_config(tmp_project)
        builder = SiteBuilder(config)
        builder.clean_output()
        builder.copy_static_assets()

        output_custom = tmp_project / "output" / "static" / "css" / "custom.css"
        assert output_custom.exists()
        assert "color: red" in output_custom.read_text()
        # Default style.css should also be there
        assert (tmp_project / "output" / "static" / "css" / "style.css").exists()


class TestSiteBuilderContent:

    def test_drafts_filtered_out(self, tmp_project):
        write_post(tmp_project, "pub.md", "Published", "2024-01-15")
        write_post(tmp_project, "draft.md", "Draft", "2024-01-15", status="draft")
        config = load_config(tmp_project)
        builder = SiteBuilder(config)
        builder.load_content()
        titles = [item.metadata["title"] for item in builder.content["blog"]]
        assert "Published" in titles
        assert "Draft" not in titles

    def test_blog_sorted_by_date_descending(self, tmp_project):
        write_post(tmp_project, "old.md", "Old", "2024-01-01")
        write_post(tmp_project, "new.md", "New", "2024-06-01")
        write_post(tmp_project, "mid.md", "Mid", "2024-03-15")
        config = load_config(tmp_project)
        builder = SiteBuilder(config)
        builder.load_content()
        titles = [item.metadata["title"] for item in builder.content["blog"]]
        assert titles == ["New", "Mid", "Old"]

    def test_empty_section_no_error(self, tmp_project):
        config = load_config(tmp_project)
        builder = SiteBuilder(config)
        builder.load_content()
        assert builder.content["blog"] == []


class TestSiteBuilderRendering:

    def test_render_index_limits_posts(self, tmp_project):
        for i in range(8):
            d = f"2024-{(i % 12) + 1:02d}-15"
            write_post(tmp_project, f"post{i}.md", f"Post {i}", d)
        builder = build(tmp_project)
        homepage = (tmp_project / "output" / "index.html").read_text()
        # Homepage should have at most 5 posts
        assert homepage.count("post-preview") <= 5

    def test_render_index_limits_projects(self, tmp_project):
        for i in range(5):
            write_project(tmp_project, f"proj{i}.md", f"Project {i}", "2024-01-01")
        builder = build(tmp_project)
        homepage = (tmp_project / "output" / "index.html").read_text()
        # Homepage should have at most 3 projects
        assert homepage.count("project-card") <= 3

    def test_section_index_rendered(self, tmp_project):
        write_post(tmp_project, "post.md", "A Post", "2024-01-15")
        build(tmp_project)
        assert (tmp_project / "output" / "blog" / "index.html").exists()

    def test_content_item_rendered_to_path(self, tmp_project):
        write_page(tmp_project, "about.md", "About")
        build(tmp_project)
        assert (tmp_project / "output" / "about" / "index.html").exists()


class TestRSSGeneration:

    def test_rss_feed_created(self, tmp_project):
        write_post(tmp_project, "post.md", "A Post", "2024-01-15")
        build(tmp_project)
        assert (tmp_project / "output" / "feed.xml").exists()

    def test_rss_feed_contains_post(self, tmp_project):
        write_post(tmp_project, "post.md", "RSS Post", "2024-01-15")
        build(tmp_project)
        feed = (tmp_project / "output" / "feed.xml").read_text()
        assert "RSS Post" in feed

    def test_rss_disabled(self, tmp_project):
        (tmp_project / "site.yaml").write_text(textwrap.dedent("""\
            site:
              title: Test Site
              description: A test site
              author: Tester
              url: https://example.com
              language: en
              locale: en-US
            build:
              generate_rss: false
        """))
        write_post(tmp_project, "post.md", "A Post", "2024-01-15")
        build(tmp_project)
        assert not (tmp_project / "output" / "feed.xml").exists()

    def test_no_rss_without_blog_posts(self, tmp_project):
        build(tmp_project)
        assert not (tmp_project / "output" / "feed.xml").exists()


class TestTemplateOverrideChain:

    def test_user_template_takes_priority(self, tmp_project):
        """A user template should override the bundled default."""
        user_templates = tmp_project / "templates"
        user_templates.mkdir()
        (user_templates / "page.html").write_text("<html>CUSTOM:{{ body|safe }}</html>")

        write_page(tmp_project, "test.md", "Test")
        build(tmp_project)
        page = (tmp_project / "output" / "test" / "index.html").read_text()
        assert "CUSTOM:" in page


class TestFullBuild:

    def test_build_produces_expected_structure(self, tmp_project):
        write_post(tmp_project, "hello.md", "Hello", "2024-01-15")
        write_project(tmp_project, "proj.md", "My Project", "2024-01-01")
        write_page(tmp_project, "about.md", "About")
        build(tmp_project)

        output = tmp_project / "output"
        assert (output / "index.html").exists()
        assert (output / "blog" / "index.html").exists()
        assert (output / "projects" / "index.html").exists()
        assert (output / "static" / "css" / "style.css").exists()
        assert (output / "feed.xml").exists()
        assert (output / "about" / "index.html").exists()

    def test_clean_output_removes_previous(self, tmp_project):
        write_post(tmp_project, "post.md", "Post", "2024-01-15")
        build(tmp_project)
        # Create a stale file in output
        (tmp_project / "output" / "stale.txt").write_text("old")
        build(tmp_project)
        assert not (tmp_project / "output" / "stale.txt").exists()
