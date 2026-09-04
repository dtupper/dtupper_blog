"""Site configuration with YAML file support."""

import dataclasses
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Any

from .validation import load_yaml_mapping, require_type, validate_links


def _default_templates_dir() -> Path:
    """Return the path to the generator's bundled default templates."""
    return Path(str(importlib_resources.files("generator") / "default_templates"))


def _default_static_dir() -> Path:
    """Return the path to the generator's bundled default static assets."""
    return Path(str(importlib_resources.files("generator") / "default_static"))


# Hardcoded defaults for a fresh site
DEFAULT_SITE_CONFIG: dict[str, Any] = {
    "title": "My Site",
    "description": "",
    "author": "",
    "url": "http://localhost:8000",
    "language": "en",
    "locale": "en-US",
    "nav": [
        {"label": "Home", "url": "/"},
        {"label": "Blog", "url": "/blog/"},
        {"label": "Projects", "url": "/projects/"},
        {"label": "About", "url": "/about/"},
    ],
}

DEFAULT_SECTIONS: dict[str, dict[str, Any]] = {
    "blog": {
        "url_pattern": "blog/{slug}",
        "template": "post.html",
        "index_template": "index.html",
        "date_in_url": True,
    },
    "projects": {
        "url_pattern": "projects/{slug}",
        "template": "project.html",
        "index_template": "index.html",
        "date_in_url": False,
    },
    "pages": {
        "url_pattern": "{slug}",
        "template": "page.html",
        "index_template": None,
        "date_in_url": False,
    },
}

DEFAULT_BUILD_SETTINGS: dict[str, Any] = {
    "date_format": "long",
    "posts_per_page": 10,
    "generate_rss": True,
    "recently_updated_days": 7,
    "recently_posted_days": 7,
    "notion_links": False,
}


@dataclasses.dataclass
class SiteConfig:
    """Resolved site configuration."""

    # Resolved directory paths (all absolute)
    project_dir: Path
    content_dir: Path
    templates_dir: Path
    static_dir: Path
    output_dir: Path

    # Fallback dirs from package data
    default_templates_dir: Path
    default_static_dir: Path

    # Site metadata
    site: dict[str, Any]

    # Sections (with resolved content_dir paths)
    sections: dict[str, dict[str, Any]]

    # Build settings
    date_format: str = "long"
    posts_per_page: int = 10
    generate_rss: bool = True
    recently_updated_days: int = 7
    recently_posted_days: int = 7
    config_path: Path | None = None
    notion_links: bool = False

    def validate_output(self) -> None:
        """Refuse output locations that could replace source or repository files."""
        output = self.output_dir.resolve()
        project = self.project_dir.resolve()
        if self.output_dir.is_symlink():
            raise ValueError(f"Output directory cannot be a symlink: {self.output_dir}")
        if self.output_dir.exists() and not self.output_dir.is_dir():
            raise ValueError(f"Output path is not a directory: {self.output_dir}")
        for protected in (project, Path.home().resolve()):
            if protected.is_relative_to(output):
                raise ValueError(f"Unsafe output directory {output}: contains {protected}")
        inputs = [
            self.content_dir, self.templates_dir, self.static_dir,
            self.default_templates_dir, self.default_static_dir, Path(__file__).parent,
            project / ".git", project / ".agents", project / ".codex",
            *(section["content_dir"] for section in self.sections.values()),
        ]
        if self.config_path is not None:
            inputs.append(self.config_path)
        for source in inputs:
            source = source.resolve()
            if source.is_relative_to(output) or output.is_relative_to(source):
                raise ValueError(f"Unsafe output directory {output}: overlaps {source}")
        if (output / ".git").exists():
            raise ValueError(f"Output directory contains a Git repository: {output}")


def _validate_config(raw: dict) -> None:
    for field in ("site", "dirs", "sections", "build"):
        if field in raw:
            require_type(raw[field], dict, field)
    for key, value in raw.get("site", {}).items():
        if key in DEFAULT_SITE_CONFIG and key != "nav":
            require_type(value, str, f"site.{key}")
        elif key == "nav":
            validate_links(value, "site.nav")
    for key, value in raw.get("dirs", {}).items():
        require_type(value, str, f"dirs.{key}")
        if not value.strip():
            raise ValueError(f"dirs.{key} cannot be empty")
    for name, section in raw.get("sections", {}).items():
        if name in {".", ".."} or "/" in name or "\\" in name or not name:
            raise ValueError(f"Invalid section name: {name!r}")
        require_type(section, dict, f"sections.{name}")
        for key in ("url_pattern", "template", "index_template"):
            if key in section and not (key == "index_template" and section[key] is None):
                require_type(section[key], str, f"sections.{name}.{key}")
        if "date_in_url" in section:
            require_type(section["date_in_url"], bool, f"sections.{name}.date_in_url")
    build = raw.get("build", {})
    for key in ("generate_rss", "notion_links"):
        if key in build:
            require_type(build[key], bool, f"build.{key}")
    if "date_format" in build:
        require_type(build["date_format"], str, "build.date_format")
    for key in ("posts_per_page", "recently_updated_days", "recently_posted_days"):
        if key in build:
            require_type(build[key], int, f"build.{key}")
            minimum = 1 if key == "posts_per_page" else 0
            if build[key] < minimum:
                raise ValueError(f"build.{key} must be at least {minimum}")


def load_config(project_dir: Path, config_path: Path | None = None) -> SiteConfig:
    """Load configuration from a project directory.

    Looks for site.yaml in project_dir unless config_path is given explicitly.
    Merges YAML values on top of defaults.
    Resolves all paths relative to project_dir.
    """
    project_dir = project_dir.resolve()
    if not project_dir.is_dir():
        raise ValueError(f"Project directory does not exist: {project_dir}")

    explicit_config = config_path is not None
    if config_path is None:
        config_path = project_dir / "site.yaml"

    raw: dict[str, Any] = {}
    if explicit_config and not config_path.is_file():
        raise ValueError(f"Configuration file does not exist: {config_path}")
    if config_path.exists():
        try:
            raw = load_yaml_mapping(config_path.read_text(encoding="utf-8"))
            _validate_config(raw)
        except ValueError as exc:
            raise ValueError(f"{config_path}: {exc}") from exc

    # --- Site metadata ---
    site = {**DEFAULT_SITE_CONFIG, **raw.get("site", {})}

    # --- Directories (relative to project_dir) ---
    dirs = raw.get("dirs", {})
    content_dir = project_dir / dirs.get("content", "content")
    templates_dir = project_dir / dirs.get("templates", "templates")
    static_dir = project_dir / dirs.get("static", "static")
    output_dir = project_dir / dirs.get("output", "output")

    # --- Sections ---
    raw_sections = raw.get("sections", {})
    sections: dict[str, dict[str, Any]] = {}
    for name, defaults in DEFAULT_SECTIONS.items():
        user = raw_sections.get(name, {})
        merged = {**defaults, **user}
        merged["content_dir"] = content_dir / name
        sections[name] = merged
    # Allow user-defined additional sections
    for name, user in raw_sections.items():
        if name not in sections:
            user.setdefault("url_pattern", f"{name}/{{slug}}")
            user.setdefault("template", "page.html")
            user.setdefault("index_template", None)
            user.setdefault("date_in_url", False)
            user["content_dir"] = content_dir / name
            sections[name] = user

    # --- Build settings ---
    build = raw.get("build", {})

    return SiteConfig(
        project_dir=project_dir,
        content_dir=content_dir,
        templates_dir=templates_dir,
        static_dir=static_dir,
        output_dir=output_dir,
        default_templates_dir=_default_templates_dir(),
        default_static_dir=_default_static_dir(),
        site=site,
        sections=sections,
        date_format=build.get("date_format", DEFAULT_BUILD_SETTINGS["date_format"]),
        posts_per_page=build.get("posts_per_page", DEFAULT_BUILD_SETTINGS["posts_per_page"]),
        generate_rss=build.get("generate_rss", DEFAULT_BUILD_SETTINGS["generate_rss"]),
        recently_updated_days=build.get("recently_updated_days", DEFAULT_BUILD_SETTINGS["recently_updated_days"]),
        recently_posted_days=build.get("recently_posted_days", DEFAULT_BUILD_SETTINGS["recently_posted_days"]),
        config_path=config_path.resolve(),
        notion_links=build.get("notion_links", False),
    )
