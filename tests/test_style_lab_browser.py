"""Optional browser checks: install .[visual] and Playwright Chromium to run."""

import shutil
import threading
from functools import partial
from http.server import ThreadingHTTPServer

import pytest

from generator.style_lab import PREVIEW, LabHandler, StyleLab

playwright = pytest.importorskip("playwright.sync_api")


@pytest.fixture
def live_lab(tmp_path):
    project = tmp_path / "project"
    shutil.copytree(PREVIEW, project)
    root = tmp_path / "lab"
    root.mkdir()
    lab = StyleLab(root, project)
    stop = threading.Event()
    with ThreadingHTTPServer(("127.0.0.1", 0), partial(LabHandler, lab=lab)) as server:
        serving = threading.Thread(target=server.serve_forever)
        watcher = threading.Thread(target=lab.watch, args=(stop,))
        serving.start()
        watcher.start()
        with playwright.sync_playwright() as driver:
            browser = driver.chromium.launch()
            page = browser.new_page(viewport={"width": 1500, "height": 1100})
            # Playwright otherwise forces light in every frame, overriding native
            # iframe inheritance. Its protocol uses the string "null" to reset it.
            page.emulate_media(color_scheme="null")
            try:
                yield page, f"http://127.0.0.1:{server.server_port}", project
            finally:
                browser.close()
                stop.set()
                watcher.join()
                server.shutdown()
                serving.join()


def test_native_schemes_viewports_and_navigation(live_lab):
    page, url, _ = live_lab
    page.goto(url + "/?viewport=mobile")
    light = page.frame_locator('iframe[title^="Current / light"]')
    dark = page.frame_locator('iframe[title^="Current / dark"]')
    playwright.expect(light.locator("body")).to_have_css("background-color", "rgb(255, 255, 255)")
    playwright.expect(dark.locator("body")).to_have_css("background-color", "rgb(26, 26, 46)")
    assert light.locator("body").evaluate("() => innerWidth") == 390
    assert dark.locator("body").evaluate("() => matchMedia('(prefers-color-scheme: dark)').matches")
    playwright.expect(light.locator(".badge-new")).to_have_count(1)
    playwright.expect(light.locator(".badge-updated")).to_have_count(2)
    light.get_by_role("link", name="Specimen", exact=True).click()
    playwright.expect(page.locator("#page")).to_have_value("/specimen/")
    playwright.expect(dark.locator("h1")).to_have_text("Typography & component specimen")
    light.locator("details:not([open]) summary").click()
    playwright.expect(light.locator("details[open]")).to_have_count(2)
    page.reload()
    playwright.expect(page.locator("#page")).to_have_value("/specimen/")
    playwright.expect(page.locator("#viewport")).to_have_value("mobile")


def test_live_css_reference_and_template_error_recovery(live_lab):
    page, url, project = live_lab
    page.goto(url + "/?mode=reference&viewport=mobile")
    current = page.frame_locator('iframe[title^="Current"]')
    reference = page.frame_locator('iframe[title^="Reference"]')
    playwright.expect(current.locator("body")).to_have_css("background-color", "rgb(255, 255, 255)")
    (project / "static/css").mkdir()
    (project / "static/css/custom.css").write_text(
        "body { background-color: rgb(210, 230, 220); }", encoding="utf-8"
    )
    playwright.expect(current.locator("body")).to_have_css(
        "background-color", "rgb(210, 230, 220)", timeout=15000
    )
    playwright.expect(reference.locator("body")).to_have_css(
        "background-color", "rgb(255, 255, 255)"
    )
    (project / "templates").mkdir()
    template = project / "templates/index.html"
    template.write_text("{% broken %}", encoding="utf-8")
    playwright.expect(page.locator("#error")).to_contain_text("broken", timeout=15000)
    playwright.expect(current.locator("h1")).to_have_text("Field notes")
    template.unlink()
    playwright.expect(page.locator("#error")).to_be_hidden(timeout=15000)
    playwright.expect(current.locator("h1")).to_have_text("Field notes")
