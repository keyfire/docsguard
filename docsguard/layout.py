"""Where one repository keeps the things the guard reads.

Everything else in this package takes a `Layout`, so that the only repository-specific
knowledge stays in one literal at the call site. The three repositories that started this
package disagree on every path: the site config sits at the root of one and under `site/` in
the others, the wrapper's `pyproject.toml` lives a directory down, the documentation folder is
the only thing they share.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


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
        return self.page_path(name).read_text(encoding="utf-8")

    def document(self, name: str) -> str:
        """The text of a repository document (README.md, pyproject.toml, ...)."""
        return (self.root / name).read_text(encoding="utf-8")
