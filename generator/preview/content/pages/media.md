---
title: Images, captions & embedded media
---

## Wide image with a caption

::image[Layered hills beneath a pale sky](/static/landscape.svg){caption="An intentionally long caption to check alignment, muted text contrast, and wrapping on a phone-sized viewport."}

## Small image

::image[A small landscape](/static/landscape.svg){width="240" caption="An image with an explicit width."}

## Video

These are real embed directives. The style lab substitutes local placeholders inside their frames, preserving the generated wrapper and dimensions. Provider widgets require a separate live check.

::youtube[preview-video]

::vimeo[123456]

## Audio player

::spotify[spotify:track:preview]{height="152"}

## Interactive example

::codepen[preview/example]{height="300"}

## Timestamp

Published ::timestamp[2025-01-15T12:00:00Z]{format="long"}.
