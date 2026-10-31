"""Decisions: what only you decide about one table, which its Table reference shows made or not.

Toolbox 8.1's tickets 02 and 03. A Decision is a line of a Table reference holding a TODO: or
a <...>: its location=, its key=, a column whose type a Conversion could only guess, or any
other <...>. You answer each in a Workflow's decisions cell, and project.write_decisions
writes each answer into its line; a line made already is kept.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import example_database, project, set_admin_log

decisions = toolbox_module("decisions")
REFERENCE = '''"""mart_dev.x - TODO: say in one line what one row is."""
from sqlglot_composer import Table

x = Table(
    "mart_dev.x",
    columns={
        "team": "string",  # TODO: guessed: nothing told its type
        "fails": "bigint",
    },
    key=None,  # TODO: the columns that pick out one row, such as key=["team"]
    location=None,  # TODO: its own folder, such as "/data/your_team/mart_dev.db/this_table"
    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
)

# --- Aliases ------------------------------------------------------------------------------
#     <alias> = x.team
'''


def kinds(text: str) -> list[tuple[str, str]]:
    return [(each.kind, each.subject) for each in decisions.open_decisions(text, "mart_dev.x")]


def test_each_open_line_is_a_decision_of_its_kind() -> None:
    assert kinds(REFERENCE) == [(decisions.GUESSED_TYPE, "team"), (decisions.KEY, ""),
                                (decisions.LOCATION, "")]


def test_a_todo_that_is_no_decision_and_a_comment_wait_on_nothing() -> None:
    # does_not_add_up's TODO, the docstring's, and the Aliases' <alias> are none.
    assert all(kind != decisions.PLACEHOLDER for kind, _ in kinds(REFERENCE))


def test_a_placeholder_names_itself_and_its_docstring_is_not_read() -> None:
    text = ('"""mart_dev.y - <COLUMN> and <COLUMN_TYPE>: a column."""\n'
            "y = Table(\n    columns={\n        <COLUMN>: <COLUMN_TYPE>,\n    },\n"
            "    location=<LOCATION>,\n)\n")
    assert kinds(text) == [(decisions.PLACEHOLDER, "<COLUMN>"), (decisions.LOCATION, "")]


def test_an_answer_is_written_into_each_open_line() -> None:
    answered = decisions.answered_text(REFERENCE, {
        "location": "/data/team/mart_dev.db/x", "key": ["team"], "types": {"team": "string"}},
        "references/mart_dev__x.py")
    assert answered.unwritten == []
    assert answered.written == ["types: team", "key", "location"]
    assert '    location="/data/team/mart_dev.db/x",' in answered.text
    assert '    key=["team"],' in answered.text
    assert '        "team": "string",\n' in answered.text
    assert kinds(answered.text) == []


def test_none_answers_a_key_that_none_names() -> None:
    answered = decisions.answered_text(REFERENCE, {"key": None}, "references/mart_dev__x.py")
    assert "    key=None,\n" in answered.text
    assert (decisions.KEY, "") not in kinds(answered.text)


def test_a_location_left_none_is_open_with_its_todo_taken_off() -> None:
    text = REFERENCE.replace(
        '    location=None,  # TODO: its own folder, such as "/data/your_team/mart_dev.db/'
        'this_table"', "    location=None,")
    assert (decisions.LOCATION, "") in kinds(text)


def test_a_line_made_already_is_kept_and_a_different_answer_named() -> None:
    todo = '    key=None,  # TODO: the columns that pick out one row, such as key=["team"]'
    made = REFERENCE.replace(todo, '    key=["fails"],')
    answered = decisions.answered_text(made, {"key": ["team"]}, "references/mart_dev__x.py")
    assert '    key=["fails"],' in answered.text
    assert answered.unwritten == [
        "key: kept as references/mart_dev__x.py holds it, made already; to change it, edit "
        'its key= line there (the decisions cell says ["team"])']


def test_an_answer_that_answers_no_decision_is_named() -> None:
    answered = decisions.answered_text(REFERENCE, {"owner": "me", "types": {"fails": "int"}},
                                       "references/mart_dev__x.py")
    assert answered.unwritten == [
        "owner: not a Decision a Table reference asks; the decisions cell answers location, "
        "key and types",
        "types: fails is no type the Toolbox guessed in references/mart_dev__x.py; to change "
        "it, edit its line there"]


# --- write_decisions, in a Project -----------------------------------------------------------


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    project.add_references("ops.job_runs", query=example_database.query)
    yield tmp_path
    forget_the_projects_modules()


def test_write_decisions_writes_each_answer_and_says_what_is_left(started: Path) -> None:
    report = repr(project.write_decisions({"ops.job_runs": {"key": ["run_id"]}}))
    assert report == ("Wrote 1 answer into references/ops__job_runs.py.\n"
                      "Each Decision of ops.job_runs is made.")
    reference = (started / "references" / "ops__job_runs.py").read_text(encoding="utf-8")
    assert '    key=["run_id"],' in reference


def test_a_table_with_no_table_reference_is_named(started: Path) -> None:
    report = repr(project.write_decisions({"ops.nothing": {"key": None}}))
    assert ("ops.nothing: no Table reference, references/ops__nothing.py, to write "
            "into.") in report


def test_a_decisions_cell_not_by_table_is_refused(started: Path) -> None:
    with pytest.raises(TypeError, match="which isn't an answer per table"):
        project.write_decisions({"ops.job_runs": ["run_id"]})
