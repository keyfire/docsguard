"""Running the checks of one repository and answering with an exit code.

The shape all three repositories had arrived at independently: every check appends its findings
to one list, the list is printed in full, and the exit code is what CI reads. Printing the whole
list matters - a guard that stops at the first finding turns one review into five runs.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterable


def report(problems: Iterable[str], *, title: str = "documentation", stream=None) -> int:
    """Print the findings and answer with the exit code: 0 when there are none."""
    stream = stream or sys.stdout
    found = list(problems)
    if not found:
        print(f"OK: {title} matches the sources", file=stream)
        return 0
    print(f"{title}: {len(found)} problem(s)", file=stream)
    for problem in found:
        print(f"  - {problem}", file=stream)
    return 1


def run(checks: Iterable[Callable[[], Iterable[str]]], *, title: str = "documentation",
        stream=None) -> int:
    """Run every check, collect what they find, print it, answer with the exit code.

    A check that raises is not allowed to hide the others: the exception is reported as a
    finding of its own and the rest still run. A guard whose own bug reads as "no problems"
    is worse than no guard.
    """
    problems: list[str] = []
    for check in checks:
        try:
            problems.extend(check())
        except Exception as error:  # noqa: BLE001 - the guard reports, it does not crash
            problems.append(f"{getattr(check, '__name__', check)}: the check itself failed - {error!r}")
    return report(problems, title=title, stream=stream)
