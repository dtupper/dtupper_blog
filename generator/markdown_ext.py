"""Custom Markdown extensions for rich media embeds and enhanced syntax."""

import re
import uuid
from html import escape, unescape
import markdown
from xml.etree.ElementTree import Element
from markdown.preprocessors import Preprocessor
from markdown.postprocessors import Postprocessor
from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

from .embeds import EMBED_PROCESSORS, IMAGE_PROCESSOR, match_embed_url
from .validation import load_yaml_mapping, validate_metadata


class FrontmatterExtractor:
    """Extract YAML frontmatter from markdown content."""

    FRONTMATTER_PATTERN = re.compile(
        r"\A---[^\S\n]*\n(.*?)^---[^\S\n]*(?:\n|\Z)", re.DOTALL | re.MULTILINE
    )

    @classmethod
    def extract(cls, content: str) -> tuple[dict, str]:
        """Extract frontmatter and return (metadata, remaining_content)."""
        content = content.removeprefix("\ufeff")
        match = cls.FRONTMATTER_PATTERN.match(content)
        if match:
            yaml_str = match.group(1)
            metadata = load_yaml_mapping(yaml_str)
            validate_metadata(metadata)
            remaining = content[match.end():]
            return metadata, remaining
        first_line = content.partition("\n")[0]
        if first_line.strip() == "---":
            raise ValueError("Unclosed YAML frontmatter: expected a closing --- line")
        return {}, content


class ProtectCodePreprocessor(Preprocessor):
    """Hide literal code until authoring transformations have finished."""

    INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`)(.*?)(?<!`)\1(?!`)", re.DOTALL)

    def run(self, lines):
        self.fragments = {}
        self.prefix = "CODE" + uuid.uuid4().hex
        output = []
        index = 0
        while index < len(lines):
            line = lines[index]
            fence = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
            if fence:
                start = index
                delimiter = fence.group(1)
                closing = re.compile(r"^ {0,3}" + re.escape(delimiter[0])
                                     + "{" + str(len(delimiter)) + r",}\s*$")
                index += 1
                while index < len(lines):
                    end = closing.match(lines[index])
                    index += 1
                    if end:
                        break
                output.append(self.store("\n".join(lines[start:index])))
                continue
            if line.startswith(("    ", "\t")):
                output.append(self.store(line))
            else:
                output.append(line)
            index += 1
        text = "\n".join(output)
        return self.INLINE_CODE.sub(lambda m: self.store(m.group(0)), text).split("\n")

    def store(self, text):
        token = f"{self.prefix}X{len(self.fragments)}X"
        self.fragments[token] = text
        return token


class RestoreCodePreprocessor(Preprocessor):
    def __init__(self, md, protector):
        super().__init__(md)
        self.protector = protector

    def run(self, lines):
        text = "\n".join(lines)
        for token, fragment in reversed(list(self.protector.fragments.items())):
            text = text.replace(token, fragment)
        return text.split("\n")


class EmbedPreprocessor(Preprocessor):
    """Process custom embed directives and auto-embed URLs before markdown parsing."""

    # Pattern: ::name[content](optional_path){optional_attrs}
    EMBED_PATTERN = re.compile(
        r"::(\w+)\[([^\]]*)\](?:\(([^)]*)\))?(?:\{([^}]*)\})?"
    )
    # Pattern for fenced code block delimiters
    CODE_FENCE_PATTERN = re.compile(r"^(`{3,}|~{3,})")

    # Auto-embed URL detection patterns
    _BARE_URL_RE = re.compile(r'^https?://\S+$')
    _INLINE_URL_RE = re.compile(r'https?://[^\s<>)\]]+')
    _INLINE_CODE_RE = re.compile(r'`[^`]+`')
    _REF_LINK_RE = re.compile(r'^\s*\[.*\]:\s+')
    _TRAILING_PUNCT = '.!?,;'

    def run(self, lines: list[str]) -> list[str]:
        """Process embed directives and auto-embed URLs in the content."""
        new_lines = []
        in_code_block = False
        code_fence = None
        pending_embeds: list[str] = []

        for line in lines:
            stripped = line.strip()

            # Check for code fence start/end
            fence_match = self.CODE_FENCE_PATTERN.match(stripped)
            if fence_match:
                fence = fence_match.group(1)
                if not in_code_block:
                    in_code_block = True
                    code_fence = fence[0]
                elif stripped.startswith(code_fence):
                    in_code_block = False
                    code_fence = None

            # Inside code blocks: pass through unchanged
            if in_code_block:
                new_lines.append(line)
                continue

            # Blank line: flush pending inline embeds, then add the blank line
            if not stripped:
                if pending_embeds:
                    for embed in pending_embeds:
                        new_lines.append(embed)
                        new_lines.append('')
                    pending_embeds = []
                new_lines.append(line)
                continue

            # Check for standalone embeddable URL (entire line is just a URL)
            standalone = self._match_standalone_url(stripped)
            if standalone:
                embed_type, content = standalone
                processor = EMBED_PROCESSORS.get(embed_type)
                if processor:
                    new_lines.append(processor(content, {}))
                    continue

            # Scan original line for inline embeddable URLs (before ::embed processing)
            inline_embeds = self._find_inline_embed_urls(line)
            pending_embeds.extend(inline_embeds)

            # Process explicit ::embed syntax (existing behavior)
            new_lines.append(self._process_line(line))

        # End of content: flush any remaining pending embeds
        if pending_embeds:
            new_lines.append('')
            for embed in pending_embeds:
                new_lines.append(embed)
                new_lines.append('')

        return new_lines

    def _match_standalone_url(self, stripped: str) -> tuple[str, str] | None:
        """Check if a stripped line is a standalone embeddable URL.

        Returns (embed_type, content) or None.
        """
        # Reject angle-bracket URLs (embed suppression)
        if stripped.startswith('<'):
            return None
        # Must be a bare URL with no other text
        if not self._BARE_URL_RE.match(stripped):
            return None
        return match_embed_url(stripped)

    def _find_inline_embed_urls(self, line: str) -> list[str]:
        """Find inline embeddable URLs and return their embed HTML.

        Skips URLs that are suppressed with <>, inside markdown links,
        inside inline code, or inside ::embed syntax.
        """
        # Skip reference link definitions
        if self._REF_LINK_RE.match(line):
            return []

        # Replace inline code spans with spaces so URLs inside them aren't matched
        scan_line = self._INLINE_CODE_RE.sub(lambda m: ' ' * len(m.group(0)), line)

        results = []
        for m in self._INLINE_URL_RE.finditer(scan_line):
            url = m.group(0)
            start = m.start()

            # Skip URLs preceded by < ( or [ (suppressed / markdown link / embed syntax)
            if start > 0 and scan_line[start - 1] in '<([':
                continue

            # Strip trailing punctuation
            while url and url[-1] in self._TRAILING_PUNCT:
                url = url[:-1]

            # Try to match against embed patterns
            result = match_embed_url(url)
            if result:
                embed_type, content = result
                processor = EMBED_PROCESSORS.get(embed_type)
                if processor:
                    results.append(processor(content, {}))

        return results

    def _process_line(self, line: str) -> str:
        """Process a single line for embed directives."""
        def replace_embed(match: re.Match) -> str:
            embed_type = match.group(1)
            content = match.group(2)
            path = match.group(3) or ""
            attrs_str = match.group(4) or ""

            attrs = self._parse_attrs(attrs_str)

            # Handle image separately (different signature)
            if embed_type == "image":
                return IMAGE_PROCESSOR(content, path, attrs)

            # Handle other embeds
            processor = EMBED_PROCESSORS.get(embed_type)
            if processor:
                return processor(content, attrs)

            # Unknown embed type - return original
            return match.group(0)

        return self.EMBED_PATTERN.sub(replace_embed, line)

    def _parse_attrs(self, attrs_str: str) -> dict[str, str]:
        """Parse attribute string like 'key="value" key2="value2"'."""
        attrs = {}
        if not attrs_str:
            return attrs

        # Pattern for key="value" or key='value'
        pattern = re.compile(r'''(\w+)=("([^"]*)"|'([^']*)')''')
        for match in pattern.finditer(attrs_str):
            attrs[match.group(1)] = match.group(3) if match.group(3) is not None else match.group(4)

        return attrs


class CodeBlockPostprocessor(Postprocessor):
    """Apply Pygments syntax highlighting to code blocks."""

    CODE_BLOCK_PATTERN = re.compile(
        r'<pre><code class="language-([^"\s]+)">(.*?)</code></pre>',
        re.DOTALL
    )

    def run(self, text: str) -> str:
        """Apply syntax highlighting to code blocks."""
        def highlight_code(match: re.Match) -> str:
            language = match.group(1)
            code = match.group(2)

            # Unescape HTML entities
            code = unescape(code)

            try:
                lexer = get_lexer_by_name(language, stripall=False, stripnl=False, ensurenl=False)
            except Exception:
                try:
                    lexer = guess_lexer(code)
                except Exception:
                    return match.group(0)

            formatter = HtmlFormatter(cssclass="highlight", nowrap=False)
            highlighted = highlight(code, lexer, formatter)
            return f'<div class="code-block" data-language="{language}">{highlighted}</div>'

        return self.CODE_BLOCK_PATTERN.sub(highlight_code, text)


class AsidePreprocessor(Preprocessor):
    """Convert <aside>...</aside> blocks to :::callout directives."""

    def run(self, lines: list[str]) -> list[str]:
        return [
            ':::callout' if line.strip() in ('<aside>', '<aside >')
            else ':::' if line.strip() == '</aside>' else line
            for line in lines
        ]


class DirectivePreprocessor(Preprocessor):
    """Process :::callout and :::details[summary] directives."""

    DIRECTIVE_PATTERN = re.compile(r'^:::(\w+)(?:\[([^\]]*)\])?\s*$')
    CODE_FENCE_PATTERN = re.compile(r'^(`{3,}|~{3,})')

    def run(self, lines: list[str]) -> list[str]:
        output = []
        stack = []
        for number, line in enumerate(lines, 1):
            stripped = line.strip()
            opening = self.DIRECTIVE_PATTERN.match(stripped)
            if opening and opening.group(1) in {"callout", "details"}:
                stack.append((opening.group(1), opening.group(2), number, []))
                continue
            if stripped == ":::" and stack:
                dtype, arg, _, content = stack.pop()
                rendered = self._render_directive(dtype, arg, content)
                (stack[-1][3] if stack else output).extend(rendered)
                continue
            (stack[-1][3] if stack else output).append(line)
        if stack:
            dtype, _, number, _ = stack[-1]
            raise ValueError(f"Unclosed :::{dtype} directive near body line {number}")
        return output

    def _render_directive(
        self, dtype: str, arg: str | None, content: list[str]
    ) -> list[str]:
        if dtype == 'callout':
            return self._render_callout(content)
        elif dtype == 'details':
            return self._render_details(arg or '', content)
        # Unknown directive — pass content through
        return content

    def _render_callout(self, content: list[str]) -> list[str]:
        # Strip leading/trailing blank lines from content
        while content and not content[0].strip():
            content = content[1:]
        while content and not content[-1].strip():
            content = content[:-1]

        emoji = None
        if content:
            first_line = content[0].strip()
            emoji, remaining_text = self._extract_emoji(first_line)
            if emoji:
                if remaining_text:
                    content[0] = remaining_text
                else:
                    # Emoji was on its own line
                    content = content[1:]
                    # Strip blank lines after standalone emoji
                    while content and not content[0].strip():
                        content = content[1:]

        out = []
        if emoji:
            out.append(f'<div class="callout" data-icon="{emoji}" markdown="1">')
            out.append('<div class="callout-content" markdown="1">')
        else:
            out.append('<div class="callout" markdown="1">')
        out.append('')
        out.extend(content)
        out.append('')
        if emoji:
            out.append('</div>')
        out.append('</div>')
        return out

    def _render_details(self, summary: str, content: list[str]) -> list[str]:
        out = []
        out.append('<details markdown="1">')
        out.append(f'<summary>{escape(summary)}</summary>')
        out.append('')
        out.extend(content)
        out.append('')
        out.append('</details>')
        return out

    # Emoji detection: covers symbols (So), and characters that become emoji
    # with a variation selector (U+FE0F). Ranges cover Miscellaneous Symbols,
    # Dingbats, Emoticons, Transport/Map, and Supplemental Symbols.
    _EMOJI_RE = re.compile(
        r'^([\U0001F100-\U0001FAFF'   # Enclosed Alphanumerics Supplement..Symbols Extended-A
        r'\u2600-\u27BF'               # Misc Symbols, Dingbats
        r'\u2300-\u23FF'               # Misc Technical
        r'\u2100-\u214F'               # Letterlike Symbols (includes ℹ U+2139)
        r'\u2B50-\u2B55'               # Stars, circles
        r'\u203C\u2049'                # Exclamation marks
        r'\u00A9\u00AE'                # (C) (R)
        r'][\uFE0F\u200D]*)'
    )

    @classmethod
    def _extract_emoji(cls, text: str) -> tuple[str | None, str]:
        """Extract a leading emoji from text. Returns (emoji, remaining_text)."""
        if not text:
            return None, text

        m = cls._EMOJI_RE.match(text)
        if not m:
            return None, text

        emoji = m.group(1)
        rest = text[m.end():].lstrip()
        return emoji, rest


class NotionLinkPreprocessor(Preprocessor):
    """Strip Notion internal links (pointing to .md files) to plain text."""

    # Matches [text](something.md) or [text](something%20hash.md)
    NOTION_LINK_PATTERN = re.compile(
        r'\[([^\]]+)\]\([^)]*\.md\)'
    )

    def run(self, lines: list[str]) -> list[str]:
        return [self.NOTION_LINK_PATTERN.sub(r'\1', line) for line in lines]


class TaskListPostprocessor(Postprocessor):
    """Convert [x] and [ ] in list items to HTML checkboxes."""

    def run(self, text: str) -> str:
        checked = '<input type="checkbox" checked disabled> '
        unchecked = '<input type="checkbox" disabled> '
        # Handle both bare <li> and paragraph-wrapped content
        text = text.replace(
            '<li>[x] ',
            f'<li class="task-list-item">{checked}'
        )
        text = text.replace(
            '<li>[ ] ',
            f'<li class="task-list-item">{unchecked}'
        )
        text = text.replace(
            '<li><p>[x] ',
            f'<li class="task-list-item"><p>{checked}'
        )
        text = text.replace(
            '<li><p>[ ] ',
            f'<li class="task-list-item"><p>{unchecked}'
        )
        return text


class BareAutoLinkInlineProcessor(InlineProcessor):
    """Auto-link bare URLs that aren't already in a link, code span, or angle brackets."""

    def handleMatch(self, m, data):
        url = m.group(1)
        el = Element('a')
        el.set('href', url)
        el.text = url
        return el, m.start(0), m.end(0)


class CustomEmbedsExtension(Extension):
    """Markdown extension for custom embeds and enhanced features."""

    def __init__(self, *, notion_links=False):
        self.notion_links = notion_links
        super().__init__()

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        """Register preprocessors, inline patterns, and postprocessors."""
        protector = ProtectCodePreprocessor(md)
        md.preprocessors.register(protector, "protect_code", 40)
        md.preprocessors.register(RestoreCodePreprocessor(md, protector), "restore_code", 27)
        md.preprocessors.register(
            AsidePreprocessor(md), "aside_preprocessor", 35
        )
        md.preprocessors.register(
            DirectivePreprocessor(md), "directive_preprocessor", 33
        )
        md.preprocessors.register(
            EmbedPreprocessor(md), "embed_preprocessor", 30
        )
        if self.notion_links:
            md.preprocessors.register(
                NotionLinkPreprocessor(md), "notion_link_preprocessor", 28
            )
        # Auto-link bare URLs (priority 110, below built-in autolink at 120)
        md.inlinePatterns.register(
            BareAutoLinkInlineProcessor(
                r'(?<![<(\["\'])(https?://[^\s<>)\]]*[^\s<>)\].,!?;:])',
                md
            ),
            "bare_auto_link", 110
        )
        md.postprocessors.register(
            TaskListPostprocessor(md), "task_list", 25
        )
        md.postprocessors.register(
            CodeBlockPostprocessor(md), "code_highlight", 20
        )


def create_markdown_processor(*, notion_links=False) -> markdown.Markdown:
    """Create a configured Markdown processor."""
    return markdown.Markdown(
        extensions=[
            "fenced_code",
            "tables",
            "toc",
            "attr_list",
            "md_in_html",
            CustomEmbedsExtension(notion_links=notion_links),
        ],
        output_format="html5",
    )


def process_markdown(content: str, *, notion_links=False) -> tuple[dict, str]:
    """Process markdown content and return (metadata, html).

    Args:
        content: Raw markdown content with optional frontmatter

    Returns:
        Tuple of (metadata dict, rendered HTML string)
    """
    # Extract frontmatter
    metadata, md_content = FrontmatterExtractor.extract(content)

    # Process markdown
    md = create_markdown_processor(notion_links=notion_links)
    html = md.convert(md_content)

    return metadata, html
