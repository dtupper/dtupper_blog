# dtupper_blog

A Python static site generator that converts Markdown to HTML. Installed as a pip package; content lives in a separate repository.

## Features

- Markdown with YAML frontmatter, code highlighting, and rich media embeds (YouTube, Twitter, Spotify, etc.)
- Multi-section structure: Blog, Projects, and Pages
- Responsive design with dark mode
- RSS feeds, sitemaps, canonical URLs, and social-preview metadata
- Paginated section indexes and deployment under a URL prefix
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

Builds validate configuration and frontmatter before publishing. Invalid YAML,
duplicate keys, and invalid field types stop the build with a source filename.
Draft status is case-insensitive; accepted statuses are `published`, `draft`,
`active`, `completed`, and `archived`.

A full build writes to a temporary directory beside output, then replaces output
after rendering and RSS generation succeed. If replacement fails, it restores
the previous site. If restoration also fails, the error output identifies the
retained backup for manual recovery. The directory replacement uses two renames,
so it is not a zero-downtime deployment mechanism or protection against a machine
crash during that switch.

Output must not overlap content, templates, static assets, configuration, or
protected directories. Output symlinks and routes that escape output are rejected.
Keep only generated files in the output directory: a successful build replaces it
entirely. An explicitly supplied project or configuration path must exist.

The completed review work and test guidelines are tracked in
[`docs/IMPROVEMENT_PLAN.md`](docs/IMPROVEMENT_PLAN.md).

## Deployment

See the workflow examples in [`.github/workflows/`](.github/workflows/) for GitHub Pages and Cloudflare Pages.

Your content repo needs a `requirements.txt`:

```
dtupper-site-generator @ git+https://github.com/dtupper/dtupper_blog.git
```

Past there, it's up to you to define the content and how it is laid out.

## Configuration

All configuration fields are optional with defaults. Full reference: [`site.yaml.example`](site.yaml.example).

## Content correctness

Published blog posts and sections using dated URLs require an explicit `date`.
Date-only and timezone-free values mean UTC; timestamps with an offset keep that
offset for display, URLs, and feeds. Undated pages and projects do not acquire a
new publication date on each build. Duplicate or empty slugs and collisions with
generated routes stop the build.

Code examples are protected from embed, aside, and directive transformations.
Unclosed callouts/details report an error. Notion `.md` link stripping is disabled
by default; enable `build.notion_links: true` for imported content that needs it.
Otherwise, use published URLs for links between site pages.

Run Python checks with `pytest` and browser badge logic checks with
`node --test tests/test_recency_badges.cjs`.

## Visual style lab

Run the generator's real templates against a fixture site, with live rebuilds,
light/dark comparison, and desktop, tablet, and mobile viewports:

```bash
pip install -e ".[dev]"
style-lab
# Open http://127.0.0.1:8765
```

Choose **Reference / current** to compare edits against the build from server
startup. Edit `generator/default_static/css/style.css`, `custom.css`, or the
bundled templates and the preview refreshes. The reference stays fixed until you
restart the server. The lab writes only to temporary directories and leaves
production output alone.

```bash
style-lab --css /path/to/experiment.css  # Try an additional CSS override
style-lab --project /path/to/content-repo  # Preview your own content and overrides
```

For full-page screenshots and a portable before/after review gallery:

```bash
pip install -e ".[visual]"
python -m playwright install chromium
style-lab --capture .style-lab/before
# Make styling changes, then:
style-lab --capture .style-lab/after --baseline .style-lab/before
# Open .style-lab/after/index.html
```

See [the style lab guide](docs/STYLE_LAB.md) for fixture coverage, browser checks,
capture filters, and preview limitations.

## Using the default theme in a content repo

The editorial styling is the bundled default, including automatic light/dark
mode based on the reader's system preference. No theme setting is needed in
`site.yaml`.

For local development, activate your content repo's virtual environment, install
an editable checkout of this generator, and build from the content repo:

```bash
python -m pip install -e /path/to/dtupper_blog
build-site
style-lab --project .
```

An editable install picks up generator CSS and template edits immediately; rebuild
to update the generated site. For deployment, push the generator commit and pin
that commit in the content repo's dependency file:

```text
dtupper-site-generator @ git+https://github.com/dtupper/dtupper_blog.git@COMMIT_SHA
```

Existing overrides take precedence. Rename or remove stale copies of
`static/css/style.css` and bundled files under `templates/` to inherit the new
defaults, preserving intentional customizations. Review `static/css/custom.css`
for rules that mask the new styles. Keep future small CSS adjustments there;
variables such as `--font-serif` and `--reading-width` can be overridden without
copying the full stylesheet. Honor any custom `dirs.static` or `dirs.templates`
paths configured in `site.yaml`.

## Publishing and templates

Set `site.url` to the complete public base URL, for example
`https://example.com/journal` or `https://username.github.io/repository`.
Write site links without that deployment prefix: `/blog/`, `/about/`, and
`/static/photo.jpg`. Bundled templates and root-relative body links/images add
the prefix automatically. Custom templates should use `site_url('blog/')` for
local links and `absolute_url('blog/')` for absolute URLs. External URLs are kept.
CSS URLs, custom `srcset` values, and JavaScript URLs remain author-controlled.

`build.posts_per_page` controls section pagination. Homepage previews remain five
posts and three projects. `site.locale` and `build.date_format` control date
formatting. A zero recency window disables that badge.

Each section can set `index_template` and `index_url`. Setting `index_template:
null` disables its index. Otherwise empty sections get an empty-state page, and
later pages use `<index_url>/page/2/`. An omitted index URL is derived from the
static prefix of `url_pattern`, falling back to the section name. URL patterns
support `{slug}`, `{year}`, `{month:02d}`, and `{day:02d}`. With `date_in_url: true`,
year/month are inserted before `{slug}` unless the pattern already contains year
or month fields.

Default navigation follows configured section index URLs. Navigation omits links
to local pages that are not generated; links to copied static files and external
URLs are preserved. Feed links appear only when a feed exists. Custom index templates
receive `items`, `section`, `pagination`, and the usual page metadata; blog and
project indexes also retain `posts` and `projects` for compatibility.

Every build includes `sitemap.xml` and `404.html`. The sitemap includes published
content and indexes, uses authored dates for `lastmod`, and excludes drafts and
the 404 page. Configure your host to serve `404.html` for missing paths. Add
`site.image` for a default social-preview image, or frontmatter `image` for a
page-specific override. Canonical and social URLs use `site.url`.

The repository uses bundled templates directly. Keep only intentional overrides
in your content repository so bundled improvements remain visible. CI tests both
the source and a wheel-installed CLI running outside the checkout.
