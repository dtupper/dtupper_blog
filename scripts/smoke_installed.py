"""Run outside the checkout after installing a wheel, including its package data."""

import subprocess
import sys
import tempfile
from pathlib import Path

import generator


checkout = Path(__file__).resolve().parents[1]
assert not Path(generator.__file__).resolve().is_relative_to(checkout), "Imported checkout, not wheel"

with tempfile.TemporaryDirectory(prefix="site-wheel-smoke-") as directory:
    project = Path(directory)
    (project / "content/blog").mkdir(parents=True)
    (project / "site.yaml").write_text(
        "site:\n  title: Installed site\n  url: https://example.com/journal\n",
        encoding="utf-8",
    )
    (project / "content/blog/hello.md").write_text(
        "---\ntitle: Hello from the wheel\ndate: 2024-01-15\n---\n\nA published post.\n",
        encoding="utf-8",
    )
    cli = Path(sys.executable).with_name("build-site")
    subprocess.run([str(cli), str(project)], cwd=project, check=True)
    output = project / "output"
    for relative in (
        "index.html", "blog/index.html", "blog/2024/01/hello/index.html", "404.html",
        "feed.xml", "sitemap.xml", "static/css/style.css", "static/css/custom.css",
        "static/js/recency-badges.js",
    ):
        assert (output / relative).is_file(), f"Wheel build is missing {relative}"
    page = (output / "blog/2024/01/hello/index.html").read_text(encoding="utf-8")
    assert "Hello from the wheel" in page
    assert 'href="/journal/static/css/style.css"' in page
    assert 'href="https://example.com/journal/blog/2024/01/hello/"' in page

print("Installed wheel and CLI smoke test passed.")
