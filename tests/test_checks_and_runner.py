"""The mirrored document, the injected block, the image - and how the runner answers."""

import io
from pathlib import Path

import pytest

from docsguard import (
    Layout,
    image_problems,
    injection_problems,
    mirror_problems,
    report,
    run,
    translation_problems,
)


@pytest.fixture()
def layout(tmp_path: Path) -> Layout:
    (tmp_path / "docs").mkdir()
    return Layout(root=tmp_path)


def test_a_mirrored_page_that_still_matches_is_silence(layout):
    (layout.root / "README.md").write_text("# Tasks\n\nThe prose.\n", encoding="utf-8")
    (layout.docs / "readme.md").write_text(
        '---\ntitle: "Tasks"\n---\n\nThe prose.\n', encoding="utf-8")
    assert mirror_problems(layout, [("readme.md", "README.md")]) == []


def test_a_mirrored_page_that_fell_behind_is_named(layout):
    (layout.root / "README.md").write_text("# Tasks\n\nThe new prose.\n", encoding="utf-8")
    (layout.docs / "readme.md").write_text(
        '---\ntitle: "Tasks"\n---\n\nThe old prose.\n', encoding="utf-8")
    problems = mirror_problems(layout, [("readme.md", "README.md")])
    assert len(problems) == 1 and "README.md" in problems[0]


def test_a_stale_injected_block_and_a_missing_marker_read_differently(layout):
    (layout.docs / "index.md").write_text(
        "## Features\n\n- **Steps** - the parts of a task.\n", encoding="utf-8")
    (layout.root / "README.md").write_text(
        "<!-- features:start -->\n- **Steps** - something else.\n<!-- features:end -->\n",
        encoding="utf-8")
    (layout.root / "OTHER.md").write_text("nothing here\n", encoding="utf-8")

    stale = injection_problems(layout, [("README.md", "features", "index.md", "Features")])
    assert len(stale) == 1 and "no longer matches" in stale[0]

    gone = injection_problems(layout, [("OTHER.md", "features", "index.md", "Features")])
    assert len(gone) == 1 and "markers" in gone[0]


def test_a_whole_page_injection_is_judged_against_the_page_body(layout):
    """Both shapes are in use: a document carries a section of a page, or the page itself."""
    (layout.docs / "tools.md").write_text(
        '---\ntitle: "Tools"\n---\n\n### Read\n\n- `read_it`\n', encoding="utf-8")
    (layout.root / "README.md").write_text(
        "<!-- tools:start -->\n### Read\n\n- `read_it`\n<!-- tools:end -->\n",
        encoding="utf-8")
    assert injection_problems(layout, [("README.md", "tools", "tools.md", None)]) == []
    (layout.docs / "tools.md").write_text(
        '---\ntitle: "Tools"\n---\n\n### Read\n\n- `read_it`\n- `read_more`\n',
        encoding="utf-8")
    problems = injection_problems(layout, [("README.md", "tools", "tools.md", None)])
    assert len(problems) == 1 and "tools.md" in problems[0]


def test_a_document_with_diagrams_is_compared_by_the_png_twins(layout):
    (layout.docs / "tools.md").write_text("![](docs/flow.svg)\n", encoding="utf-8")
    (layout.root / "README.md").write_text(
        "<!-- tools:start -->\n![](docs/flow.png)\n<!-- tools:end -->\n", encoding="utf-8")
    injections = [("README.md", "tools", "tools.md", None)]
    assert len(injection_problems(layout, injections)) == 1
    assert injection_problems(layout, injections, svg_to_png=True) == []


def test_an_image_the_repository_does_not_carry(layout):
    (layout.docs / "index.md").write_text(
        "![a](flow.png)\n![b](https://example.test/x.png)\n", encoding="utf-8")
    problems = image_problems(layout, ["index.md"])
    assert len(problems) == 1 and "flow.png" in problems[0]
    (layout.docs / "flow.png").write_bytes(b"\x89PNG")
    assert image_problems(layout, ["index.md"]) == []


def test_a_raw_link_is_resolved_to_a_repository_file(tmp_path):
    """A mirrored README reaches an image through the raw prefix, and the page carries the same
    link - judging it as "somebody else's host" would let a dead link through."""
    (tmp_path / "docs").mkdir()
    prefix = "https://raw.githubusercontent.com/owner/repo/main/"
    layout = Layout(root=tmp_path, raw_prefix=prefix)
    (layout.docs / "index.md").write_text(f"![a]({prefix}docs/flow.png)\n", encoding="utf-8")
    assert len(image_problems(layout, ["index.md"])) == 1
    (layout.docs / "flow.png").write_bytes(b"\x89PNG")
    assert image_problems(layout, ["index.md"]) == []


def test_a_page_that_shows_the_png_instead_of_the_svg(tmp_path):
    (tmp_path / "docs").mkdir()
    layout = Layout(root=tmp_path)
    (layout.docs / "index.md").write_text("![a](flow.png)\n", encoding="utf-8")
    (layout.docs / "flow.png").write_bytes(b"\x89PNG")
    assert image_problems(layout, ["index.md"]) == []
    (layout.docs / "flow.svg").write_text("<svg/>", encoding="utf-8")
    problems = image_problems(layout, ["index.md"], prefer_svg=True)
    assert len(problems) == 1 and "flow.svg" in problems[0]


def test_a_page_without_its_translation(layout):
    """A bilingual site loses a translation silently: the page just stops being offered."""
    (layout.docs / "index.md").write_text("x\n", encoding="utf-8")
    (layout.docs / "install.md").write_text("x\n", encoding="utf-8")
    (layout.docs / "index.ru.md").write_text("x\n", encoding="utf-8")
    problems = translation_problems(layout, sorted(layout.docs.glob("*.md")))
    assert len(problems) == 1 and "install.md" in problems[0]


def test_a_repository_document_is_judged_for_existence_only(layout):
    """The README shows the PNG on purpose - GitHub follows no theme."""
    (layout.root / "README.md").write_text("![a](docs/flow.png)\n", encoding="utf-8")
    (layout.docs / "flow.png").write_bytes(b"\x89PNG")
    (layout.docs / "flow.svg").write_text("<svg/>", encoding="utf-8")
    assert image_problems(layout, documents=["README.md"], prefer_svg=True) == []


def test_the_runner_prints_every_finding_and_answers_one():
    stream = io.StringIO()
    code = run([lambda: ["first"], lambda: ["second", "third"]], stream=stream)
    assert code == 1
    printed = stream.getvalue()
    assert "first" in printed and "second" in printed and "third" in printed


def test_a_check_that_raises_becomes_a_finding_and_the_rest_still_run():
    """A guard whose own bug reads as "no problems" is worse than no guard."""
    def broken():
        raise RuntimeError("the page moved")

    stream = io.StringIO()
    code = run([broken, lambda: ["still counted"]], stream=stream)
    assert code == 1
    printed = stream.getvalue()
    assert "the check itself failed" in printed and "still counted" in printed


def test_quiet_prints_the_summary_alone():
    stream = io.StringIO()
    assert run([lambda: ["a finding"]], stream=stream, quiet=True) == 1
    printed = stream.getvalue()
    assert "a finding" not in printed and "1 problem" in printed


def test_no_findings_answer_zero():
    stream = io.StringIO()
    assert report([], stream=stream) == 0
    assert "OK" in stream.getvalue()
