# dtupper-site-generator

A Python-based static site generator (v2.0.0) designed as a standalone installable package. Content lives in a separate repository that installs this generator as a dependency.

## Architecture

The generator is a pip-installable Python package. It ships with default templates and static assets as package data. Content repos provide a `site.yaml` config file, Markdown content, and optional template/static overrides.

**Key design pattern**: Jinja2 `ChoiceLoader` checks user templates first, then falls back to bundled defaults. Static assets use the same layered approach (defaults copied first, user overrides on top).

## Quick Commands

```bash
# Install in development mode
pip install -e .

# Build site from current directory (reads site.yaml)
build-site

# Build from a specific project directory
build-site /path/to/content-repo

# Build with config and output overrides
build-site -c /path/to/site.yaml -o /path/to/output

# View locally
python -m http.server -d output 8000
```

## Project Structure

```
generator/                      # Python package
├── __init__.py                 # Package version
├── config.py                   # SiteConfig dataclass + load_config() YAML loader
├── build.py                    # SiteBuilder class + argparse CLI entry point
├── markdown_ext.py             # Custom Markdown extensions (frontmatter, embeds, syntax highlighting)
├── embeds.py                   # Rich media embed processors (YouTube, Twitter, etc.)
├── default_templates/          # Bundled Jinja2 templates (package data)
│   ├── base.html, index.html, post.html, project.html, page.html
│   └── partials/header.html, partials/footer.html
└── default_static/             # Bundled static assets (package data)
    └── css/style.css
```

**Also in repo root (for testing, will move to content repo later):**
- `site.yaml` - Site configuration
- `content/` - Sample Markdown content (blog/, projects/, pages/)
- `templates/` - User template overrides (takes priority over defaults)
- `static/` - User static overrides (copied on top of defaults)

## Key Modules

### config.py
- `SiteConfig` dataclass: holds all resolved paths, site metadata, sections, and build settings
- `load_config(project_dir, config_path=None)`: reads `site.yaml`, merges with `DEFAULT_SITE_CONFIG`, `DEFAULT_SECTIONS`, `DEFAULT_BUILD_SETTINGS`, resolves paths
- Uses `importlib.resources.files("generator")` to locate bundled default_templates/ and default_static/

### build.py
- `ContentItem`: represents a single Markdown file; `load(section_config)` parses frontmatter, generates slug/URL
- `SiteBuilder(config: SiteConfig)`: main builder; `_create_jinja_env()` sets up `ChoiceLoader`; `build()` orchestrates clean → copy static → load content → render → RSS
- `main()`: argparse CLI entry point (`build-site` command)

### markdown_ext.py
- `FrontmatterExtractor`: extracts YAML frontmatter
- `EmbedPreprocessor`: processes `::embed[content](path){attrs}` syntax
- `CodeBlockPostprocessor`: Pygments syntax highlighting
- Zero dependency on config.py

### embeds.py
- Pure functions for each embed type (YouTube, Vimeo, Twitter, Bluesky, Gist, CodePen, Spotify, image, timestamp)
- `EMBED_PROCESSORS` dict maps type names to processor functions
- Zero dependency on config.py

## Configuration (site.yaml)

```yaml
site:
  title: "Site Title"
  description: "Site description"
  author: "Author Name"
  url: "https://example.com"
  language: "en"
  locale: "en-US"
  nav:
    - label: Home
      url: /
    - label: Blog
      url: /blog/

# dirs:                   # All relative to project root
#   content: content
#   templates: templates
#   static: static
#   output: output

# sections:               # Merged with defaults (blog, projects, pages)
#   blog:
#     date_in_url: true

# build:
#   date_format: long
#   posts_per_page: 10
#   generate_rss: true
```

## Custom Markdown Syntax

```markdown
::image[alt text](path){caption="..." width="..."}
::youtube[VIDEO_ID]
::twitter[TWEET_URL]
::bluesky[POST_URL]
::vimeo[VIDEO_ID]
::gist[USER/GIST_ID]
::codepen[USER/PEN_ID]
::spotify[URI]
::timestamp[2024-01-15T10:30:00]{locale="en-US" format="long"}
```

## Frontmatter Fields

```yaml
---
title: Post Title
date: 2024-01-15
tags: [tag1, tag2]
status: published  # or draft
description: Short description for meta tags
slug: custom-url-slug
---
```
