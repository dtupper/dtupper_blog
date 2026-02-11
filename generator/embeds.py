"""Rich media embed processors."""

import re
from datetime import datetime
from typing import Any
from babel.dates import format_datetime


def process_youtube(video_id: str, attrs: dict[str, str]) -> str:
    """Generate YouTube embed HTML."""
    width = attrs.get("width", "560")
    height = attrs.get("height", "315")
    return f'''<div class="embed embed-youtube">
<iframe width="{width}" height="{height}" src="https://www.youtube.com/embed/{video_id}"
frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
allowfullscreen loading="lazy"></iframe>
</div>'''


def process_vimeo(video_id: str, attrs: dict[str, str]) -> str:
    """Generate Vimeo embed HTML."""
    width = attrs.get("width", "560")
    height = attrs.get("height", "315")
    return f'''<div class="embed embed-vimeo">
<iframe width="{width}" height="{height}" src="https://player.vimeo.com/video/{video_id}"
frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen loading="lazy"></iframe>
</div>'''


def process_twitter(tweet_url: str, attrs: dict[str, str]) -> str:
    """Generate Twitter/X embed HTML."""
    theme = attrs.get("theme", "light")
    return f'''<div class="embed embed-twitter">
<blockquote class="twitter-tweet" data-theme="{theme}">
<a href="{tweet_url}"></a>
</blockquote>
<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
</div>'''


def process_bluesky(post_url: str, attrs: dict[str, str]) -> str:
    """Generate Bluesky embed HTML."""
    return f'''<div class="embed embed-bluesky">
<blockquote class="bluesky-embed" data-bluesky-uri="{post_url}">
<a href="{post_url}">View on Bluesky</a>
</blockquote>
<script async src="https://embed.bsky.app/static/embed.js" charset="utf-8"></script>
</div>'''


def process_gist(gist_id: str, attrs: dict[str, str]) -> str:
    """Generate GitHub Gist embed HTML."""
    file_param = f"?file={attrs['file']}" if "file" in attrs else ""
    return f'''<div class="embed embed-gist">
<script src="https://gist.github.com/{gist_id}.js{file_param}"></script>
</div>'''


def process_codepen(pen_id: str, attrs: dict[str, str]) -> str:
    """Generate CodePen embed HTML."""
    height = attrs.get("height", "300")
    theme = attrs.get("theme", "dark")
    default_tab = attrs.get("tab", "result")
    # pen_id format: username/pen_id
    parts = pen_id.split("/")
    if len(parts) != 2:
        return f'<p class="error">Invalid CodePen ID: {pen_id}</p>'
    username, pen = parts
    return f'''<div class="embed embed-codepen">
<iframe height="{height}" style="width: 100%;" scrolling="no"
src="https://codepen.io/{username}/embed/{pen}?default-tab={default_tab}&theme-id={theme}"
frameborder="no" loading="lazy" allowtransparency="true" allowfullscreen="true">
</iframe>
</div>'''


def process_spotify(uri: str, attrs: dict[str, str]) -> str:
    """Generate Spotify embed HTML."""
    height = attrs.get("height", "352")
    # Convert spotify:track:xxx to track/xxx format if needed
    if uri.startswith("spotify:"):
        parts = uri.split(":")
        if len(parts) >= 3:
            uri = f"{parts[1]}/{parts[2]}"
    # Handle URLs like track/xxx or playlist/xxx
    return f'''<div class="embed embed-spotify">
<iframe style="border-radius:12px"
src="https://open.spotify.com/embed/{uri}"
width="100%" height="{height}" frameBorder="0" allowfullscreen=""
allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy">
</iframe>
</div>'''


def process_image(alt_text: str, path: str, attrs: dict[str, str]) -> str:
    """Generate enhanced image HTML with caption support."""
    caption = attrs.get("caption", "")
    width = attrs.get("width", "")
    css_class = attrs.get("class", "")

    width_attr = f' width="{width}"' if width else ""
    class_attr = f' class="image {css_class}"' if css_class else ' class="image"'

    img_html = f'<img src="{path}" alt="{alt_text}"{width_attr} loading="lazy">'

    if caption:
        return f'''<figure{class_attr}>
{img_html}
<figcaption>{caption}</figcaption>
</figure>'''
    else:
        return f'<div{class_attr}>{img_html}</div>'


def process_timestamp(iso_time: str, attrs: dict[str, str]) -> str:
    """Generate locale-aware timestamp HTML."""
    locale = attrs.get("locale", "en-US")
    fmt = attrs.get("format", "long")

    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))

        # Map format names to Babel format patterns
        format_map = {
            "short": "short",
            "medium": "medium",
            "long": "long",
            "full": "full",
        }
        babel_format = format_map.get(fmt, "long")

        formatted = format_datetime(dt, format=babel_format, locale=locale.replace("-", "_"))

        return f'<time datetime="{iso_time}">{formatted}</time>'
    except (ValueError, TypeError) as e:
        return f'<time datetime="{iso_time}">{iso_time}</time>'


# Registry of embed processors
EMBED_PROCESSORS: dict[str, Any] = {
    "youtube": process_youtube,
    "vimeo": process_vimeo,
    "twitter": process_twitter,
    "bluesky": process_bluesky,
    "gist": process_gist,
    "codepen": process_codepen,
    "spotify": process_spotify,
    "timestamp": process_timestamp,
}

# Special processor for images (different signature)
IMAGE_PROCESSOR = process_image


# URL patterns for auto-embed detection
# Each tuple: (compiled_regex, embed_type, content_extractor)
_EMBED_URL_PATTERNS: list[tuple[re.Pattern, str, Any]] = [
    # YouTube
    (re.compile(r'https?://(?:www\.)?youtube\.com/watch\?.*?v=([a-zA-Z0-9_-]+)'),
     'youtube', lambda m: m.group(1)),
    (re.compile(r'https?://(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]+)'),
     'youtube', lambda m: m.group(1)),
    (re.compile(r'https?://youtu\.be/([a-zA-Z0-9_-]+)'),
     'youtube', lambda m: m.group(1)),
    # Vimeo
    (re.compile(r'https?://(?:www\.)?vimeo\.com/(\d+)'),
     'vimeo', lambda m: m.group(1)),
    # Twitter / X
    (re.compile(r'https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/\d+'),
     'twitter', lambda m: m.group(0)),
    # Bluesky
    (re.compile(r'https?://bsky\.app/profile/[^/]+/post/[a-zA-Z0-9]+'),
     'bluesky', lambda m: m.group(0)),
    # GitHub Gist
    (re.compile(r'https?://gist\.github\.com/([^/]+/[a-f0-9]+)'),
     'gist', lambda m: m.group(1)),
    # CodePen
    (re.compile(r'https?://codepen\.io/([^/]+)/pen/([a-zA-Z0-9]+)'),
     'codepen', lambda m: f"{m.group(1)}/{m.group(2)}"),
    # Spotify
    (re.compile(r'https?://open\.spotify\.com/(track|album|playlist|episode|show)/([a-zA-Z0-9]+)'),
     'spotify', lambda m: f"{m.group(1)}/{m.group(2)}"),
]


def match_embed_url(url: str) -> tuple[str, str] | None:
    """Match a URL against known embed service patterns.

    Returns (embed_type, content) if matched, None otherwise.
    The content value is exactly what the corresponding processor expects.
    """
    for pattern, embed_type, extractor in _EMBED_URL_PATTERNS:
        match = pattern.match(url)
        if match:
            return (embed_type, extractor(match))
    return None
