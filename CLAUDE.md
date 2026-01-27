# Static Site Generator

A Python-based static site generator that converts Markdown to HTML with support for rich media embeds, multi-section site structure, and automated deployment.

## Quick Commands

```bash
# Install dependencies
pip install -e .

# Build the site
python -m generator.build

# View locally
python -m http.server -d output 8000
```

## Project Structure

- `generator/` - Python source code for the static site generator
- `content/` - Markdown content organized by section (blog, projects, pages)
- `templates/` - Jinja2 HTML templates
- `static/` - CSS, images, and other static assets
- `output/` - Generated site (gitignored)

## Content Sections

- `content/blog/` - Blog posts with date-based URLs
- `content/projects/` - Project showcase pages
- `content/pages/` - Static pages (about, contact, etc.)

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
section: blog  # blog, project, or page
status: published  # draft or published
description: Short description for meta tags
---
```

## Deployment

Configured for both Cloudflare Pages and GitHub Pages via GitHub Actions.
