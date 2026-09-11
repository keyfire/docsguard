# docsguard

**English** · [Русский](README.ru.md)

A documentation guard is the check that keeps a repository's documentation honest: the tools it
registers have rows in the table, the environment variables it reads are described somewhere,
the mirrored README still matches the page it mirrors, and the one-line annotations still name
what the front page lists. Every repository ends up writing one, and every one of them ends up
writing the same six readers underneath it.

This package is those six readers, plus the checks that are the same everywhere. What stays in
the repository is the table of positions - where its pages, site config and manifest live - and
the checks that are about its own subject.

Written after the same check had been implemented three times in three repositories, with the
copies already drifting: one of them skipped the generator notes when reading a page and the
next kept them, so the same defect was a finding in one place and silence in the other.

## Install

The guard runs in CI and is not shipped to users, so it is installed from git rather than
released - and by TAG, not by a branch:

```
pip install git+https://github.com/keyfire/docsguard@v0.4.0
```

A consumer pinned to `@main` takes a change made here in the middle of a run of its own, and a
red run nobody caused is a red run nobody reads. It also leaves the order of merging to be
remembered rather than written down: the shared package first, the consumer after it. A tag
turns that into a line in the consumer's own pull request, reviewed and tested there.

Raising a pin, in order:

1. **the change lands here** - `__version__` and the install lines above go up in the same
   commit; the guard fails the run when they disagree, so neither can be forgotten;
2. **`main` is tagged** `v<version>`, annotated, right after the merge;
3. **each consumer raises its pin** to that tag, in a pull request of its own - the run that
   goes red on a change here goes red in the repository that asked for the change.

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
    # A row with no words is a headline deliberately kept out of the annotations -
    # the reason belongs beside it.
    PitchItem("Steps", "Шаги", None, None),
)


def check_annotations():
    return pitch_problems(ITEMS, headlines(), surfaces())


raise SystemExit(run([check_annotations, check_tools, check_environment]))
```

## What is in it

- **`Layout`** - the positions of one repository: root, docs folder, site config, manifest.
  Every function takes one, so the repository-specific knowledge stays in one literal.
- **Page readers** - `page_body` (without frontmatter and generator notes), `section_body`,
  `box_headlines`, `headings`, `front_description`, `lede`, `injected`, `mirror_source`,
  `site_pages`, and `IMAGE` - the pattern the image links of a page are read with, shared so
  that a repository judging its own images reads them the way the checks here do.
- **Annotations** - `site_description`, `pyproject_description` and `pitch_problems`: the gap
  between the features block, the repository's own table of `PitchItem` rows and the one-liners
  quoted instead of the page. Both directions are judged, so a feature that disappears does not
  leave the guard demanding a word for it.
- **Claims** - `Claim`, `claim_text`, `claim_texts` and `claim_problems`: one fact told in several
  documents and in the docstrings of the code at once. Every place the table names has to state
  it, and the superseded wording - in the spelling it really had - may appear nowhere that was
  searched. The table itself stays in the repository: which statements matter and in which words
  is knowledge about the subject, not about guarding.
- **Mirror checks** - `mirror_problems`, `injection_problems`, `image_problems`,
  `translation_problems`.
- **Coverage** - `coverage_problems`: what the sources offer against what one document lists.
  The tools an MCP server registers, the variables the code reads, the names a package exports:
  each repository had written that set difference by hand, more than once inside the same file.
  Both directions again, and an empty sources-side set is a finding of its own: a reader
  that has stopped finding anything reads exactly like a clean repository.
- **Conventions of the sources** - `process_encoding_problems`, with `python_sources`,
  `process_starts`, `asks_for_text` and `encoding_problems` underneath it: the rules no test of
  a feature would ever notice. The one that is here is the encoding of a started process - a
  process read as TEXT has to name `encoding="utf-8"`, or it is decoded with whatever code page
  the machine has and the failure is the silent kind: the text comes back as replacement
  characters and the exit code goes on saying the run went well. Read with `ast`, because the
  call that started this is written `(run or subprocess.run)(...)` and a search for the text of
  a call looks straight past it. What stays with the consumer is the list of folders to read.
- **`run`** and **`report`** - `run` calls every check, collects what they find and hands the
  list to `report`, which prints it and answers with the exit code CI reads. A check that
  raises becomes a finding of its own: a guard whose own bug reads as "no problems" is worse
  than no guard.

## Guarding itself

The package is pointed at its own README: `python scripts/check_docs.py` judges the section
above the way a consumer's guard judges its tool table - every public name of `__all__` is
named in both editions, and neither edition names one that is gone. The install lines are
judged with it: the tag they pin has to be the version the package reports, so a bump cannot
leave consumers reading last release's URL. It runs in CI on every push, and the test suite
asserts the same thing, so a new function reaches `main` only with the two lines that tell a
reader it exists. The package is held to the conventions it ships as well: its own suite runs
`process_encoding_problems` over `docsguard`, `tests` and `scripts`.

The gap it was written for was its own: a function had been living in the package and named
in no edition of the README, while three repositories were installing this package to be told
about exactly that.

## Licence

MIT - see [LICENSE](LICENSE).
