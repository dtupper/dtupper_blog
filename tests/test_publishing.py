"""Check that publishing settings cannot hide content or break deployed links."""

from xml.etree import ElementTree

import pytest
from lxml import html

from conftest import build, write_post, write_page


def test_paginated_custom_index_keeps_every_post_reachable(tmp_project):
    (tmp_project / 'site.yaml').write_text('''site:
  url: https://example.com/journal/
sections:
  blog:
    url_pattern: news/{slug}
    index_template: news.html
build:
  posts_per_page: 2
''')
    templates = tmp_project / 'templates'
    templates.mkdir()
    (templates / 'news.html').write_text('''{% extends "index.html" %}
{% block head %}<meta name="custom-index" content="yes">{% endblock %}''')
    for day in range(1, 6):
        write_post(tmp_project, f'post{day}.md', f'Post {day}', f'2024-01-0{day}')

    build(tmp_project)

    found = []
    for page, relative in enumerate(['news', 'news/page/2', 'news/page/3'], 1):
        document = html.fromstring((tmp_project / 'output' / relative / 'index.html').read_text())
        assert document.xpath('//meta[@name="custom-index"]')
        assert '/journal/news/' in document.xpath('//nav[@class="main-nav"]/a/@href')
        canonical = document.xpath('//link[@rel="canonical"]/@href')
        assert canonical == [f'https://example.com/journal/{relative}/']
        titles = document.xpath('//article[@class="post-preview"]//h3/a/text()')
        assert len(titles) <= 2
        found.extend(titles)
        for link in document.xpath('//nav[@class="pagination"]/a/@href'):
            destination = link.removeprefix('/journal/').rstrip('/')
            assert (tmp_project / 'output' / destination / 'index.html').exists()
    assert found == ['Post 5', 'Post 4', 'Post 3', 'Post 2', 'Post 1']
    assert not (tmp_project / 'output/blog/index.html').exists()


def test_base_path_applies_to_assets_body_links_feed_and_social_metadata(tmp_project):
    (tmp_project / 'site.yaml').write_text('''site:
  url: https://example.com/blog
  image: /static/cover.svg
  nav:
    - label: Cover
      url: /static/cover.svg
''')
    (tmp_project / 'static').mkdir()
    (tmp_project / 'static/cover.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    write_post(tmp_project, 'post.md', 'Post', '2024-01-15')
    post = tmp_project / 'content/blog/post.md'
    post.write_text(post.read_text() + '''
[Home](/) ![Cover](/static/cover.svg)

`href="/literal"`

<span title='Example src="/literal"'>Example</span>
''')
    build(tmp_project)

    document = html.fromstring((tmp_project / 'output/blog/2024/01/post/index.html').read_text())
    assert document.xpath('//link[@rel="stylesheet"]/@href') == [
        '/blog/static/css/style.css', '/blog/static/css/custom.css',
    ]
    assert document.xpath('//img/@src') == ['/blog/static/cover.svg']
    assert '/blog/static/cover.svg' in document.xpath('//nav[@class="main-nav"]/a/@href')
    assert (tmp_project / 'output/static/cover.svg').exists()
    assert document.xpath('//code/text()') == ['href="/literal"']
    assert document.xpath('//span[@title]/@title') == ['Example src="/literal"']
    assert document.xpath('//meta[@property="og:image"]/@content') == [
        'https://example.com/blog/static/cover.svg',
    ]
    assert document.xpath('//link[@rel="canonical"]/@href') == [
        'https://example.com/blog/blog/2024/01/post/',
    ]
    feed = ElementTree.parse(tmp_project / 'output/feed.xml')
    assert feed.findtext('./channel/item/link') == 'https://example.com/blog/blog/2024/01/post/'


def test_configured_locale_and_date_format_reach_rendered_pages(tmp_project):
    (tmp_project / 'site.yaml').write_text('site:\n  locale: fr-FR\nbuild:\n  date_format: short\n')
    write_post(tmp_project, 'post.md', 'Post', '2024-01-15')
    build(tmp_project)

    document = html.fromstring((tmp_project / 'output/blog/2024/01/post/index.html').read_text())
    assert document.xpath('//div[@class="post-meta"]/time/text()') == ['15/01/2024']


def test_disabled_index_and_feed_are_not_advertised(tmp_project):
    (tmp_project / 'site.yaml').write_text('''sections:
  blog:
    index_template: null
build:
  generate_rss: false
''')
    write_post(tmp_project, 'post.md', 'Post', '2024-01-15')
    build(tmp_project)

    for path in (tmp_project / 'output').rglob('*.html'):
        document = html.fromstring(path.read_text())
        assert '/blog/' not in document.xpath('//a/@href')
        assert '/feed.xml' not in document.xpath('//a/@href | //link/@href')
    assert not (tmp_project / 'output/blog/index.html').exists()
    assert not (tmp_project / 'output/feed.xml').exists()


def test_sitemap_excludes_drafts_and_404_and_keeps_authored_last_modified(tmp_project):
    write_post(tmp_project, 'public.md', 'Public', '2024-01-15', last_updated='2024-02-01T10:00:00-07:00')
    write_post(tmp_project, 'private.md', 'Private', '2024-01-15', status='draft')
    write_page(tmp_project, 'about.md', 'About')
    build(tmp_project)

    namespace = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    sitemap = ElementTree.parse(tmp_project / 'output/sitemap.xml')
    entries = {entry.findtext('s:loc', namespaces=namespace): entry.findtext('s:lastmod', namespaces=namespace)
               for entry in sitemap.findall('s:url', namespace)}
    assert entries['https://example.com/blog/2024/01/public/'] == '2024-02-01T10:00:00-07:00'
    assert entries['https://example.com/about/'] is None
    assert not any('private' in url or '404' in url for url in entries)
    missing = html.fromstring((tmp_project / 'output/404.html').read_text())
    assert missing.xpath('//meta[@name="robots"]/@content') == ['noindex']
    assert '/' in missing.xpath('//a/@href')


def test_pagination_cannot_overwrite_an_authored_page(tmp_project):
    (tmp_project / 'site.yaml').write_text('''build:
  posts_per_page: 1
sections:
  pages:
    url_pattern: blog/page/{slug}
''')
    write_post(tmp_project, 'first.md', 'First', '2024-01-01')
    write_post(tmp_project, 'second.md', 'Second', '2024-01-02')
    write_page(tmp_project, '2.md', 'My page')

    with pytest.raises(ValueError, match='Route collision'):
        build(tmp_project)
    assert not (tmp_project / 'output').exists()
