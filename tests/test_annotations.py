"""The annotations check: both directions of the gap, and the deliberate silence."""

from pathlib import Path

from docsguard import (
    Layout,
    PitchItem,
    pitch_problems,
    pyproject_description,
    site_description,
)

ITEMS = (
    PitchItem("Reports", "Отчёты", "report", "отчёт"),
    PitchItem("Steps", "Шаги", None, None),  # deliberately out of the annotations
)


def test_an_annotation_that_names_everything_is_silence():
    problems = pitch_problems(
        ITEMS,
        {"en": ["Reports", "Steps"]},
        {"en": {"pyproject.toml": "Tasks, steps and a weekly report"}},
    )
    assert problems == []


def test_an_annotation_missing_the_word_is_named_with_the_place():
    problems = pitch_problems(
        ITEMS,
        {"en": ["Reports", "Steps"]},
        {"en": {"pyproject.toml": "Tasks and steps"}},
    )
    assert len(problems) == 1
    assert "pyproject.toml" in problems[0] and "Reports" in problems[0]


def test_a_headline_the_table_does_not_know():
    problems = pitch_problems(
        ITEMS,
        {"en": ["Reports", "Steps", "Calendar"]},
        {"en": {"pyproject.toml": "Tasks, steps and a weekly report"}},
        pages={"en": "docs/index.md"},
    )
    assert len(problems) == 1
    assert "Calendar" in problems[0] and problems[0].startswith("docs/index.md")


def test_a_table_row_the_page_no_longer_lists():
    """The opposite direction: without it the guard would demand a word for a dead feature."""
    problems = pitch_problems(
        ITEMS,
        {"en": ["Steps"]},
        {"en": {"pyproject.toml": "Tasks, steps and a weekly report"}},
    )
    assert len(problems) == 1
    assert "Reports" in problems[0] and "the page does not" in problems[0]


def test_each_locale_is_judged_by_its_own_word():
    problems = pitch_problems(
        ITEMS,
        {"en": ["Reports", "Steps"], "ru": ["Отчёты", "Шаги"]},
        {"en": {"pyproject.toml": "report"}, "ru": {"docs/index.ru.md": "шаги и только"}},
    )
    assert len(problems) == 1
    assert "docs/index.ru.md" in problems[0]


def test_the_site_description_joins_the_parts_it_is_written_in(tmp_path: Path):
    config = tmp_path / "blume.config.ts"
    config.write_text(
        'export default defineConfig({\n  title: "Tasks",\n'
        '  description:\n    "Tasks, steps " +\n    "and a weekly report.",\n});\n',
        encoding="utf-8")
    layout = Layout(root=tmp_path, site_config=config)
    assert site_description(layout) == "Tasks, steps and a weekly report."


def test_the_manifest_summary_is_the_pypi_card_line(tmp_path: Path):
    manifest = tmp_path / "pyproject.toml"
    manifest.write_text('[project]\nname = "tasks"\ndescription = "Tasks and steps."\n',
                        encoding="utf-8")
    layout = Layout(root=tmp_path, pyproject=manifest)
    assert pyproject_description(layout) == "Tasks and steps."


def test_a_repository_without_those_files_answers_empty(tmp_path: Path):
    layout = Layout(root=tmp_path)
    assert site_description(layout) == "" and pyproject_description(layout) == ""
