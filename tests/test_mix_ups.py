"""Two mix-ups that are easy to make, each refused saying what went wrong.

- An object made by another Toolbox folder, such as a Table reference whose file still imports a
  folder left over from an earlier version, given to this Edition's functions. Each function
  that checks what it was given names that folder, where it would otherwise call the object the
  wrong kind of thing.
- A send that gives back Spark's own DataFrame, as `send=spark.sql` does without
  `.toPandas()`. Whatever reads what came back says how to make the send give back pandas,
  where it would otherwise skip the row limit or fail with Python's own error. A write isn't
  refused: Spark has carried it out by the time its send returns.

Both are faked, so both runs test them without the other Edition or a Spark.
"""

from __future__ import annotations

import pandas as pd
import pytest

from conftest import edition
from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    INSERT_OVERWRITE,
    JOIN,
    ORDER_BY,
    SELECT,
    WHERE,
    all_columns,
    by_day,
    check_key,
    check_table_reference,
    count_rows,
    derived,
    drop_table,
    equals,
    example_database,
    export_lineage,
    if_else,
    run,
    statement,
    sum_of,
    to_hive,
    write_table_reference,
)
from table_references.runs_to_review import runs_to_review

job_runs = example_database.job_runs


def _made_by(folder: str, kind: str):
    """An object whose class a folder named `folder` made, as the other Edition's are."""
    return type(kind, (), {"__module__": f"{folder}.tables",
                           "__repr__": lambda self: f"<{kind} from {folder}>"})()


OTHER = "elsewhere_composer"
OTHERS_TABLE = _made_by(OTHER, "Table")
OTHERS_COLUMN = _made_by(OTHER, "Column")
OTHERS_CONDITION = _made_by(OTHER, "Condition")
OTHERS_STATEMENT = _made_by(OTHER, "Statement")
OTHERS_DERIVED_TABLE = _made_by(OTHER, "Table")
OTHERS_DERIVED_TABLE._statement = OTHERS_STATEMENT


def _one_day(*clauses):
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
    (lambda: check_key(OTHERS_TABLE, send=example_database.send), "check_key",
     "a Table reference"),
], ids=["FROM", "JOIN", "JOIN ON", "FROM a Derived table", "all_columns", "SELECT", "AS", "WHERE", "GROUP_BY",
        "ORDER_BY", "equals column", "equals value", "arithmetic", "sum_of",
        "count_rows where", "if_else", "statement", "derived", "to_hive", "by_day",
        "export_lineage", "check_key"])
def test_an_object_the_other_editions_folder_made_is_named_so(call, given: str,
                                                              called: str) -> None:
    with pytest.raises(TypeError) as refused:
        call()
    message = str(refused.value)
    assert (f"was given {called} made by the {OTHER} folder, which isn't part of the Toolbox "
            f"you imported, {edition().folder}.") in message and given in message
    # The fix says which file to change, and how.
    assert (f"In the file the {called.split(' ', 1)[1]} came from, change `from {OTHER} import` "
            f"to `from {edition().folder} import`.") in message


def test_an_object_no_edition_made_gets_the_message_it_got_before() -> None:
    with pytest.raises(TypeError, match="isn't a table") as refused:
        FROM(_made_by("elsewhere", "Table"))
    assert "import" not in str(refused.value)


class _SparksDataFrame:
    """What spark.sql(hive) gives back: rows not yet read, and a way to read them."""

    def toPandas(self):  # noqa: N802 - Spark's own name
        raise AssertionError("the Toolbox shouldn't read the rows itself")


def _spark_sql(hive):
    return _SparksDataFrame()


@pytest.mark.parametrize("call", [
    lambda: run(_one_day(), send=_spark_sql),
    lambda: check_key(job_runs, send=_spark_sql),
    lambda: write_table_reference("ops.job_runs", send=_spark_sql),
], ids=["run", "check_key", "write_table_reference"])
def test_a_send_that_gives_back_sparks_dataframe_says_to_give_back_pandas(call) -> None:
    with pytest.raises(TypeError, match=r"send=lambda hive: spark\.sql\(hive\)\.toPandas\(\)"):
        call()


def test_check_table_reference_reports_a_send_that_gives_back_sparks_dataframe() -> None:
    assert "Make your send give back pandas" in str(check_table_reference(job_runs,
                                                                          send=_spark_sql))


@pytest.mark.parametrize("write", [
    lambda: statement(INSERT_OVERWRITE(runs_to_review), SELECT(job_runs.run_id, job_runs.job_id),
                      FROM(job_runs), WHERE(equals(job_runs.dt, "2026-09-24"))),
    lambda: drop_table(runs_to_review),
], ids=["INSERT_OVERWRITE", "drop_table"])
def test_a_write_isnt_refused_once_spark_has_carried_it_out(write) -> None:
    # Refused, it would be sent again, and INSERT_INTO would add its rows twice.
    assert isinstance(run(write(), send=_spark_sql), _SparksDataFrame)


def test_a_pandas_dataframe_with_a_column_named_to_pandas_is_taken() -> None:
    frame = pd.DataFrame({"toPandas": [1]})
    assert run(_one_day(), send=lambda hive: frame) is frame
