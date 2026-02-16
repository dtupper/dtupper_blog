---
title: Markdown Features Test
description: Testing callouts, collapsible sections, task lists, and more
status: published
enable_diffs: true
---

# Markdown Features Test

## Callout Boxes

A callout without an emoji:

:::callout
This is a plain callout box with **bold text** and a [link](#task-lists).
:::

A callout with an emoji icon:

:::callout
⚠️ **Warning:** This build is centered around the AMD 5700X3D. This CPU uses the older AM4 socket type, which will receive no future CPU releases.
:::

Another callout with emoji on its own line:

:::callout
ℹ️
This is an informational callout. The emoji appears as a larger icon on the left side of the box.
:::

A multi-paragraph callout with an emoji icon:

:::callout
⚠️ **Warning**

This is the first paragraph of a multi-paragraph callout with an emoji icon.

This is the second paragraph. Both should stack _vertically_ beneath the icon, not side by side.
:::

A callout with an emoji from the Enclosed Alphanumerics block:

:::callout
🆕 This callout uses an emoji from a different Unicode range to verify broad emoji support.
:::

## Callouts from Notion `<aside>` syntax

<aside>

This is a callout using Notion's aside syntax. It should render the same as `:::callout`.

</aside>

<aside>

🔵 This aside has an emoji and should show it as an icon.

</aside>

## Collapsible Sections

:::details[Click to expand this section]
This content is hidden by default. It only appears when you click the summary.

- Item one
- Item two
- **Bold item**

```python
print("Code works inside collapsible sections too!")
```
:::

:::details[Another collapsible]
Short hidden content.
:::

## Task Lists

- [x] Initial release
- [x] Documentation
- [ ] Additional features
- [ ] Version 2.0

## Blockquotes

> AI is all the rage, commanding billions of dollars in sales.
> **Gaming was just under 9% of the total.**

## Heading Anchors

The `toc` extension generates IDs for all headings. You can link to any section:

- [Jump to Task Lists](#task-lists)
- [Jump to Blockquotes](#blockquotes)
- [Back to top](#markdown-features-test)
