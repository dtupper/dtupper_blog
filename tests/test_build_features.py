"""Tests for build time timezone fix, recently-updated, and recently-posted features."""

import textwrap
from datetime import datetime, timedelta, timezone

import pytest

from generator.config import DEFAULT_BUILD_SETTINGS, load_config
from generator.build import SiteBuilder

from conftest import build as _build, write_post as _write_post, write_project as _write_project


# ─── Bug fix: build_time is UTC-aware ────────────────────────────────

class TestBuildTimeTimezone:

    def test_build_time_is_utc(self, tmp_project):
        """build_time should be a timezone-aware UTC datetime."""
        config = load_config(tmp_project)
        builder = SiteBuilder(config)
        build_time = builder.env.globals["build_time"]

        assert build_time.tzinfo is not None, "build_time must be timezone-aware"
        assert build_time.tzinfo == timezone.utc, "build_time must be UTC"

    def test_build_time_close_to_now(self, tmp_project):
        """build_time should be within a few seconds of the current UTC time."""
        before = datetime.now(timezone.utc)
        config = load_config(tmp_project)
        builder = SiteBuilder(config)
        after = datetime.now(timezone.utc)

        build_time = builder.env.globals["build_time"]
        assert before <= build_time <= after

    def test_footer_contains_utc_datetime_z(self, tmp_project):
        """The rendered footer should have a datetime attribute ending with Z."""
        builder = _build(tmp_project)
        index_html = (tmp_project / "output" / "index.html").read_text()
        # Look for the Z-terminated ISO datetime in the time element
        assert 'datetime="' in index_html
        # Extract the datetime attribute value
        import re
        match = re.search(r'datetime="([^"]+)"', index_html)
        assert match is not None
        dt_value = match.group(1)
        assert dt_value.endswith("Z"), f"datetime attribute should end with Z, got: {dt_value}"


# ─── Config: recently_updated_days / recently_posted_days ────────────

class TestRecencyConfig:

    def test_default_values(self, tmp_project):
        """Default recency settings should be 7 days."""
        config = load_config(tmp_project)
        assert config.recently_updated_days == 7
        assert config.recently_posted_days == 7

    def test_custom_values(self, tmp_project):
        """Custom recency settings from site.yaml should be respected."""
        (tmp_project / "site.yaml").write_text(textwrap.dedent("""\
            site:
              title: Test Site
              description: Test
              author: Tester
              url: https://example.com
              language: en
              locale: en-US
            build:
              recently_updated_days: 14
              recently_posted_days: 3
        """))
        config = load_config(tmp_project)
        assert config.recently_updated_days == 14
        assert config.recently_posted_days == 3

    def test_cutoff_globals_set(self, tmp_project):
        """Template globals should include recency cutoff dates."""
        config = load_config(tmp_project)
        builder = SiteBuilder(config)
        assert "recently_updated_cutoff" in builder.env.globals
        assert "recently_posted_cutoff" in builder.env.globals
        assert isinstance(builder.env.globals["recently_updated_cutoff"], datetime)
        assert isinstance(builder.env.globals["recently_posted_cutoff"], datetime)

    def test_cutoff_uses_configured_days(self, tmp_project):
        """Cutoff dates should reflect the configured number of days."""
        (tmp_project / "site.yaml").write_text(textwrap.dedent("""\
            site:
              title: Test Site
              description: Test
              author: Tester
              url: https://example.com
              language: en
              locale: en-US
            build:
              recently_updated_days: 14
              recently_posted_days: 3
        """))
        before = datetime.now()
        config = load_config(tmp_project)
        builder = SiteBuilder(config)
        after = datetime.now()

        updated_cutoff = builder.env.globals["recently_updated_cutoff"]
        posted_cutoff = builder.env.globals["recently_posted_cutoff"]

        # The cutoff should be approximately now - N days
        assert (before - timedelta(days=14)) <= updated_cutoff <= (after - timedelta(days=14))
        assert (before - timedelta(days=3)) <= posted_cutoff <= (after - timedelta(days=3))


# ─── Feature: "New" badge for recently posted blog entries ───────────

class TestRecentlyPostedBadge:

    def test_new_badge_on_recent_post_in_listing(self, tmp_project):
        """A blog post dated today should get a 'New' badge on the listing page."""
        today = datetime.now().strftime("%Y-%m-%d")
        _write_post(tmp_project, "fresh.md", "Fresh Post", today)
        _build(tmp_project)

        index_html = (tmp_project / "output" / "blog" / "index.html").read_text()
        assert "badge-new" in index_html
        assert "New" in index_html

    def test_no_new_badge_on_old_post_in_listing(self, tmp_project):
        """A blog post older than the cutoff should NOT get a 'New' badge."""
        old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        _write_post(tmp_project, "old.md", "Old Post", old_date)
        _build(tmp_project)

        index_html = (tmp_project / "output" / "blog" / "index.html").read_text()
        assert "badge-new" not in index_html

    def test_new_badge_on_recent_post_detail_page(self, tmp_project):
        """A recent blog post's own page should show the 'New' badge."""
        today = datetime.now().strftime("%Y-%m-%d")
        _write_post(tmp_project, "fresh.md", "Fresh Post", today)
        builder = _build(tmp_project)

        # Find the rendered post page
        post_pages = list((tmp_project / "output" / "blog").rglob("fresh/index.html"))
        # date_in_url might be on, so search more broadly
        if not post_pages:
            post_pages = list((tmp_project / "output").rglob("**/fresh/index.html"))
        assert len(post_pages) >= 1, "Post page should exist"

        post_html = post_pages[0].read_text()
        assert "badge-new" in post_html

    def test_no_new_badge_on_old_post_detail_page(self, tmp_project):
        """An old blog post's page should NOT show the 'New' badge."""
        old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        _write_post(tmp_project, "old.md", "Old Post", old_date)
        builder = _build(tmp_project)

        post_pages = list((tmp_project / "output").rglob("**/old/index.html"))
        assert len(post_pages) >= 1
        post_html = post_pages[0].read_text()
        assert "badge-new" not in post_html

    def test_new_badge_respects_custom_days(self, tmp_project):
        """With recently_posted_days=2, a 5-day-old post should NOT get the badge."""
        (tmp_project / "site.yaml").write_text(textwrap.dedent("""\
            site:
              title: Test Site
              description: Test
              author: Tester
              url: https://example.com
              language: en
              locale: en-US
            build:
              recently_posted_days: 2
        """))
        five_days_ago = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        _write_post(tmp_project, "medium.md", "Medium Post", five_days_ago)
        _build(tmp_project)

        index_html = (tmp_project / "output" / "blog" / "index.html").read_text()
        assert "badge-new" not in index_html

    def test_new_badge_on_homepage(self, tmp_project):
        """Recent posts should also show the 'New' badge on the homepage."""
        today = datetime.now().strftime("%Y-%m-%d")
        _write_post(tmp_project, "fresh.md", "Fresh Post", today)
        _build(tmp_project)

        homepage = (tmp_project / "output" / "index.html").read_text()
        assert "badge-new" in homepage


# ─── Feature: "Recently Updated" badge ───────────────────────────────

class TestRecentlyUpdatedBadge:

    def test_updated_badge_on_listing(self, tmp_project):
        """A post with last_updated within the cutoff should show 'Recently Updated'."""
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        _write_post(tmp_project, "updated.md", "Updated Post", old_date,
                     last_updated=today)
        _build(tmp_project)

        index_html = (tmp_project / "output" / "blog" / "index.html").read_text()
        assert "badge-updated" in index_html
        assert "Recently Updated" in index_html

    def test_updated_badge_takes_priority_over_new(self, tmp_project):
        """If a post is both recent and recently updated, 'Recently Updated' wins."""
        today = datetime.now().strftime("%Y-%m-%d")
        _write_post(tmp_project, "both.md", "Both Post", today,
                     last_updated=today)
        _build(tmp_project)

        index_html = (tmp_project / "output" / "blog" / "index.html").read_text()
        assert "badge-updated" in index_html
        # Should NOT also show "New" for the same post
        assert "badge-new" not in index_html

    def test_no_updated_badge_when_stale(self, tmp_project):
        """A post with last_updated older than the cutoff should NOT show the badge."""
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        old_update = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        _write_post(tmp_project, "stale.md", "Stale Post", old_date,
                     last_updated=old_update)
        _build(tmp_project)

        index_html = (tmp_project / "output" / "blog" / "index.html").read_text()
        assert "badge-updated" not in index_html

    def test_updated_badge_on_post_detail(self, tmp_project):
        """The post detail page should also show the 'Recently Updated' badge."""
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        _write_post(tmp_project, "updated.md", "Updated Post", old_date,
                     last_updated=today)
        builder = _build(tmp_project)

        post_pages = list((tmp_project / "output").rglob("**/updated/index.html"))
        assert len(post_pages) >= 1
        post_html = post_pages[0].read_text()
        assert "badge-updated" in post_html

    def test_updated_badge_on_project_listing(self, tmp_project):
        """Projects with recent last_updated should show the badge on the listing."""
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        _write_project(tmp_project, "my-project.md", "My Project", old_date,
                        last_updated=today, status="active")
        _build(tmp_project)

        projects_html = (tmp_project / "output" / "projects" / "index.html").read_text()
        assert "badge-updated" in projects_html

    def test_no_updated_badge_on_project_without_last_updated(self, tmp_project):
        """Projects without last_updated should not show the badge."""
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        _write_project(tmp_project, "plain.md", "Plain Project", old_date,
                        status="active")
        _build(tmp_project)

        projects_html = (tmp_project / "output" / "projects" / "index.html").read_text()
        assert "badge-updated" not in projects_html

    def test_updated_badge_respects_custom_days(self, tmp_project):
        """With recently_updated_days=3, a 5-day-old update should NOT get the badge."""
        (tmp_project / "site.yaml").write_text(textwrap.dedent("""\
            site:
              title: Test Site
              description: Test
              author: Tester
              url: https://example.com
              language: en
              locale: en-US
            build:
              recently_updated_days: 3
        """))
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        five_days_ago = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        _write_post(tmp_project, "medium-update.md", "Medium Update", old_date,
                     last_updated=five_days_ago)
        _build(tmp_project)

        index_html = (tmp_project / "output" / "blog" / "index.html").read_text()
        assert "badge-updated" not in index_html


# ─── Mixed scenarios ─────────────────────────────────────────────────

class TestMixedScenarios:

    def test_mixed_posts_correct_badges(self, tmp_project):
        """Multiple posts with different ages should get the correct badges."""
        today = datetime.now().strftime("%Y-%m-%d")
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

        _write_post(tmp_project, "new-post.md", "New Post", today)
        _write_post(tmp_project, "updated-post.md", "Updated Post", old_date,
                     last_updated=today)
        _write_post(tmp_project, "old-post.md", "Old Post", old_date)
        _build(tmp_project)

        index_html = (tmp_project / "output" / "blog" / "index.html").read_text()

        # "New Post" should have badge-new
        assert "badge-new" in index_html
        # "Updated Post" should have badge-updated
        assert "badge-updated" in index_html

        # Verify old post section has neither badge by checking the structure
        # Split by article boundaries and check each one
        articles = index_html.split('<article class="post-preview">')
        for article in articles[1:]:  # skip content before first article
            if "Old Post" in article:
                assert "badge-new" not in article, "Old Post should not have New badge"
                assert "badge-updated" not in article, "Old Post should not have Updated badge"

    def test_no_badges_when_all_content_is_old(self, tmp_project):
        """When all content is old, no badges should appear anywhere."""
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        _write_post(tmp_project, "old1.md", "Old One", old_date)
        _write_post(tmp_project, "old2.md", "Old Two", old_date)
        _write_project(tmp_project, "old-proj.md", "Old Project", old_date)
        _build(tmp_project)

        for html_file in (tmp_project / "output").rglob("*.html"):
            content = html_file.read_text()
            assert "badge-new" not in content, f"Unexpected New badge in {html_file}"
            assert "badge-updated" not in content, f"Unexpected Updated badge in {html_file}"
