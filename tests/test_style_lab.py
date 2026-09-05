"""Regression checks for the preview's source/output isolation and failure recovery."""

import shutil

from generator.style_lab import PREVIEW, StyleLab


def test_preview_preserves_project_output_and_keeps_reference_on_failed_rebuild(tmp_path):
    project = tmp_path / "project"
    shutil.copytree(PREVIEW, project)
    published = project / "output"
    published.mkdir()
    (published / "index.html").write_text("Published site: do not replace", encoding="utf-8")
    source = {
        path.relative_to(project): path.read_bytes()
        for path in project.rglob("*")
        if path.is_file()
    }
    root = tmp_path / "lab"
    root.mkdir()
    lab = StyleLab(root, project)
    assert {
        path.relative_to(project): path.read_bytes()
        for path in project.rglob("*")
        if path.is_file()
    } == source

    reference = (root / "reference/index.html").read_bytes()
    current = (root / "current/index.html").read_bytes()
    template = project / "templates/index.html"
    template.parent.mkdir()
    template.write_text("{% invalid_tag %}", encoding="utf-8")
    lab.rebuild()
    assert lab.error and "invalid_tag" in lab.error
    assert lab.revision == 1
    assert (root / "current/index.html").read_bytes() == current
    assert (root / "reference/index.html").read_bytes() == reference

    template.write_text(
        '{% extends "base.html" %}{% block content %}' "New design{% endblock %}", encoding="utf-8"
    )
    lab.rebuild()
    assert lab.error is None
    assert lab.revision == 2
    assert b"New design" in (root / "current/index.html").read_bytes()
    assert (root / "reference/index.html").read_bytes() == reference
    assert (published / "index.html").read_text() == "Published site: do not replace"


def test_deleted_experiment_keeps_last_good_preview_and_recovers(tmp_path):
    css = tmp_path / "experiment.css"
    css.write_text("body { color: purple; }", encoding="utf-8")
    root = tmp_path / "lab"
    root.mkdir()
    lab = StyleLab(root, PREVIEW, css)
    before = (root / "current/static/lab-extra.css").read_bytes()
    css.unlink()
    lab.rebuild()
    assert lab.error
    assert (root / "current/static/lab-extra.css").read_bytes() == before
    css.write_text("body { color: green; }", encoding="utf-8")
    lab.rebuild()
    assert lab.error is None
    assert b"green" in (root / "current/static/lab-extra.css").read_bytes()
    assert (root / "reference/static/lab-extra.css").read_bytes() == before
