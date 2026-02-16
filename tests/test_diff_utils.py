"""Tests for diff utility functions."""

import json

from generator.diff_utils import build_version_json, compute_change_markers, make_lazy


class TestComputeChangeMarkers:
    def test_identical_html_no_markers(self):
        html = "<p>Hello world</p>"
        result = compute_change_markers(html, html)
        assert "diff-ins" not in result
        assert "diff-del" not in result
        assert "Hello world" in result

    def test_insertion_marked(self):
        old = "<p>Hello</p>"
        new = "<p>Hello world</p>"
        result = compute_change_markers(old, new)
        assert "diff-ins" in result
        assert "world" in result

    def test_deletion_marked(self):
        old = "<p>Hello world</p>"
        new = "<p>Hello</p>"
        result = compute_change_markers(old, new)
        assert "diff-del" in result
        assert "world" in result

    def test_replacement_shows_both(self):
        old = "<p>foo</p>"
        new = "<p>bar</p>"
        result = compute_change_markers(old, new)
        assert "diff-del" in result
        assert "diff-ins" in result
        assert "foo" in result
        assert "bar" in result

    def test_added_paragraph(self):
        old = "<p>First</p>"
        new = "<p>First</p>\n<p>Second</p>"
        result = compute_change_markers(old, new)
        assert "diff-ins" in result
        assert "Second" in result

    def test_tag_change_preserved(self):
        old = "<h2>Title</h2>"
        new = "<h3>Title</h3>"
        result = compute_change_markers(old, new)
        # Both old and new tags should appear in diff
        assert "diff-del" in result
        assert "diff-ins" in result


class TestMakeLazy:
    def test_img_src_becomes_data_src(self):
        html = '<img src="/photo.jpg" alt="photo">'
        result = make_lazy(html)
        assert 'data-src="/photo.jpg"' in result
        assert 'src="data:image/gif' in result

    def test_iframe_src_becomes_data_src(self):
        html = '<iframe src="https://youtube.com/embed/abc"></iframe>'
        result = make_lazy(html)
        assert 'data-src="https://youtube.com/embed/abc"' in result
        # The original src= should be gone (only data-src= remains)
        assert ' src="https://youtube.com/embed/abc"' not in result

    def test_no_change_when_no_resources(self):
        html = "<p>Just text</p>"
        assert make_lazy(html) == html

    def test_multiple_images(self):
        html = '<img src="/a.jpg"><img src="/b.jpg">'
        result = make_lazy(html)
        assert 'data-src="/a.jpg"' in result
        assert 'data-src="/b.jpg"' in result


class TestBuildVersionJson:
    def test_roundtrip(self):
        versions = [
            {"html": "<p>hi</p>", "date": "2024-01-01T00:00:00+00:00"}
        ]
        result = build_version_json(versions)
        parsed = json.loads(result)
        assert parsed == versions

    def test_unicode_preserved(self):
        versions = [{"html": "<p>café</p>"}]
        result = build_version_json(versions)
        assert "café" in result
