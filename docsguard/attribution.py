r"""Text that credits a person for a change, where what the reader needs is the change itself.

These repositories have one author, and that author is the owner. So a sentence saying that
the owner asked for something, decided something or caught something tells the reader nothing
they can act on, and tells them one thing that is not true: that the code was written for
somebody else. "The rule is on by default because the owner's call is the opposite" leaves a
reader with a person to believe. "The rule is on by default because what the platform
documents as a convention is a standard" leaves them with the reason.

Three of those sentences were found by hand in one repository in one day, in the docstrings of
its tests, and they had been read past in review for weeks. That is what this is for.

What is caught is a TURN OF PHRASE rather than a word, and there is no choice about it.
"owner" and "владелец" are words of the subject these repositories are about: a metadata object
has an owner, the translation dictionary has an owner table, a form is generated under the
owner that holds it. A guard that reported the word would report all of that, and a guard that
reports the legitimate text of the day is switched off by the end of the week.

So a finding needs two halves. Either a possessive beside a noun of deciding or asking - the
owner's call, the owner's decision, at the owner's request, по решению владельца - or the word
beside a verb of speaking or judging: the owner said, the owner caught, владелец попросил. One
half alone is the subject talking; both halves together are a person being credited.

The gap between the halves is where a check like this goes wrong. "The owner could not read
them" needs two words of room, and giving the room away to ANY two words turns "the owner table
is read first" into a finding. So the English gap is a closed list - a modal, a negation, an
adverb - and a noun in the gap ends the match. That single decision is what keeps the owner
table, the owner-object attributes and `А.Владелец.ПометкаУдаления` quiet.

The check reads pages and sources through the same judge, and a source is read as text rather
than parsed. The jargon dictionary next door parses, because it looks for ONE word and a word
can be spelled across two literals written side by side. A turn of phrase is several words with
spaces in them, and spaces are what source code has least of: `owner.said()` has a dot where
the turn needs a space, and `{"owner": "said"}` has a quote and a colon. Reading the text also
reaches the place these sentences actually live - a comment, which no parser hands back at all.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .jargon import empty_exceptions, without_code
from .layout import Layout, read_text
from .pages import docs_pages


@dataclass(frozen=True)
class AttributionTurn:
    """One turn of phrase that credits a person, and what to write in its place.

    name    - the turn as a repository names it to switch the row off, written the way it
              reads in a sentence, so an exception at a call site says what is being allowed.
    pattern - the regular expression of the whole turn, both halves and the gap between them.
              The edges of a word are the pattern's own business here: half of these turns end
              in a Russian verb and half in an English noun.
    instead - what a finding asks for instead.
    """

    name: str
    pattern: str
    instead: str


#: The nouns that turn a possessive into an act of deciding or of asking. Six of them, and the
#: list is short for the same reason the gap is closed: every noun added to it is one more way
#: to report a sentence about an owner OBJECT. "The choices follow the owner's kind" is real
#: text from one of these repositories and has to stay quiet, and it does - the noun after the
#: possessive is "kind".
_DECIDED_EN = r"(?:call|decision|request|ask|choice|verdict)s?"

#: The verbs of speaking and of judging. A verb that a machine can also be the subject of is
#: deliberately missing: "calls" is what code does to a function, "objects" is a plural noun in
#: half the sentences of this family, and "returns" belongs to a method.
#:
#: "decides" went the same way, and it went after the list met the sources rather than before.
#: One repository writes "there the owner decides, and the owner is what we just failed to
#: find" about a TYPE, and that sentence is correct as it stands. The present tense describes
#: a mechanism, so it stays out; "decided" narrates what somebody once did, so it stays in.
_SAID_EN = (r"(?:said|says|asked|asks|wants|wanted|caught|catches|decided"
            r"|noticed|notices|read|reads|complained|complains|insisted|insists)")

#: What may stand between the word and the verb: a modal, a negation, an adverb. A CLOSED list,
#: and that is the whole difference between a check that finds "the owner could not read them"
#: and one that reports "the owner table is read first". "is" and "are" are not here on
#: purpose: they are how a sentence about an object goes on - the owner IS read, IS called, IS
#: asked for - and letting them in would hand the check every passive sentence in the sources.
_GAP_EN = (r"(?:could|can|would|will|should|might|must|did|does|do|has|have|had|never|not"
           r"|also|then|just|again|already|once|finally|exactly|later|still|since|himself"
           r"|personally|[a-z]+n't)")

#: The Russian nouns of a decision and of a request, by their stems: решение, решения, решению,
#: решением, просьба, просьбе, указание, замечания. The ending is left to the reader, because a
#: Russian noun arrives in six cases and writing them out invites the one that was forgotten.
_DECIDED_RU = r"(?:решени|просьб|указани|замечани)[а-яё]{0,3}"

#: The Russian verbs of speaking and of judging. Masculine singular only - the word they stand
#: beside is "владелец", and it has no other form to agree with.
_SAID_RU = (r"(?:сказал|говорил|говорит|попросил|просил|поймал|решил|решает|заметил"
            r"|замечает|потребовал|требует|хочет|хотел|захотел|велел|указал|отметил"
            r"|прочитал|прочёл|счёл|считает|подтвердил|назвал)")

#: The Russian gap: a negation, an adverb, a particle.
_GAP_RU = r"(?:не|уже|тогда|сам|потом|снова|ещё|именно|сразу|позже|наконец|так|же|бы|всё)"

#: The turns, two per edition. Four rows and not forty: a row here is a SHAPE of sentence, and
#: the words that fill the shape live in the five lists above, where a new verb is one word
#: rather than one more row to keep in step with the README.
ATTRIBUTION: tuple[AttributionTurn, ...] = (
    AttributionTurn(
        "owner's decision",
        rf"owner(?:'|\u2019)s\s+(?:\w+\s+){{0,2}}{_DECIDED_EN}\b",
        "what the decision changed, not whose it was",
    ),
    AttributionTurn(
        "the owner said",
        rf"\bowner\b\s+(?:{_GAP_EN}\s+){{0,2}}{_SAID_EN}\b",
        "what the behaviour or the text got wrong, not who noticed it",
    ),
    AttributionTurn(
        "решение владельца",
        rf"{_DECIDED_RU}\s+(?:[а-яё]+\s+){{0,2}}владельца\b",
        "what the decision changed, not whose it was",
    ),
    AttributionTurn(
        "владелец сказал",
        rf"владелец\s+(?:{_GAP_RU}\s+){{0,2}}{_SAID_RU}"
        rf"|{_SAID_RU}\s+(?:{_GAP_RU}\s+){{0,2}}владелец\b",
        "what the behaviour or the text got wrong, not who noticed it",
    ),
)


@lru_cache(maxsize=None)
def _reader(pattern: str) -> re.Pattern[str]:
    """The compiled reader of one turn, case-blind: a sentence may open with either half."""
    return re.compile(pattern, re.IGNORECASE)


def _prose(text: str, *, fenced: bool = True) -> str:
    """The text with the identifiers blanked out, ready to be judged as prose.

    The blanking is the jargon dictionary's, and for the same two reasons: a turn inside
    backticks is being quoted rather than written, and blanking in place keeps every line where
    it was, so a finding names a line a reader can open.

    `fenced` is what a page has and a source has not. A fenced block spans lines, so a page is
    blanked whole. A source is blanked line by line, because the backticks in its comments are
    not balanced by anything: one stray backtick in a file pairs with the next one further
    down, and everything between them is blanked as if it were code. That is not a theory -
    it is how one of the three sentences this check was written for stayed hidden while the
    other two were found.
    """
    if fenced:
        return without_code(text)
    return "\n".join(without_code(line) for line in text.split("\n"))


def _found(
    text: str,
    *,
    allow: Iterable[str] = (),
    turns: Iterable[AttributionTurn] = ATTRIBUTION,
    fenced: bool = True,
) -> list[tuple[int, AttributionTurn, str]]:
    """Every credited turn of one text as (line, row, the words), in the order they are written."""
    allowed = set(allow)
    prose = _prose(text, fenced=fenced)
    found: list[tuple[int, AttributionTurn, str]] = []
    for turn in turns:
        if turn.name in allowed:
            continue
        for match in _reader(turn.pattern).finditer(prose):
            found.append((match.start(), turn, match.group(0)))
    return [(prose.count("\n", 0, at) + 1, turn, written)
            for at, turn, written in sorted(found, key=lambda item: item[0])]


def attribution_findings(
    text: str,
    where: str,
    *,
    allow: Iterable[str] = (),
    turns: Iterable[AttributionTurn] = ATTRIBUTION,
    fenced: bool = True,
) -> list[str]:
    """The credited turns of one text, each finding carrying the line and the words written.

    The words are quoted as the text writes them, whole turn and all, because that is what a
    writer has to rewrite. Quoting the row name instead would send them looking for a phrase
    that is not on the page. A turn that ran over a line break is quoted on one line all the
    same: a finding that breaks in half is a finding that gets skipped.

    `fenced` says whether the text is a page, whose code blocks span lines, or a source, whose
    backticks are balanced by nothing at all. The source entry below turns it off; what goes
    wrong when it is left on is written where the blanking is.
    """
    return [f'{where}:{line}: "{" ".join(written.split())}" credits a person for the change - '
            f"write {turn.instead}"
            for line, turn, written in _found(text, allow=allow, turns=turns, fenced=fenced)]


#: The pages this check reads unless a repository says otherwise: every page, both editions.
#: The jargon dictionary next door reads the Russian half alone, because its words are English
#: to begin with. This one has a row for each edition, and the English edition is where two of
#: the three sentences that started it were written.
BOTH_EDITIONS = ("*.md",)


def attribution_problems(
    layout: Layout,
    *,
    pages: Iterable[str] = BOTH_EDITIONS,
    documents: Iterable[str] = (),
    allow: Iterable[str] = (),
    turns: Iterable[AttributionTurn] = ATTRIBUTION,
) -> list[str]:
    """Every credited turn in the documentation of one repository, in both editions.

    pages     - glob patterns inside the documentation folder.
    documents - documents at the root by name: the READMEs, the changelogs, the contributing
                notes. The same file reached both ways is read once.
    allow     - the rows this repository switches off, by name. A name no row carries is a
                finding of its own, the way it is for the dictionary next door.
    """
    rows = tuple(turns)
    allowed = tuple(allow)
    problems = empty_exceptions(allowed, rows, what="table of turns")

    texts: dict[str, str] = {}
    for path in docs_pages(layout, pages):
        texts[path.relative_to(layout.root).as_posix()] = read_text(path)
    for name in documents:
        if name not in texts:
            texts[name] = layout.document(name)

    for where, text in texts.items():
        problems += attribution_findings(text, where, allow=allowed, turns=rows)
    return problems


#: The sources this check reads unless a repository names others. Python by default, because
#: two of these three repositories are written in it; the third passes `*.java` beside it.
SOURCE_FILES = ("*.py",)


def prose_sources(layout: Layout, folders: Iterable[str],
                  patterns: Iterable[str] = SOURCE_FILES) -> list[Path]:
    """Every source of the named folders that matches one of the patterns, in a stable order.

    Folders rather than a list of files, which is where this parts company with the jargon
    check: there the Russian a person reads is one message catalog per repository, and naming
    the rest would judge identifiers. A comment explaining a decision can be written in any
    file there is, so the whole tree is read and the shape of the turn does the narrowing.
    """
    found: list[Path] = []
    for folder in folders:
        for pattern in patterns:
            found.extend(sorted((layout.root / folder).rglob(pattern)))
    return sorted(set(found))


def source_attribution_problems(
    layout: Layout,
    folders: Iterable[str],
    *,
    patterns: Iterable[str] = SOURCE_FILES,
    allow: Iterable[str] = (),
    turns: Iterable[AttributionTurn] = ATTRIBUTION,
) -> list[str]:
    """Every credited turn in the comments, docstrings and strings of one repository's sources.

    folders  - the folders to read, by path from the root.
    patterns - the file names to read inside them; `*.py` unless a repository writes its
               comments in another language as well.

    A named folder that is not there is a finding rather than silence. A folder that has been
    renamed leaves this check walking an empty tree and passing, which is the failure this
    package exists to make impossible.
    """
    rows = tuple(turns)
    allowed = tuple(allow)
    problems = empty_exceptions(allowed, rows, what="table of turns")
    for folder in folders:
        if not (layout.root / folder).is_dir():
            problems.append(f"{folder}: the folder is named for the attribution check and is "
                            "not there - has it been renamed?")
    for path in prose_sources(layout, folders, patterns):
        problems += attribution_findings(read_text(path),
                                         path.relative_to(layout.root).as_posix(),
                                         allow=allowed, turns=rows, fenced=False)
    return problems


#: The sentences that have to be found, each beside the row that has to find it. The first
#: seven are not written for the samples: they are the sentences that were in the repositories
#: of this family, and the reason the check exists.
CREDITED: tuple[tuple[str, str], ...] = (
    ("An Unreleased buffer holds work merged ahead of the owner's release call.",
     "owner's decision"),
    ("It used to be off and info. The owner's call is the opposite.", "owner's decision"),
    ("The rule was turned on by the owner's decision of 17 July.", "owner's decision"),
    ("A second heading of the same day splits the section (the owner caught exactly that).",
     "the owner said"),
    ("The lines ran together, so the owner could not read them.", "the owner said"),
    ("The entries were written in transliteration and the owner said so.", "the owner said"),
    ("The column was dropped at the owner's request.", "owner's decision"),
    ("Правило включено по решению владельца.", "решение владельца"),
    ("Решение владельца: так и задумано.", "решение владельца"),
    ("Столбец убран по просьбе владельца.", "решение владельца"),
    ("Замечание владельца записано в задаче.", "решение владельца"),
    ("Владелец сказал, что читать это тяжело.", "владелец сказал"),
    ("Владелец попросил убрать столбец.", "владелец сказал"),
    ("Так решил владелец, и запись об этом осталась.", "владелец сказал"),
)

#: The sentences that have to stay quiet. Three kinds, and each kind is a way this check could
#: have been written wrong. The first is the subject itself - an owner in these repositories is
#: a metadata object, a table of the translation dictionary, the element a form is generated
#: under - and every sentence of that kind here is real text from one of them. The second is
#: the passive voice, where a sentence about an object walks right past a verb of speaking. The
#: third is the way the same thing reads once the person is out of it.
IMPERSONAL: tuple[str, ...] = (
    "The owner table of the translation dictionary is read first.",
    "The owner-object attributes are copied into the generated form.",
    "The choices follow the owner's kind: object and list for data objects.",
    "Which forms are offered depends on the owner's kind.",
    "The generator registers the form in the owner's Interface by itself.",
    "Pass force=true - the owner's explicit override - and the method is deleted.",
    "The owner is read from the file beside it, and the guess is confirmed afterwards.",
    "A member several types declare is answered with the owners to choose from.",
    "Language data belongs to its respective owners, see the notice.",
    "Уникальность `Ид` проверяется в пределах владельца.",
    "Ссылка владельца у объекта метаданных заполняется сама.",
    "Таблица владельца в словаре переводов читается первой.",
    "`А.Владелец.ПометкаУдаления` записывается как есть.",
    "Реквизиты владельца показаны на панели данных.",
    "An Unreleased buffer holds work merged before a release is called.",
    "It used to be off and info. The call went the other way.",
    "The lines ran together and the page could not be read.",
    "Правило включено: то, что платформа описывает как соглашение, это стандарт.",
    "Прежний текст объяснял решение ссылкой на человека, и причина в нём терялась.",
)


def attribution_self_check(
    turns: Iterable[AttributionTurn] = ATTRIBUTION,
) -> list[str]:
    """Prove the table on the samples, and say so as findings.

    A pattern is one careless edit away from silence: a verb drops out of a list, a gap loses a
    word, and the check goes on passing every page ever written. The samples answer that, and
    they run beside the pages rather than in the test suite alone, so a repository that pinned
    a version of this package is told the same thing.
    """
    rows = tuple(turns)
    by_name = {turn.name: turn for turn in rows}
    problems: list[str] = []
    for sentence, name in CREDITED:
        if name not in by_name:
            problems.append(f"the sample {sentence!r} names the row {name} and there is no "
                            "such row in the table of turns")
            continue
        if not _found(sentence, turns=(by_name[name],)):
            problems.append(f"the sample {sentence!r} credits a person by the row {name} and "
                            "the table reads straight past it")
    for sentence in IMPERSONAL:
        for _, turn, written in _found(sentence, turns=rows):
            problems.append(f"the sample {sentence!r} names nobody and the row {turn.name} "
                            f'found "{written}" in it')
    return problems
