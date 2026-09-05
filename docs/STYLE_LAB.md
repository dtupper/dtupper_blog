# Iterating on the blog's appearance

The style lab calls `SiteBuilder` with the same Markdown processors, template
loaders, and static override cascade as `build-site`. Its controls live outside
the generated pages, so the lab's own CSS cannot leak into the blog. No changes
to production templates or styles are necessary to run it.

## Start a session

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
style-lab
```

Open <http://127.0.0.1:8765>. Use `--port 9000` if that port is busy.
`python -m generator.style_lab` is equivalent to the installed command.

1. Choose a page and viewport. The canvas scales to fit, but the iframe keeps
   its actual CSS viewport: mobile 390×844, tablet 820×1180, desktop 1440×1000.
2. Compare light/dark side by side, reference/current in one scheme, or use a
   single larger preview. Color scheme uses native iframe inheritance, exercising
   the real `prefers-color-scheme` rules; no theme classes are injected.
   Use a current Chromium or Firefox browser for the interactive comparison;
   iframe theme inheritance varies in older browsers. The capture command
   always uses its installed Chromium.
3. Edit the bundled CSS or templates. The lab checks source files every half
   second, rebuilds, and refreshes the page while retaining its scroll position.
   Changes to fixture Markdown, config, assets, and `--css` also rebuild.
4. Use the same page, viewport, and scheme to compare against the reference from
   startup. Restart to accept the current design as the next reference.

The URL stores your page, viewport, and comparison controls, so it can be copied
or bookmarked. Links inside a preview synchronize the other panel. Scroll inside
the iframe to read long pages; use Tab to inspect keyboard focus, and click
disclosures to inspect their expanded state. A full-page screenshot includes the
whole document. **Open page** uses the standalone browser's viewport and system
color scheme, independently of the lab controls.

If a template or content edit breaks the build, the lab displays the error and
keeps the last successful preview. Fix the source to recover automatically.
Python generator implementation changes require a server restart. The server
binds only to `127.0.0.1`, and its generated files are removed when it exits.

## Try styling variants and real content

```bash
style-lab --css /path/to/experiment.css
style-lab --project /path/to/content-repo
style-lab --project /path/to/content-repo --css /path/to/experiment.css
```

The extra stylesheet is copied and loaded last, after `custom.css`. Edit it live.
When a variant is ready, move the desired rules into bundled CSS or your content
repo's `static/css/custom.css`. The lab never writes experiments back to sources.
Relative asset URLs in the extra stylesheet resolve from `/current/static/`;
put supporting assets in the project's static directory.

The supplied project's configuration and overrides are respected, with its
public URL remapped to a local preview prefix. Its configured output directory
is never used. Existing authored CSS/JavaScript containing hardcoded absolute
paths may need an adjustment for that prefix, just as for a prefixed deployment.
Adding or deleting a page updates the selector; a newly added route naturally
has no counterpart in the startup reference.

## Coverage

Fixtures are in `generator/preview/`, shipped as package data. They exercise:

| Surface | Cases |
| --- | --- |
| Homepage and indexes | Blog previews, project cards, first/last pagination pages, empty custom section |
| Posts | New, recently updated, old, long title, many tags, missing optional metadata, short and long body |
| Projects | Active, completed, archived, links, missing description |
| Pages | Ordinary prose, component specimen, media, 404 |
| Typography | H2–H6 plus template H1, emphasis, links, lists, nested lists, task lists, blockquotes, separators |
| Components | Highlighted code, long scrolling code, table, plain/icon callouts, closed/open disclosures |
| Media | Local wide/small images, captions, generated video/audio/CodePen wrappers, timestamp |

The preview clock and build metadata are fixed at January 15, 2025. Fixtures
therefore keep their New/Recently Updated/old badge states. This also applies
with `--project`; use the fixtures for representative badge coverage.

Remote iframe sources are replaced with a local placeholder while retaining
their generated dimensions and wrappers. Remote scripts are removed. This tests
the blog's surrounding media layout, **not provider widget internals**. Check
those separately in a normal build. The default fixtures need no network.
Screenshot captures also block remote requests; external images/fonts in a
custom content repository will not be available in captures.

## Save and compare screenshots

```bash
pip install -e ".[visual]"
python -m playwright install chromium
style-lab --capture .style-lab/before
# Edit styles or supply --css, then use a NEW destination:
style-lab --capture .style-lab/after --baseline .style-lab/before
```

Captures cover every catalog page at all three viewports in both native browser
color schemes. A new directory is required to avoid overwriting a reference.
Each contains PNGs, `manifest.json`, and a standalone `index.html` gallery. The
gallery puts matching baseline and current images beside each other; baseline
images are copied into the report so it can be moved or shared as a directory.
Missing baseline matches display only the current image. This is a visual review
tool, not an automatic pixel-difference pass/fail gate.

For a quick focused pass, repeat `--page` using the paths in the preview URLs:

```bash
style-lab --capture .style-lab/prose --page /specimen/ --page /blog/2025/01/quiet-web/
```

Chromium uses 1× device scale, `en-US`, UTC, reduced motion, and the preview's
fixed clock. Animations are disabled for capture, local images/fonts are awaited,
and lazy images/frames are made eager. Compare captures on the same OS and browser
version for consistent font rasterization. Pin your environment if you need
strict image baselines.

The manifest and gallery flag document overflow, broken images, and JavaScript
errors. These are findings for review, not assertions that the design is correct;
contrast, wrapping, hierarchy, hover, and focus still deserve visual inspection.

## Harness checks

```bash
pytest tests/test_style_lab.py
pip install -e ".[dev,visual]"
python -m playwright install chromium
pytest tests/test_style_lab_browser.py
```

The browser tests skip when Playwright is not installed. With the visual extra,
install its Chromium binary before running them. They verify real light/dark
media queries, mobile viewport sizing, navigation, reference isolation, and
rebuild failure/recovery. The existing Python and badge tests continue to check
generator behavior independently of visual review.

The **Visual previews** GitHub Actions workflow runs these checks and uploads the
full screenshot gallery for pull requests that change the generator or harness.
It can also be started manually. Download the `style-lab-gallery` artifact and
open its `index.html` to review it. CI captures are references for that CI browser
and operating system; they may rasterize fonts differently from local captures.
