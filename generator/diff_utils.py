"""Utilities for computing HTML diffs and preparing version data."""

import json
import re
from difflib import SequenceMatcher


def compute_change_markers(old_html: str, new_html: str) -> str:
    """Produce HTML showing new_html with inline change markers.

    Wraps inserted text in <ins class="diff-ins"> and deleted text in
    <del class="diff-del">. Operates on text tokens split on HTML tag
    boundaries so that tag structure is mostly preserved.

    Args:
        old_html: Previous version's rendered HTML.
        new_html: Current version's rendered HTML.

    Returns:
        HTML string with <ins>/<del> annotations.
    """
    old_tokens = _tokenize_html(old_html)
    new_tokens = _tokenize_html(new_html)

    sm = SequenceMatcher(None, old_tokens, new_tokens)
    result: list[str] = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            result.extend(new_tokens[j1:j2])
        elif tag == "insert":
            result.append('<ins class="diff-ins">')
            result.extend(new_tokens[j1:j2])
            result.append("</ins>")
        elif tag == "delete":
            result.append('<del class="diff-del">')
            result.extend(old_tokens[i1:i2])
            result.append("</del>")
        elif tag == "replace":
            result.append('<del class="diff-del">')
            result.extend(old_tokens[i1:i2])
            result.append("</del>")
            result.append('<ins class="diff-ins">')
            result.extend(new_tokens[j1:j2])
            result.append("</ins>")

    return "".join(result)


def _tokenize_html(html: str) -> list[str]:
    """Split HTML into tokens (tags and text chunks) for diffing."""
    return [t for t in re.split(r"(<[^>]+>)", html) if t]


def make_lazy(html: str) -> str:
    """Convert eager-loading resources to lazy in HTML.

    Replaces src= with data-src= on <img> and <iframe> tags so they
    only load when activated by JavaScript.

    Args:
        html: Rendered HTML string.

    Returns:
        Modified HTML with lazy-loading attributes.
    """
    # For img tags: replace src with data-src, use transparent GIF placeholder
    html = re.sub(
        r"<img\s([^>]*?)src=\"([^\"]*?)\"",
        r'<img \1data-src="\2" src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="',
        html,
    )
    # For iframes: replace src with data-src
    html = re.sub(
        r"<iframe\s([^>]*?)src=\"([^\"]*?)\"",
        r'<iframe \1data-src="\2"',
        html,
    )
    return html


def build_version_json(versions: list[dict]) -> str:
    """Serialize version data to JSON for embedding in a <script> tag.

    Args:
        versions: List of version dicts with html, diff_html, date,
                  commit_hash, author, message keys.

    Returns:
        JSON string.
    """
    return json.dumps(versions, ensure_ascii=False)
