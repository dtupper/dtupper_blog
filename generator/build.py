"""Main build orchestration for the static site generator."""

import argparse
import dataclasses
import shutil
import subprocess
import tempfile
import warnings
from datetime import date, datetime, timezone
from pathlib import Path

from babel.dates import format_date
from feedgen.feed import FeedGenerator
from jinja2 import ChoiceLoader, Environment, FileSystemLoader, TemplateError
from slugify import slugify

from .config import SiteConfig, load_config
from .dates import parse_date
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

    def load(self, section_config: dict, *, notion_links=False) -> None:
        """Load and process the markdown file."""
        content = self.path.read_text(encoding="utf-8")
        try:
            self.metadata, self.html = process_markdown(content, notion_links=notion_links)
        except ValueError as exc:
            raise ValueError(f"{self.path}: {exc}") from exc

        # Generate slug from filename if not in metadata
        self.slug = self.metadata.get("slug", self.path.stem)
        self.slug = slugify(self.slug)

        if not self.slug:
            raise ValueError(f"{self.path}: slug must contain letters or numbers")
        self.metadata.setdefault("title", self.path.stem.replace("-", " ").title())
        self.metadata.setdefault("status", "published")
        self.metadata.setdefault("tags", [])
        for field in ("date", "last_updated"):
            if self.metadata.get(field) is not None:
                self.metadata[field] = parse_date(self.metadata[field])

        if not self.is_published:
            return
        if (self.section == "blog" or section_config.get("date_in_url")) and not self.date:
            raise ValueError(f"{self.path}: published posts with dates require an explicit date")

        pattern = section_config.get("url_pattern", "{slug}")
        if section_config.get("date_in_url"):
            # Preserve the established /blog/YYYY/MM/slug route while honoring prefixes.
            if "{year" not in pattern and "{month" not in pattern:
                pattern = pattern.replace("{slug}", "{year}/{month:02d}/{slug}")
        values = {"slug": self.slug}
        if self.date:
            values.update(year=self.date.year, month=self.date.month, day=self.date.day)
        try:
            self.url = pattern.format(**values).rstrip("/")
        except (KeyError, ValueError, IndexError) as exc:
            raise ValueError(f"{self.path}: invalid URL pattern {pattern!r}: {exc}") from exc

    @property
    def is_published(self) -> bool:
        """Check if content is published (not draft)."""
        return self.metadata.get("status", "published").strip().lower() != "draft"

    @property
    def date(self) -> datetime | None:
        """Return the normalized publication date, if one was supplied."""
        return self.metadata.get("date")

    @property
    def reading_time(self) -> int:
        """Estimate reading time in minutes."""
        # Average reading speed: ~200 words per minute
        word_count = len(self.html.split())
        return max(1, round(word_count / 200))


class SiteBuilder:
    """Main site builder class."""

    def __init__(self, config: SiteConfig):
        config.validate_output()
        self.config = config
        self._staging_dir: Path | None = None
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

        self.env.globals["recently_updated_days"] = self.config.recently_updated_days
        self.env.globals["recently_posted_days"] = self.config.recently_posted_days

        # Add date formatting filter
        def format_date_filter(d, format_type="long", locale="en_US"):
            if isinstance(d, str):
                d = datetime.fromisoformat(d)
            return format_date(d, format=format_type, locale=locale)

        self.env.filters["format_date"] = format_date_filter

    def clean_output(self) -> None:
        """Remove existing output directory."""
        self.config.validate_output()
        if self.config.output_dir.exists():
            shutil.rmtree(self.config.output_dir)
        self.config.output_dir.mkdir(parents=True)

    @property
    def output_dir(self) -> Path:
        """Destination for this build's writes; staging during a full build."""
        return self._staging_dir or self.config.output_dir

    def _output_path(self, relative: str) -> Path:
        root = self.output_dir.resolve()
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or "\\" in relative:
            raise ValueError(f"Output path must stay inside {root}: {relative!r}")
        destination = root / path
        if not destination.resolve().is_relative_to(root):
            raise ValueError(f"Output path must stay inside {root}: {relative!r}")
        return destination

    def copy_static_assets(self) -> None:
        """Copy static assets to output directory with layered override."""
        dest = self._output_path("static")
        # Copy bundled defaults first
        if self.config.default_static_dir.exists():
            shutil.copytree(self.config.default_static_dir, dest)
        # Overlay user static on top (overwriting conflicts)
        if self.config.static_dir.exists():
            shutil.copytree(self.config.static_dir, dest, dirs_exist_ok=True)

    def load_content(self) -> None:
        """Load all content from content directories."""
        self.content = {name: [] for name in self.config.sections}
        for section_name, section_config in self.config.sections.items():
            content_dir = section_config["content_dir"]
            if not content_dir.exists():
                continue

            for md_file in sorted(content_dir.glob("*.md")):
                item = ContentItem(md_file, section_name)
                item.load(section_config, notion_links=self.config.notion_links)
                if item.is_published:
                    self.content[section_name].append(item)

        for items in self.content.values():
            items.sort(key=lambda item: item.date or datetime.min.replace(tzinfo=timezone.utc),
                       reverse=True)

    def validate_routes(self) -> None:
        """Reserve generated files and reject collisions before any rendering."""
        routes = {"index.html": "homepage", "feed.xml": "RSS feed",
                  "sitemap.xml": "sitemap", "404.html": "404 page"}
        for section in ("blog", "projects"):
            routes[f"{section}/index.html"] = f"{section} index"
        for items in self.content.values():
            for item in items:
                relative = f"{item.url}/index.html"
                try:
                    path = self._output_path(relative).relative_to(self.output_dir.resolve())
                except ValueError as exc:
                    raise ValueError(f"{item.path}: {exc}") from exc
                key = path.as_posix().casefold()
                if path.parts[0].casefold() == "static":
                    raise ValueError(f"{item.path}: route conflicts with static assets")
                for existing, owner in routes.items():
                    if (key == existing or key.startswith(existing + "/")
                            or existing.startswith(key + "/")):
                        raise ValueError(f"Route collision: {item.path} and {owner} at {item.url}")
                routes[key] = str(item.path)

    def render_content(self) -> None:
        """Render all content items to HTML files."""
        for section_name, items in self.content.items():
            section_config = self.config.sections.get(section_name, {})
            template_name = section_config.get("template", "page.html")
            template = self.env.get_template(template_name)

            for item in items:
                # Create output directory structure
                try:
                    output_path = self._output_path(f"{item.url}/index.html")
                except ValueError as exc:
                    raise ValueError(f"{item.path}: {exc}") from exc
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

        output_path = self._output_path("index.html")
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
            output_path = self._output_path("blog/index.html")
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
            output_path = self._output_path("projects/index.html")
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
            fe = fg.add_entry(order="append")
            fe.id(f"{site['url']}/{post.url}")
            fe.title(post.metadata["title"])
            fe.link(href=f"{site['url']}/{post.url}")
            fe.description(post.metadata.get("description", ""))
            fe.published(post.date)

        rss_path = self._output_path("feed.xml")
        fg.rss_file(str(rss_path))

    def _publish(self, staged: Path, backup: Path) -> None:
        """Replace output, restoring the previous build if installation fails."""
        self.config.validate_output()
        output = self.config.output_dir
        if output.exists():
            output.rename(backup)
        try:
            staged.rename(output)
        except BaseException:
            if backup.exists():
                backup.rename(output)
            raise
        if backup.exists():
            try:
                shutil.rmtree(backup)
            except OSError as exc:
                warnings.warn(f"Site published, but old output remains at {backup}: {exc}")

    def build(self) -> None:
        """Execute the full build process."""
        print("Starting build...")

        self.config.validate_output()
        print("  Loading and validating content...")
        self.load_content()
        self.validate_routes()

        output = self.config.output_dir
        output.parent.mkdir(parents=True, exist_ok=True)
        workspace = Path(tempfile.mkdtemp(prefix=f".{output.name}-build-", dir=output.parent))
        staged = workspace / "site"
        backup = workspace / "previous"
        try:
            staged.mkdir()
            self._staging_dir = staged
            print("  Copying static assets...")
            self.copy_static_assets()
            print("  Rendering content...")
            self.render_content()
            print("  Rendering index pages...")
            self.render_index()
            self.render_section_indexes()
            print("  Generating RSS feed...")
            self.generate_rss()
            print("  Publishing completed build...")
            self._publish(staged, backup)
        finally:
            self._staging_dir = None
            # Never remove a backup if restoration or cleanup failed.
            if backup.exists():
                warnings.warn(f"Previous output retained at {backup}")
            else:
                try:
                    shutil.rmtree(workspace)
                except OSError as exc:
                    warnings.warn(f"Could not remove build workspace {workspace}: {exc}")

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

    try:
        config = load_config(project_dir, config_path)

        # Keep the final component unresolved so validation can reject symlinks.
        if args.output:
            config = dataclasses.replace(config, output_dir=Path(args.output).absolute())

        builder = SiteBuilder(config)
        builder.build()
    except (ValueError, OSError, TemplateError) as exc:
        parser.exit(1, f"build-site: {exc}\n")


if __name__ == "__main__":
    main()
