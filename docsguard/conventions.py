"""Conventions of the sources that no test of a feature would ever notice.

A convention nobody wrote down is a convention every new file gets to rediscover. Two of them
live here, and both were rediscovered the hard way in the repositories this package serves.

The first is the encoding of a started PROCESS: every process one repository starts asks for
text and names the encoding, a new script did not, and the failure was SILENT - the output of a
generator was decoded with the code page of the console, the Russian page names turned into
replacement characters, the text was lost, and the exit code went on saying that everything had
gone well.

The second is the newline of a written FILE. `write_text` and `open` in text mode translate a
line feed into whatever the platform's line ending is, so a generator that rewrites a page on
Windows hands back a file with every line changed. Locally that is invisible - a checkout with
`core.autocrlf=input` normalizes it away on commit - and on a machine without that setting the
whole file goes to a public repository as one line-ending change. It was caught by a generator
that appends a link to two changelog editions and rewrote both of them entirely; the generators
beside it were already passing `newline=""`, which is the only reason the convention was
recognizable as one.

Nothing about either is one repository's business. The engine and the bridge start processes the
same way, write their pages the same way, and have the same silent failure waiting - which is why the mechanics live here and what stays with the
consumer is the list of folders to read.

Read with `ast` rather than with a regular expression, and that is the whole point: the call
that started the first of them is written `(run or subprocess.run)(...)`, so a check looking for
the text `subprocess.run(` at the head of a call would have passed over exactly the one that
mattered.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

from .layout import Layout, read_text

#: The functions of `subprocess` that start a process.
STARTERS = frozenset({"run", "Popen", "call", "check_call", "check_output"})
#: The keywords that turn the streams into text. Any of them, and the bytes have to be decoded
#: by somebody - so the encoding has to be said out loud.
TEXT_FLAGS = ("text", "universal_newlines")


def python_sources(layout: Layout, folders: Iterable[str]) -> list[Path]:
    """Every Python file of the named folders, in a stable order.

    The folders are the consumer's own knowledge: which of them hold code that starts processes
    is a fact about that repository. A convention that stops at the test folder is half a
    convention - it was a test helper that carried one of the first offenders.
    """
    found: list[Path] = []
    for folder in folders:
        found.extend(sorted((layout.root / folder).rglob("*.py")))
    return found


def process_starts(tree: ast.AST) -> list[ast.Call]:
    """The calls that start a process, however the callable is spelled at the call site.

    The whole callable expression is searched, not just its head: `(run or subprocess.run)(...)`
    is a process start, and that shape is what a runner seam for the tests looks like.
    """
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for inner in ast.walk(node.func):
            if (
                isinstance(inner, ast.Attribute)
                and inner.attr in STARTERS
                and isinstance(inner.value, ast.Name)
                and inner.value.id == "subprocess"
            ):
                calls.append(node)
                break
    return calls


def asks_for_text(call: ast.Call) -> bool:
    """Does the call want str back - by `text=`, by `universal_newlines=` or by `encoding=`."""
    for keyword in call.keywords:
        if keyword.arg in TEXT_FLAGS and not (
            isinstance(keyword.value, ast.Constant) and keyword.value.value is False
        ):
            return True
        if keyword.arg == "encoding":
            return True
    return False


def encoding_problems(source: str, where: str) -> list[str]:
    """The process starts of one file that ask for text and do not name the encoding.

    A call that asks for no text at all - bytes in, bytes out - decodes nothing and is left
    alone: demanding an encoding of it would be noise, and noise is what a guard gets ignored
    for.
    """
    problems = []
    for call in process_starts(ast.parse(source)):
        if not asks_for_text(call):
            continue  # bytes in, bytes out - nothing is being decoded
        if not any(keyword.arg == "encoding" for keyword in call.keywords):
            problems.append(f"{where}:{call.lineno}: a process is read as text without "
                            'encoding="utf-8"')
    return problems


def process_encoding_problems(layout: Layout, folders: Iterable[str]) -> list[str]:
    """Every process read as text without an encoding, across the folders of one repository."""
    problems: list[str] = []
    for path in python_sources(layout, folders):
        problems += encoding_problems(read_text(path),
                                      path.relative_to(layout.root).as_posix())
    return problems


#: The mode characters that open a file for WRITING. A mode without any of them only reads, and
#: reading is where the platform's newline translation is wanted: a page written on Windows and
#: one written on Linux then both come back with bare line feeds.
WRITE_MODES = frozenset("wax+")


def writes_text(call: ast.Call) -> bool:
    """Does this call write a TEXT file - `p.write_text(...)`, or an `open` in a text write mode.

    `open` is judged by its mode: absent, it is `"r"` and nothing is written; with a `b` in it
    the bytes go through untouched and there is no newline to translate. A mode that is not a
    literal - a variable, a value chosen above - is taken as a write, because a guard that
    trusts what it cannot read is a guard that stops at the first indirection.
    """
    name = call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", "")
    if name == "write_text":
        return True
    if name != "open":
        return False
    mode = next((keyword.value for keyword in call.keywords if keyword.arg == "mode"), None)
    if mode is None and len(call.args) > 1:
        mode = call.args[1]
    if mode is None:
        return False  # the default is "r"
    if not isinstance(mode, ast.Constant) or not isinstance(mode.value, str):
        return True  # unreadable from here; judged rather than waved through
    return "b" not in mode.value and any(item in WRITE_MODES for item in mode.value)


def text_writes(tree: ast.AST) -> list[ast.Call]:
    """Every call of one file that writes a text file, in the order they are written."""
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call) and writes_text(node)]


def newline_problems(source: str, where: str) -> list[str]:
    """The text writes of one file that leave the line ending to the platform.

    Naming `newline` is what the rule asks for, not naming a particular value: the empty string
    and a bare line feed both write the text through untouched, and a generator that deliberately
    wants the platform's ending says `newline=None` and is telling the reader so.
    """
    problems = []
    for call in text_writes(ast.parse(source)):
        if not any(keyword.arg == "newline" for keyword in call.keywords):
            problems.append(f"{where}:{call.lineno}: a text file is written without "
                            'newline=""')
    return problems


def text_write_newline_problems(layout: Layout, folders: Iterable[str]) -> list[str]:
    """Every text file written with the platform's line ending, across one repository.

    The folders are the consumer's knowledge again, and they are not the same list the process
    convention takes. That one reaches into the test folder, because a test helper that starts a
    generator can eat its output as thoroughly as the generator can. This one has no business
    there: a test writes into a temporary directory that is gone when the run ends, nothing it
    writes is committed, shipped or compared between machines, and a fixture deliberately
    carrying the other line ending is a test in its own right. What belongs here is the code
    whose writes OUTLIVE the run.
    """
    problems: list[str] = []
    for path in python_sources(layout, folders):
        problems += newline_problems(read_text(path),
                                     path.relative_to(layout.root).as_posix())
    return problems
