"""Two mix-ups that both Editions side by side make easy, each refused saying what went wrong.

- An object made by the other Edition's folder, such as a Table reference whose file imports
  that folder, given to this Edition's functions. Each function that checks what it was given
  names the other folder, where it would otherwise call the object the wrong kind of thing.
- A send that gives back Spark's own DataFrame, as `send=spark.sql` does without
  `.toPandas()`. Whatever reads what came back says to end the send with `.toPandas()`, where
  it would otherwise skip the row limit or fail with Python's own error.

Both are faked, so both runs test them without the other Edition or a Spark.
"""

from __future__ import annotations

import pytest

from conftest import edition
from sql_composer import (
    AS,
    FROM,
    GROUP_BY,
    JOIN,
    ORDER_BY,
    SELECT,
    WHERE,
    by_day,
    check_key,
    count_rows,
    derived,
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


def _one_day(*clauses):
    return statement(SELECT(job_runs.run_id), FROM(job_runs),
                     WHERE(equals(job_runs.dt, "2026-09-24")), *clauses)


@pytest.mark.parametrize(("call", "given"), [
    (lambda: FROM(OTHERS_TABLE), "FROM"),
    (lambda: JOIN(OTHERS_TABLE, ON=equals(job_runs.run_id, 1)), "JOIN"),
    (lambda: JOIN(example_database.jobs, ON=OTHERS_CONDITION), "JOIN"),
    (lambda: SELECT(OTHERS_COLUMN), "SELECT"),
    (lambda: AS(OTHERS_COLUMN, "x"), "AS"),
    (lambda: WHERE(OTHERS_CONDITION), "WHERE"),
    (lambda: GROUP_BY(OTHERS_COLUMN), "GROUP_BY"),
    (lambda: ORDER_BY(OTHERS_COLUMN), "ORDER_BY"),
    (lambda: equals(OTHERS_COLUMN, 1), "equals"),
    (lambda: equals(job_runs.status, OTHERS_COLUMN), "equals"),
    (lambda: sum_of(OTHERS_COLUMN), "sum_of"),
    (lambda: count_rows(where=OTHERS_CONDITION), "count_rows"),
    (lambda: if_else(OTHERS_CONDITION, 1, 0), "if_else"),
    (lambda: statement(OTHERS_STATEMENT), "statement"),
    (lambda: derived("d", OTHERS_STATEMENT), "derived"),
    (lambda: to_hive(OTHERS_STATEMENT), "to_hive"),
    (lambda: by_day(OTHERS_STATEMENT), "by_day"),
    (lambda: export_lineage(OTHERS_STATEMENT), "export_lineage"),
    (lambda: check_key(OTHERS_TABLE, send=example_database.send), "check_key"),
], ids=["FROM", "JOIN", "JOIN ON", "SELECT", "AS", "WHERE", "GROUP_BY", "ORDER_BY",
        "equals column", "equals value", "sum_of", "count_rows where", "if_else", "statement",
        "derived", "to_hive", "by_day", "export_lineage", "check_key"])
def test_an_object_the_other_editions_folder_made_is_named_so(call, given: str) -> None:
    with pytest.raises(TypeError) as refused:
        call()
    message = str(refused.value)
    assert f"from {OTHER}" in message and given in message
    assert f"from {edition().folder} import" in message


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
def test_a_send_that_gives_back_sparks_dataframe_says_to_end_it_with_to_pandas(call) -> None:
    with pytest.raises(TypeError, match=r"End your send with \.toPandas\(\)") as refused:
        call()
    assert "Spark DataFrame" in str(refused.value)
