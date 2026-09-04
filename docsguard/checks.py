"""Checks that are the same wherever documentation is mirrored into a repository document.

Two of them, and each caught a real defect before this package existed: a mirrored README that
had fallen behind the page it mirrors, and an image link that pointed at a file the mirror
cannot show.
"""

from __future__ import annotations

from .layout import Layout
from .pages import IMAGE, injected, mirror_source, page_body, section_body


def mirror_problems(
    layout: Layout,
    pairs: tuple[tuple[str, str], ...] | list[tuple[str, str]],
) -> list[str]:
    """A page mirrored from a repository document that no longer matches it.

    pairs - (page name, document name). The comparison is on the TEXT, not on its length: a
    mirroring script may reflow or add its own notes, and only a divergence of what is said is
    a finding.
    """
    problems: list[str] = []
    for name, document in pairs:
        try:
            body = page_body(layout, name)
        except FileNotFoundError:
            problems.append(f"{name}: the page is mirrored from {document} and does not exist")
            continue
        source = mirror_source(layout, document)
        if body.split() != source.split():
            problems.append(
                f"{name}: the page no longer matches {document} it mirrors - "
                "regenerate the mirrors"
            )
    return problems


def injection_problems(
    layout: Layout,
    injections: tuple[tuple[str, str, str, str | None], ...]
    | list[tuple[str, str, str, str | None]],
    *,
    svg_to_png: bool = False,
) -> list[str]:
    """A block injected into a repository document that no longer matches its source.

    injections - (document, marker, page name, section heading). A heading of None means the
    document carries the WHOLE page: both shapes are in use, and a check that knew only the
    section one reported every full-page injection as stale.

    `svg_to_png` is passed on to the page reader: a document that carries diagrams carries the
    PNG twins, and comparing it against the SVG links of the page would report it as stale on
    every run.

    A missing marker pair is reported apart from a stale block: one means the document was
    rewritten without the markers, the other that the mirroring script has not been run.
    """
    problems: list[str] = []
    for document, marker, name, heading in injections:
        what = f'the section "{heading}" of {name}' if heading else name
        block = injected(layout, document, marker)
        if block is None:
            problems.append(
                f'{document}: the markers of the injected block "{marker}" are gone - '
                f"{what} reaches nobody"
            )
            continue
        if heading is None:
            source = page_body(layout, name, svg_to_png=svg_to_png)
        else:
            source = section_body(layout, name, heading)
            if source is None:
                problems.append(f'{name}: no section "{heading}" for the block "{marker}"')
                continue
        if block.split() != source.split():
            problems.append(
                f'{document}: the injected block "{marker}" no longer matches {what} - '
                "regenerate the mirrors"
            )
    return problems


def image_problems(
    layout: Layout,
    names: tuple[str, ...] | list[str],
    *,
    prefer_svg: bool = False,
) -> list[str]:
    """An image a page links and the repository does not carry.

    A link through the layout's `raw_prefix` is a repository file too - that is how a mirrored
    README reaches an image, and the page it was mirrored from carries the same link. Any other
    absolute link belongs to a host, and whether it answers is not a question a file check can
    settle.

    `prefer_svg` adds the rule a diagram brings with it: a page must show the SVG, which carries
    both palettes, while the PNG twin has one baked in. A reader in the light theme was served
    a dark picture for a while because the page linked the README's copy.
    """
    problems: list[str] = []
    for name in names:
        for link in IMAGE.findall(layout.page(name)):
            if layout.raw_prefix and link.startswith(layout.raw_prefix):
                target = (layout.root / link[len(layout.raw_prefix):]).resolve()
            elif link.startswith(("http://", "https://", "data:", "#")):
                continue
            else:
                target = (layout.docs / link).resolve()
                if not target.is_file():
                    target = (layout.root / link.lstrip("/")).resolve()
            if not target.is_file():
                problems.append(f"{name}: the image {link} is not in the repository")
                continue
            if prefer_svg and target.suffix == ".png" and target.with_suffix(".svg").is_file():
                problems.append(
                    f"{name}: {target.name} follows no theme - the page needs "
                    f"{target.with_suffix('.svg').name}, the PNG belongs to the mirrored copy"
                )
    return problems
