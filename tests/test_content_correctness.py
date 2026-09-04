"""Regression checks for silently lost text, overwritten pages, and unstable dates."""

import re
from html import unescape
from xml.etree import ElementTree

import pytest

from generator.build import SiteBuilder
from generator.config import load_config
from generator.embeds import process_image, process_gist
from generator.markdown_ext import process_markdown

from conftest import build, write_post, write_page


def visible_text(markup):
    return unescape(re.sub(r"<[^>]+>", "", markup))


@pytest.mark.parametrize("source, expected", [
    ('```markdown\n[Page](page.md)\n```', '[Page](page.md)'),
    ('```html\n<aside>\nExample\n</aside>\n```', '<aside>\nExample\n</aside>'),
    ('`::youtube[example]`', '::youtube[example]'),
    ('``Use `::youtube[example]` literally``', 'Use `::youtube[example]` literally'),
    ('    https://youtu.be/example', 'https://youtu.be/example'),
    ('````markdown\n```\n::youtube[example]\n```\n````', '```\n::youtube[example]\n```'),
    ('```text\n    &quot;literal entity&quot;\n```', '    &quot;literal entity&quot;'),
])
def test_authoring_transformations_preserve_code(source, expected):
    _, markup = process_markdown(source, notion_links=True)

    assert expected in visible_text(markup)
    assert '<iframe' not in markup


@pytest.mark.parametrize('directive', ['callout', 'details[More]'])
def test_unclosed_directive_reports_error_instead_of_dropping_article(directive):
    with pytest.raises(ValueError, match='Unclosed :::'):
        process_markdown(f'Before\n\n:::{directive}\nKeep the rest of my article.')


def test_nested_directives_keep_content_after_inner_close():
    source = ':::callout\nOuter\n:::details[More]\nInner\n:::\nEnding\n:::'
    _, markup = process_markdown(source)
    assert all(text in visible_text(markup) for text in ['Outer', 'Inner', 'Ending'])
    assert '<details>' in markup


def test_opening_colon_paragraph_and_markdown_links_are_preserved_by_default():
    _, markup = process_markdown('Note: keep this paragraph.\n\n[Other page](other.md)')
    assert 'Note: keep this paragraph.' in markup
    assert 'href="other.md"' in markup


def test_embed_attributes_cannot_turn_quoted_text_into_html_attributes():
    from lxml import html

    markup = process_image('A "quoted" photo', '/photo?a=1&b=2', {
        'width': '100" onerror="alert(1)', 'caption': '<script>example</script>',
    })
    image = html.fromstring(markup).find('.//img')
    assert image.get('alt') == 'A "quoted" photo'
    assert image.get('width') == '100" onerror="alert(1)'
    assert 'onerror' not in image.attrib
    assert '<script>' not in markup
    assert 'file=a%26b+file.py' in process_gist('user/abc', {'file': 'a&b file.py'})


def test_mixed_date_formats_sort_and_rss_preserves_instants(tmp_project):
    write_post(tmp_project, 'earlier.md', 'Earlier', '2024-01-02')
    write_post(tmp_project, 'later.md', 'Later', '2024-01-01T20:00:00-07:00')
    builder = build(tmp_project)

    assert [post.metadata['title'] for post in builder.content['blog']] == ['Later', 'Earlier']
    entries = ElementTree.parse(tmp_project / 'output/feed.xml').findall('./channel/item')
    assert [entry.findtext('title') for entry in entries] == ['Later', 'Earlier']
    assert entries[0].findtext('pubDate') == 'Mon, 01 Jan 2024 20:00:00 -0700'


def test_missing_blog_date_cannot_move_existing_published_url(tmp_project):
    write_post(tmp_project, 'post.md', 'Stable', '2024-01-15')
    build(tmp_project)
    old_page = tmp_project / 'output/blog/2024/01/post/index.html'
    previous = old_page.read_bytes()
    (tmp_project / 'content/blog/post.md').write_text('---\ntitle: Stable\n---\n\nBody')

    with pytest.raises(ValueError, match='post.md.*explicit date'):
        build(tmp_project)

    assert old_page.read_bytes() == previous


@pytest.mark.parametrize('slug', ['same', '!!!'])
def test_duplicate_or_empty_slugs_cannot_overwrite_posts(tmp_project, slug):
    write_post(tmp_project, 'first.md', 'First', '2024-01-15', slug='same')
    write_post(tmp_project, 'second.md', 'Second', '2024-01-15', slug=f'"{slug}"')

    with pytest.raises(ValueError, match='Route collision|slug must contain'):
        build(tmp_project)
    assert not (tmp_project / 'output').exists()


@pytest.mark.parametrize('pattern', ['blog', 'static/css', 'feed.xml/nested'])
def test_content_cannot_overwrite_generated_routes(tmp_project, pattern):
    write_page(tmp_project, 'page.md', 'Page')
    config = load_config(tmp_project)
    config.sections['pages']['url_pattern'] = pattern

    with pytest.raises(ValueError, match='Route collision|static assets'):
        SiteBuilder(config).build()
    assert not (tmp_project / 'output').exists()
