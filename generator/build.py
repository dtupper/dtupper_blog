"""Main build orchestration for the static site generator."""

import shutil
from datetime import date, datetime
from pathlib import Path

from babel.dates import format_date
from feedgen.feed import FeedGenerator
from jinja2 import Environment, FileSystemLoader
from slugify import slugify

from .config import (
    BASE_DIR,
    CONTENT_DIR,
    OUTPUT_DIR,
    SECTIONS,
    SITE_CONFIG,
    STATIC_DIR,
    TEMPLATES_DIR,
    GENERATE_RSS,
)
from .markdown_ext import process_markdown


class ContentItem:
    """Represents a piece of content (post, project, page)."""

    def __init__(self, path: Path, section: str):
        self.path = path
        self.section = section
        self.metadata: dict = {}
        self.html: str = ""
        self.slug: str = ""
        self.url: str = ""

    def load(self) -> None:
        """Load and process the markdown file."""
        content = self.path.read_text(encoding="utf-8")
        self.metadata, self.html = process_markdown(content)

        # Generate slug from filename if not in metadata
        self.slug = self.metadata.get("slug", self.path.stem)
        self.slug = slugify(self.slug)

        # Set defaults
        if "title" not in self.metadata:
            self.metadata["title"] = self.path.stem.replace("-", " ").title()
        if "date" not in self.metadata:
            self.metadata["date"] = datetime.now()
        if "status" not in self.metadata:
            self.metadata["status"] = "published"
        if "tags" not in self.metadata:
            self.metadata["tags"] = []

        # Generate URL
        section_config = SECTIONS.get(self.section, {})
        url_pattern = section_config.get("url_pattern", "{slug}")

        if section_config.get("date_in_url") and self.metadata.get("date"):
            date = self.metadata["date"]
            if isinstance(date, str):
                date = datetime.fromisoformat(date)
            self.url = f"blog/{date.year}/{date.month:02d}/{self.slug}"
        else:
            self.url = url_pattern.format(slug=self.slug)

    @property
    def is_published(self) -> bool:
        """Check if content is published (not draft)."""
        return self.metadata.get("status", "published") != "draft"

    @property
    def date(self) -> datetime:
        """Get the content date as datetime."""
        d = self.metadata.get("date")
        if isinstance(d, datetime):
            return d
        if isinstance(d, date):
            return datetime.combine(d, datetime.min.time())
        if isinstance(d, str):
            return datetime.fromisoformat(d)
        return datetime.now()

    @property
    def reading_time(self) -> int:
        """Estimate reading time in minutes."""
        # Average reading speed: ~200 words per minute
        word_count = len(self.html.split())
        return max(1, round(word_count / 200))


class SiteBuilder:
    """Main site builder class."""

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True,
        )
        self._setup_template_globals()
        self.content: dict[str, list[ContentItem]] = {
            "blog": [],
            "projects": [],
            "pages": [],
        }

    def _setup_template_globals(self) -> None:
        """Set up global variables and filters for templates."""
        self.env.globals["site"] = SITE_CONFIG
        self.env.globals["now"] = datetime.now()

        # Add date formatting filter
        def format_date_filter(date, format_type="long", locale="en_US"):
            if isinstance(date, str):
                date = datetime.fromisoformat(date)
            return format_date(date, format=format_type, locale=locale)

        self.env.filters["format_date"] = format_date_filter

    def clean_output(self) -> None:
        """Remove existing output directory."""
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)
        OUTPUT_DIR.mkdir(parents=True)

    def copy_static_assets(self) -> None:
        """Copy static assets to output directory."""
        if STATIC_DIR.exists():
            shutil.copytree(STATIC_DIR, OUTPUT_DIR / "static")

    def load_content(self) -> None:
        """Load all content from content directories."""
        for section_name, section_config in SECTIONS.items():
            content_dir = section_config["content_dir"]
            if not content_dir.exists():
                content_dir.mkdir(parents=True)
                continue

            for md_file in content_dir.glob("*.md"):
                item = ContentItem(md_file, section_name)
                item.load()
                if item.is_published:
                    self.content[section_name].append(item)

        # Sort blog posts by date (newest first)
        self.content["blog"].sort(key=lambda x: x.date, reverse=True)

    def render_content(self) -> None:
        """Render all content items to HTML files."""
        for section_name, items in self.content.items():
            section_config = SECTIONS.get(section_name, {})
            template_name = section_config.get("template", "page.html")
            template = self.env.get_template(template_name)

            for item in items:
                # Create output directory structure
                output_path = OUTPUT_DIR / item.url / "index.html"
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Render template
                html = template.render(
                    content=item,
                    title=item.metadata.get("title"),
                    metadata=item.metadata,
                    body=item.html,
                )
                output_path.write_text(html, encoding="utf-8")

    def render_index(self) -> None:
        """Render the homepage."""
        template = self.env.get_template("index.html")

        html = template.render(
            posts=self.content["blog"][:5],
            projects=self.content["projects"][:3],
            title=SITE_CONFIG["title"],
        )

        output_path = OUTPUT_DIR / "index.html"
        output_path.write_text(html, encoding="utf-8")

    def render_section_indexes(self) -> None:
        """Render index pages for blog and projects sections."""
        # Blog index
        if self.content["blog"]:
            template = self.env.get_template("index.html")
            html = template.render(
                posts=self.content["blog"],
                projects=[],
                title=f"Blog - {SITE_CONFIG['title']}",
                section="blog",
            )
            output_path = OUTPUT_DIR / "blog" / "index.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")

        # Projects index
        if self.content["projects"]:
            template = self.env.get_template("index.html")
            html = template.render(
                posts=[],
                projects=self.content["projects"],
                title=f"Projects - {SITE_CONFIG['title']}",
                section="projects",
            )
            output_path = OUTPUT_DIR / "projects" / "index.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")

    def generate_rss(self) -> None:
        """Generate RSS feed for blog posts."""
        if not GENERATE_RSS or not self.content["blog"]:
            return

        fg = FeedGenerator()
        fg.id(SITE_CONFIG["url"])
        fg.title(SITE_CONFIG["title"])
        fg.description(SITE_CONFIG["description"])
        fg.link(href=SITE_CONFIG["url"], rel="alternate")
        fg.language(SITE_CONFIG["language"])

        for post in self.content["blog"][:20]:
            fe = fg.add_entry()
            fe.id(f"{SITE_CONFIG['url']}/{post.url}")
            fe.title(post.metadata["title"])
            fe.link(href=f"{SITE_CONFIG['url']}/{post.url}")
            fe.description(post.metadata.get("description", ""))
            fe.published(post.date.strftime("%Y-%m-%dT%H:%M:%S+00:00"))

        rss_path = OUTPUT_DIR / "feed.xml"
        fg.rss_file(str(rss_path))

    def build(self) -> None:
        """Execute the full build process."""
        print("Starting build...")

        print("  Cleaning output directory...")
        self.clean_output()

        print("  Copying static assets...")
        self.copy_static_assets()

        print("  Loading content...")
        self.load_content()

        print("  Rendering content...")
        self.render_content()

        print("  Rendering index pages...")
        self.render_index()
        self.render_section_indexes()

        print("  Generating RSS feed...")
        self.generate_rss()

        # Print summary
        total = sum(len(items) for items in self.content.values())
        print(f"\nBuild complete!")
        print(f"  Blog posts: {len(self.content['blog'])}")
        print(f"  Projects: {len(self.content['projects'])}")
        print(f"  Pages: {len(self.content['pages'])}")
        print(f"  Total: {total} items")
        print(f"\nOutput: {OUTPUT_DIR}")


def main() -> None:
    """Main entry point for the build script."""
    builder = SiteBuilder()
    builder.build()


if __name__ == "__main__":
    main()
