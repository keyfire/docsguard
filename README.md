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
released:

```
pip install git+https://github.com/keyfire/docsguard@main
```

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
  `site_pages`.
- **Annotations** - `site_description`, `pyproject_description` and `pitch_problems`: the gap
  between the features block, the repository's own table and the one-liners quoted instead of
  the page. Both directions are judged, so a feature that disappears does not leave the guard
  demanding a word for it.
- **Mirror checks** - `mirror_problems`, `injection_problems`, `image_problems`.
- **`run`** - runs every check, prints every finding, answers with the exit code CI reads. A
  check that raises becomes a finding of its own: a guard whose own bug reads as "no problems"
  is worse than no guard.

## Licence

MIT - see [LICENSE](LICENSE).
