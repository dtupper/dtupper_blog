# dtupper_blog

A Python static site generator that converts Markdown to HTML. Installed as a pip package; content lives in a separate repository.

## Features

- Markdown with YAML frontmatter, code highlighting, and rich media embeds (YouTube, Twitter, Spotify, etc.)
- Multi-section structure: Blog, Projects, and Pages
- Responsive design with dark mode
- RSS feed generation
- Template and static asset override system
- YAML-based configuration

## words

This is _opinionated software_ -- it is written _for me_ and nobody else. It is not intended for usage by anyone except its author. 

I really can't recommend using this or building off it, but if you want to, go for it (within MIT terms)

As such, you might observe weird things, "unPythonic behavior", or mild Geneva Convention violations. 🤷

also, yes, I built this with claude. i want a blog, not a coding project.

## Installation

```bash
pip install git+https://github.com/dtupper/dtupper_blog.git
```

## Quick Start

Create a content directory with a `site.yaml`:

```yaml
site:
  title: "My Website"
  author: "Your Name"
  url: "https://example.com"
  nav:
    - label: Home
      url: /
    - label: Blog
      url: /blog/
```

Add Markdown files and build:

```bash
mkdir -p content/blog content/projects content/pages
build-site
python -m http.server -d output 8000
```

## Content Repo Structure

```
my-website/
├── site.yaml                   # Site configuration
├── requirements.txt            # Points to this generator
├── content/                    # Markdown content
│   ├── blog/
│   ├── projects/
│   └── pages/
├── templates/                  # Template overrides (optional)
├── static/                     # Static asset overrides (optional)
└── .github/workflows/          # Deployment workflow
```

## CLI

```bash
build-site                          # Build from current directory
build-site /path/to/content-repo    # Build from a specific directory
build-site -c site.yaml -o dist     # Override config/output paths
```

## Deployment

See the workflow examples in [`.github/workflows/`](.github/workflows/) for GitHub Pages and Cloudflare Pages.

Your content repo needs a `requirements.txt`:

```
dtupper-site-generator @ git+https://github.com/dtupper/dtupper_blog.git
```

Past there, it's up to you to define the content and how it is laid out.

## Configuration

See [`site.yaml`](site.yaml) for a working example. All fields are optional with sensible defaults. Full reference: [`site.yaml.example`](site.yaml.example).
