"""Where one repository keeps the things the guard reads, and how every file here is read.

Everything else in this package takes a `Layout`, so that the only repository-specific
knowledge stays in one literal at the call site. The three repositories that started this
package disagree on every path: the site config sits at the root of one and under `site/` in
the others, the wrapper's `pyproject.toml` lives a directory down, the documentation folder is
the only thing they share.

The reading itself is here for the same reason. Every file this package opens goes through
`read_text`, so the byte-order mark is dealt with once instead of in each reader.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def read_text(path: Path) -> str:
    """The text of a file, without the byte-order mark some editors put at the head of it.

    A plain `utf-8` read keeps that mark as an invisible first character, and every reader
    behind it then works on text that starts with something the writer never typed. A page
    loses its first heading, because the line no longer begins with `#`. A Python source is
    worse: `ast.parse` raises a SyntaxError, so the check over it does not report a finding -
    it falls over. Editors on Windows write the mark by default, and `utf-8-sig` reads a file
    without one exactly as `utf-8` does, so this is what the package reads with everywhere.
    """
    return path.read_text(encoding="utf-8-sig")


@dataclass(frozen=True)
class Layout:
    """The positions of one repository.

    root         - the repository root.
    docs         - the folder of documentation pages (`Name.md` + `Name.ru.md` pairs).
    site_config  - the site config whose `description` heads every page; None when the
                   repository publishes no site.
    pyproject    - the packaging manifest whose `description` heads the PyPI card; None for a
                   repository that ships no Python package.
    raw_prefix   - the raw-content prefix a mirrored document uses for images, e.g.
                   "https://raw.githubusercontent.com/<owner>/<repo>/main/".
    """

    root: Path
    docs: Path = field(default=None)  # type: ignore[assignment]
    site_config: Path | None = None
    pyproject: Path | None = None
    raw_prefix: str = ""

    def __post_init__(self) -> None:
        if self.docs is None:
            object.__setattr__(self, "docs", self.root / "docs")

    def page_path(self, name: str) -> Path:
        """The path of a documentation page by its file name."""
        return self.docs / name

    def page(self, name: str) -> str:
        """The text of a documentation page."""
        return read_text(self.page_path(name))

    def document(self, name: str) -> str:
        """The text of a repository document (README.md, pyproject.toml, ...)."""
        return read_text(self.root / name)
