"""A process read as text names its encoding - the shapes it is written in, and this package.

The rule came from one repository and belongs to none: every repository of this family starts
processes, reads them as text, and has the same silent failure waiting - the output decoded
with the code page of the console, the Russian names coming back as replacement characters, the
text lost, and the exit code still saying the run went well.

The provocations are here rather than in a consumer, because they are about the READER: the
shape it has to see through, the shape it must leave alone, and the shape that started all of
this - a callable chosen at the call site, which a search for the text of a call looks straight
past.
"""

import ast
from pathlib import Path

import pytest

from docsguard import (
    Layout,
    encoding_problems,
    newline_problems,
    process_encoding_problems,
    process_starts,
    python_sources,
    text_write_newline_problems,
)

ROOT = Path(__file__).resolve().parents[1]

#: Everything written in Python here: the package, its tests and the guard over its own README.
FOLDERS = ("docsguard", "tests", "scripts")
#: The folders of the newline convention - the code whose writes OUTLIVE the run. A test writes
#: into a temporary directory that is gone when the run ends, so it is not among them.
WRITING_FOLDERS = ("docsguard", "scripts")


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


def test_the_finding_names_the_line_it_is_about():
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
