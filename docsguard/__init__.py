"""Shared parts of the documentation guard that three repositories were keeping in triplicate.

What a repository keeps for itself is the TABLE OF POSITIONS - where its pages, site config and
manifest live - and the checks that are about its own subject: the tools it registers, the
environment variables it reads, the rules it implements. What lives here is everything those
checks had in common and had already copied three times: reading a page without its
frontmatter, the block between injection markers, the annotations a repository states about
itself, and the runner that prints the findings and answers with an exit code.

    from pathlib import Path
    from docsguard import Layout, PitchItem, pitch_problems, run

    LAYOUT = Layout(root=Path(__file__).resolve().parent.parent,
                    site_config=Path("site/blume.config.ts"))

    def check_pitches():
        return pitch_problems(ITEMS, headlines(), surfaces())

    raise SystemExit(run([check_pitches, ...]))
"""

from .annotations import PitchItem, pitch_problems, pyproject_description, site_description
from .checks import (
    image_problems,
    injection_problems,
    mirror_problems,
    translation_problems,
)
from .layout import Layout
from .pages import (
    IMAGE,
    box_headlines,
    front_description,
    headings,
    injected,
    lede,
    mirror_source,
    page_body,
    section_body,
    site_pages,
)
from .runner import report, run

__version__ = "0.1.0"

__all__ = [
    "IMAGE",
    "Layout",
    "PitchItem",
    "__version__",
    "box_headlines",
    "front_description",
    "headings",
    "image_problems",
    "injected",
    "injection_problems",
    "lede",
    "mirror_problems",
    "mirror_source",
    "page_body",
    "pitch_problems",
    "pyproject_description",
    "report",
    "run",
    "section_body",
    "site_description",
    "site_pages",
    "translation_problems",
]
