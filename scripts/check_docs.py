#!/usr/bin/env python
"""Does the README of docsguard still name everything docsguard offers.

The joke that writes itself: a guard for documentation whose own documentation nobody guards.
It had already happened - a function lived in the package and was named in no edition of the
README, while three repositories were installing that same package to be told about exactly
this kind of gap. The mechanics were here all along; what was missing was pointing them at
this repository.

What stays here is what is about this repository. Its pages ARE its two READMEs - there is no
`docs` folder, so the layout says the pages live at the root - and its public surface is what
`__all__` declares. The judging comes from the package itself, which is the point: the guard
that fails here fails in every consumer the same way.

Run: `python scripts/check_docs.py`; the exit code is what CI reads.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Run from a checkout, without installing: CI installs the package for the test job and this
# script has to work in either case.
sys.path.insert(0, str(ROOT))

import docsguard  # noqa: E402
from docsguard import (  # noqa: E402
    JARGON,
    Layout,
    coverage_problems,
    jargon_problems,
    jargon_self_check,
    run,
    section_body,
)

#: The repository publishes no site and keeps no `docs` folder: the pages are the two editions
#: of the README at the root, and the layout says so instead of a reader special-casing it.
LAYOUT = Layout(root=ROOT, docs=ROOT, pyproject=ROOT / "pyproject.toml")

#: The section of each edition that has to name the whole surface.
SURFACE = (("README.md", "What is in it"), ("README.ru.md", "Что внутри"))

#: A name quoted in prose: `page_body`, `Layout`. The closing backtick has to follow the name
#: itself, so a quoted path or file name - `docs/index.md`, `pyproject.toml` - is not one.
_QUOTED = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`")

#: Words the surface section quotes that are not part of the surface. One each, with its
#: reason: `ast` is the standard-library module a reader is told the check parses with, and
#: `pipeline` is the identifier the jargon bullet shows being left alone. A word is added
#: here only when it is deliberately not a capability - the list is short on purpose, because
#: anything in it is a name the coverage check stops judging.
NOT_THE_SURFACE = frozenset({"ast", "pipeline"})

#: The install line a consumer copies: the URL and what it is pinned to.
_INSTALL = re.compile(r"pip install git\+https://github\.com/[\w.-]+/docsguard@(\S+)")

#: A dictionary word the way an edition quotes it: backticks around Russian letters and nothing
#: besides them. `allow=("хук",)` is a call rather than a word, and this reads past it.
_JARGON_WORD = re.compile(r"`([а-яё]+)`")


def public_names() -> set[str]:
    """The public surface as the package declares it: `__all__` without the dunders.

    `__version__` is in `__all__` and is not a capability - a README that had to name it would
    be naming the packaging, not the package.
    """
    return {name for name in docsguard.__all__ if not name.startswith("_")}


def check_surface() -> list[str]:
    """Every public name is named in both editions, and neither names a name that is gone."""
    problems: list[str] = []
    for name, heading in SURFACE:
        body = section_body(LAYOUT, name, heading)
        if body is None:
            problems.append(
                f'{name}: no section "{heading}" - where does the README list the surface now?'
            )
            continue
        problems += coverage_problems(
            public_names(),
            set(_QUOTED.findall(body)) - NOT_THE_SURFACE,
            what="public name",
            where=f"{name} / {heading}",
        )
    return problems


def check_install() -> list[str]:
    """The tag the install lines pin is the version the package reports.

    The package is installed from git, so the tag IS the release: a version bumped without the
    line above going up leaves every consumer copying the address of the previous one. The two
    are one step, and this is what makes them one step.
    """
    expected = f"v{docsguard.__version__}"
    problems: list[str] = []
    for name, _ in SURFACE:
        pinned = _INSTALL.findall(LAYOUT.page(name))
        if not pinned:
            problems.append(
                f"{name}: no install line - where does a consumer read the URL and the tag?"
            )
            continue
        for tag in pinned:
            if tag != expected:
                problems.append(
                    f"{name}: the install line pins {tag} and the package reports {expected} - "
                    "a version bump and the line a consumer copies are one step"
                )
    return problems


def check_jargon_list() -> list[str]:
    """Both editions name every word of the dictionary, and neither names a word that is gone.

    The words are a copy of `JARGON`, and a copy drifts - the defect this package was written
    for. The owner shortened the dictionary by eleven rows on 12 September 2026, and a README
    left alone would have gone on forbidding words that are allowed now.
    """
    problems: list[str] = []
    for name, heading in SURFACE:
        body = section_body(LAYOUT, name, heading)
        if body is None:
            continue  # check_surface has already said where the section went.
        problems += coverage_problems(
            {word.name for word in JARGON},
            set(_JARGON_WORD.findall(body)),
            what="jargon word",
            where=f"{name} / {heading}",
        )
    return problems


def check_jargon() -> list[str]:
    """The Russian edition is written in Russian, and the dictionary that says so is awake.

    Two halves, and the first one is about the guard rather than about the README. A root
    that has lost a letter finds nothing and reads exactly like a repository in order, so
    the dictionary is proved on its own samples before it is let near a page. Then it reads
    the Russian README, the way a consumer points it at its own pages. This repository's
    pages ARE its two READMEs, so that one file is the whole of its Russian documentation.
    """
    return jargon_self_check() + jargon_problems(LAYOUT)


CHECKS = (check_surface, check_install, check_jargon_list, check_jargon)


def problems() -> list[str]:
    """Every finding of every check - what the test suite asserts on."""
    found: list[str] = []
    for check in CHECKS:
        found.extend(check())
    return found


if __name__ == "__main__":
    sys.exit(run(CHECKS, title="docsguard's own documentation"))
