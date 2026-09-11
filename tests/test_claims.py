"""One fact, one wording - the claim table and what it finds."""

from pathlib import Path

import pytest

from docsguard import Claim, Layout, claim_problems, claim_text, claim_texts

CLAIM = Claim(
    name="the platform deletes the builds nobody uses",
    told_in=("docs/spec.md", "README.md", "src/tool/client.py"),
    wording=("nobody uses", "никто не пользуется"),
    retired=("store limit", "предел хранения"),
)


@pytest.fixture()
def layout(tmp_path: Path) -> Layout:
    (tmp_path / "docs").mkdir()
    (tmp_path / "src" / "tool").mkdir(parents=True)
    (tmp_path / "docs" / "spec.md").write_text(
        "# Requirements\n\nThe platform deletes the builds nobody uses.\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "The store keeps what is in use: it deletes the builds nobody uses.\n", encoding="utf-8")
    (tmp_path / "src" / "tool" / "client.py").write_text(
        '"""The listing: the platform deletes the builds nobody uses."""\n', encoding="utf-8")
    return Layout(root=tmp_path)


def test_a_fact_told_everywhere_it_is_named_is_silence(layout):
    assert claim_problems(layout, [CLAIM]) == []


def test_a_place_that_stopped_telling_the_fact_is_named(layout):
    """The failure the table exists for: a correction reaches the pages and leaves the code."""
    (layout.root / "src" / "tool" / "client.py").write_text(
        '"""The listing: old builds are pushed out."""\n', encoding="utf-8")

    problems = claim_problems(layout, [CLAIM])

    assert len(problems) == 1
    assert "src/tool/client.py" in problems[0]
    assert "nobody uses" in problems[0]


def test_the_superseded_wording_coming_back_is_named(layout):
    """A page that copied the old sentence, or one the correction simply never reached."""
    page = layout.docs / "platform.md"
    page.write_text("The store limit is thirty builds.\n", encoding="utf-8")

    problems = claim_problems(layout, [CLAIM], claim_texts(layout, documents=["README.md"]))

    assert len(problems) == 1
    assert "docs/platform.md" in problems[0] and "superseded" in problems[0]


def test_a_claim_that_names_a_place_the_repository_has_not_got(layout):
    """A renamed file must not turn a claim into a check of nothing."""
    gone = Claim(name="invented", told_in=("docs/no-such-page.md",), wording=("x",))

    problems = claim_problems(layout, [gone])

    assert len(problems) == 1 and "no-such-page.md" in problems[0]


def test_without_a_search_set_the_places_the_claim_names_are_the_ones_searched(layout):
    """The copy that kept living is caught even by a repository that lists nothing else."""
    (layout.root / "README.md").write_text(
        "It deletes the builds nobody uses, up to the store limit.\n", encoding="utf-8")

    problems = claim_problems(layout, [CLAIM])

    assert len(problems) == 1
    assert "README.md" in problems[0] and "store limit" in problems[0]


def test_a_page_of_a_documentation_folder_that_is_not_under_the_root(tmp_path):
    """The table names a page `docs/...` however far the folder itself sits from the root."""
    elsewhere = tmp_path / "site" / "pages"
    elsewhere.mkdir(parents=True)
    (elsewhere / "spec.md").write_text("The builds nobody uses are deleted.\n", encoding="utf-8")
    layout = Layout(root=tmp_path / "repo", docs=elsewhere)

    assert claim_text(layout, "docs/spec.md") is not None
    assert claim_problems(layout, [Claim(name="deletion", told_in=("docs/spec.md",),
                                         wording=("nobody uses",))]) == []


def test_the_search_set_is_the_places_a_reader_names(layout):
    """The labels of the findings are the paths of the repository, not absolute ones."""
    (layout.docs / "changelog.md").write_text("It said `store limit` once.\n", encoding="utf-8")

    texts = claim_texts(layout, exclude=("changelog*",), documents=["README.md"],
                        sources=["src/*/*.py"])

    assert list(texts) == ["docs/spec.md", "README.md", "src/tool/client.py"]
    # ...and the changelog is out on purpose: an entry about a correction quotes what it
    # corrected, and that quote is the record of the fix rather than a relapse
    assert claim_problems(layout, [CLAIM], texts) == []
