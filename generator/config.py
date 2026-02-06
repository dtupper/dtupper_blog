"""Site configuration with YAML file support."""

import dataclasses
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Any

import yaml


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
}


@dataclasses.dataclass
class SiteConfig:
    """Resolved, immutable site configuration."""

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


def load_config(project_dir: Path, config_path: Path | None = None) -> SiteConfig:
    """Load configuration from a project directory.

    Looks for site.yaml in project_dir unless config_path is given explicitly.
    Merges YAML values on top of defaults.
    Resolves all paths relative to project_dir.
    """
    project_dir = project_dir.resolve()

    if config_path is None:
        config_path = project_dir / "site.yaml"

    raw: dict[str, Any] = {}
    if config_path.exists():
        with open(config_path) as f:
            raw = yaml.safe_load(f) or {}

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
    )
