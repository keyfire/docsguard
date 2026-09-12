"""The dictionary of jargon: what it has to find, and everything it has to leave alone.

Leaving alone is the harder half, and it is where a check like this dies. A guard that reports
"пингвин" because "пин" is inside it, or the `pipeline` a page quotes on purpose, is a guard a
writer switches off within a week. So most of the provocations here are innocent text: a root
sitting inside a Russian word, an identifier in backticks, a fenced block, a link, a file name.
"""

from pathlib import Path

import pytest

from docsguard import (
    JARGON,
    JargonWord,
    Layout,
    jargon_findings,
    jargon_problems,
    jargon_self_check,
    without_code,
)


@pytest.fixture()
def layout(tmp_path: Path) -> Layout:
    (tmp_path / "docs").mkdir()
    return Layout(root=tmp_path)


def test_the_dictionary_proves_itself_on_its_own_samples():
    """The samples inside the module: awake on one set of sentences, silent on the other."""
    assert jargon_self_check() == []


def test_a_jargon_word_is_found_with_its_line_and_a_russian_word_to_write():
    text = "Первая строка.\nКрасный прогон никто не читает.\n"

    found = jargon_findings(text, "index.ru.md")

    assert len(found) == 1
    assert found[0].startswith('index.ru.md:2: "прогон" is jargon')
    assert "запуск, проверка" in found[0]


def test_the_word_is_quoted_the_way_the_page_writes_it():
    """A writer searches the page for what the finding shows, not for a dictionary form."""
    found = jargon_findings("Сторож работает в прогонах CI.", "index.ru.md")

    assert '"прогонах"' in found[0]


def test_clean_russian_is_silence():
    text = ("Версия закреплена меткой, поднять её можно одним коммитом.\n"
            "Проверки прошли, задача конвейера зелёная, сборка применилась.\n")

    assert jargon_findings(text, "index.ru.md") == []


@pytest.mark.parametrize("innocent", [
    "Пингвин отпер шпингалет.",
    "Пинг прошёл за десять миллисекунд.",
    "Билдер собирает страницу.",
    "Префикс и суффикс остаются на месте.",
    "Фиксация правки прошла.",
])
def test_a_root_inside_another_word_is_not_a_finding(innocent):
    """The jargon roots live inside ordinary Russian words, and there they are nobody's business."""
    assert jargon_findings(innocent, "index.ru.md") == []


@pytest.mark.parametrize("allowed", [
    "Фичу отложили до следующей недели.",
    "Джобы конвейера встали в очередь.",
    "Пайплайна на этой ветке нет.",
    "Чекаут делают заново.",
    "Раннеры заняты.",
    "Тайм-аут вышел.",
    "Ветку смёржили вечером.",
    "Ребейзить поздно.",
    "Варнинги никто не смотрит.",
    "Кейсы перечислены ниже.",
    "Смоук-тест после выкладки прошёл.",
])
def test_a_word_the_owner_allowed_is_silence(allowed):
    """Eleven rows went on 12 September 2026, and every one of them used to be a finding."""
    assert jargon_findings(allowed, "index.ru.md") == []


@pytest.mark.parametrize("written, instead", [
    ("Скаффолдинг завёл объект в дереве метаданных.", "создание метаданных"),
    ("Скаффолдингом заводят и форму, и маршрут.", "создание метаданных"),
    ("Воркспейс переехал на другой диск.", "рабочая папка"),
    ("Воркфлоу не склоняется, и это его не спасает.", "процесс, файл процесса"),
])
def test_the_words_added_on_12_september_are_found(written, instead):
    """Three rows joined the dictionary that day, and each one offers its own Russian."""
    found = jargon_findings(written, "index.ru.md")

    assert len(found) == 1 and instead in found[0]


@pytest.mark.parametrize("latin", [
    "Модуль xbsl.scaffold заводит объект.",
    "Поле workspace в launch.json указывает на папку.",
    "Сервер читает server.workspace при старте.",
    "Скрипт workflow лежит рядом с исходниками.",
])
def test_the_latin_name_the_word_came_from_is_silence(latin):
    """A jargon word is Russian letters. Its Latin original is the name of a thing."""
    assert jargon_findings(latin, "index.ru.md") == []


@pytest.mark.parametrize("quoted", [
    "Ключ `прогон` называется так и никак иначе.",
    "```\nпрогон\n```",
    "~~~\nпрогон\n~~~",
    "Ссылка на [страницу](docs/прогон.ru.md) ведёт куда следует.",
    "Файл прогон.md называется так, как называется.",
    "Адрес https://example.com/прогон открывается.",
])
def test_an_identifier_is_not_prose(quoted):
    """Backticks, a fenced block, a link target, a file name and an address are names."""
    assert jargon_findings(quoted, "index.ru.md") == []


def test_blanking_an_identifier_keeps_the_lines_where_they_were():
    """A finding names the line a reader opens, so a blanked span stays the size it was."""
    text = "`прогон`\nКрасный прогон.\n"

    blanked = without_code(text)

    assert blanked.count("\n") == text.count("\n")
    assert jargon_findings(text, "index.ru.md")[0].startswith("index.ru.md:2:")


def test_a_repository_switches_off_the_word_its_subject_needs():
    """A word the subject really needs is a word the guard has no business with."""
    text = "Хуки стоят перед коммитом, и прогон это подтверждает."

    assert len(jargon_findings(text, "index.ru.md")) == 2
    assert len(jargon_findings(text, "index.ru.md", allow=("хук",))) == 1
    assert jargon_findings(text, "index.ru.md", allow=("хук", "прогон")) == []


def test_switching_off_a_word_that_is_in_no_row_is_a_finding(layout):
    """An exception that guards nothing looks exactly like one that works."""
    (layout.docs / "index.ru.md").write_text("Чистый текст.\n", encoding="utf-8")

    problems = jargon_problems(layout, allow=("прогонка",))

    assert len(problems) == 1 and "прогонка" in problems[0]


def test_the_russian_pages_are_read_and_the_english_ones_are_left_alone(layout):
    """The dictionary is a list of English words, and in English they are the right ones."""
    (layout.docs / "index.ru.md").write_text("Красный прогон.\n", encoding="utf-8")
    (layout.docs / "index.md").write_text("The pipeline is green.\n", encoding="utf-8")

    problems = jargon_problems(layout)

    assert len(problems) == 1 and problems[0].startswith("docs/index.ru.md:")


def test_a_root_document_is_read_by_name(layout):
    (layout.root / "README.ru.md").write_text("Подъём пина идёт в три шага.\n",
                                              encoding="utf-8")

    problems = jargon_problems(layout, documents=("README.ru.md",))

    assert len(problems) == 1 and problems[0].startswith("README.ru.md:1:")


def test_the_same_file_reached_twice_is_reported_once(tmp_path: Path):
    """A repository whose pages ARE its root documents reaches the same file both ways."""
    (tmp_path / "README.ru.md").write_text("Красный прогон.\n", encoding="utf-8")

    problems = jargon_problems(Layout(root=tmp_path, docs=tmp_path),
                               documents=("README.ru.md",))

    assert len(problems) == 1


def test_a_repository_may_bring_a_dictionary_of_its_own():
    """The rows are data. A repository with a word of its own adds a row, not a check."""
    own = (JargonWord("релизить", r"(?:за)?релизить", "выпускать, выпустить"),)

    assert jargon_findings("Зарелизить успели в пятницу.", "index.ru.md", dictionary=own)
    assert jargon_findings("Красный прогон.", "index.ru.md", dictionary=own) == []


def test_every_row_carries_a_name_a_root_and_a_russian_word_to_write():
    """A row missing one of the three cannot be switched off, or acted on, or both."""
    for word in JARGON:
        assert word.name and word.root and word.instead, word

    assert len({word.name for word in JARGON}) == len(JARGON)
