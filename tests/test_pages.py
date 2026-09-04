"""Reading a page: what the checks get and what they must not get."""

from pathlib import Path

import pytest

from docsguard import (
    Layout,
    box_headlines,
    front_description,
    headings,
    injected,
    lede,
    mirror_source,
    page_body,
    section_body,
    site_pages,
)

PAGE = '''---
title: "Tasks"
description: "A demo project: tasks, steps and their reports."
---

<!-- Generated from README.md - do not edit by hand. -->

# Tasks

## Features

- **[Reports](reports.md)** - what happened last week.
- **Steps** - the parts of a task.
- plain line without a headline

## Install

    pip install tasks

### One machine

### Many machines
'''


@pytest.fixture()
def layout(tmp_path: Path) -> Layout:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text(PAGE, encoding="utf-8")
    return Layout(root=tmp_path)


def test_the_body_drops_the_frontmatter_and_the_generator_notes(layout):
    body = page_body(layout, "index.md")
    assert body.startswith("# Tasks")
    assert "description:" not in body and "do not edit" not in body


def test_a_diagram_link_becomes_the_png_twin_when_asked(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "p.md").write_text("![](docs/flow.svg)\n", encoding="utf-8")
    layout = Layout(root=tmp_path)
    assert "docs/flow.svg" in page_body(layout, "p.md")
    assert "docs/flow.png" in page_body(layout, "p.md", svg_to_png=True)


def test_a_section_body_stops_at_the_next_section(layout):
    body = section_body(layout, "index.md", "Install")
    assert "pip install tasks" in body
    assert "Features" not in body and "One machine" in body


def test_a_missing_section_answers_none(layout):
    assert section_body(layout, "index.md", "Nothing") is None


def test_a_linked_headline_answers_with_its_text(layout):
    assert box_headlines(layout, "index.md", "Features") == ["Reports", "Steps"]


def test_headings_of_a_level_come_in_page_order(layout):
    assert headings(layout, "index.md", level=3) == ["One machine", "Many machines"]


def test_the_front_description_is_the_search_snippet(layout):
    assert front_description(layout, "index.md").startswith("A demo project")


def test_the_lede_skips_badges_headings_and_the_switcher(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Tasks\n\n**English** · [Русский](README.ru.md)\n\n"
        "![badge](https://example.test/b.svg)\n\n"
        "> a quote\n\nThe first sentence a reader meets.\n\nMore prose.\n",
        encoding="utf-8")
    assert lede(readme) == "The first sentence a reader meets."


def test_an_injected_block_is_read_between_its_markers(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(
        "head\n<!-- features:start -->\n- **Steps**\n<!-- features:end -->\ntail\n",
        encoding="utf-8")
    layout = Layout(root=tmp_path)
    assert injected(layout, "README.md", "features") == "- **Steps**"
    # A document without the markers answers None - a different finding from an empty block.
    assert injected(layout, "README.md", "missing") is None


def test_the_mirror_source_loses_the_h1_and_the_switcher(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(
        "# Tasks\n\n**English** · [Русский](README.ru.md)\n\nThe prose stays.\n",
        encoding="utf-8")
    layout = Layout(root=tmp_path)
    assert mirror_source(layout, "README.md") == "The prose stays."


def test_site_pages_respect_what_the_config_excludes(tmp_path):
    (tmp_path / "docs").mkdir()
    for name in ("index.md", "index.ru.md", "draft.md"):
        (tmp_path / "docs" / name).write_text("x\n", encoding="utf-8")
    config = tmp_path / "site" / "blume.config.ts"
    config.parent.mkdir()
    config.write_text('export default { exclude: ["**/draft.md"] }\n', encoding="utf-8")
    layout = Layout(root=tmp_path, site_config=config)
    assert [p.name for p in site_pages(layout)] == ["index.md", "index.ru.md"]


def test_without_a_config_every_page_counts(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("x\n", encoding="utf-8")
    assert [p.name for p in site_pages(Layout(root=tmp_path))] == ["index.md"]
