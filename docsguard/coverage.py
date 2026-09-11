"""Everything the sources offer is named in the documentation, and nothing else is.

The shape every one of these repositories wrote by hand, more than once inside the same file:
the set the SOURCES have - the tools an MCP server registers, the variables the code reads, the
extensions an archive packs, the names a package exports - against the set a document LISTS.

The judging is dull; what is not dull is that both directions matter. A name the document does
not carry is a capability nobody can find. A name the document carries and the sources have not
got is a reader sent after something that no longer exists - and one repository had both at
once, in the same table.

The third failure is the reader itself. A check whose sources-side set comes back empty finds
nothing and reads exactly like a clean repository, so an empty set is a finding of its own: it
means the shape the reader knew has changed and the check has been passing for free.
"""

from __future__ import annotations

from collections.abc import Iterable


def coverage_problems(
    offered: Iterable[str],
    listed: Iterable[str],
    *,
    what: str,
    where: str,
    phantoms: bool = True,
) -> list[str]:
    """The gap between what the sources offer and what one document lists.

    offered  - what the sources have; read them, do not retype them.
    listed   - what the document names.
    what     - the kind of thing counted, as a finding will name it: "tool", "public name".
    where    - the document, as a finding will name it: "mcp.ru.md", "README.md / What is in it".
    phantoms - judge the other direction as well. Off for a document that lists MORE than the
               sources offer on purpose - a page describing the variables of a neighbouring tool
               beside its own.
    """
    offered, listed = set(offered), set(listed)
    if not offered:
        return [
            f"{where}: no {what} was found in the sources - has the shape the reader knows "
            "changed?"
        ]
    problems = [f"{where}: the {what} {name} is named nowhere here" for name in sorted(offered - listed)]
    if phantoms:
        problems += [
            f"{where}: {name} is named here as a {what} and the sources have no such thing"
            for name in sorted(listed - offered)
        ]
    return problems
