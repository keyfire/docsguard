"""The table of positions, and the one reading every check in this package goes through.

The reading is worth a file of its own because of what a byte-order mark does. An editor on
Windows writes it without being asked, a diff does not show it, and a plain `utf-8` read hands
it on as an invisible first character. Behind that character a page loses its first heading and
a Python source stops parsing altogether. So the provocations here are made on real bytes: a
file with the mark, the same file without it, and the answer has to be the same text.
"""

import codecs
from pathlib import Path

from docsguard import Layout, read_text


def test_a_file_is_read_the_same_with_the_mark_and_without_it(tmp_path: Path):
    """The mark is not part of the text, and nothing behind this reader should ever see it."""
    marked = tmp_path / "marked.md"
    plain = tmp_path / "plain.md"
    marked.write_bytes(codecs.BOM_UTF8 + "# Заголовок\n".encode("utf-8"))
    plain.write_bytes("# Заголовок\n".encode("utf-8"))

    assert read_text(marked) == read_text(plain) == "# Заголовок\n"


def test_a_heading_at_the_head_of_a_marked_page_is_still_a_heading(tmp_path: Path):
    """What the mark costs a reader: the line no longer begins with `#`, so nothing matches."""
    page = tmp_path / "index.md"
    page.write_bytes(codecs.BOM_UTF8 + "# Title\n\nThe prose.\n".encode("utf-8"))

    assert read_text(page).startswith("# ")


def test_the_pages_and_documents_of_a_layout_go_through_the_same_reading(tmp_path: Path):
    """Both ways into a repository's text, so neither is left with a mark to trip over."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_bytes(codecs.BOM_UTF8 + b"# Page\n")
    (tmp_path / "README.md").write_bytes(codecs.BOM_UTF8 + b"# Document\n")
    layout = Layout(root=tmp_path)

    assert layout.page("index.md") == "# Page\n"
    assert layout.document("README.md") == "# Document\n"


def test_the_docs_folder_defaults_to_docs_beside_the_root(tmp_path: Path):
    """A repository that keeps its pages where everybody does says nothing about them."""
    assert Layout(root=tmp_path).docs == tmp_path / "docs"


def test_a_repository_whose_pages_are_its_readmes_says_so(tmp_path: Path):
    """The shape this package itself has: no `docs` folder, the pages live at the root."""
    layout = Layout(root=tmp_path, docs=tmp_path)

    assert layout.page_path("README.md") == tmp_path / "README.md"
