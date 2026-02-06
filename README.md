# dtupper-site-generator

A Python-based static site generator that converts Markdown to HTML with support for rich media embeds, multi-section site structure, and automated deployment. Designed to be installed as a standalone package and used by a separate content repository.

## Features

- **Markdown to HTML** conversion with YAML frontmatter
- **Rich media embeds**: YouTube, Vimeo, Twitter, Bluesky, Spotify, GitHub Gists, CodePen
- **Multi-section structure**: Blog, Projects, and static Pages
- **Responsive design** with CSS custom properties and dark mode
- **RSS feed generation**
- **Code syntax highlighting** via Pygments
- **Locale-aware timestamps** via Babel
- **Template and static asset overrides** - customize only what you need
- **YAML-based configuration** via `site.yaml`

## Installation

Install directly from the git repository:

```bash
pip install git+https://github.com/yourusername/dtupper-site-generator.git
```

Or for local development:

```bash
git clone https://github.com/yourusername/dtupper-site-generator.git
cd dtupper-site-generator
pip install -e .
```

## Quick Start: Setting Up a Content Repo

Create a new directory for your site content:

```bash
mkdir my-website && cd my-website
```

Create a `site.yaml` configuration file:

```yaml
site:
  title: "My Website"
  description: "A personal blog and project showcase"
  author: "Your Name"
  url: "https://example.com"
  nav:
    - label: Home
      url: /
    - label: Blog
      url: /blog/
    - label: About
      url: /about/
```

Create your content directories and add some Markdown:

```bash
mkdir -p content/blog content/projects content/pages
```

Build the site:

```bash
build-site
```

The generated site will be in the `output/` directory. Preview locally with:

```bash
python -m http.server -d output 8000
```

## CLI Usage

```bash
# Build from current directory (looks for site.yaml here)
build-site

# Build from a specific project directory
build-site /path/to/my-website

# Use a specific config file
build-site -c /path/to/site.yaml

# Override the output directory
build-site -o /path/to/output

# Also works as a Python module
python -m generator.build
```

## Configuration Reference

All configuration lives in `site.yaml` in your content project root. Every field is optional and has sensible defaults.

```yaml
# Site metadata
site:
  title: "My Site"              # Site title (default: "My Site")
  description: ""               # Site description for meta tags
  author: ""                    # Author name
  url: "http://localhost:8000"  # Production URL
  language: "en"                # HTML lang attribute
  locale: "en-US"               # Date formatting locale
  nav:                          # Navigation links
    - label: Home
      url: /
    - label: Blog
      url: /blog/

# Directory overrides (relative to project root)
dirs:
  content: content              # Where Markdown files live
  templates: templates          # Template overrides (optional)
  static: static               # Static asset overrides (optional)
  output: output                # Build output directory

# Section configuration
sections:
  blog:
    url_pattern: "blog/{slug}"
    template: post.html
    date_in_url: true           # URLs like /blog/2024/01/my-post/
  projects:
    url_pattern: "projects/{slug}"
    template: project.html
    date_in_url: false
  pages:
    url_pattern: "{slug}"
    template: page.html
    date_in_url: false

# Build settings
build:
  date_format: long             # Babel format: short, medium, long, full
  posts_per_page: 10
  generate_rss: true
```

## Writing Content

Content is written in Markdown with YAML frontmatter:

```markdown
---
title: My Post Title
date: 2024-01-15
tags: [python, tutorial]
description: A brief description for SEO
status: published
---

Your content here...
```

### Content Sections

- `content/blog/` - Blog posts with date-based URLs
- `content/projects/` - Project showcase pages
- `content/pages/` - Static pages (about, contact, etc.)

### Rich Media Embeds

```markdown
::image[alt text](path/to/image.jpg){caption="Photo credit" width="600px"}
::youtube[VIDEO_ID]
::twitter[https://twitter.com/user/status/123456789]
::bluesky[https://bsky.app/profile/user/post/id]
::vimeo[VIDEO_ID]
::gist[username/gist_id]
::codepen[username/pen_id]
::spotify[track/4iV5W9uYEdYUVa79Axb7Rh]
::timestamp[2024-01-15T10:30:00]{locale="en-US" format="long"}
```

### Frontmatter Fields

| Field | Description | Default |
|-------|-------------|---------|
| `title` | Post title | Derived from filename |
| `date` | Publication date | Current date |
| `tags` | List of tags | `[]` |
| `description` | SEO description / excerpt | Empty |
| `status` | `published` or `draft` | `published` |
| `slug` | URL slug | Derived from filename |
| `links` | Project links (projects only) | `[]` |

## Template Overrides

The generator ships with default templates. To customize, create a `templates/` directory in your content project and add any templates you want to override:

```
my-website/
  templates/
    partials/
      header.html    # Override just the header
  ...
```

Templates use Jinja2. Override files are checked first, then the built-in defaults are used as fallback. You can override individual templates without replacing them all.

### Available Templates

| Template | Purpose |
|----------|---------|
| `base.html` | Base layout (head, header, footer) |
| `index.html` | Homepage and section listings |
| `post.html` | Individual blog post |
| `project.html` | Individual project page |
| `page.html` | Static page |
| `partials/header.html` | Site header and navigation |
| `partials/footer.html` | Site footer |

## Static Asset Overrides

Similarly, create a `static/` directory to add or override static assets:

```
my-website/
  static/
    css/
      style.css      # Replaces the default stylesheet
      custom.css     # Additional CSS
    images/
      logo.png       # Site-specific image
```

The generator's default assets are copied first, then your project's static files are copied on top (overwriting any conflicts).

## Deployment

### GitHub Pages

Example workflow (`.github/workflows/deploy.yml`):

```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install git+https://github.com/yourusername/dtupper-site-generator.git
      - run: build-site
      - uses: actions/upload-pages-artifact@v3
        with:
          path: output
      - uses: actions/deploy-pages@v4
```

### Cloudflare Pages

```yaml
name: Deploy to Cloudflare Pages
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install git+https://github.com/yourusername/dtupper-site-generator.git
      - run: build-site
      - uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: pages deploy output --project-name=my-site
```

## Generator Project Structure

```
dtupper-site-generator/
├── generator/                  # Python package
│   ├── __init__.py
│   ├── config.py               # SiteConfig dataclass + YAML loader
│   ├── build.py                # SiteBuilder + CLI entry point
│   ├── markdown_ext.py         # Custom Markdown extensions
│   ├── embeds.py               # Rich media embed processors
│   ├── default_templates/      # Bundled default templates
│   └── default_static/         # Bundled default static assets
├── pyproject.toml
└── README.md
```

## Content Repo Structure

```
my-website/
├── site.yaml                   # Site configuration (required)
├── content/                    # Markdown content (required)
│   ├── blog/
│   ├── projects/
│   └── pages/
├── templates/                  # Template overrides (optional)
├── static/                     # Static asset overrides (optional)
└── .github/workflows/          # Deployment workflows
```

## License

MIT License
