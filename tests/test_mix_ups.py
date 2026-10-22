"""A mix-up that is easy to make, refused saying what went wrong.

An object made by another Toolbox folder, such as a Table reference whose file still imports a
folder left over from an earlier version, given to the Toolbox's functions. Each function that
checks what it was given names that folder, where it would otherwise call the object the wrong
kind of thing. The folder is faked, so it is tested without an old copy.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from conftest import FOLDER
from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    JOIN,
    ORDER_BY,
    SELECT,
    WHERE,
    Statement,
    all_columns,
    by_day,
    check_key,
    count_rows,
    derived,
    equals,
    example_database,
    export_lineage,
    if_else,
    statement,
    sum_of,
    to_hive,
)
from sqlglot_composer.clauses import Clause

job_runs = example_database.job_runs


def _made_by(folder: str, kind: str) -> object:
    """An object whose class a folder named `folder` made, as an old Toolbox folder's are."""
    return type(kind, (), {"__module__": f"{folder}.tables",
                           "__repr__": lambda self: f"<{kind} from {folder}>"})()


OTHER = "elsewhere_composer"
OTHERS_TABLE = _made_by(OTHER, "Table")
OTHERS_COLUMN = _made_by(OTHER, "Column")
OTHERS_CONDITION = _made_by(OTHER, "Condition")
OTHERS_STATEMENT = _made_by(OTHER, "Statement")
OTHERS_DERIVED_TABLE = _made_by(OTHER, "Table")
OTHERS_DERIVED_TABLE._statement = OTHERS_STATEMENT


def _one_day(*clauses: Clause) -> Statement:
    return statement(SELECT(job_runs.run_id), FROM(job_runs),
                     WHERE(equals(job_runs.dt, "2026-09-24")), *clauses)


@pytest.mark.parametrize(("call", "given", "called"), [
    (lambda: FROM(OTHERS_TABLE), "FROM", "a Table reference"),
    (lambda: JOIN(OTHERS_TABLE, ON=equals(job_runs.run_id, 1)), "JOIN", "a Table reference"),
    (lambda: JOIN(example_database.jobs, ON=OTHERS_CONDITION), "JOIN", "a condition"),
    (lambda: FROM(OTHERS_DERIVED_TABLE), "FROM", "a Derived table"),
    (lambda: all_columns(OTHERS_TABLE), "all_columns", "a Table reference"),
    (lambda: SELECT(OTHERS_COLUMN), "SELECT", "a column"),
    (lambda: AS(OTHERS_COLUMN, "x"), "AS", "a column"),
    (lambda: WHERE(OTHERS_CONDITION), "WHERE", "a condition"),
    (lambda: GROUP_BY(OTHERS_COLUMN), "GROUP_BY", "a column"),
    (lambda: ORDER_BY(OTHERS_COLUMN), "ORDER_BY", "a column"),
    (lambda: equals(OTHERS_COLUMN, 1), "equals", "a column"),
    (lambda: equals(job_runs.status, OTHERS_COLUMN), "equals", "a column"),
    (lambda: job_runs.duration_mins + OTHERS_COLUMN, "+", "a column"),
    (lambda: sum_of(OTHERS_COLUMN), "sum_of", "a column"),
    (lambda: count_rows(where=OTHERS_CONDITION), "count_rows", "a condition"),
    (lambda: if_else(OTHERS_CONDITION, 1, 0), "if_else", "a condition"),
    (lambda: statement(OTHERS_STATEMENT), "statement", "a Statement"),
    (lambda: derived("d", OTHERS_STATEMENT), "derived", "a Statement"),
    (lambda: to_hive(OTHERS_STATEMENT), "to_hive", "a Statement"),
    (lambda: by_day(OTHERS_STATEMENT), "by_day", "a Statement"),
    (lambda: export_lineage(OTHERS_STATEMENT), "export_lineage", "a Statement"),
    (lambda: check_key(OTHERS_TABLE, query=example_database.query), "check_key",
     "a Table reference"),
], ids=["FROM", "JOIN", "JOIN ON", "FROM a Derived table", "all_columns", "SELECT", "AS", "WHERE", "GROUP_BY",
        "ORDER_BY", "equals column", "equals value", "arithmetic", "sum_of",
        "count_rows where", "if_else", "statement", "derived", "to_hive", "by_day",
        "export_lineage", "check_key"])
def test_an_object_another_folder_made_is_named_so(call: Callable[[], object], given: str,
                                                              called: str) -> None:
    with pytest.raises(TypeError) as refused:
        call()
    message = str(refused.value)
    assert (f"was given {called} made by the {OTHER} folder, which isn't part of the Toolbox "
            f"you imported, {FOLDER}.") in message and given in message
    # The fix says which file to change, and how.
    assert (f"In the file the {called.split(' ', 1)[1]} came from, change `from {OTHER} import` "
            f"to `from {FOLDER} import`.") in message


def test_an_object_no_toolbox_folder_made_gets_the_message_it_got_before() -> None:
    with pytest.raises(TypeError, match="isn't a table") as refused:
        FROM(_made_by("elsewhere", "Table"))
    assert "import" not in str(refused.value)
