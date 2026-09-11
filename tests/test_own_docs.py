"""The guard is pointed at its own README - and it still bites when the README goes stale.

Two failures live here, the same two every consumer of this package has. The first is coverage:
a public name the package offers and no edition of the README carries - the gap this check was
written for, because it was this package's own. The second is the guard going quiet: a check
that finds nothing looks exactly like a repository in order, so the finding is provoked on a
COPY of the pages rather than by patching the check's insides, which would prove nothing about
the check that actually runs.
"""

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

from docsguard import Layout

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def guard():
    spec = importlib.util.spec_from_file_location(
        "docsguard_check_docs", ROOT / "scripts" / "check_docs.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        del sys.modules[spec.name]
        raise
    return module


@pytest.fixture()
def sabotage(guard, tmp_path, monkeypatch):
    """Edit a COPY of the READMEs and let the guard read that copy."""
    for name in ("README.md", "README.ru.md"):
        shutil.copy(ROOT / name, tmp_path / name)
    monkeypatch.setattr(guard, "LAYOUT", Layout(root=tmp_path, docs=tmp_path))

    def edit(name: str, old: str, new: str) -> None:
        path = tmp_path / name
        text = path.read_text(encoding="utf-8")
        assert old in text, f"{name}: {old!r} is not there any more - has the README been rewritten?"
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    return edit


def test_the_readme_names_everything_the_package_offers(guard):
    """The check itself: both editions name every public name, and neither names a ghost."""
    assert guard.problems() == []


def test_the_surface_read_from_the_package_is_not_empty(guard):
    """A reader that comes back with nothing passes every README ever written."""
    names = guard.public_names()

    assert len(names) > 20
    assert "coverage_problems" in names
    # `__version__` is in `__all__` and is not a capability: a README naming it would be
    # describing the packaging rather than the package.
    assert not any(name.startswith("_") for name in names)


def test_a_public_name_dropped_from_the_english_edition_is_found(sabotage, guard):
    """The gap this check exists for: a function in the package, named in no edition."""
    sabotage("README.md", "`claim_text`, ", "")

    problems = guard.problems()

    assert len(problems) == 1
    assert "README.md" in problems[0]
    assert "claim_text" in problems[0]


def test_a_public_name_dropped_from_the_russian_edition_is_found(sabotage, guard):
    """Both editions are judged: a translation that fell behind is the same defect."""
    sabotage("README.ru.md", "`claim_text`, ", "")

    problems = guard.problems()

    assert len(problems) == 1
    assert "README.ru.md" in problems[0]


def test_a_name_the_package_no_longer_exports_is_found(sabotage, guard):
    """The other direction: a renamed function leaves the README pointing at nothing."""
    sabotage("README.md", "`coverage_problems`", "`coverage_gaps`")

    problems = guard.problems()

    assert len(problems) == 2
    assert any("coverage_problems" in problem for problem in problems)
    assert any("coverage_gaps" in problem and "no such thing" in problem
               for problem in problems)


def test_a_renamed_section_is_a_finding_rather_than_silence(sabotage, guard):
    """A heading nobody can find would otherwise turn the whole check into nothing."""
    sabotage("README.md", "## What is in it", "## The surface")

    problems = guard.problems()

    assert len(problems) == 1
    assert "What is in it" in problems[0]
