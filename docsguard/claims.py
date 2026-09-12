"""One fact, one wording - a statement several documents and the code all have to make.

A statement about the subject of a repository lives in the specification, on a reference page,
in the README and in the docstrings of the code at once, and it gets corrected in one of them.
In the repository this was written for it happened twice: the correction reached the pages and
left the tool hints, the requirements and the comments telling the model it replaced - one
document carried both at the same time. The neighbouring repositories have the same shape of
documentation and the same defect waiting.

The mechanics are here; the TABLE stays in the repository. Which statements matter, where they
are told and in which words is knowledge about the subject, not about guarding.

Two halves, because the failure has two shapes. A place the claim names must still STATE it,
which catches the page a correction never reached. And the SUPERSEDED wording, in the spelling
it really had, must be nowhere, which catches both the copy that kept living and a new page that
copied it. Spellings, not meaning: a checker cannot read, and the wordings are taken from the
diff of the correction itself.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from .layout import Layout, read_text


@dataclass(frozen=True)
class Claim:
    """One statement that several places have to make.

    name     - the fact in a few words, the way a finding will name it.
    told_in  - the places that must state it, as paths a reader of the repository writes them:
               pages (`docs/...`), repository documents and source files. The list is kept by
               hand, because being told in this many places is a property of the fact, not
               something a reader can derive.
    wording  - the spellings that count as stating it; one of them has to occur.
    retired  - the spellings of the SUPERSEDED statement, in the form they really had. Those
               must be nowhere among the places searched - and the places where a quotation of
               the old wording is the record of the fix rather than a relapse, a changelog
               above all, are the ones left out of that search.
    """

    name: str
    told_in: tuple[str, ...]
    wording: tuple[str, ...]
    retired: tuple[str, ...] = ()


def claim_text(layout: Layout, where: str) -> str | None:
    """The text of a place a claim is told in; None when the repository has no such file.

    A place is written the way the repository writes it. `docs/` goes through the layout rather
    than through the root: a repository whose pages live somewhere else still names them
    `docs/...` in its table, because that is how its readers name them.
    """
    if where.startswith("docs/"):
        path = layout.page_path(where[len("docs/"):])
    else:
        path = layout.root / where
    try:
        return read_text(path)
    except FileNotFoundError:
        return None


def claim_texts(
    layout: Layout,
    *,
    pages: Iterable[str] = ("*.md",),
    exclude: Iterable[str] = (),
    documents: Iterable[str] = (),
    sources: Iterable[str] = (),
) -> dict[str, str]:
    """Everywhere a superseded wording could be hiding: {the place as a reader names it: text}.

    pages     - glob patterns inside the documentation folder;
    exclude   - glob patterns of pages to leave out. A changelog belongs here: an entry about a
                correction QUOTES the model it corrected, and that quote is the record of the
                fix, not a relapse. The guard's own tests are out for the same reason - a
                provocation has to spell the wording out;
    documents - repository documents by name, the READMEs and their like;
    sources   - glob patterns relative to the root (`src/*/*.py`), for the docstrings and the
                comments of the code, which drift exactly the way the pages do.
    """
    texts: dict[str, str] = {}
    skip = tuple(exclude)
    for pattern in pages:
        for path in sorted(layout.docs.glob(pattern)):
            if any(fnmatch.fnmatch(path.name, rule) for rule in skip):
                continue
            texts[f"docs/{path.name}"] = read_text(path)
    for name in documents:
        texts[name] = layout.document(name)
    for pattern in sources:
        for path in sorted(layout.root.glob(pattern)):
            texts[path.relative_to(layout.root).as_posix()] = read_text(path)
    return texts


def claim_problems(
    layout: Layout,
    claims: Iterable[Claim],
    searched: Mapping[str, str] | None = None,
) -> list[str]:
    """One fact, one wording - in every place that states it.

    `searched` is everywhere a superseded wording could be hiding, as {place: text}; build it
    with `claim_texts`. Without it only the places the claims themselves name are searched,
    which still catches the copy that kept living but not the new page that copied it.

    A place a claim names and the repository has not got is a finding of its own: a renamed file
    must not quietly turn a claim into a check of nothing.
    """
    claims = tuple(claims)
    problems: list[str] = []
    for claim in claims:
        for where in claim.told_in:
            text = claim_text(layout, where)
            if text is None:
                problems.append(
                    f'{where}: the claim "{claim.name}" names a place that is not in the '
                    "repository"
                )
                continue
            if not any(word.lower() in text.lower() for word in claim.wording):
                problems.append(
                    f'{where}: the claim "{claim.name}" is stated everywhere else and not here '
                    f"- say it in the words the other places use ({', '.join(claim.wording)})"
                )
    if searched is None:
        searched = {
            where: claim_text(layout, where) or ""
            for claim in claims for where in claim.told_in
        }
    for where, text in searched.items():
        lowered = text.lower()
        for claim in claims:
            for phrase in claim.retired:
                if phrase.lower() in lowered:
                    problems.append(
                        f'{where}: "{phrase}" is the superseded wording of the claim '
                        f'"{claim.name}" - the correction did not reach here'
                    )
    return problems
