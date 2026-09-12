"""Reading a documentation page the way the checks need it.

None of this is clever, and that is the point: every one of these six readers had three copies,
one per repository, and the copies had already drifted - the same helper skipped the generator
notes in one repository and kept them in another, so the same defect was a finding in one place
and silence in the next.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from .layout import Layout, read_text

#: A frontmatter block at the top of a page.
_FRONTMATTER = re.compile(r"^---\n[\s\S]*?\n---\n")
#: An HTML comment - the generator notes a page carries for the reader of the source.
_COMMENT = re.compile(r"<!--[\s\S]*?-->\n?")
#: A bullet whose headline is bold, optionally a link: `- **Headline**` / `- **[Headline](x)**`.
_BULLET = re.compile(r"- \*\*(.+?)\*\*")
_LINKED = re.compile(r"\[(.+?)\]\(.*\)")
#: The `description:` line of a page's frontmatter.
_FRONT_DESCRIPTION = re.compile(r'^description:\s*"(.*)"\s*$', re.M)
#: An image reference of a markdown page.
IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")

#: The lines a mirrored document loses on its way into a page: the language switcher of a
#: bilingual README, in either spelling.
_SWITCHER_PREFIXES = ("**English**", "**Русский**", "**Английская", "[English]", "[Русский]")


def page_body(layout: Layout, name: str, *, svg_to_png: bool = False) -> str:
    """A page without its frontmatter and without the generator notes.

    `svg_to_png` rewrites diagram links the way a README carries them: a page shows an SVG and
    follows the reader's theme, a README on GitHub cannot, so the mirroring script writes the
    PNG twin. A repository whose pages carry no diagrams leaves the flag alone.
    """
    text = _COMMENT.sub("", _FRONTMATTER.sub("", layout.page(name))).strip()
    if svg_to_png:
        text = re.sub(r"(docs/[\w.-]+)\.svg\)", r"\1.png)", text)
    return text


def section_body(layout: Layout, name: str, section: str) -> str | None:
    """The body of one `## Section` of a page - what a README embeds; None when there is none."""
    lines = layout.page(name).split("\n")
    try:
        start = lines.index(f"## {section}")
    except ValueError:
        return None
    rest = lines[start + 1:]
    end = next((i for i, line in enumerate(rest) if line.startswith("## ")), len(rest))
    return "\n".join(rest[:end]).strip()


def headings(layout: Layout, name: str, level: int = 3) -> list[str]:
    """The headings of one level, in page order - the groups a page is divided into."""
    prefix = "#" * level + " "
    return [line[len(prefix):].strip()
            for line in layout.page(name).splitlines() if line.startswith(prefix)]


def box_headlines(layout: Layout, name: str, heading: str) -> list[str]:
    """The bold headline of every bullet of one section, in page order.

    A headline written as a link answers with its text: the block of features is read by people,
    and half of its lines link the page that details the feature.
    """
    found = []
    for line in (section_body(layout, name, heading) or "").splitlines():
        bullet = _BULLET.match(line)
        if not bullet:
            continue
        label = bullet.group(1)
        link = _LINKED.fullmatch(label)
        found.append(link.group(1) if link else label)
    return found


def front_description(layout: Layout, name: str) -> str:
    """The `description` of a page's frontmatter - its meta description and search snippet."""
    found = _FRONT_DESCRIPTION.search(layout.page(name))
    return found.group(1) if found else ""


def lede(path: Path) -> str:
    """The first paragraph of prose of a document - what GitHub shows above the fold.

    Badges, headings, quotes and the language switcher are skipped: they are furniture, and the
    sentence a reader actually meets is the one after them.
    """
    skip = ("#", ">", "!", "[") + _SWITCHER_PREFIXES + ("**Documentation", "**Документация")
    for block in re.split(r"\n\s*\n", read_text(path)):
        if block.strip() and not block.strip().startswith(skip):
            return block.strip()
    return ""


def injected(layout: Layout, document: str, marker: str) -> str | None:
    """The block a mirroring script writes into a repository document between its markers.

    None means the document carries no such block at all - a different finding from an empty
    one, and the caller says which of the two its check is about.
    """
    text = layout.document(document)
    open_tag, close_tag = f"<!-- {marker}:start -->", f"<!-- {marker}:end -->"
    if open_tag not in text or close_tag not in text:
        return None
    return text.split(open_tag, 1)[1].split(close_tag, 1)[0].strip()


def mirror_source(layout: Layout, name: str) -> str:
    """A root document the way a mirrored page carries it: no H1, no language switcher.

    The page states the title in its frontmatter and the switcher belongs to the site, so both
    are dropped on the way in - and a comparison that kept them would report every mirrored
    page as out of date.
    """
    lines = [line for line in layout.document(name).split("\n")
             if not line.startswith(_SWITCHER_PREFIXES)]
    first = next((i for i, line in enumerate(lines) if line.strip()), None)
    if first is not None and lines[first].startswith("# "):
        del lines[first]
    return "\n".join(lines).strip()


def site_pages(layout: Layout) -> list[Path]:
    """The pages the site actually publishes - the site config says which are left out."""
    if layout.site_config is None or not layout.site_config.is_file():
        return sorted(layout.docs.glob("*.md"))
    config = read_text(layout.site_config)
    block = re.search(r"exclude:\s*\[([^\]]*)\]", config, re.S)
    patterns = re.findall(r'"([^"]+)"', block.group(1)) if block else []
    return [
        path for path in sorted(layout.docs.glob("*.md"))
        if not any(fnmatch.fnmatch(path.name, pattern.removeprefix("**/"))
                   for pattern in patterns)
    ]
