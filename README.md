# docsguard

**English** · [Русский](README.ru.md)

A documentation guard is the check that keeps a repository's documentation honest. Does every
tool the repository registers have a row in the table? Is every environment variable the code
reads described somewhere? Does the mirrored README still match the page it was taken from? Do
the one-line annotations still name what the front page lists? Sooner or later every repository
writes a guard like that, and underneath they all write the same six readers.

This package is those six readers, plus the checks that come out the same everywhere. The
repository keeps two things of its own: a table of positions that says where its pages, site
config and manifest live, and the checks about its own subject.

The package was written after the same check had been implemented three times in three
repositories. The copies had already drifted. One of them dropped the generator notes when it
read a page, the next one kept them, so the same defect was a finding in one repository and
silence in the other.

## Install

The guard runs in CI and is never shipped to users, so it is installed from git rather than
released. Pin it to a tag, not to a branch:

```
pip install git+https://github.com/keyfire/docsguard@v0.8.0
```

A consumer pinned to `@main` picks up a change made here in the middle of its own run. Nobody
asked for that red run, so nobody reads it. A branch pin also leaves the order of merging to
memory: the shared package first, the consumer after it. A tag turns that order into a line in
the consumer's own pull request, where it is reviewed and tested.

Raise a pin in three steps.

1. The change lands here. `__version__` and the install lines above go up in the same commit.
   The guard fails the run when the two disagree, so neither can be forgotten.
2. `main` gets an annotated tag `v<version>` right after the merge.
3. Each consumer raises its pin to that tag in a pull request of its own. A change made here
   then turns the run red in the repository that asked for the change.

## Use

```python
from pathlib import Path

from docsguard import Layout, PitchItem, pitch_problems, run, site_description

LAYOUT = Layout(
    root=Path(__file__).resolve().parent.parent,
    site_config=Path(__file__).resolve().parent.parent / "site" / "config.ts",
    pyproject=Path(__file__).resolve().parent.parent / "pyproject.toml",
)

ITEMS = (
    PitchItem("Reports", "Отчёты", "report", "отчёт"),
    # A row with no words is a headline left out of the annotations on purpose.
    # Write the reason next to it.
    PitchItem("Steps", "Шаги", None, None),
)


def check_annotations():
    return pitch_problems(ITEMS, headlines(), surfaces())


raise SystemExit(run([check_annotations, check_tools, check_environment]))
```

## What is in it

- **`Layout`** holds the positions of one repository: root, docs folder, site config, manifest.
  Every function takes one, so what is specific to a repository stays in a single literal.
- **Page readers.** `page_body` gives a page without its frontmatter and generator notes,
  `section_body` the body of one section, `headings` the headings of one level,
  `box_headlines` the bold headline of every bullet. `front_description` reads the description
  from the frontmatter, `lede` the first paragraph of prose, `injected` the block a mirroring
  script writes between its markers, `mirror_source` a root document the way a mirrored page
  carries it. `site_pages` lists the pages the site really publishes. `IMAGE` is the pattern
  that image links are read with. A repository judging its own images takes the pattern from
  here and so reads them the way the checks here do.
- **Annotations.** `site_description` and `pyproject_description` read the one-liners that get
  quoted instead of the page: the meta description of the site and the summary line of the
  packaging manifest. `pitch_problems` measures those against the features block and against
  the repository's own table of `PitchItem` rows. It judges both directions, so a feature that
  disappears does not leave the guard asking for a word about it.
- **Claims.** `Claim`, `claim_text`, `claim_texts` and `claim_problems` hold one fact to one
  wording across several documents and the docstrings of the code at once. Every place the
  table names has to state that fact. The wording it replaced has to be gone from everywhere
  that was searched, in the spelling it really had. The table itself stays in the repository:
  which statements matter, and in which words, is knowledge about the subject rather than
  about guarding.
- **Mirror checks.** `mirror_problems`, `injection_problems`, `image_problems` and
  `translation_problems`.
- **Coverage.** `coverage_problems` compares what the sources offer with what one document
  lists: the tools an MCP server registers, the variables the code reads, the names a package
  exports. Every repository had written that set difference by hand, more than once inside the
  same file. Both directions are judged here as well. An empty set on the sources side is a
  finding of its own, because a reader that has stopped finding anything would otherwise pass
  in silence.
- **Conventions of the sources.** Two rules that no test of a feature would ever notice. Both
  are read with `ast`, and both leave the list of folders to the consumer.
  - `process_encoding_problems` watches the encoding of a started process, with
    `python_sources`, `process_starts`, `asks_for_text` and `encoding_problems` underneath it.
    A process whose output is read as text has to name `encoding="utf-8"`. Otherwise the output
    is decoded with whatever code page the machine has, and the failure is a silent one: the
    text comes back as replacement characters while the exit code still says the run went well.
    The rule is read with `ast` rather than searched for, because the call that started all
    this is written `(run or subprocess.run)(...)` and a search for the text of a call looks
    straight past it.
  - `text_write_newline_problems` watches the line ending of a written file, with `text_writes`,
    `writes_text` and `newline_problems` underneath it. A text file written without `newline=""`
    takes the line ending of the platform. A generator that rewrites a page on Windows then
    hands back a file in which every line has changed. A checkout with `core.autocrlf=input`
    hides it, and on a machine without that setting the whole file goes to a public repository
    as one change of line endings. This rule takes a shorter list of folders than the process
    one: what a test writes goes to a temporary directory and outlives nothing.
- **Jargon.** `jargon_problems` reads the Russian pages of a repository and names the
  transliterated word that has a Russian one. The dictionary is `JARGON`, one `JargonWord` per
  word: the root it is recognized by, the name a repository switches it off by, and the Russian
  to write instead. A repository that needs a word of its own adds a row. A repository whose
  subject needs a word the dictionary forbids switches that row off by name, and
  `empty_exceptions` reports an exception that no longer matches any row. The twenty-one words it
  forbids: `пин`, `прогон`, `базлайн`, `хук`, `фолбэк`, `фикс`, `билд`, `дефолт`, `эксепшн`,
  `апдейт`, `скоуп`, `ворктри`, `скаффолдинг`, `воркспейс`, `воркфлоу`, `дашборд`, `бэкенд`,
  `лаунчер`, `мейнтейнер`, `топ-объект`, `легаси`. The owner rewrote the list on 12 September
  2026 and kept the words that stop him mid-sentence. The last six came from the documentation
  of the tools a day later. `jargon_findings` judges one text and quotes the word in the form the
  page wrote it, which is the form a writer can search for. `russian_pages` collects the pages.
  `without_code` blanks out what is not prose: an identifier in backticks, a fenced block, a link
  target, a file name. It blanks in place, so the line numbers hold and `pipeline` stays the name
  of a thing. `jargon_self_check` proves the dictionary on samples before it reads a page. A root
  that has lost a letter finds nothing, and finding nothing reads exactly like a repository in
  order.
- **Jargon in the sources.** The help of a command and the message it prints go straight to a
  terminal, and both are written in the sources. `source_jargon_problems` reads the files a
  repository names, one message catalog each in these three, and judges the string literals that
  have Cyrillic in them. The English half of a catalog stays as it is, and so do the key above
  it, the Latin names and the `{path}` a template fills in. `russian_strings` picks the literals
  out with `ast`, the way the conventions above are read. A search over the text would report
  `"пин"` on a line that holds `"пин" "гвин"`, and would miss a word spelled across two lines.
  `source_findings` judges one file. A named source that is not there is a finding of its own: a
  renamed catalog would otherwise leave the check reading nothing and passing.
- **`run` and `report`.** `run` calls every check, collects what they find and hands the list
  to `report`, which prints it and answers with the exit code CI reads. A check that raises
  becomes a finding of its own, so a bug in the guard cannot read as "no problems".

## Guarding itself

The package is pointed at its own README. `python scripts/check_docs.py` judges the section
above the way a consumer's guard judges its tool table: every public name of `__all__` is
named in both editions, and neither edition names one that is gone. The install lines are
judged with it. The tag they pin has to be the version the package reports, so a bump cannot
leave consumers copying the URL of the previous release. The check runs in CI on every push,
and the test suite asserts the same thing. A new function reaches `main` only together with the
two lines that tell a reader it exists.

The jargon dictionary reads the Russian edition of this README as well, and proves itself on
its own samples in the same run. The words it catches are quoted in backticks above, which is
what tells the check they are names here. The guard reads that list against the dictionary both
ways. A row added or dropped in the code alone fails the run until both editions are edited
too.

The package keeps the conventions it ships. Its own suite runs `process_encoding_problems` over
`docsguard`, `tests` and `scripts`, and `text_write_newline_problems` over `docsguard` and
`scripts`, the two whose writes outlive the run.

The gap this was written for was the package's own. A function lived here and was named in no
edition of the README, while three repositories were installing the package to be told about
exactly that.

## Licence

MIT, see [LICENSE](LICENSE).
