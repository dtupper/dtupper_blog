"""Failures must not delete source, publish drafts, or replace a working site."""

import dataclasses
from pathlib import Path

import pytest
from jinja2 import TemplateSyntaxError

from generator.build import SiteBuilder, main
from generator.config import load_config

from conftest import build, write_page, write_post


def snapshot(directory):
    """Compare all published bytes, including static assets and the feed."""
    return {
        path.relative_to(directory): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize("output", [
    ".", "..", "content", "content/generated", "templates", "static", ".git/build",
])
def test_output_cannot_replace_source_directories(tmp_project, output):
    write_post(tmp_project, "keep.md", "Keep this source", "2024-01-15")
    original = snapshot(tmp_project)
    config = dataclasses.replace(load_config(tmp_project), output_dir=tmp_project / output)

    with pytest.raises(ValueError, match="Unsafe output directory"):
        SiteBuilder(config).build()

    assert snapshot(tmp_project) == original


def test_cli_output_override_cannot_delete_project(tmp_project, monkeypatch, capsys):
    original = snapshot(tmp_project)
    monkeypatch.setattr("sys.argv", ["build-site", str(tmp_project), "-o", str(tmp_project)])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 1
    assert "Unsafe output directory" in capsys.readouterr().err
    assert snapshot(tmp_project) == original


def test_missing_project_cannot_replace_existing_output(tmp_project, monkeypatch):
    write_page(tmp_project, "about.md", "Keep this site")
    build(tmp_project)
    previous = snapshot(tmp_project / "output")
    monkeypatch.setattr("sys.argv", [
        "build-site", str(tmp_project / "typo"), "-o", str(tmp_project / "output"),
    ])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 1
    assert snapshot(tmp_project / "output") == previous


def test_symlinked_output_cannot_replace_its_target(tmp_project):
    source = tmp_project / "content"
    original = snapshot(source)
    (tmp_project / "output").symlink_to(source, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink"):
        build(tmp_project)

    assert (tmp_project / "output").is_symlink()
    assert snapshot(source) == original


def test_source_symlink_cannot_hide_output_overlap(tmp_project):
    shared = tmp_project / "shared"
    shared.mkdir()
    (shared / "keep.css").write_text("original CSS")
    (tmp_project / "static").symlink_to(shared, target_is_directory=True)
    config = dataclasses.replace(load_config(tmp_project), output_dir=shared)

    with pytest.raises(ValueError, match="overlaps"):
        SiteBuilder(config).build()

    assert (shared / "keep.css").read_text() == "original CSS"


def test_external_config_cannot_be_deleted_by_output(tmp_project):
    output = tmp_project / "output"
    output.mkdir()
    config_path = output / "custom.yaml"
    config_path.write_text("site:\n  title: Keep this configuration\n")

    with pytest.raises(ValueError, match="overlaps"):
        SiteBuilder(load_config(tmp_project, config_path)).build()

    assert config_path.read_text() == "site:\n  title: Keep this configuration\n"


@pytest.mark.parametrize("route", ["../escaped/{slug}", "/escaped/{slug}"])
def test_route_cannot_write_outside_output(tmp_project, route):
    write_page(tmp_project, "page.md", "Original")
    build(tmp_project)
    previous = snapshot(tmp_project / "output")
    config = load_config(tmp_project)
    # The absolute case points to our own fixture, never a real system path.
    if route.startswith("/"):
        route = str(tmp_project / "escaped" / "{slug}")
    config.sections["pages"]["url_pattern"] = route

    with pytest.raises(ValueError, match="page.md.*must stay inside"):
        SiteBuilder(config).build()

    assert not (tmp_project / "escaped").exists()
    assert snapshot(tmp_project / "output") == previous


@pytest.mark.parametrize("frontmatter", [
    "status: draft\ntags: [broken\n---\n",
    "status: draft\n",  # Missing closing delimiter.
    "status: draft\nstatus: published\n---\n",
    "- status: draft\n---\n",  # Accidental list instead of a mapping.
    "status: [draft]\n---\n",
    "status: drfat\n---\n",
])
def test_invalid_draft_fails_without_changing_published_site(tmp_project, frontmatter):
    write_post(tmp_project, "public.md", "Public post", "2024-01-15")
    build(tmp_project)
    previous = snapshot(tmp_project / "output")
    draft = tmp_project / "content" / "blog" / "private.md"
    draft.write_text(f"---\n{frontmatter}\nPrivate draft body.\n")

    with pytest.raises(ValueError, match="private.md"):
        build(tmp_project)

    assert snapshot(tmp_project / "output") == previous


@pytest.mark.parametrize("prefix", ["", "\ufeff"], ids=["plain-utf8", "utf8-with-bom"])
def test_capitalized_draft_is_not_published(tmp_project, prefix):
    write_post(tmp_project, "private.md", "Private draft", "2024-01-15", status="Draft")
    draft = tmp_project / "content" / "blog" / "private.md"
    draft.write_text(prefix + draft.read_text())

    build(tmp_project)

    assert not (tmp_project / "output" / "blog" / "2024" / "01" / "private").exists()
    assert "Private draft" not in (tmp_project / "output" / "index.html").read_text()
    assert not (tmp_project / "output" / "feed.xml").exists()


def test_template_failure_preserves_previous_site(tmp_project):
    write_page(tmp_project, "about.md", "About")
    build(tmp_project)
    previous = snapshot(tmp_project / "output")
    templates = tmp_project / "templates"
    templates.mkdir()
    (templates / "index.html").write_text("{% invalid template %}")

    with pytest.raises(TemplateSyntaxError):
        build(tmp_project)

    assert snapshot(tmp_project / "output") == previous
    assert not list(tmp_project.glob(".output-build-*"))


def test_feed_write_failure_preserves_previous_site(tmp_project, monkeypatch):
    write_post(tmp_project, "post.md", "Original", "2024-01-15")
    build(tmp_project)
    previous = snapshot(tmp_project / "output")
    write_post(tmp_project, "post.md", "Changed", "2024-01-15")

    def fail_feed_write(*args, **kwargs):
        raise OSError("Disk full while writing feed")

    monkeypatch.setattr("generator.build.FeedGenerator.rss_file", fail_feed_write)
    with pytest.raises(OSError, match="Disk full"):
        build(tmp_project)

    assert snapshot(tmp_project / "output") == previous
    assert not list(tmp_project.glob(".output-build-*"))


def test_failed_install_restores_previous_output(tmp_project, monkeypatch):
    write_page(tmp_project, "about.md", "Original")
    build(tmp_project)
    previous = snapshot(tmp_project / "output")
    write_page(tmp_project, "about.md", "Changed")
    rename = Path.rename

    def fail_staged_install(path, target):
        if path.name == "site" and target == tmp_project / "output":
            raise OSError("Cannot install completed build")
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_staged_install)
    with pytest.raises(OSError, match="Cannot install"):
        build(tmp_project)

    assert snapshot(tmp_project / "output") == previous
    assert not list(tmp_project.glob(".output-build-*"))


def test_failed_restore_keeps_backup_for_recovery(tmp_project, monkeypatch):
    write_page(tmp_project, "about.md", "Original")
    build(tmp_project)
    previous = snapshot(tmp_project / "output")
    rename = Path.rename

    def fail_install_and_restore(path, target):
        if target == tmp_project / "output":
            raise OSError("Output directory unavailable")
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_install_and_restore)
    with pytest.warns(UserWarning, match="Previous output retained"):
        with pytest.raises(OSError, match="unavailable"):
            build(tmp_project)

    backups = list(tmp_project.glob(".output-build-*/previous"))
    assert len(backups) == 1
    assert snapshot(backups[0]) == previous


def test_reusing_builder_does_not_republish_a_newly_drafted_post(tmp_project):
    write_post(tmp_project, "post.md", "Withdraw this post", "2024-01-15")
    builder = SiteBuilder(load_config(tmp_project))
    builder.build()
    write_post(tmp_project, "post.md", "Withdraw this post", "2024-01-15", status="draft")

    builder.build()

    assert "Withdraw this post" not in (tmp_project / "output" / "index.html").read_text()
    assert not (tmp_project / "output" / "blog" / "2024" / "01" / "post").exists()
    assert not (tmp_project / "output" / "feed.xml").exists()
