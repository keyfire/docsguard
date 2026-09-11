"""What the sources offer against what a document lists - and the reader that stopped reading."""

from docsguard import coverage_problems

OFFERED = ("deploy", "probe", "list_apps")


def test_a_document_that_names_everything_is_silence():
    assert coverage_problems(OFFERED, OFFERED, what="tool", where="mcp.md") == []


def test_a_name_the_document_does_not_carry_is_named():
    """The plain failure: a capability was added and nobody can find it."""
    problems = coverage_problems(OFFERED, ("deploy", "probe"), what="tool", where="mcp.md")

    assert len(problems) == 1
    assert "mcp.md" in problems[0]
    assert "list_apps" in problems[0]


def test_a_name_the_sources_no_longer_have_is_named_too():
    """The other direction: a renamed tool leaves the reader sent after something gone."""
    problems = coverage_problems(
        OFFERED, OFFERED + ("upload",), what="tool", where="mcp.md")

    assert len(problems) == 1
    assert "upload" in problems[0]
    assert "no such thing" in problems[0]


def test_the_other_direction_can_be_turned_off():
    """A page that documents more than this repository offers - on purpose."""
    assert coverage_problems(
        OFFERED, OFFERED + ("upload",), what="tool", where="mcp.md", phantoms=False) == []


def test_a_reader_that_finds_nothing_is_a_finding_of_its_own():
    """A check whose sources-side set is empty passes every repository, this one included."""
    problems = coverage_problems((), ("deploy",), what="tool", where="mcp.md")

    assert len(problems) == 1
    assert "no tool was found in the sources" in problems[0]


def test_both_directions_are_reported_in_one_run():
    """A guard that stops at the first finding turns one review into five runs."""
    problems = coverage_problems(
        OFFERED, ("deploy", "upload"), what="tool", where="mcp.md")

    assert len(problems) == 3
    assert sum("is named nowhere here" in problem for problem in problems) == 2
    assert sum("no such thing" in problem for problem in problems) == 1


def test_findings_are_sorted_so_a_diff_of_two_runs_reads():
    names = coverage_problems(
        ("zeta", "alpha", "mu"), (), what="tool", where="mcp.md")

    named = [problem.split(" is named ")[0].split()[-1] for problem in names]

    assert named == ["alpha", "mu", "zeta"]
