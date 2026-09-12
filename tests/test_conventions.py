"""The three conventions of the sources - the shapes they are written in, and this package.

All three rules came from one repository and belong to none. Every repository of this family
starts processes and reads them as text, with the same silent failure waiting: the output
decoded with the code page of the console, the Russian names coming back as replacement
characters, the text lost, and the exit code still saying the run went well. Every one of them
writes pages from Python too, and a text file written without naming its newline takes the
platform's line ending - a page rewritten on Windows comes back with every line changed, which
a checkout with `core.autocrlf=input` hides right up until the machine that has not got the
setting. And every one of them writes tests, where one name used twice retires the older of
the two without saying so.

The provocations are here rather than in a consumer, because they are about the READER: the
shape it has to see through, the shape it must leave alone, and the shape that started all of
this - a callable chosen at the call site, which a search for the text of a call looks straight
past.
"""

import ast
import codecs
from pathlib import Path

import pytest

from docsguard import (
    Layout,
    encoding_problems,
    newline_problems,
    process_encoding_problems,
    process_starts,
    python_sources,
    shadowed_definitions,
    shadowed_problems,
    shadowed_test_problems,
    text_write_newline_problems,
)

ROOT = Path(__file__).resolve().parents[1]

#: Everything written in Python here: the package, its tests and the guard over its own README.
FOLDERS = ("docsguard", "tests", "scripts")
#: The folders of the newline convention - the code whose writes OUTLIVE the run. A test writes
#: into a temporary directory that is gone when the run ends, so it is not among them.
WRITING_FOLDERS = ("docsguard", "scripts")
#: The folders of the test-name convention: the ones pytest collects tests from.
TEST_FOLDERS = ("tests",)


def parsed(source: str) -> ast.AST:
    return ast.parse(source)


def test_a_call_that_asks_for_text_without_an_encoding_is_caught():
    """Both shapes the repositories write a process start in."""
    plain = "import subprocess\nsubprocess.run(command, capture_output=True, text=True)\n"
    seam = "import subprocess\n(run or subprocess.run)(command, text=True)\n"

    assert len(encoding_problems(plain, "plain.py")) == 1
    # the shape the failure came in: the callable is chosen at the call site, and a check
    # reading the head of the call would have looked straight past it
    assert len(encoding_problems(seam, "seam.py")) == 1


def test_a_call_that_decodes_nothing_is_left_alone():
    """Bytes in, bytes out: there is no encoding to name, and demanding one would be noise."""
    bytes_only = "import subprocess\nsubprocess.run(command, capture_output=True, check=True)\n"
    spelled = ('import subprocess\nsubprocess.run(command, capture_output=True, text=True, '
               'encoding="utf-8")\n')

    assert encoding_problems(bytes_only, "bytes.py") == []
    assert encoding_problems(spelled, "spelled.py") == []


@pytest.mark.parametrize("starter", ["run", "Popen", "call", "check_call", "check_output"])
def test_every_way_of_starting_a_process_is_judged(starter):
    """A reader that knew only `run` would pass the one call that was written differently."""
    source = f"import subprocess\nsubprocess.{starter}(command, text=True)\n"

    assert len(encoding_problems(source, "starter.py")) == 1


def test_universal_newlines_asks_for_text_too():
    """The older spelling of the same request, and the same silent decode behind it."""
    source = "import subprocess\nsubprocess.run(command, universal_newlines=True)\n"

    assert len(encoding_problems(source, "old.py")) == 1


def test_text_turned_off_explicitly_is_not_a_request_for_text():
    source = "import subprocess\nsubprocess.run(command, text=False)\n"

    assert encoding_problems(source, "off.py") == []


def test_the_finding_names_the_line_it_is_about():
    """A finding without a line number sends the reader to re-read the file."""
    source = "import subprocess\n\n\nsubprocess.run(command, text=True)\n"

    assert encoding_problems(source, "where.py") == [
        'where.py:4: a process is read as text without encoding="utf-8"'
    ]


def test_a_call_of_something_else_named_run_is_not_a_process():
    """The reader looks for `subprocess`, not for a popular verb."""
    source = "runner.run(command, text=True)\n"

    assert process_starts(parsed(source)) == []
    assert encoding_problems(source, "other.py") == []


def test_the_package_holds_itself_to_the_convention():
    """The rule this package hands out is the rule its own sources live by."""
    layout = Layout(root=ROOT)

    assert process_encoding_problems(layout, FOLDERS) == []


def test_the_reader_is_given_every_python_file_of_the_named_folders():
    """A folder list that has stopped matching the repository judges nothing at all."""
    layout = Layout(root=ROOT)
    found = [path.relative_to(ROOT).as_posix() for path in python_sources(layout, FOLDERS)]

    assert "docsguard/conventions.py" in found
    assert "scripts/check_docs.py" in found
    # Folder by folder in the order the consumer wrote them, sorted inside each: the order is
    # what makes two runs of the guard comparable line by line.
    order = {folder: number for number, folder in enumerate(FOLDERS)}
    assert found == sorted(found, key=lambda name: (order[name.split("/")[0]], name))


def test_a_text_file_written_without_a_newline_is_caught():
    """Both spellings of a write, and the failure is the same one in each."""
    written = 'from pathlib import Path\nPath("page.md").write_text(text, encoding="utf-8")\n'
    opened = 'with open("page.md", "w", encoding="utf-8") as handle:\n    handle.write(text)\n'

    assert len(newline_problems(written, "written.py")) == 1
    assert len(newline_problems(opened, "opened.py")) == 1


def test_a_write_that_names_the_newline_is_left_alone():
    """Any value counts: naming it is the rule, and `None` says the platform's ending is meant."""
    empty = 'p.write_text(text, encoding="utf-8", newline="")\n'
    feed = r'p.write_text(text, encoding="utf-8", newline="\n")' + "\n"
    deliberate = 'p.write_text(text, encoding="utf-8", newline=None)\n'

    assert newline_problems(empty, "empty.py") == []
    assert newline_problems(feed, "feed.py") == []
    assert newline_problems(deliberate, "deliberate.py") == []


def test_bytes_are_not_a_text_file():
    """Binary goes through untouched: there is no line ending to translate, and no keyword."""
    binary = 'open("archive.zip", "wb").write(blob)\n'
    write_bytes = 'p.write_bytes(blob)\n'

    assert newline_problems(binary, "binary.py") == []
    assert newline_problems(write_bytes, "bytes.py") == []


def test_a_file_opened_for_reading_is_not_a_write():
    """The default mode reads, and reading is where translating the ending is what is wanted."""
    default = 'open("page.md", encoding="utf-8").read()\n'
    spelled = 'with path.open("r", encoding="utf-8-sig") as handle:\n    handle.read()\n'

    assert newline_problems(default, "default.py") == []
    assert newline_problems(spelled, "spelled.py") == []


@pytest.mark.parametrize("mode", ["w", "a", "x", "r+", "w+", "at"])
def test_every_mode_that_writes_is_judged(mode):
    """A reader that knew only `"w"` would pass an append - the shape a log or a journal has."""
    source = f'open("page.md", "{mode}", encoding="utf-8").write(text)\n'

    assert len(newline_problems(source, "mode.py")) == 1


def test_a_mode_that_cannot_be_read_from_here_is_judged_rather_than_waved_through():
    """A guard that trusts what it cannot see stops at the first indirection."""
    source = 'open(path, mode).write(text)\n'

    assert len(newline_problems(source, "indirect.py")) == 1


def test_the_newline_finding_names_the_line_it_is_about():
    source = 'from pathlib import Path\n\n\nPath("page.md").write_text(text)\n'

    assert newline_problems(source, "where.py") == [
        'where.py:4: a text file is written without newline=""'
    ]


def test_the_package_holds_itself_to_the_newline_convention():
    """The rule this package hands out is the rule its own sources live by.

    A shorter list of folders than the process convention takes, and deliberately so: what a
    test writes goes into a temporary directory and is never committed, shipped or compared
    between machines - see `text_write_newline_problems`.
    """
    assert text_write_newline_problems(Layout(root=ROOT), WRITING_FOLDERS) == []


def test_the_writes_reader_finds_the_calls_it_is_meant_to_judge(tmp_path):
    """A detector that finds nothing passes every repository, this one included."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "offender.py").write_text(
        'p.write_text(text, encoding="utf-8")\n', encoding="utf-8", newline="")

    problems = text_write_newline_problems(Layout(root=tmp_path), ("src",))

    assert len(problems) == 1
    assert "src/offender.py:1" in problems[0]


def test_a_test_replaced_by_a_namesake_is_caught():
    """The failure this rule came from: one name used twice, and the older test is gone.

    Python keeps the last definition, pytest collects what the module ended up with, and the
    count goes UP because the newcomer was added - so nothing about the run says a test was
    lost. It happened in this very file: the newline convention arrived with a
    finding-names-the-line test, the process convention already had one under exactly that
    name, and the older one went without a word.
    """
    source = "def test_one():\n    pass\n\n\ndef test_one():\n    pass\n"

    assert shadowed_problems(source, "twice.py") == [
        "twice.py:5: test_one is defined again here - the earlier test of that name has "
        "stopped running"
    ]


def test_the_line_named_is_the_newcomer_rather_than_the_test_it_replaced():
    """The first definition still runs. What has to be renamed is the one that arrived."""
    source = "def test_one():\n    pass\n\n\ndef test_one():\n    pass\n"

    assert shadowed_definitions(parsed(source)) == [(5, "test_one")]


def test_two_classes_are_allowed_a_method_of_the_same_name():
    """Each namespace is judged on its own, and neither of these takes anything from anybody."""
    source = ("class TestOne:\n    def test_same(self):\n        pass\n\n\n"
              "class TestTwo:\n    def test_same(self):\n        pass\n")

    assert shadowed_problems(source, "classes.py") == []


def test_a_name_used_twice_inside_one_class_is_caught():
    """A method replaced by a namesake loses a test exactly the way a function does."""
    source = ("class TestOne:\n    def test_same(self):\n        pass\n\n"
              "    def test_same(self):\n        pass\n")

    assert len(shadowed_problems(source, "inside.py")) == 1


def test_something_that_is_not_collected_may_be_defined_twice():
    """Only what pytest runs is judged: a helper rewritten is between an author and a review."""
    source = "def helper():\n    pass\n\n\ndef helper():\n    pass\n"

    assert shadowed_problems(source, "helper.py") == []


def test_the_package_holds_itself_to_the_test_name_convention():
    """The rule this package hands out is the rule its own tests live by."""
    assert shadowed_test_problems(Layout(root=ROOT), TEST_FOLDERS) == []


def test_the_test_name_reader_finds_the_files_it_is_meant_to_judge(tmp_path):
    """A detector that finds nothing passes every repository, this one included."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_twice.py").write_text(
        "def test_one():\n    pass\n\n\ndef test_one():\n    pass\n",
        encoding="utf-8", newline="")

    problems = shadowed_test_problems(Layout(root=tmp_path), TEST_FOLDERS)

    assert len(problems) == 1
    assert "tests/test_twice.py:5" in problems[0]


def test_a_source_that_begins_with_a_byte_order_mark_is_still_judged(tmp_path):
    """A mark at the head of a file used to take the check down instead of past it.

    Editors on Windows write it by default and nobody sees it in a diff. Read as plain `utf-8`
    it stays in the text as a first character `ast.parse` refuses, and the check then raised a
    SyntaxError - worse than silence, because one such file left the repository with no
    findings from any of the others either.
    """
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "marked.py").write_bytes(
        codecs.BOM_UTF8 + b"import subprocess\nsubprocess.run(command, text=True)\n")

    problems = process_encoding_problems(Layout(root=tmp_path), ("src",))

    assert len(problems) == 1
    assert "src/marked.py:2" in problems[0]


def test_the_readers_behind_the_mark_all_see_the_same_text(tmp_path):
    """The mark is dropped by the reading, so no check has to know about it."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "marked.py").write_bytes(
        codecs.BOM_UTF8 + b'p.write_text(text, encoding="utf-8")\n')
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_marked.py").write_bytes(
        codecs.BOM_UTF8 + b"def test_one():\n    pass\n\n\ndef test_one():\n    pass\n")

    assert len(text_write_newline_problems(Layout(root=tmp_path), ("src",))) == 1
    assert len(shadowed_test_problems(Layout(root=tmp_path), TEST_FOLDERS)) == 1
