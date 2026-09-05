---
title: Making a little more room for the quiet web
date: 2025-01-15
description: A personal site can be a notebook, a workshop, and a place to think out loud. These are a few notes on building one slowly.
tags: [design, personal sites, writing]
---

There is something satisfying about a page that does one thing well. It gives a thought enough room to breathe, makes the next paragraph easy to find, and gets out of the way.

## A place for unfinished ideas

The best notebooks are full of useful imperfections. A sketch in the margin. A question with no answer yet. A [link to an earlier experiment](/projects/workbench/).

This is **bold text**, this is *emphasis*, and this is `a small piece of code`. All three should feel at home in a paragraph without disturbing its rhythm.

> The page is a space for attention. Good typography makes it easier to stay.

## What I keep coming back to

1. A comfortable measure for longer passages.
2. Enough contrast to read in the afternoon sun.
3. A navigation system that stays familiar on a small screen.

:::callout
💡 A small reminder

The article should still be pleasant to read when its title wraps onto three lines and its metadata fills two.
:::

## A small example

```python
from pathlib import Path

def collect_notes(folder: Path) -> list[Path]:
    return sorted(folder.glob("*.md"))
```

::image[Layered hills beneath a pale sky](/static/landscape.svg){caption="A local illustration, so previews work without a network connection."}

## Keep going

Writing on a personal site is a long conversation with your future self. Leave a few signposts. Explain the odd decisions. Make the next visit feel familiar.
