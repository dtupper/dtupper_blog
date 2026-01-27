"""Custom Markdown extensions for rich media embeds and enhanced syntax."""

import re
import yaml
import markdown
from markdown.preprocessors import Preprocessor
from markdown.postprocessors import Postprocessor
from markdown.extensions import Extension
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

from .embeds import EMBED_PROCESSORS, IMAGE_PROCESSOR


class FrontmatterExtractor:
    """Extract YAML frontmatter from markdown content."""

    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

    @classmethod
    def extract(cls, content: str) -> tuple[dict, str]:
        """Extract frontmatter and return (metadata, remaining_content)."""
        match = cls.FRONTMATTER_PATTERN.match(content)
        if match:
            yaml_str = match.group(1)
            try:
                metadata = yaml.safe_load(yaml_str) or {}
            except yaml.YAMLError:
                metadata = {}
            remaining = content[match.end():]
            return metadata, remaining
        return {}, content


class EmbedPreprocessor(Preprocessor):
    """Process custom embed directives before markdown parsing."""

    # Pattern: ::name[content](optional_path){optional_attrs}
    EMBED_PATTERN = re.compile(
        r"::(\w+)\[([^\]]*)\](?:\(([^)]*)\))?(?:\{([^}]*)\})?"
    )
    # Pattern for fenced code block delimiters
    CODE_FENCE_PATTERN = re.compile(r"^(`{3,}|~{3,})")

    def run(self, lines: list[str]) -> list[str]:
        """Process embed directives in the content."""
        new_lines = []
        in_code_block = False
        code_fence = None

        for line in lines:
            # Check for code fence start/end
            fence_match = self.CODE_FENCE_PATTERN.match(line.strip())
            if fence_match:
                fence = fence_match.group(1)
                if not in_code_block:
                    in_code_block = True
                    code_fence = fence[0]  # Store the fence character (` or ~)
                elif line.strip().startswith(code_fence):
                    in_code_block = False
                    code_fence = None

            # Only process embeds outside code blocks
            if in_code_block:
                new_lines.append(line)
            else:
                new_lines.append(self._process_line(line))

        return new_lines

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
        pattern = re.compile(r'(\w+)=["\']([^"\']*)["\']')
        for match in pattern.finditer(attrs_str):
            attrs[match.group(1)] = match.group(2)

        return attrs


class CodeBlockPostprocessor(Postprocessor):
    """Apply Pygments syntax highlighting to code blocks."""

    CODE_BLOCK_PATTERN = re.compile(
        r'<pre><code class="language-(\w+)">(.*?)</code></pre>',
        re.DOTALL
    )

    def run(self, text: str) -> str:
        """Apply syntax highlighting to code blocks."""
        def highlight_code(match: re.Match) -> str:
            language = match.group(1)
            code = match.group(2)

            # Unescape HTML entities
            code = (code
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&amp;", "&")
                .replace("&quot;", '"')
            )

            try:
                lexer = get_lexer_by_name(language, stripall=True)
            except Exception:
                try:
                    lexer = guess_lexer(code)
                except Exception:
                    return match.group(0)

            formatter = HtmlFormatter(cssclass="highlight", nowrap=False)
            highlighted = highlight(code, lexer, formatter)
            return f'<div class="code-block" data-language="{language}">{highlighted}</div>'

        return self.CODE_BLOCK_PATTERN.sub(highlight_code, text)


class CustomEmbedsExtension(Extension):
    """Markdown extension for custom embeds and enhanced features."""

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        """Register preprocessors and postprocessors."""
        md.preprocessors.register(
            EmbedPreprocessor(md), "embed_preprocessor", 30
        )
        md.postprocessors.register(
            CodeBlockPostprocessor(md), "code_highlight", 20
        )


def create_markdown_processor() -> markdown.Markdown:
    """Create a configured Markdown processor."""
    return markdown.Markdown(
        extensions=[
            "fenced_code",
            "tables",
            "toc",
            "attr_list",
            "meta",
            CustomEmbedsExtension(),
        ],
        output_format="html5",
    )


def process_markdown(content: str) -> tuple[dict, str]:
    """Process markdown content and return (metadata, html).

    Args:
        content: Raw markdown content with optional frontmatter

    Returns:
        Tuple of (metadata dict, rendered HTML string)
    """
    # Extract frontmatter
    metadata, md_content = FrontmatterExtractor.extract(content)

    # Process markdown
    md = create_markdown_processor()
    html = md.convert(md_content)

    return metadata, html
