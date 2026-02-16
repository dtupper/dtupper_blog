"""Tests for generator/embeds.py — embed processors and URL matching."""

import pytest

from generator.embeds import (
    EMBED_PROCESSORS,
    IMAGE_PROCESSOR,
    match_embed_url,
    process_bluesky,
    process_codepen,
    process_gist,
    process_image,
    process_spotify,
    process_timestamp,
    process_twitter,
    process_vimeo,
    process_youtube,
)


class TestEmbedProcessorRegistry:

    def test_all_expected_types_registered(self):
        expected = {"youtube", "vimeo", "twitter", "bluesky", "gist", "codepen", "spotify", "timestamp"}
        assert set(EMBED_PROCESSORS.keys()) == expected

    def test_image_processor_separate(self):
        assert IMAGE_PROCESSOR is process_image


class TestYouTubeEmbed:

    def test_default_dimensions(self):
        html = process_youtube("dQw4w9WgXcQ", {})
        assert 'src="https://www.youtube.com/embed/dQw4w9WgXcQ"' in html
        assert 'width="560"' in html
        assert 'height="315"' in html
        assert 'class="embed embed-youtube"' in html

    def test_custom_dimensions(self):
        html = process_youtube("abc123", {"width": "800", "height": "450"})
        assert 'width="800"' in html
        assert 'height="450"' in html


class TestVimeoEmbed:

    def test_default(self):
        html = process_vimeo("123456", {})
        assert 'src="https://player.vimeo.com/video/123456"' in html
        assert 'class="embed embed-vimeo"' in html


class TestTwitterEmbed:

    def test_default_theme(self):
        url = "https://twitter.com/user/status/123"
        html = process_twitter(url, {})
        assert 'data-theme="light"' in html
        assert f'href="{url}"' in html

    def test_dark_theme(self):
        html = process_twitter("https://x.com/u/status/1", {"theme": "dark"})
        assert 'data-theme="dark"' in html


class TestBlueskyEmbed:

    def test_basic(self):
        url = "https://bsky.app/profile/user.bsky.social/post/abc123"
        html = process_bluesky(url, {})
        assert f'data-bluesky-uri="{url}"' in html
        assert 'class="embed embed-bluesky"' in html


class TestGistEmbed:

    def test_basic(self):
        html = process_gist("user/abc123", {})
        assert 'src="https://gist.github.com/user/abc123.js"' in html

    def test_with_file(self):
        html = process_gist("user/abc123", {"file": "main.py"})
        assert 'src="https://gist.github.com/user/abc123.js?file=main.py"' in html


class TestCodePenEmbed:

    def test_valid_format(self):
        html = process_codepen("user/penid", {})
        assert 'src="https://codepen.io/user/embed/penid' in html
        assert 'class="embed embed-codepen"' in html

    def test_custom_attrs(self):
        html = process_codepen("user/penid", {"height": "500", "theme": "light", "tab": "css"})
        assert 'height="500"' in html
        assert "theme-id=light" in html
        assert "default-tab=css" in html

    def test_invalid_format_returns_error(self):
        html = process_codepen("invalid", {})
        assert '<p class="error">' in html
        assert "Invalid CodePen ID" in html


class TestSpotifyEmbed:

    def test_url_path_format(self):
        html = process_spotify("track/abc123", {})
        assert 'src="https://open.spotify.com/embed/track/abc123"' in html

    def test_uri_format_conversion(self):
        html = process_spotify("spotify:track:abc123", {})
        assert 'src="https://open.spotify.com/embed/track/abc123"' in html

    def test_custom_height(self):
        html = process_spotify("track/abc", {"height": "250"})
        assert 'height="250"' in html


class TestImageEmbed:

    def test_without_caption(self):
        html = process_image("Alt text", "/img/photo.jpg", {})
        assert '<div class="image">' in html
        assert 'alt="Alt text"' in html
        assert 'src="/img/photo.jpg"' in html
        assert "<figure" not in html

    def test_with_caption(self):
        html = process_image("Alt", "/img/x.jpg", {"caption": "A photo"})
        assert "<figure" in html
        assert "<figcaption>A photo</figcaption>" in html

    def test_with_width_and_class(self):
        html = process_image("Alt", "/img/x.jpg", {"width": "400", "class": "hero"})
        assert 'width="400"' in html
        assert 'class="image hero"' in html


class TestTimestampEmbed:

    def test_valid_iso(self):
        html = process_timestamp("2024-01-15T10:30:00", {})
        assert '<time datetime="2024-01-15T10:30:00">' in html
        assert "January" in html  # long format default

    def test_short_format(self):
        html = process_timestamp("2024-06-01T12:00:00", {"format": "short"})
        assert '<time datetime="2024-06-01T12:00:00">' in html

    def test_invalid_iso_falls_back(self):
        html = process_timestamp("not-a-date", {})
        assert '<time datetime="not-a-date">' in html
        assert "not-a-date" in html


class TestMatchEmbedUrl:

    @pytest.mark.parametrize("url,expected_type", [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("https://youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("https://youtu.be/dQw4w9WgXcQ", "youtube"),
        ("https://youtube.com/shorts/dQw4w9WgXcQ", "youtube"),
        ("https://vimeo.com/123456", "vimeo"),
        ("https://twitter.com/user/status/123456", "twitter"),
        ("https://x.com/user/status/123456", "twitter"),
        ("https://bsky.app/profile/user.bsky.social/post/abc123", "bluesky"),
        ("https://gist.github.com/user/abc123def", "gist"),
        ("https://codepen.io/user/pen/abcXYZ", "codepen"),
        ("https://open.spotify.com/track/abc123", "spotify"),
        ("https://open.spotify.com/album/abc123", "spotify"),
        ("https://open.spotify.com/playlist/abc123", "spotify"),
    ])
    def test_known_urls(self, url, expected_type):
        result = match_embed_url(url)
        assert result is not None
        embed_type, content = result
        assert embed_type == expected_type

    @pytest.mark.parametrize("url", [
        "https://example.com",
        "https://google.com/search?q=test",
        "https://github.com/user/repo",
        "not-a-url",
    ])
    def test_non_matching_urls(self, url):
        assert match_embed_url(url) is None

    def test_youtube_extracts_video_id(self):
        _, content = match_embed_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert content == "dQw4w9WgXcQ"

    def test_codepen_extracts_user_and_pen(self):
        _, content = match_embed_url("https://codepen.io/myuser/pen/abcXYZ")
        assert content == "myuser/abcXYZ"

    def test_spotify_extracts_type_and_id(self):
        _, content = match_embed_url("https://open.spotify.com/track/abc123")
        assert content == "track/abc123"
