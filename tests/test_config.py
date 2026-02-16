"""Tests for generator/config.py — SiteConfig and load_config."""

import dataclasses
import textwrap
from pathlib import Path

import pytest

from generator.config import (
    DEFAULT_BUILD_SETTINGS,
    DEFAULT_SECTIONS,
    DEFAULT_SITE_CONFIG,
    SiteConfig,
    load_config,
)


class TestLoadConfigDefaults:

    def test_no_site_yaml_uses_all_defaults(self, tmp_path):
        """When site.yaml doesn't exist, all defaults should be used."""
        config = load_config(tmp_path)
        assert config.site["title"] == DEFAULT_SITE_CONFIG["title"]
        assert config.date_format == DEFAULT_BUILD_SETTINGS["date_format"]
        assert config.posts_per_page == DEFAULT_BUILD_SETTINGS["posts_per_page"]

    def test_default_directory_layout(self, tmp_path):
        config = load_config(tmp_path)
        assert config.content_dir == tmp_path / "content"
        assert config.templates_dir == tmp_path / "templates"
        assert config.static_dir == tmp_path / "static"
        assert config.output_dir == tmp_path / "output"

    def test_default_sections_present(self, tmp_path):
        config = load_config(tmp_path)
        assert "blog" in config.sections
        assert "projects" in config.sections
        assert "pages" in config.sections

    def test_default_section_configs(self, tmp_path):
        config = load_config(tmp_path)
        assert config.sections["blog"]["date_in_url"] is True
        assert config.sections["blog"]["template"] == "post.html"
        assert config.sections["projects"]["date_in_url"] is False
        assert config.sections["pages"]["template"] == "page.html"

    def test_section_content_dirs_resolved(self, tmp_path):
        config = load_config(tmp_path)
        assert config.sections["blog"]["content_dir"] == tmp_path / "content" / "blog"
        assert config.sections["projects"]["content_dir"] == tmp_path / "content" / "projects"


class TestLoadConfigOverrides:

    def test_site_metadata_merge(self, tmp_path):
        """User site values override defaults; unset keys keep defaults."""
        (tmp_path / "site.yaml").write_text(textwrap.dedent("""\
            site:
              title: My Custom Site
        """))
        config = load_config(tmp_path)
        assert config.site["title"] == "My Custom Site"
        # Unset keys fall back to defaults
        assert config.site["language"] == DEFAULT_SITE_CONFIG["language"]
        assert config.site["nav"] == DEFAULT_SITE_CONFIG["nav"]

    def test_custom_dirs(self, tmp_path):
        (tmp_path / "site.yaml").write_text(textwrap.dedent("""\
            site:
              title: Test
            dirs:
              content: src
              output: dist
        """))
        config = load_config(tmp_path)
        assert config.content_dir == tmp_path / "src"
        assert config.output_dir == tmp_path / "dist"
        # Non-overridden dirs keep defaults
        assert config.templates_dir == tmp_path / "templates"

    def test_custom_sections(self, tmp_path):
        """User-defined sections beyond the three defaults."""
        (tmp_path / "site.yaml").write_text(textwrap.dedent("""\
            site:
              title: Test
            sections:
              tutorials:
                template: post.html
                date_in_url: true
        """))
        config = load_config(tmp_path)
        assert "tutorials" in config.sections
        assert config.sections["tutorials"]["template"] == "post.html"
        assert config.sections["tutorials"]["content_dir"] == tmp_path / "content" / "tutorials"
        # Default sections still present
        assert "blog" in config.sections

    def test_partial_build_settings(self, tmp_path):
        """Overriding some build settings keeps the rest as defaults."""
        (tmp_path / "site.yaml").write_text(textwrap.dedent("""\
            site:
              title: Test
            build:
              posts_per_page: 25
        """))
        config = load_config(tmp_path)
        assert config.posts_per_page == 25
        assert config.date_format == DEFAULT_BUILD_SETTINGS["date_format"]
        assert config.generate_rss is True

    def test_explicit_config_path(self, tmp_path):
        """load_config with an explicit config_path reads that file."""
        alt = tmp_path / "alt.yaml"
        alt.write_text(textwrap.dedent("""\
            site:
              title: Alt Config
        """))
        config = load_config(tmp_path, config_path=alt)
        assert config.site["title"] == "Alt Config"

    def test_section_override_merges_with_defaults(self, tmp_path):
        """Overriding one field in a default section keeps other defaults."""
        (tmp_path / "site.yaml").write_text(textwrap.dedent("""\
            site:
              title: Test
            sections:
              blog:
                date_in_url: false
        """))
        config = load_config(tmp_path)
        assert config.sections["blog"]["date_in_url"] is False
        assert config.sections["blog"]["template"] == DEFAULT_SECTIONS["blog"]["template"]


class TestSiteConfigDataclass:

    def test_replace_output_dir(self, tmp_path):
        config = load_config(tmp_path)
        new_output = tmp_path / "custom_out"
        replaced = dataclasses.replace(config, output_dir=new_output)
        assert replaced.output_dir == new_output
        assert replaced.content_dir == config.content_dir

    def test_bundled_dirs_exist(self, tmp_path):
        config = load_config(tmp_path)
        assert config.default_templates_dir.exists()
        assert config.default_static_dir.exists()
