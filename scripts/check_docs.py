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
from docsguard import Layout, coverage_problems, run, section_body  # noqa: E402

#: The repository publishes no site and keeps no `docs` folder: the pages are the two editions
#: of the README at the root, and the layout says so instead of a reader special-casing it.
LAYOUT = Layout(root=ROOT, docs=ROOT, pyproject=ROOT / "pyproject.toml")

#: The section of each edition that has to name the whole surface.
SURFACE = (("README.md", "What is in it"), ("README.ru.md", "Что внутри"))

#: A name quoted in prose: `page_body`, `Layout`. The closing backtick has to follow the name
#: itself, so a quoted path or file name - `docs/index.md`, `pyproject.toml` - is not one.
_QUOTED = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`")


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
            set(_QUOTED.findall(body)),
            what="public name",
            where=f"{name} / {heading}",
        )
    return problems


CHECKS = (check_surface,)


def problems() -> list[str]:
    """Every finding of every check - what the test suite asserts on."""
    found: list[str] = []
    for check in CHECKS:
        found.extend(check())
    return found


if __name__ == "__main__":
    sys.exit(run(CHECKS, title="docsguard's own documentation"))
