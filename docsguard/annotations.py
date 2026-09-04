"""The short annotations - and why a guard exists for them at all.

A repository states what it is in several one-liners: the site config's `description`, the
frontmatter of the front page, the summary in `pyproject.toml`, the lede of the README. Nobody
reads all four together, so they drift: at one of the repositories a whole capability was
missing from every annotation for two weeks while the front page had named it all along, and
the assistant answering from search results described the older tool.

The check is therefore not "is the text nice" but "does each annotation still name what the
front page lists". The bridge between the two is a table the repository writes itself: one row
per headline of the features block, carrying the word that has to stand for that headline in
each language. A row with no words is a headline deliberately kept out of the annotations - and
the reason for that belongs beside it, in the repository's own table.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .layout import Layout

#: The `description` of a site config, possibly written as several concatenated string parts.
_SITE_DESCRIPTION = re.compile(r"\n  description:\s*((?:\s*\"[^\"]*\"\s*\+?)+),")
#: The `description` of a packaging manifest.
_PYPROJECT_DESCRIPTION = re.compile(r'^description = "(.*)"\s*$', re.M)


@dataclass(frozen=True)
class PitchItem:
    """One headline of the features block and the words that stand for it.

    english / russian - the headline as each page writes it.
    en_word / ru_word - the word an annotation of that language must contain; None means the
    headline is deliberately absent from the annotations.
    """

    english: str
    russian: str
    en_word: str | None = None
    ru_word: str | None = None

    def headline(self, locale: str) -> str:
        return self.english if locale == "en" else self.russian

    def word(self, locale: str) -> str | None:
        return self.en_word if locale == "en" else self.ru_word


def site_description(layout: Layout) -> str:
    """The `description` of the site config - the meta description of every page."""
    if layout.site_config is None or not layout.site_config.is_file():
        return ""
    found = _SITE_DESCRIPTION.search(layout.site_config.read_text(encoding="utf-8"))
    return "".join(re.findall(r'"([^"]*)"', found.group(1))) if found else ""


def pyproject_description(layout: Layout) -> str:
    """The `description` of the packaging manifest - the summary line of the PyPI card."""
    if layout.pyproject is None or not layout.pyproject.is_file():
        return ""
    found = _PYPROJECT_DESCRIPTION.search(layout.pyproject.read_text(encoding="utf-8"))
    return found.group(1) if found else ""


def pitch_problems(
    items: tuple[PitchItem, ...] | list[PitchItem],
    headlines: dict[str, list[str]],
    surfaces: dict[str, dict[str, str]],
    *,
    pages: dict[str, str] | None = None,
) -> list[str]:
    """The gaps between the features block, the table and the annotations.

    items     - the repository's table.
    headlines - {locale: the headlines the page lists}, in page order.
    surfaces  - {locale: {where: the annotation text}} - what is quoted instead of the page.
    pages     - {locale: the page name to name in a message}; defaults to the locale itself.

    Both directions are judged. A headline the table does not know means the table was not
    updated when the page grew; a table row the page does not list means the opposite, and the
    guard would otherwise demand a word for a feature that no longer exists.
    """
    named = pages or {locale: locale for locale in headlines}
    problems: list[str] = []
    for locale, listed in headlines.items():
        where = named.get(locale, locale)
        known = [item.headline(locale) for item in items]
        for headline in listed:
            if headline not in known:
                problems.append(
                    f'{where}: "{headline}" is in no table row - add the word that stands for '
                    f"it in the annotations, or the reason it stays out of them"
                )
        for headline in known:
            if headline not in listed:
                problems.append(f'{where}: the table names "{headline}", the page does not')

    for item in items:
        for locale in headlines:
            word = item.word(locale)
            if not word:
                continue
            for where, text in surfaces.get(locale, {}).items():
                if word.lower() not in text.lower():
                    problems.append(
                        f'{where}: the short annotation says nothing about "{item.english}" '
                        f'(expected "{word}")'
                    )
    return problems
