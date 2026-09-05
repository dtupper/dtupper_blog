"""Local visual iteration harness. Production builds never import this module."""

import argparse
import dataclasses
import json
import re
import shutil
import tempfile
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from jinja2 import TemplateError

from .build import SiteBuilder
from .config import load_config

PREVIEW = Path(str(files("generator") / "preview"))
FIXED_TIME = datetime(2025, 1, 15, 12, tzinfo=timezone.utc)
VIEWPORTS = {"mobile": (390, 844), "tablet": (820, 1180), "desktop": (1440, 1000)}


def prepare_html(html: str, extra_css: bool) -> str:
    """Add preview-only clock and replace remote iframe content, not its layout."""
    html = re.sub(
        r'(<iframe\b[^>]*\bsrc=)["\']https?://[^"\']+["\']',
        r'\1"/__lab/media.html"',
        html,
        flags=re.I,
    )
    # Remote script widgets cannot be deterministic or work offline.
    html = re.sub(
        r'<script\b[^>]*\bsrc=["\']https?://[^>]*>\s*</script>',
        "",
        html,
        flags=re.I,
    )
    html = html.replace("<head>", '<head><script src="/__lab/clock.js"></script>', 1)
    if extra_css:
        html = html.replace(
            "</head>", '<link rel="stylesheet" href="/current/static/lab-extra.css">' "</head>", 1
        )
    return html


class StyleLab:
    def __init__(self, root: Path, project: Path, css: Path | None = None):
        self.root = root
        self.project = project.resolve()
        self.css = css.resolve() if css else None
        self.lock = threading.RLock()
        self.revision = 0
        self.error = None
        self.pages = []
        self.inputs = [self.project, PREVIEW]
        self.rebuild()
        if self.error:
            raise ValueError(self.error)
        shutil.copytree(root / "current", root / "reference")
        for path in (root / "reference").rglob("*.html"):
            path.write_text(
                path.read_text(encoding="utf-8").replace("/current/", "/reference/"),
                encoding="utf-8",
            )

    def rebuild(self):
        with self.lock:
            try:
                config = load_config(self.project)
                self.inputs = [
                    config.config_path,
                    config.templates_dir,
                    config.static_dir,
                    config.default_templates_dir,
                    config.default_static_dir,
                    PREVIEW / "ui",
                    *(section["content_dir"] for section in config.sections.values()),
                ]
                if self.css:
                    self.inputs.append(self.css)
                # Every build happens in a fresh temporary workspace. Only a successful,
                # fully prepared site replaces the last preview; never touch project output.
                with tempfile.TemporaryDirectory(prefix="build-", dir=self.root) as temporary:
                    config = dataclasses.replace(
                        config,
                        output_dir=Path(temporary) / "site",
                        site={**config.site, "url": "http://style-lab.invalid/current"},
                    )
                    builder = SiteBuilder(config)
                    builder.env.globals.update(
                        now=FIXED_TIME, build_time=FIXED_TIME, build_hash="preview"
                    )
                    builder.build()
                    for path in config.output_dir.rglob("*.html"):
                        path.write_text(
                            prepare_html(path.read_text(encoding="utf-8"), self.css is not None),
                            encoding="utf-8",
                        )
                    if self.css:
                        shutil.copyfile(self.css, config.output_dir / "static/lab-extra.css")
                    pages = [{"path": "/", "label": "Home"}]
                    pages.extend(
                        {
                            "path": "/" + page["url"].lstrip("/"),
                            "label": f'{page["section"].title()} · '
                            f'page {page["pagination"]["number"]}',
                        }
                        for page in builder.index_pages()
                    )
                    pages.extend(
                        {
                            "path": "/" + item.url + "/",
                            "label": f'{section.title()} · {item.metadata["title"]}',
                        }
                        for section, items in builder.content.items()
                        for item in items
                    )
                    pages.append({"path": "/404.html", "label": "404 · Page not found"})
                    destination = self.root / "current"
                    previous = Path(temporary) / "previous"
                    if destination.exists():
                        destination.rename(previous)
                    try:
                        config.output_dir.rename(destination)
                    except OSError:
                        if previous.exists():
                            previous.rename(destination)
                        raise
                shutil.copytree(PREVIEW / "ui", self.root / "__lab", dirs_exist_ok=True)
                self.pages = pages
                self.revision += 1
                self.error = None
            except (ValueError, OSError, TemplateError) as exc:
                self.error = str(exc)
                print(f"Preview build failed: {exc}", flush=True)

    def fingerprint(self):
        result = []
        for source in self.inputs:
            if source is None:
                continue
            paths = source.rglob("*") if source.is_dir() else [source]
            for path in paths:
                try:
                    if path.is_file():
                        stat = path.stat()
                        result.append((str(path), stat.st_mtime_ns, stat.st_size))
                except FileNotFoundError:
                    pass  # An editor may replace files while we scan.
        return sorted(result)

    def watch(self, stop: threading.Event):
        previous = self.fingerprint()
        while not stop.wait(0.5):
            current = self.fingerprint()
            if current != previous:
                previous = current
                self.rebuild()


class LabHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, lab: StyleLab, **kwargs):
        self.lab = lab
        super().__init__(*args, directory=str(lab.root), **kwargs)

    def log_message(self, format, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        with self.lab.lock:
            path = urlsplit(self.path).path
            if path == "/__lab/status":
                data = json.dumps(
                    {
                        "revision": self.lab.revision,
                        "error": self.lab.error,
                        "pages": self.lab.pages,
                        "viewports": VIEWPORTS,
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if path == "/":
                self.path = "/__lab/index.html"
            # Do not expose source files or follow copied static symlinks outside the lab.
            target = Path(self.translate_path(self.path)).resolve()
            if not target.is_relative_to(self.lab.root.resolve()):
                self.send_error(403)
                return
            super().do_GET()

    def list_directory(self, path):
        self.send_error(404)
        return None


def capture(
    lab: StyleLab,
    base_url: str,
    destination: Path,
    baseline: Path | None = None,
    selected: list[str] | None = None,
):
    """Capture real browser media queries, plus a portable visual review gallery."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ValueError(
            'Screenshots require pip install -e ".[visual]" and '
            "python -m playwright install chromium"
        ) from exc
    pages = lab.pages
    if selected:
        unknown = set(selected) - {page["path"] for page in pages}
        if unknown:
            raise ValueError(f"Unknown preview paths: {sorted(unknown)}")
        pages = [page for page in pages if page["path"] in selected]
    # Refuse to overwrite an earlier review or baseline.
    destination.mkdir(parents=True, exist_ok=False)
    rows = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for name, (width, height) in VIEWPORTS.items():
            for scheme in ("light", "dark"):
                context = browser.new_context(
                    viewport={"width": width, "height": height},
                    color_scheme=scheme,
                    device_scale_factor=1,
                    locale="en-US",
                    timezone_id="UTC",
                    reduced_motion="reduce",
                )
                # Keep captures independent of analytics, fonts, and provider availability.
                context.route(
                    "**/*",
                    lambda route: (
                        route.continue_()
                        if route.request.url.startswith(base_url + "/")
                        else route.abort()
                    ),
                )
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                for entry in pages:
                    errors.clear()
                    response = page.goto(base_url + "/current" + entry["path"])
                    if response.status != 200:
                        raise ValueError(f'Preview returned {response.status}: {entry["path"]}')
                    page.locator("img, iframe").evaluate_all(
                        "elements => elements.forEach(el => el.loading = 'eager')"
                    )
                    page.evaluate("document.fonts.ready")
                    page.wait_for_function("Array.from(document.images).every(i => i.complete)")
                    page.wait_for_load_state("networkidle")
                    filename = entry["path"].strip("/").replace("/", "--") or "home"
                    filename += f"--{name}--{scheme}.png"
                    page.screenshot(
                        path=str(destination / filename), full_page=True, animations="disabled"
                    )
                    overflow = page.evaluate("document.documentElement.scrollWidth > innerWidth")
                    broken = page.locator("img").evaluate_all(
                        "images => images.filter(i => !i.naturalWidth).map(i => i.src)"
                    )
                    row = {
                        **entry,
                        "viewport": name,
                        "scheme": scheme,
                        "image": filename,
                        "overflow": overflow,
                        "errors": list(errors),
                        "brokenImages": broken,
                    }
                    if baseline and (baseline / filename).is_file():
                        reference = destination / "reference"
                        reference.mkdir(exist_ok=True)
                        shutil.copyfile(baseline / filename, reference / filename)
                        row["reference"] = "reference/" + filename
                    rows.append(row)
                context.close()
        browser.close()
    (destination / "manifest.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    # Embed data so the gallery works via file:// as well as an HTTP server.
    report = (PREVIEW / "ui/report.html").read_text(encoding="utf-8")
    report = report.replace("/* MANIFEST */[]", json.dumps(rows).replace("<", "\\u003c"))
    (destination / "index.html").write_text(report, encoding="utf-8")
    print(f"Captured {len(rows)} screenshots. Review: {destination / 'index.html'}")
    problems = [row for row in rows if row["overflow"] or row["errors"] or row["brokenImages"]]
    if problems:
        print(f"{len(problems)} cases have layout or resource findings; see the gallery.")


def main():
    parser = argparse.ArgumentParser(
        description="Preview real blog templates across visual states."
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=PREVIEW,
        help="Content repository to preview instead of bundled fixtures",
    )
    parser.add_argument("--css", type=Path, help="Extra CSS loaded after the project's overrides")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--capture", type=Path, help="Save screenshots to a NEW directory, then exit"
    )
    parser.add_argument(
        "--baseline", type=Path, help="Earlier capture directory for visual comparison"
    )
    parser.add_argument("--page", action="append", help="Capture only this route; repeat as needed")
    args = parser.parse_args()
    if (args.baseline or args.page) and not args.capture:
        parser.error("--baseline and --page require --capture")
    if args.baseline and not (args.baseline / "manifest.json").is_file():
        parser.error("--baseline must be an existing style-lab capture directory")
    if args.css and not args.css.is_file():
        parser.error(f"CSS file does not exist: {args.css}")
    try:
        with tempfile.TemporaryDirectory(prefix="style-lab-") as directory:
            lab = StyleLab(Path(directory), args.project, args.css)
            with ThreadingHTTPServer(
                ("127.0.0.1", 0 if args.capture else args.port), partial(LabHandler, lab=lab)
            ) as server:
                url = f"http://127.0.0.1:{server.server_port}"
                if args.capture:
                    threading.Thread(target=server.serve_forever, daemon=True).start()
                    try:
                        capture(lab, url, args.capture.resolve(), args.baseline, args.page)
                    finally:
                        server.shutdown()
                else:
                    stop = threading.Event()
                    watcher = threading.Thread(target=lab.watch, args=(stop,), daemon=True)
                    watcher.start()
                    print(
                        f"\nStyle lab: {url}\nReference frozen at startup. Ctrl+C to stop.",
                        flush=True,
                    )
                    try:
                        server.serve_forever()
                    finally:
                        stop.set()
                        watcher.join()
    except KeyboardInterrupt:
        pass
    except (ValueError, OSError) as exc:
        parser.exit(1, f"style-lab: {exc}\n")


if __name__ == "__main__":
    main()
