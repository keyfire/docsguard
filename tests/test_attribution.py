"""The table of turns: the sentences that credit a person, and everything it has to leave alone.

Leaving alone is the harder half here, harder than it is for the dictionary next door. An owner
in these repositories is a metadata object with attributes, a table of the translation
dictionary, the element a form is generated under - so most of the provocations below are real
sentences taken out of the three repositories the package serves, and every one of them has to
stay quiet. The three that have to be FOUND are real as well: they were written in the
docstrings of one repository's tests, found by hand, and are the reason this exists.

The sources are judged through the same table and have their own way of going wrong, so they
have their own provocations at the bottom: a comment, which no parser hands back, and a file
whose backticks do not pair up.
"""

import codecs
from pathlib import Path

import pytest

from docsguard import (
    ATTRIBUTION,
    AttributionTurn,
    Layout,
    attribution_findings,
    attribution_problems,
    attribution_self_check,
    prose_sources,
    source_attribution_problems,
)


@pytest.fixture()
def layout(tmp_path: Path) -> Layout:
    (tmp_path / "docs").mkdir()
    return Layout(root=tmp_path)


def test_the_table_proves_itself_on_its_own_samples():
    """The samples inside the module: awake on one set of sentences, silent on the other."""
    assert attribution_self_check() == []


def test_a_credited_turn_is_found_with_its_line_and_what_to_write_instead():
    text = "Первая строка.\nПравило включено по решению владельца.\n"

    found = attribution_findings(text, "index.ru.md")

    assert len(found) == 1
    assert found[0].startswith('index.ru.md:2: "решению владельца" credits a person')
    assert "what the decision changed" in found[0]


def test_the_turn_is_quoted_the_way_the_text_writes_it():
    """A writer searches the page for what the finding shows, not for a row name."""
    found = attribution_findings("The column was dropped at the owner's request.", "index.md")

    assert '"owner\'s request"' in found[0]


def test_a_turn_that_ran_over_a_line_break_is_quoted_on_one_line():
    """A finding that breaks in half is a finding that gets skipped."""
    found = attribution_findings("It used to be off. The owner's\n    call is the opposite.",
                                 "index.md")

    assert len(found) == 1
    assert '"owner\'s call"' in found[0]
    assert "\n" not in found[0]


#: The sentences this check was written for, as they were written. All three were in the
#: docstrings of one repository's tests and were found by hand on one day.
BY_HAND = (
    "An `## Unreleased` buffer may sit on top between releases - work merged ahead of the\n"
    "owner's release call lives there until the tag renames it.",
    "It used to be off and `info`: the group was treated as accumulated debt. The owner's\n"
    "call is the opposite.",
    "A second `### Added` under the same heading splits what a reader expects to see in one\n"
    "place (the owner caught exactly that).",
)


@pytest.mark.parametrize("sentence", BY_HAND)
def test_the_sentences_that_were_found_by_hand_are_found_here(sentence):
    """Three of them in one day, in a repository nobody was reading with a guard."""
    assert len(attribution_findings(sentence, "test_something.py", fenced=False)) == 1


@pytest.mark.parametrize("domain", [
    # Real sentences from the repositories this package serves. An owner there is a thing.
    "The owner table of the translation dictionary is read first.",
    "The owner-object attributes are copied into the generated form.",
    "Which forms are offered depends on the owner's kind.",
    "The choices follow the owner's kind: object and list for data objects.",
    "The generator registers the form in the owner's Interface by itself.",
    "Pass force=true - the owner's explicit override - and the method is deleted.",
    "Language data belongs to its respective owners, see the notice.",
    "There the owner decides, and the owner is what we just failed to find.",
    "Уникальность `Ид` проверяется в пределах владельца.",
    "Ссылка владельца у объекта метаданных заполняется сама.",
    "Реквизиты объекта-владельца показаны на панели данных.",
    "Формы регистрируются в `Интерфейс` владельца.",
])
def test_the_subject_of_these_repositories_is_not_a_person(domain):
    """An owner is a metadata object here, and a guard that says otherwise gets switched off."""
    assert attribution_findings(domain, "index.md") == []


@pytest.mark.parametrize("passive", [
    "The owner is read from the file beside it.",
    "The owner is asked for by name.",
    "The owner was noticed missing and the guess was dropped.",
    "The owner table is read before the names are.",
])
def test_the_passive_voice_of_a_sentence_about_an_object_is_silence(passive):
    """"is" and "are" are how a sentence about a thing goes on, so they close the gap."""
    assert attribution_findings(passive, "index.md") == []


def test_the_gap_holds_a_modal_and_a_negation_and_nothing_else():
    """"could not read" is two words of room; a noun in the same room is another sentence."""
    assert len(attribution_findings("The lines ran together, so the owner could not read them.",
                                    "index.md")) == 1
    assert attribution_findings("The owner table can be read from the yaml.", "index.md") == []


@pytest.mark.parametrize("credited, instead", [
    ("The rule went on by the owner's decision of 17 July.", "what the decision changed"),
    ("The column was dropped at the owner's request.", "what the decision changed"),
    ("The owner asked for the column back.", "what the behaviour or the text got wrong"),
    ("The owner wants the rule on by default.", "what the behaviour or the text got wrong"),
    ("Столбец убран по просьбе владельца.", "what the decision changed"),
    ("Замечание владельца записано в задаче.", "what the decision changed"),
    ("Владелец попросил убрать столбец.", "what the behaviour or the text got wrong"),
    ("Так решил владелец, и запись об этом осталась.",
     "what the behaviour or the text got wrong"),
])
def test_both_shapes_are_found_in_both_editions(credited, instead):
    """A possessive beside a noun of deciding, or the word beside a verb of speaking."""
    found = attribution_findings(credited, "index.md")

    assert len(found) == 1 and instead in found[0]


@pytest.mark.parametrize("quoted", [
    "Оборот `по решению владельца` называется так и никак иначе.",
    "```\nthe owner said\n```",
    "Ссылка на [страницу](docs/решение-владельца.md) ведёт куда следует.",
])
def test_a_quotation_is_not_a_sentence(quoted):
    """Backticks, a fenced block and a link target are how a page quotes the rule itself."""
    assert attribution_findings(quoted, "index.md") == []


def test_both_editions_of_the_pages_are_read(layout):
    """The jargon dictionary reads the Russian half; two of these three sentences were English."""
    (layout.docs / "index.ru.md").write_text("Правило включено по решению владельца.\n",
                                             encoding="utf-8")
    (layout.docs / "index.md").write_text("The rule went on at the owner's request.\n",
                                          encoding="utf-8")

    problems = attribution_problems(layout)

    assert len(problems) == 2
    assert any(problem.startswith("docs/index.md:") for problem in problems)
    assert any(problem.startswith("docs/index.ru.md:") for problem in problems)


def test_a_root_document_is_read_by_name(layout):
    (layout.root / "CHANGELOG.md").write_text("The owner asked for the column back.\n",
                                              encoding="utf-8")

    problems = attribution_problems(layout, documents=("CHANGELOG.md",))

    assert len(problems) == 1 and problems[0].startswith("CHANGELOG.md:1:")


def test_the_same_file_reached_twice_is_reported_once(tmp_path: Path):
    """A repository whose pages ARE its root documents reaches the same file both ways."""
    (tmp_path / "README.md").write_text("The owner wants it the other way.\n", encoding="utf-8")

    problems = attribution_problems(Layout(root=tmp_path, docs=tmp_path),
                                    documents=("README.md",))

    assert len(problems) == 1


def test_a_repository_switches_off_a_turn_by_name():
    text = "The owner asked for it, and по решению владельца it stays."

    assert len(attribution_findings(text, "index.md")) == 2
    assert len(attribution_findings(text, "index.md", allow=("the owner said",))) == 1
    assert attribution_findings(
        text, "index.md", allow=("the owner said", "решение владельца")) == []


def test_switching_off_a_turn_that_is_in_no_row_is_a_finding(layout):
    """An exception that guards nothing looks exactly like one that works."""
    (layout.docs / "index.md").write_text("Clean text.\n", encoding="utf-8")

    problems = attribution_problems(layout, allow=("the owner sang",))

    assert len(problems) == 1
    assert "the owner sang" in problems[0] and "table of turns" in problems[0]


def test_a_repository_may_bring_a_table_of_its_own():
    """The rows are data. A repository with a turn of its own adds a row, not a check."""
    own = (AttributionTurn("the boss", r"\bthe boss\b", "what the change fixes"),)

    assert attribution_findings("The boss wanted it green.", "index.md", turns=own)
    assert attribution_findings("The owner asked for it.", "index.md", turns=own) == []


def test_every_row_carries_a_name_a_pattern_and_what_to_write():
    """A row missing one of the three cannot be switched off, or acted on, or both."""
    for turn in ATTRIBUTION:
        assert turn.name and turn.pattern and turn.instead, turn

    assert len({turn.name for turn in ATTRIBUTION}) == len(ATTRIBUTION)


#: A source the way these repositories write one: the sentence lives in a docstring, in a
#: comment, and in the message a command prints - three places, one file.
SOURCE = '''\
"""The release card of the newest version.

An Unreleased buffer holds work merged ahead of the owner's release call.
"""

# The rule is on by default: the owner's call is the opposite.

MESSAGE = "Столбец убран по просьбе владельца."
'''


def test_a_docstring_a_comment_and_a_message_are_all_read(tmp_path: Path):
    """The comment is why this reads text: no parser hands one back at all."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "relnotes.py").write_text(SOURCE, encoding="utf-8")

    problems = source_attribution_problems(Layout(root=tmp_path), ("tools",))

    assert len(problems) == 3
    assert [problem.split(":")[1] for problem in problems] == ["3", "6", "8"]


def test_a_source_is_blanked_line_by_line(tmp_path: Path):
    """One stray backtick used to swallow every sentence after it.

    A page's fenced block spans lines, so a page is blanked whole. A source has no fences and
    no balance: an odd backtick in a comment pairs with the next one further down, and the
    prose between them is blanked as if it were code. That is how one of the three sentences
    this check was written for stayed hidden while the other two were found.
    """
    source = ('# A quote that opens with a ` and never closes it.\n'
              '"""The owner asked for the column back."""\n'
              '# Another `name` in backticks.\n')
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "one.py").write_text(source, encoding="utf-8")

    problems = source_attribution_problems(Layout(root=tmp_path), ("tools",))

    assert len(problems) == 1 and problems[0].startswith("tools/one.py:2:")


def test_a_folder_that_is_not_there_is_a_finding(tmp_path: Path):
    """A renamed folder leaves this check walking an empty tree and passing."""
    problems = source_attribution_problems(Layout(root=tmp_path), ("tools",))

    assert len(problems) == 1 and "not there" in problems[0]


def test_the_files_read_are_the_patterns_the_repository_names(tmp_path: Path):
    """Two of these repositories write their comments in Python and one of them in Java."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Tool.java").write_text(
        "// The owner asked for the column back.\n", encoding="utf-8")
    (tmp_path / "src" / "tool.py").write_text(
        '"""The owner wants it the other way."""\n', encoding="utf-8")

    layout = Layout(root=tmp_path)

    assert [path.name for path in prose_sources(layout, ("src",))] == ["tool.py"]
    assert len(source_attribution_problems(layout, ("src",))) == 1
    assert len(source_attribution_problems(layout, ("src",), patterns=("*.py", "*.java"))) == 2


def test_a_source_switches_off_a_turn_the_same_way_a_page_does(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "one.py").write_text('T = "The owner asked for it."\n', encoding="utf-8")
    layout = Layout(root=tmp_path)

    assert len(source_attribution_problems(layout, ("src",))) == 1
    assert source_attribution_problems(layout, ("src",), allow=("the owner said",)) == []
    assert len(source_attribution_problems(layout, ("src",), allow=("the owner sang",))) == 2


def test_a_marked_source_is_read_rather_than_crashed_on(tmp_path: Path):
    """A byte-order mark at the head of a file is not a reason to read nothing."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "one.py").write_bytes(
        codecs.BOM_UTF8 + '# The owner asked for it.\n'.encode("utf-8"))

    problems = source_attribution_problems(Layout(root=tmp_path), ("src",))

    assert len(problems) == 1 and "owner asked" in problems[0]
