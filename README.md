# Static Site Generator

A Python-based static site generator that converts Markdown to HTML with support for rich media embeds, multi-section site structure, and automated deployment to Cloudflare Pages or GitHub Pages.

## Features

- **Markdown to HTML** conversion with YAML frontmatter
- **Rich media embeds**: YouTube, Vimeo, Twitter, Bluesky, Spotify, GitHub Gists, CodePen
- **Multi-section structure**: Blog, Projects, and static Pages
- **Responsive design** with CSS custom properties for theming
- **RSS feed generation**
- **Code syntax highlighting** via Pygments
- **Locale-aware timestamps** via Babel
- **Automated deployment** to Cloudflare Pages or GitHub Pages

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/dtupper_blog.git
cd dtupper_blog

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Usage

### Building the Site

```bash
# Build the site
python -m generator.build

# Or use the installed script
build-site
```

The generated site will be in the `output/` directory.

### Local Development

```bash
# Build and serve locally
python -m generator.build
python -m http.server -d output 8000
```

Then open http://localhost:8000 in your browser.

## Writing Content

Content is written in Markdown with YAML frontmatter. See [docs/CONTENT_GUIDE.md](docs/CONTENT_GUIDE.md) for detailed instructions.

### Basic Structure

```markdown
---
title: My Post Title
date: 2024-01-15
tags: [python, tutorial]
description: A brief description for SEO
---

Your content here...
```

### Content Sections

- `content/blog/` - Blog posts (date-based URLs)
- `content/projects/` - Project pages
- `content/pages/` - Static pages (about, contact, etc.)

### Rich Media Embeds

```markdown
::youtube[dQw4w9WgXcQ]
::twitter[https://twitter.com/user/status/123456789]
::spotify[track/4iV5W9uYEdYUVa79Axb7Rh]
::gist[username/gist_id]
```

## Deployment

### Cloudflare Pages

1. Add `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` to repository secrets
2. Push to `main` branch
3. GitHub Actions will build and deploy automatically

### GitHub Pages

1. Enable GitHub Pages in repository settings (source: GitHub Actions)
2. Push to `main` branch
3. GitHub Actions will build and deploy automatically

## Project Structure

```
dtupper_blog/
├── generator/          # Python source code
├── content/            # Markdown content
│   ├── blog/
│   ├── projects/
│   └── pages/
├── templates/          # Jinja2 templates
├── static/             # CSS, images
├── output/             # Generated site (gitignored)
└── docs/               # Documentation
```

## License

MIT License
