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
    └── css/style.css, custom.css
```

**Also in repo root (for testing, will move to content repo later):**
- `site.yaml` - Site configuration
- `content/` - Sample Markdown content (blog/, projects/, pages/)
- `templates/` - User template overrides (takes priority over defaults)
- `static/` - User static overrides (copied on top of defaults)

## CSS Override Strategy

The generator ships a full default stylesheet (`generator/default_static/css/style.css`) and an empty `custom.css`. Both are linked in `base.html`, with `custom.css` loaded second.

Content repos can customize styling in three ways:
- **Extend**: Provide `static/css/custom.css` to add rules on top of the defaults (cascade wins)
- **Replace**: Provide `static/css/style.css` to fully replace the default stylesheet
- **Both**: Provide both files for complete control

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

### Auto-embed URLs (Discord-style)

URLs from supported services are automatically embedded. A URL on its own line replaces it with the embed. An inline URL leaves the text as-is and appends the embed after the paragraph.

To suppress auto-embedding, wrap the URL in angle brackets: `<https://youtube.com/watch?v=xxx>` — this renders as a plain link instead.

Supported URL patterns:
- `https://youtube.com/watch?v=ID`, `https://youtu.be/ID`, `https://youtube.com/shorts/ID`
- `https://vimeo.com/ID`
- `https://twitter.com/user/status/ID`, `https://x.com/user/status/ID`
- `https://bsky.app/profile/user/post/ID`
- `https://gist.github.com/user/id`
- `https://codepen.io/user/pen/id`
- `https://open.spotify.com/track/ID` (also album, playlist, episode, show)

### Explicit embed syntax

For custom attributes (width, height, caption, etc.), use the explicit `::embed` syntax:

```markdown
::image[alt text](path){caption="..." width="..."}
::youtube[VIDEO_ID]{width="800" height="450"}
::twitter[TWEET_URL]{theme="dark"}
::bluesky[POST_URL]
::vimeo[VIDEO_ID]
::gist[USER/GIST_ID]{file="filename.js"}
::codepen[USER/PEN_ID]{height="500" theme="dark" tab="css"}
::spotify[URI]{height="250"}
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
