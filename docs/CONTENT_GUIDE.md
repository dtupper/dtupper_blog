# Content Guide

This guide explains how to write and organize content for the static site generator.

## File Structure

Content is organized into three sections:

```
content/
├── blog/           # Blog posts
├── projects/       # Project pages
└── pages/          # Static pages (about, contact, etc.)
```

Each markdown file becomes a page on your site.

## Frontmatter

Every content file starts with YAML frontmatter between `---` markers:

```yaml
---
title: My Post Title
date: 2024-01-15
tags: [python, tutorial, web]
description: A brief description for SEO and previews
status: published
---

Your content here...
```

### Required Fields

- `title` - The page title (used in `<title>` and headings)

### Optional Fields

- `date` - Publication date (YYYY-MM-DD format)
- `tags` - List of tags for categorization
- `description` - Short description for meta tags and previews
- `status` - `published` (default) or `draft` (drafts are not built)
- `slug` - Custom URL slug (defaults to filename)

### Project-Specific Fields

For project pages, you can also use:

```yaml
---
title: My Project
status: Active
description: A brief project description
links:
  - label: GitHub
    url: https://github.com/user/repo
  - label: Live Demo
    url: https://example.com
---
```

## Writing Content

Content is written in standard Markdown with some extensions.

### Basic Markdown

```markdown
# Heading 1
## Heading 2
### Heading 3

Regular paragraph text with **bold** and *italic*.

- Bullet list
- Another item

1. Numbered list
2. Second item

> Blockquote

[Link text](https://example.com)

![Image alt](path/to/image.jpg)
```

### Code Blocks

Use fenced code blocks with language hints for syntax highlighting:

    ```python
    def hello():
        print("Hello, world!")
    ```

Supported languages include: python, javascript, typescript, html, css, bash, json, yaml, and many more.

### Tables

```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
```

## Rich Media Embeds

Use special directive syntax to embed rich media.

### YouTube Videos

```markdown
::youtube[VIDEO_ID]
```

Example: `::youtube[dQw4w9WgXcQ]`

The VIDEO_ID is the part after `v=` in YouTube URLs.

### Vimeo Videos

```markdown
::vimeo[VIDEO_ID]
```

### Twitter/X Posts

```markdown
::twitter[TWEET_URL]
```

Example: `::twitter[https://twitter.com/username/status/123456789]`

Optional theme attribute:
```markdown
::twitter[https://twitter.com/username/status/123456789]{theme="dark"}
```

### Bluesky Posts

```markdown
::bluesky[POST_URL]
```

### Spotify

Embed tracks, albums, or playlists:

```markdown
::spotify[track/4iV5W9uYEdYUVa79Axb7Rh]
::spotify[album/4LH4d3cOWNNsVw41Gqt2kv]
::spotify[playlist/37i9dQZF1DXcBWIGoYBM5M]
```

### GitHub Gists

```markdown
::gist[username/gist_id]
```

To show a specific file from a multi-file gist:
```markdown
::gist[username/gist_id]{file="example.py"}
```

### CodePen

```markdown
::codepen[username/pen_id]
```

Optional attributes:
```markdown
::codepen[username/pen_id]{height="400" theme="light" tab="css,result"}
```

### Enhanced Images

For images with captions:

```markdown
::image[Alt text](/path/to/image.jpg){caption="Image caption" width="600"}
```

### Timestamps

For locale-aware formatted dates:

```markdown
::timestamp[2024-01-15T10:30:00]{locale="en-US" format="long"}
```

Format options: `short`, `medium`, `long`, `full`

## URL Structure

### Blog Posts

Blog posts get date-based URLs:
- File: `content/blog/my-post.md`
- URL: `/blog/2024/01/my-post/`

### Projects

Projects use simple slugs:
- File: `content/projects/my-project.md`
- URL: `/projects/my-project/`

### Pages

Static pages go at the root:
- File: `content/pages/about.md`
- URL: `/about/`

## Images and Assets

Place images in `static/images/` and reference them:

```markdown
![My image](/static/images/photo.jpg)
```

Or use the enhanced image directive:

```markdown
::image[My image](/static/images/photo.jpg){caption="Photo credit: Me"}
```

## Building the Site

After writing content, build the site:

```bash
python -m generator.build
```

Preview locally:

```bash
python -m http.server -d output 8000
```

Then open http://localhost:8000 in your browser.
