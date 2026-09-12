r"""Jargon in the Russian documentation - the transliterated word that has a Russian one.

The documentation of this family of repositories comes in two editions, and the Russian one
keeps drifting into transliterated English. A changelog entry says that a "пин" was raised
after a "прогон", and the reader has to translate both back before the sentence means anything.
A word like that is invisible to the person writing it, because it is the word that person says
out loud all day, so a review does not catch it either. A dictionary does.

Every row is one word: the root it is recognized by, the name a repository switches the row off
by, and the Russian to write instead. The root is ONE regular expression and covers the forms,
because a Russian word arrives in six cases and two numbers, and a list of forms written out by
hand goes stale the moment a participle turns up.

An identifier is not jargon. `pipeline` in backticks is the name of a thing, a fenced block is
code, a link target is an address and a file name is a file name, so all of them are blanked out
before the dictionary reads a page. Blanked rather than cut: the blanks hold the line numbers,
and a finding names the line a reader will open.

The traps are inside Russian words themselves. "пин" sits in "пингвин" and in "шпингалет",
"билд" in "билдер", "фикс" in "префикс" and in "фиксация". That is why a root carries its own
endings instead of a blanket `\w*` wherever an ending could grow into another word, and why the
module proves itself before it judges anybody: `jargon_self_check` runs the dictionary over
sentences that have to be found and sentences that have to stay quiet.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .layout import Layout


@dataclass(frozen=True)
class JargonWord:
    """One row of the dictionary: a word not to write, and what to write in its place.

    name    - the row as a repository names it to switch the row off; the jargon word itself,
              so that an exception in a consumer reads as a sentence.
    root    - the regular expression that recognizes the word, its endings included. The edges
              of the word are added by the reader, so a root says nothing about them.
    instead - the Russian a finding offers instead.
    """

    name: str
    root: str
    instead: str


#: The dictionary. Rows in the order of the writing rules these repositories keep, so that the
#: two can be read side by side. A root with a blanket `\w*` is a root that grows into no other
#: Russian word; the rest carry their endings, because "пин" with a free tail eats "пингвин".
#:
#: The dictionary got shorter on 12 September 2026. The owner read it and kept the words that
#: stop him mid-sentence. Eleven others, "фича" and "джоба" among them, he reads without
#: translating, so their rows are gone. Putting one back takes the same decision from him.
JARGON: tuple[JargonWord, ...] = (
    JargonWord(
        "пин",
        r"пин(?:а|у|е|ом|ы|ов|ам|ами|ах)?"
        r"|(?:за|при)?пин(?:ить|ит|ят|ую|уют|ует|ил|ила|или|ен|ена|ены)",
        "закреплённая версия, версия закреплена меткой, поднять версию",
    ),
    JargonWord(
        "прогон",
        r"прогон(?:а|у|е|ом|ы|ов|ам|ами|ах)?"
        r"|прогна(?:ть|л|ла|ли|н|на|но|ны)"
        r"|прогоня(?:ть|ет|ют|ем|ешь|ется|ются|л|ла|ли|лся)",
        "запуск, проверка (о CI - проверки, сборка на CI)",
    ),
    JargonWord("базлайн", r"(?:баз|бейз)лайн\w*", "список принятых замечаний"),
    JargonWord("хук", r"хук(?:а|у|е|ом|и|ов|ам|ами|ах)?", "обработчик, перехватчик"),
    JargonWord("фолбэк", r"фол{1,2}б[эе]к\w*", "запасной путь"),
    JargonWord("фикс", r"фикс(?:а|у|е|ом|ы|ов|ам|ами|ах)?|(?:за|по)?фиксить", "исправление"),
    JargonWord("билд", r"билд(?:а|у|е|ом|ы|ов|ам|ами|ах)?|билдить", "сборка"),
    JargonWord("дефолт", r"дефолт\w*", "значение по умолчанию, по умолчанию"),
    JargonWord("эксепшн", r"эксепше?н\w*", "исключение"),
    JargonWord("апдейт", r"ап-?дейт\w*", "обновление"),
    JargonWord("скоуп", r"скоуп\w*", "область"),
    JargonWord("ворктри", r"ворктри\w*", "рабочее дерево (сама команда остаётся `git worktree`)"),
)

#: The spans of a page that are identifiers rather than prose: a fenced block, an inline code
#: span of any number of backticks, the target of a link or an image, an autolink, a bare
#: address, a reference definition, a file name. `pipeline`, `baseline` and `--as-ci-job` are
#: the names of things and stay exactly as they are written.
_NOT_PROSE = re.compile(
    r"```[\s\S]*?(?:```|\Z)"
    r"|~~~[\s\S]*?(?:~~~|\Z)"
    r"|(?P<ticks>`+)[\s\S]*?(?P=ticks)"
    r"|\]\([^)]*\)"
    r"|<https?://[^>\s]+>"
    r"|https?://\S+"
    r"|^[ \t]*\[[^\]]+\]:[ \t]*\S+"
    r"|[\w./\\-]*\w\.(?:md|py|ts|js|json|toml|yml|yaml|cfg|ini|txt|xbsl|png|svg)\b",
    re.M,
)


def without_code(text: str) -> str:
    """The text with every identifier blanked out, line by line and column by column.

    A span that is not prose becomes the same number of blanks, so nothing moves: the line a
    finding names is the line a reader opens, and a word half inside backticks cannot be glued
    to the word after them.
    """
    return _NOT_PROSE.sub(lambda span: re.sub(r"[^\n]", " ", span.group(0)), text)


@lru_cache(maxsize=None)
def _reader(root: str) -> re.Pattern[str]:
    """The compiled reader of one root, held between the edges of a word.

    Both edges are a letter test rather than `\\b`, and that is what makes "шпингалет" silent
    and "билд-сервер" a finding: a letter before the root means the root is somebody else's
    tail, while a hyphen after it is simply where the word ends.
    """
    return re.compile(rf"(?<!\w)(?:{root})(?!\w)", re.IGNORECASE)


def _found(
    text: str,
    *,
    allow: Iterable[str] = (),
    dictionary: Iterable[JargonWord] = JARGON,
) -> list[tuple[int, JargonWord, str]]:
    """Every jargon word of one text as (line, row, the word), in the order they are written."""
    allowed = set(allow)
    prose = without_code(text)
    found: list[tuple[int, JargonWord, str]] = []
    for word in dictionary:
        if word.name in allowed:
            continue
        for match in _reader(word.root).finditer(prose):
            found.append((match.start(), word, match.group(0)))
    return [(prose.count("\n", 0, at) + 1, word, written)
            for at, word, written in sorted(found, key=lambda item: item[0])]


def jargon_findings(
    text: str,
    where: str,
    *,
    allow: Iterable[str] = (),
    dictionary: Iterable[JargonWord] = JARGON,
) -> list[str]:
    """The jargon of one text, each finding carrying the line, the word and what to write.

    The word is quoted the way the page writes it rather than in its dictionary form. A writer
    looking for "прогонах" finds it; a writer looking for "прогон" reads the page twice.
    """
    return [f'{where}:{line}: "{written}" is jargon - write {word.instead}'
            for line, word, written in _found(text, allow=allow, dictionary=dictionary)]


#: The pages a jargon check reads unless a repository says otherwise: the Russian edition of
#: every page. The English edition is left alone - the words of the dictionary are English to
#: begin with, and there they are the right ones.
RUSSIAN_PAGES = ("*.ru.md",)


def russian_pages(layout: Layout, patterns: Iterable[str] = RUSSIAN_PAGES) -> list[Path]:
    """The Russian pages of a repository, in a stable order."""
    found: list[Path] = []
    for pattern in patterns:
        found.extend(sorted(layout.docs.glob(pattern)))
    return found


def jargon_problems(
    layout: Layout,
    *,
    pages: Iterable[str] = RUSSIAN_PAGES,
    documents: Iterable[str] = (),
    allow: Iterable[str] = (),
    dictionary: Iterable[JargonWord] = JARGON,
) -> list[str]:
    """Every jargon word of the Russian documentation of one repository.

    pages     - glob patterns inside the documentation folder.
    documents - Russian documents at the root by name: the README, the changelog, the
                contributing notes. A repository whose pages ARE those documents names them
                once; the same file read twice is reported once.
    allow     - the rows this repository switches off, by name. A word the subject really
                needs is a word the guard has no business with, and there the exception belongs
                to the repository that has the subject. A name no row carries is a finding of
                its own: an exception that guards nothing looks exactly like one that works.
    """
    rows = tuple(dictionary)
    allowed = tuple(allow)
    problems = [
        f'"{name}" is switched off and the dictionary has no such row - '
        "the exception guards nothing now"
        for name in sorted(set(allowed) - {word.name for word in rows})
    ]

    texts: dict[str, str] = {}
    for path in russian_pages(layout, pages):
        texts[path.relative_to(layout.root).as_posix()] = path.read_text(encoding="utf-8")
    for name in documents:
        if name not in texts:
            texts[name] = layout.document(name)

    for where, text in texts.items():
        problems += jargon_findings(text, where, allow=allowed, dictionary=rows)
    return problems


#: The sentences the dictionary has to find, each beside the row that has to find it. Not one
#: of them is there to show that jargon is caught at all: each is a form that an obvious root
#: reads past - a verb, a plural, a word glued to a Russian tail with a hyphen.
CAUGHT: tuple[tuple[str, str], ...] = (
    ("Пин поднимают до свежего тега.", "пин"),
    ("Тег, который они пинуют, устарел.", "пин"),
    ("Красный прогон никто не читает.", "прогон"),
    ("Правку прогнали по трём репозиториям.", "прогон"),
    ("Базлайн пополнился за неделю.", "базлайн"),
    ("Хуки стоят перед коммитом.", "хук"),
    ("Фолбэк на прежний адрес.", "фолбэк"),
    ("Фикс уехал в релиз.", "фикс"),
    ("Билд-сервер снова занят.", "билд"),
    ("По дефолту стоит ноль.", "дефолт"),
    ("Эксепшен доходит до пользователя.", "эксепшн"),
    ("Апдейтить придётся оба.", "апдейт"),
    ("Скоуп правки шире.", "скоуп"),
    ("Ворктри на каждую задачу.", "ворктри"),
)

#: The sentences that have to stay quiet. Four kinds, and each kind is a way the check could
#: have been written wrong: a root sitting inside an innocent Russian word, an identifier the
#: page quotes on purpose, the Russian the dictionary itself asks for, and a word the owner
#: allowed. The last two sentences were findings until 12 September 2026. Put one of those rows
#: back and the self-check reports them again.
QUIET: tuple[str, ...] = (
    "Пингвин отпер шпингалет, пинг прошёл.",
    "Билдер собирает страницу, префикс остаётся.",
    "Фиксация правки и её фиксирование - обычные слова.",
    "Версия закреплена меткой, проверки прошли, задача конвейера зелёная.",
    "Ставим `пин` и `--as-ci-job` как есть - это имена.",
    "```\nпрогон\n```",
    "Ссылка на [страницу](docs/прогон.ru.md) ведёт куда следует.",
    "Файл прогон.md называется так и никак иначе.",
    "Фичу отложили до следующей недели.",
    "Смоук-тест после выкладки прошёл.",
)


def jargon_self_check(dictionary: Iterable[JargonWord] = JARGON) -> list[str]:
    """Prove the dictionary on the samples, and say so as findings.

    A dictionary is one careless edit away from silence: a root loses a letter, an ending goes
    missing, and the check keeps passing every page ever written. The samples are the answer,
    and they run beside the pages rather than in the test suite alone, so that a repository
    which pinned a version of this package is told the same thing.
    """
    rows = tuple(dictionary)
    by_name = {word.name: word for word in rows}
    problems: list[str] = []
    for sentence, name in CAUGHT:
        if name not in by_name:
            problems.append(f"the sample {sentence!r} names the row {name} and there is no "
                            "such row in the dictionary")
            continue
        if not _found(sentence, dictionary=(by_name[name],)):
            problems.append(f"the sample {sentence!r} is jargon of the row {name} and the "
                            "dictionary reads straight past it")
    for sentence in QUIET:
        for _, word, written in _found(sentence, dictionary=rows):
            problems.append(f"the sample {sentence!r} is clean and the row {word.name} found "
                            f'"{written}" in it')
    return problems
