"""Tests for generator/markdown_ext.py — Markdown extensions and processing."""

import pytest

from generator.markdown_ext import (
    FrontmatterExtractor,
    create_markdown_processor,
    process_markdown,
)


class TestFrontmatterExtractor:

    def test_valid_frontmatter(self):
        content = "---\ntitle: Hello\ndate: 2024-01-15\n---\n\nBody text."
        meta, remaining = FrontmatterExtractor.extract(content)
        assert meta["title"] == "Hello"
        assert remaining.strip() == "Body text."

    def test_no_frontmatter(self):
        content = "Just some text without frontmatter."
        meta, remaining = FrontmatterExtractor.extract(content)
        assert meta == {}
        assert remaining == content

    def test_malformed_yaml(self):
        content = "---\n: [invalid yaml\n---\n\nBody."
        with pytest.raises(ValueError, match="Invalid YAML"):
            FrontmatterExtractor.extract(content)

    def test_frontmatter_with_tags_list(self):
        content = "---\ntitle: Post\ntags: [python, web]\n---\n\nBody."
        meta, _ = FrontmatterExtractor.extract(content)
        assert meta["tags"] == ["python", "web"]

    def test_empty_frontmatter(self):
        """Empty frontmatter requires at least a newline between the delimiters."""
        content = "---\n\n---\n\nBody."
        meta, remaining = FrontmatterExtractor.extract(content)
        assert meta == {}
        assert remaining.strip() == "Body."


class TestProcessMarkdown:

    def test_basic_content(self):
        meta, html = process_markdown("# Hello\n\nParagraph text.")
        assert meta == {}
        assert "<h1" in html  # toc extension adds id attr to headings
        assert "Hello" in html
        assert "Paragraph text." in html

    def test_frontmatter_and_body(self):
        content = "---\ntitle: My Post\n---\n\n**Bold** text."
        meta, html = process_markdown(content)
        assert meta["title"] == "My Post"
        assert "<strong>Bold</strong>" in html

    def test_fenced_code_block(self):
        content = "```python\nprint('hello')\n```"
        _, html = process_markdown(content)
        assert "code-block" in html or "highlight" in html

    def test_table_rendering(self):
        content = "| A | B |\n|---|---|\n| 1 | 2 |"
        _, html = process_markdown(content)
        assert "<table>" in html


class TestAutoEmbedUrls:

    def test_standalone_youtube_url_becomes_embed(self):
        content = "---\ntitle: T\n---\n\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ"
        _, html = process_markdown(content)
        assert "embed-youtube" in html
        assert "dQw4w9WgXcQ" in html

    def test_angle_bracket_url_suppresses_embed(self):
        content = "---\ntitle: T\n---\n\n<https://www.youtube.com/watch?v=dQw4w9WgXcQ>"
        _, html = process_markdown(content)
        assert "embed-youtube" not in html

    def test_url_inside_code_fence_not_embedded(self):
        content = "---\ntitle: T\n---\n\n```\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ\n```"
        _, html = process_markdown(content)
        assert "embed-youtube" not in html

    def test_inline_url_appends_embed(self):
        content = "---\ntitle: T\n---\n\nCheck out https://www.youtube.com/watch?v=dQw4w9WgXcQ for fun."
        _, html = process_markdown(content)
        # The inline text should remain AND the embed should appear
        assert "Check out" in html
        assert "embed-youtube" in html


class TestExplicitEmbedSyntax:

    def test_youtube_directive(self):
        content = '---\ntitle: T\n---\n\n::youtube[dQw4w9WgXcQ]{width="800" height="450"}'
        _, html = process_markdown(content)
        assert "embed-youtube" in html
        assert 'width="800"' in html

    def test_image_directive(self):
        content = '---\ntitle: T\n---\n\n::image[Alt text](/img/photo.jpg){caption="A photo"}'
        _, html = process_markdown(content)
        assert "<figure" in html
        assert "A photo" in html

    def test_unknown_embed_type_passes_through(self):
        content = "---\ntitle: T\n---\n\n::unknown[content](path){attr=\"val\"}"
        _, html = process_markdown(content)
        assert "::unknown" in html


class TestCalloutDirective:

    def test_callout_basic(self):
        content = "---\ntitle: T\n---\n\n:::callout\nImportant note.\n:::"
        _, html = process_markdown(content)
        assert 'class="callout"' in html
        assert "Important note." in html

    def test_callout_with_emoji(self):
        content = "---\ntitle: T\n---\n\n:::callout\n\U0001f4a1 Tip content here.\n:::"
        _, html = process_markdown(content)
        assert 'data-icon="\U0001f4a1"' in html
        assert "Tip content here." in html

    def test_details_directive(self):
        content = "---\ntitle: T\n---\n\n:::details[Click to expand]\nHidden content.\n:::"
        _, html = process_markdown(content)
        assert "<details" in html
        assert "<summary>Click to expand</summary>" in html
        assert "Hidden content." in html


class TestAsidePreprocessor:

    def test_aside_converted_to_callout(self):
        content = "---\ntitle: T\n---\n\n<aside>\nNote text.\n</aside>"
        _, html = process_markdown(content)
        assert 'class="callout"' in html
        assert "Note text." in html


class TestNotionLinkPreprocessor:

    def test_notion_md_links_stripped(self):
        content = "---\ntitle: T\n---\n\nSee [My Page](some-page.md) for details."
        _, html = process_markdown(content, notion_links=True)
        assert "My Page" in html
        assert "some-page.md" not in html
        # Should not be a link
        assert 'href="some-page.md"' not in html


class TestTaskListPostprocessor:

    def test_checked_item(self):
        content = "---\ntitle: T\n---\n\n- [x] Done item"
        _, html = process_markdown(content)
        assert 'type="checkbox"' in html
        assert "checked" in html
        assert "task-list-item" in html

    def test_unchecked_item(self):
        content = "---\ntitle: T\n---\n\n- [ ] Todo item"
        _, html = process_markdown(content)
        assert 'type="checkbox"' in html
        assert "task-list-item" in html


class TestCodeHighlighting:

    def test_python_syntax_highlighting(self):
        content = '---\ntitle: T\n---\n\n```python\ndef hello():\n    return "world"\n```'
        _, html = process_markdown(content)
        assert 'data-language="python"' in html
        assert "highlight" in html
