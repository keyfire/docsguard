"""Shared parts of the documentation guard that three repositories were keeping in triplicate.

What a repository keeps for itself is the TABLE OF POSITIONS - where its pages, site config and
manifest live - and the checks that are about its own subject: the tools it registers, the
environment variables it reads, the rules it implements. What lives here is everything those
checks had in common and had already copied three times: reading a file whatever mark its
editor put at the head of it, reading a page without its frontmatter, the block between
injection markers, the annotations a repository states about itself, the statements that have
to be told in the same words everywhere, the coverage of what the sources offer by what a
document lists, the conventions of the sources that no test of a feature would notice, and the
runner that prints the findings and answers with an exit code.

    from pathlib import Path
    from docsguard import Layout, PitchItem, pitch_problems, run

    LAYOUT = Layout(root=Path(__file__).resolve().parent.parent,
                    site_config=Path("site/blume.config.ts"))

    def check_pitches():
        return pitch_problems(ITEMS, headlines(), surfaces())

    raise SystemExit(run([check_pitches, ...]))
"""

from .annotations import PitchItem, pitch_problems, pyproject_description, site_description
from .claims import Claim, claim_problems, claim_text, claim_texts
from .checks import (
    image_problems,
    injection_problems,
    mirror_problems,
    translation_problems,
)
from .conventions import (
    asks_for_text,
    encoding_problems,
    newline_problems,
    process_encoding_problems,
    process_starts,
    python_sources,
    shadowed_definitions,
    shadowed_problems,
    shadowed_test_problems,
    text_write_newline_problems,
    text_writes,
    writes_text,
)
from .coverage import coverage_problems
from .jargon import (
    JARGON,
    JargonWord,
    empty_exceptions,
    jargon_findings,
    jargon_problems,
    jargon_self_check,
    russian_pages,
    russian_strings,
    source_findings,
    source_jargon_problems,
    without_code,
)
from .layout import Layout, read_text
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

__version__ = "0.9.0"

__all__ = [
    "IMAGE",
    "JARGON",
    "Claim",
    "JargonWord",
    "Layout",
    "PitchItem",
    "__version__",
    "asks_for_text",
    "box_headlines",
    "claim_problems",
    "claim_text",
    "claim_texts",
    "coverage_problems",
    "empty_exceptions",
    "encoding_problems",
    "front_description",
    "headings",
    "image_problems",
    "injected",
    "injection_problems",
    "jargon_findings",
    "jargon_problems",
    "jargon_self_check",
    "lede",
    "mirror_problems",
    "mirror_source",
    "newline_problems",
    "page_body",
    "pitch_problems",
    "process_encoding_problems",
    "process_starts",
    "pyproject_description",
    "python_sources",
    "read_text",
    "report",
    "run",
    "russian_pages",
    "russian_strings",
    "section_body",
    "shadowed_definitions",
    "shadowed_problems",
    "shadowed_test_problems",
    "site_description",
    "site_pages",
    "source_findings",
    "source_jargon_problems",
    "text_write_newline_problems",
    "text_writes",
    "translation_problems",
    "without_code",
    "writes_text",
]
