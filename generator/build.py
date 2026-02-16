"""Main build orchestration for the static site generator."""

import argparse
import dataclasses
import shutil
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from babel.dates import format_date
from feedgen.feed import FeedGenerator
from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from slugify import slugify

from .config import SiteConfig, load_config
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

    def load(self, section_config: dict) -> None:
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

        # Normalize last_updated to datetime
        if "last_updated" in self.metadata:
            lu = self.metadata["last_updated"]
            if isinstance(lu, str):
                self.metadata["last_updated"] = datetime.fromisoformat(lu)
            elif isinstance(lu, date) and not isinstance(lu, datetime):
                self.metadata["last_updated"] = datetime.combine(
                    lu, datetime.min.time()
                )

        # Generate URL
        url_pattern = section_config.get("url_pattern", "{slug}")

        if section_config.get("date_in_url") and self.metadata.get("date"):
            d = self.metadata["date"]
            if isinstance(d, str):
                d = datetime.fromisoformat(d)
            self.url = f"blog/{d.year}/{d.month:02d}/{self.slug}"
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

    def __init__(self, config: SiteConfig):
        self.config = config
        self.env = self._create_jinja_env()
        self._setup_template_globals()
        self.content: dict[str, list[ContentItem]] = {
            name: [] for name in config.sections
        }

    def _create_jinja_env(self) -> Environment:
        """Create Jinja2 environment with template override chain."""
        loaders = []
        # User templates take priority (if directory exists)
        if self.config.templates_dir.exists():
            loaders.append(FileSystemLoader(self.config.templates_dir))
        # Bundled default templates as fallback
        loaders.append(FileSystemLoader(self.config.default_templates_dir))

        return Environment(
            loader=ChoiceLoader(loaders),
            autoescape=True,
        )

    def _get_git_hash(self) -> str | None:
        """Get the short hash of the latest git commit, or None."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.config.project_dir,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            pass
        return None

    def _setup_template_globals(self) -> None:
        """Set up global variables and filters for templates."""
        self.env.globals["site"] = self.config.site
        self.env.globals["now"] = datetime.now()
        self.env.globals["build_time"] = datetime.now(timezone.utc)
        self.env.globals["build_hash"] = self._get_git_hash()

        # Recency cutoff dates for "recently updated/posted" callouts
        now = datetime.now()
        self.env.globals["recently_updated_cutoff"] = now - timedelta(days=self.config.recently_updated_days)
        self.env.globals["recently_posted_cutoff"] = now - timedelta(days=self.config.recently_posted_days)

        # Add date formatting filter
        def format_date_filter(d, format_type="long", locale="en_US"):
            if isinstance(d, str):
                d = datetime.fromisoformat(d)
            return format_date(d, format=format_type, locale=locale)

        self.env.filters["format_date"] = format_date_filter

    def clean_output(self) -> None:
        """Remove existing output directory."""
        if self.config.output_dir.exists():
            shutil.rmtree(self.config.output_dir)
        self.config.output_dir.mkdir(parents=True)

    def copy_static_assets(self) -> None:
        """Copy static assets to output directory with layered override."""
        dest = self.config.output_dir / "static"
        # Copy bundled defaults first
        if self.config.default_static_dir.exists():
            shutil.copytree(self.config.default_static_dir, dest)
        # Overlay user static on top (overwriting conflicts)
        if self.config.static_dir.exists():
            shutil.copytree(self.config.static_dir, dest, dirs_exist_ok=True)

    def load_content(self) -> None:
        """Load all content from content directories."""
        for section_name, section_config in self.config.sections.items():
            content_dir = section_config["content_dir"]
            if not content_dir.exists():
                content_dir.mkdir(parents=True)
                continue

            for md_file in content_dir.glob("*.md"):
                item = ContentItem(md_file, section_name)
                item.load(section_config)
                if item.is_published:
                    self.content[section_name].append(item)

        # Sort blog posts by date (newest first)
        if "blog" in self.content:
            self.content["blog"].sort(key=lambda x: x.date, reverse=True)

    def render_content(self) -> None:
        """Render all content items to HTML files."""
        for section_name, items in self.content.items():
            section_config = self.config.sections.get(section_name, {})
            template_name = section_config.get("template", "page.html")
            template = self.env.get_template(template_name)

            for item in items:
                # Create output directory structure
                output_path = self.config.output_dir / item.url / "index.html"
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
            posts=self.content.get("blog", [])[:5],
            projects=self.content.get("projects", [])[:3],
            title=self.config.site["title"],
        )

        output_path = self.config.output_dir / "index.html"
        output_path.write_text(html, encoding="utf-8")

    def render_section_indexes(self) -> None:
        """Render index pages for blog and projects sections."""
        site_title = self.config.site["title"]

        # Blog index
        if self.content.get("blog"):
            template = self.env.get_template("index.html")
            html = template.render(
                posts=self.content["blog"],
                projects=[],
                title=f"Blog - {site_title}",
                section="blog",
            )
            output_path = self.config.output_dir / "blog" / "index.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")

        # Projects index
        if self.content.get("projects"):
            template = self.env.get_template("index.html")
            html = template.render(
                posts=[],
                projects=self.content["projects"],
                title=f"Projects - {site_title}",
                section="projects",
            )
            output_path = self.config.output_dir / "projects" / "index.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")

    def generate_rss(self) -> None:
        """Generate RSS feed for blog posts."""
        if not self.config.generate_rss or not self.content.get("blog"):
            return

        site = self.config.site
        fg = FeedGenerator()
        fg.id(site["url"])
        fg.title(site["title"])
        fg.description(site["description"] or site["title"])
        fg.link(href=site["url"], rel="alternate")
        fg.language(site["language"])

        for post in self.content["blog"][:20]:
            fe = fg.add_entry()
            fe.id(f"{site['url']}/{post.url}")
            fe.title(post.metadata["title"])
            fe.link(href=f"{site['url']}/{post.url}")
            fe.description(post.metadata.get("description", ""))
            fe.published(post.date.strftime("%Y-%m-%dT%H:%M:%S+00:00"))

        rss_path = self.config.output_dir / "feed.xml"
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
        print(f"  Blog posts: {len(self.content.get('blog', []))}")
        print(f"  Projects: {len(self.content.get('projects', []))}")
        print(f"  Pages: {len(self.content.get('pages', []))}")
        print(f"  Total: {total} items")
        print(f"\nOutput: {self.config.output_dir}")


def main() -> None:
    """Main entry point for the build script."""
    parser = argparse.ArgumentParser(
        prog="build-site",
        description="Build a static site from Markdown content",
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Path to the project directory containing site.yaml (default: current directory)",
    )
    parser.add_argument(
        "-c", "--config",
        default=None,
        help="Path to site.yaml config file (default: PROJECT_DIR/site.yaml)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Override the output directory",
    )

    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    config_path = Path(args.config).resolve() if args.config else None

    config = load_config(project_dir, config_path)

    # CLI override for output dir
    if args.output:
        config = dataclasses.replace(config, output_dir=Path(args.output).resolve())

    builder = SiteBuilder(config)
    builder.build()


if __name__ == "__main__":
    main()
