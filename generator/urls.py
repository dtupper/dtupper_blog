"""One URL policy for templates, feeds, and authored root-relative links."""

import re
from html import escape, unescape
from html.parser import HTMLParser
from urllib.parse import urlsplit


class SiteURLs:
    def __init__(self, site_url: str):
        parsed = urlsplit(site_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("site.url must be an absolute http or https URL")
        if parsed.query or parsed.fragment or ".." in parsed.path.split("/"):
            raise ValueError("site.url cannot contain a query, fragment, or parent path")
        self.origin = f"{parsed.scheme}://{parsed.netloc}"
        self.base_path = parsed.path.rstrip("/")

    def local(self, path: str) -> str:
        parsed = urlsplit(path)
        if parsed.scheme or parsed.netloc or path.startswith(("#", "?")):
            return path
        return self.base_path + "/" + path.lstrip("/")

    def absolute(self, path: str) -> str:
        local = self.local(path)
        parsed = urlsplit(local)
        if parsed.scheme:
            return local
        if parsed.netloc:
            return urlsplit(self.origin).scheme + ":" + local
        return self.origin + local

    def rewrite_body(self, markup: str) -> str:
        if not self.base_path:
            return markup
        parser = BodyURLs(self)
        parser.feed(markup)
        parser.close()
        return "".join(parser.output)


class BodyURLs(HTMLParser):
    """Keep authored HTML intact, replacing only root-relative URL attributes."""

    ATTR = re.compile(r'''(\s+)([^\s=/>]+)(\s*=\s*)(["'])(.*?)\4''', re.S)

    def __init__(self, urls):
        super().__init__(convert_charrefs=False)
        self.urls = urls
        self.output = []

    def handle_starttag(self, tag, attrs):
        def replace(match):
            value = unescape(match.group(5))
            if (match.group(2).lower() in {"href", "src", "poster", "action"}
                    and value.startswith("/") and not value.startswith("//")):
                value = escape(self.urls.local(value), quote=True)
                return "".join(match.group(i) for i in (1, 2, 3, 4)) + value + match.group(4)
            return match.group(0)
        self.output.append(self.ATTR.sub(replace, self.get_starttag_text()))

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        self.output.append(f"</{tag}>")

    def handle_data(self, data):
        self.output.append(data)

    def handle_entityref(self, name):
        self.output.append(f"&{name};")

    def handle_charref(self, name):
        self.output.append(f"&#{name};")

    def handle_comment(self, data):
        self.output.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.output.append(f"<!{decl}>")
