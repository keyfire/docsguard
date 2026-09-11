"""Conventions of the sources that no test of a feature would ever notice.

A convention nobody wrote down is a convention every new file gets to rediscover. This one was
rediscovered the hard way in the repository it came from: every process it starts asks for text
and names the encoding, a new script did not, and the failure was SILENT - the output of a
generator was decoded with the code page of the console, the Russian page names turned into
replacement characters, the text was lost, and the exit code went on saying that everything had
gone well.

Nothing about that is one repository's business. The engine and the bridge start processes the
same way, read them as text the same way, and have the same silent failure waiting - which is
why the mechanics live here and what stays with the consumer is the list of folders to read.

Read with `ast` rather than with a regular expression, and that is the whole point: the call
that started it is written `(run or subprocess.run)(...)`, so a check looking for the text
`subprocess.run(` at the head of a call would have passed over exactly the one that mattered.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

from .layout import Layout

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
        problems += encoding_problems(path.read_text(encoding="utf-8"),
                                      path.relative_to(layout.root).as_posix())
    return problems
