---
title: Typography & component specimen
description: A compact inventory of the generator's prose styling.
---

## Heading level two

A paragraph with **bold**, *italic*, ***bold italic***, <del>deleted text</del>, `inline_code()`, and a [link with a hover and keyboard focus state](#lists). Some letters deserve attention: Ångström, naïve, café, 日本語, and an em dash — with punctuation.

### Heading level three

The quick brown fox jumps over the lazy dog. Good spacing should make headings feel connected to the paragraph that follows them.

#### Heading level four

A short paragraph after a smaller heading.

##### Heading level five

Another short paragraph.

###### Heading level six

The smallest heading still needs a recognizable hierarchy.

## Lists

- First unordered item
- Second item with a longer explanation that should wrap naturally without losing the hanging indent on small screens.
    - A nested item
    - Another nested item

### Ordered list

1. First ordered item
2. Second ordered item
    1. A nested ordered item

### Task list

- [x] Completed task
- [ ] An open task with a longer description that wraps on a phone

## Quotations and separators

> A quotation with **emphasis** and a [link](#lists).
>
> A second paragraph should retain the same comfortable spacing.

---

## Code

Inline code in context: `python -m generator.style_lab`.

```python
def describe(theme: str, width: int = 390) -> str:
    # Syntax colors need to work in both schemes.
    return f"Previewing {theme} at {width}px"

print(describe("dark"))
```

```text
An intentionally long line: /a/very/long/path/that/should/scroll/inside/the/code/block/without/making/the/entire/page/overflow/at/mobile/widths/example.txt
```

## Tables

| Element | What to inspect | State |
| --- | --- | --- |
| Article title | Wrapping and rhythm | Ready |
| Navigation | Spacing and focus | Review |
| Code block | Internal scrolling | Ready |

## Callouts

:::callout
A plain callout with **bold text** and a [link](#lists).
:::

:::callout
⚠️ A multi-paragraph callout

The icon belongs beside the content. This second paragraph should stack underneath the first, with a list below it.

- A useful detail
- One more detail
:::

## Collapsible content

:::details[Open this section to inspect its expanded state]
A paragraph inside a disclosure.

```css
:root { --max-width: 48rem; }
```
:::

<details open markdown="1">
<summary>Already expanded</summary>

This disclosure is open in screenshots, so both states are represented.

- A nested piece of content
- Another piece

</details>
