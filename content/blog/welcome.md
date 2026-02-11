---
title: Welcome to My Blog Software
date: 2024-01-15
tags: [welcome, introduction]
description: An introduction to my new blog and what to expect
---

# Welcome!

Hello and welcome to my blog software. It's a static site generator designed to work via GitHub actions to upload either to GitHub or Cloudflare Pages. 

This is _opinionated software_ -- it is written _for me_ and nobody else. It is not intended for usage by anyone except its author. 

As such, you might observe weird things, "unPythonic behavior", or mild Geneva Convention violations. 🤷

## AI Disclosure

Most of this site was constructed using AI coding agents. Specifically:

- Claude Code

The reason for this is that I wished to have a website I could customize completely, that is owned *completely* by me, and was maintainable in a language I am familiar with. 

At the same time, I do not have the time, expertise, or interest in writing the software from scratch. This software was created to serve a purpose in its product, not in its journey.

If you disagree with this reasoning, I understand completely. You may press Ctrl/Cmd-W to continue.

## Code Examples

Here's a quick Python example to demonstrate syntax highlighting:

```python
def greet(name: str) -> str:
    """Generate a greeting message."""
    return f"Hello, {name}! Welcome to the blog."

if __name__ == "__main__":
    print(greet("World"))
```

## Rich Media

This blog supports various embeds. Here's how you'd embed a YouTube video:

```markdown
::youtube[VIDEO_ID]
```

For example:

::youtube[cIw-wqIvkdw]

This also supports Discord-style embedding. Just put a URL in, and it will embed at the next newline: https://www.youtube.com/watch?v=cIw-wqIvkdw

This does NOT work with [custom text](https://www.youtube.com/watch?v=cIw-wqIvkdw) intentionally.

Finally, if you want to avoid this completely, you can disable embeds by wrapping the URL in angle brackets:

```markdown
<https://www.youtube.com/watch?v=cIw-wqIvkdw>
```

This will prevent URLs from embedding. <https://www.youtube.com/watch?v=cIw-wqIvkdw>

This software supports the following types of embeds:

| Pattern | Type | Extracted Content |
|---------|------|-------------------|
| youtube.com/watch?v=ID | youtube | video ID |
| youtube.com/shorts/ID | youtube | video ID |
| youtu.be/ID | youtube | video ID |
| vimeo.com/ID | vimeo | video ID |
| twitter.com/user/status/ID | twitter | full URL |
| x.com/user/status/ID | twitter | full URL |
| bsky.app/profile/user/post/ID | bluesky | full URL |
| gist.github.com/user/id | gist | user/id |
| codepen.io/user/pen/id | codepen | user/id |
| open.spotify.com/type/id | spotify | type/id |