"""Each misuse a beginner is likely to make is refused with all four parts and no opt-out."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import editions

from sql_composer import (
    AS,
    FROM,
    INSERT_OVERWRITE,
    GROUP_BY,
    HAVING,
    JOIN,
    LIMIT,
    ORDER_BY,
    SELECT,
    WHERE,
    Table,
    any_of,
    by_day,
    contains,
    count_rows,
    derived,
    descending,
    equals,
    example_database,
    export_lineage,
    hive_function,
    if_else,
    is_in,
    last_n_days,
    run,
    set_load_limits,
    statement,
    sum_of,
    to_hive,
)
from composer_core.example_database import job_runs, jobs

MISUSES = [
    pytest.param(lambda: LIMIT(0), ValueError, "LIMIT(0) needs a whole number of rows",
                 id="limit_0"),
    pytest.param(lambda: LIMIT("3"), ValueError, "LIMIT('3') needs a whole number",
                 id="limit_text"),
    pytest.param(lambda: ORDER_BY(), TypeError, "nothing to sort by", id="order_by_nothing"),
    pytest.param(lambda: ORDER_BY(5), TypeError, "ORDER_BY was given 5", id="order_by_5"),
    pytest.param(lambda: WHERE(), TypeError, "WHERE(...) was given no conditions",
                 id="where_nothing"),
    pytest.param(lambda: WHERE(5), TypeError, "isn't a condition", id="where_5"),
    pytest.param(lambda: HAVING(), TypeError, "HAVING(...) was given no conditions",
                 id="having_nothing"),
    pytest.param(lambda: SELECT(), TypeError, "nothing to select", id="select_nothing"),
    pytest.param(lambda: SELECT(5), TypeError, "SELECT(...) was given 5", id="select_5"),
    pytest.param(lambda: SELECT(job_runs.run_id, job_runs.run_id), ValueError,
                 "more than one column called run_id", id="select_twice"),
    pytest.param(lambda: AS(5, "x"), TypeError, "can't be named", id="as_5"),
    pytest.param(lambda: AS(job_runs.run_id, ""), TypeError, "needs a name as a string",
                 id="as_no_name"),
    pytest.param(lambda: FROM("ops.jobs"), TypeError, "isn't a table", id="from_text"),
    pytest.param(lambda: JOIN(jobs, ON=5), TypeError, "ON= isn't a condition", id="join_on_5"),
    pytest.param(lambda: GROUP_BY(5), TypeError, "GROUP_BY was given 5", id="group_by_5"),
    pytest.param(lambda: derived("bad name", statement(SELECT(jobs.team), FROM(jobs))),
                 ValueError, "needs a plain name", id="derived_name"),
    pytest.param(lambda: derived("x", 5), TypeError, "derived('x', ...) was given 5",
                 id="derived_5"),
    pytest.param(lambda: statement(5), TypeError, "isn't a clause", id="statement_5"),
    pytest.param(lambda: statement(SELECT(jobs.team)), ValueError, "has no FROM(...)",
                 id="statement_no_from"),
    pytest.param(lambda: equals(5, 1), TypeError, "where a column goes", id="equals_5"),
    pytest.param(lambda: is_in(job_runs.status, "FAILED"), TypeError,
                 "where a list of values goes", id="is_in_text"),
    pytest.param(lambda: is_in(job_runs.status, []), ValueError, "an empty list",
                 id="is_in_empty"),
    pytest.param(lambda: last_n_days(job_runs.dt, 0), ValueError, "1 or more",
                 id="last_0_days"),
    pytest.param(lambda: any_of(), TypeError, "any_of(...) was given no conditions",
                 id="any_of_nothing"),
    pytest.param(lambda: any_of(5), TypeError, "isn't a condition", id="any_of_5"),
    pytest.param(lambda: sum_of(5), TypeError, "where a column goes", id="sum_of_5"),
    pytest.param(lambda: count_rows(where=5), TypeError, "where=5 isn't a condition",
                 id="count_rows_where_5"),
    pytest.param(lambda: if_else(5, 1, 0), TypeError, "where a condition goes", id="if_else_5"),
    pytest.param(lambda: descending(5), TypeError, "where a column goes", id="descending_5"),
    pytest.param(lambda: hive_function("drop table", jobs.team), ValueError,
                 "isn't a function name", id="hive_function_name"),
    pytest.param(lambda: to_hive(42), TypeError, "isn't a Statement", id="to_hive_42"),
    pytest.param(lambda: by_day(42), TypeError, "isn't a Statement", id="by_day_42"),
    pytest.param(lambda: run(statement(SELECT(jobs.team), FROM(jobs)), send=None), TypeError,
                 "send isn't a function", id="run_send_none"),
    pytest.param(lambda: job_runs.duration_mins + "a", TypeError, "+ was used with 'a'",
                 id="plus_text"),
    pytest.param(lambda: export_lineage(), TypeError, "was given no Statement",
                 id="lineage_nothing"),
    pytest.param(lambda: export_lineage(5), TypeError, "isn't a Statement", id="lineage_5"),
    pytest.param(lambda: set_load_limits(rows=-1), ValueError, "a limit must be a whole number",
                 id="load_limits_negative"),
    pytest.param(lambda: Table("bad name", columns={"a": "string"}, date_partition=None),
                 ValueError, "isn't a table name", id="table_name"),
    pytest.param(lambda: Table("ops.t", columns={"a": "string"}, date_partition=None,
                               date_format="%Y%m%d"),
                 ValueError, "has a date_format but no date_partition", id="table_date_format"),
    pytest.param(lambda: Table("ops.t", columns=["a"], date_partition=None), ValueError,
                 "needs a dict of column names", id="table_columns_list"),
    pytest.param(lambda: Table("ops.t", columns={"a": "string"}, date_partition=None,
                               key=["b"]),
                 ValueError, "isn't one of its columns", id="table_key_not_a_column"),
    pytest.param(lambda: Table("ops.t", columns={"a": "string"}, date_partition=None, key=5),
                 ValueError, "isn't a list of column names", id="table_key_5"),
    pytest.param(lambda: derived("x", statement(
        INSERT_OVERWRITE(Table("mart.d", columns={"team": "string", "dt": "string"},
                               date_partition="dt")),
        SELECT(jobs.team), FROM(jobs))),
                 ValueError, "was given a write", id="derived_write"),
    pytest.param(lambda: example_database.send("DESCRIBE ops.nope"), ValueError,
                 "The Example database has no table 'ops.nope'", id="example_database_table"),
    pytest.param(lambda: contains(jobs.team, 5), TypeError, "needs a string to look for",
                 id="contains_5"),
    pytest.param(lambda: equals(jobs.team, ["a", "b"]), TypeError, "isn't a single value",
                 id="equals_a_list"),
]


@pytest.mark.parametrize(("make", "error", "said"), MISUSES)
def test_a_misuse_is_refused_in_four_parts(make, error, said) -> None:
    with pytest.raises(error) as refused:
        make()
    message = str(refused.value)
    assert said in message
    for part in ("What happened:", "Why it matters:", "Usual fix:",
                 "Opt-out:        none - this one can't be switched off."):
        assert part in message


def test_every_refusal_is_built_in_refusals_py() -> None:
    """The shared files refuse through refusals.py, so every message has the same four parts:
    none builds one itself. __init__.py builds its import stops before refusals.py loads.

    This reads the source, as no call can show that a file never builds a message; the table
    above shows the four parts of each misuse, and test_refusals.py those of each Guard."""
    folder = Path(__file__).parent.parent / editions.CORE
    for path in folder.glob("*.py"):
        if path.name in ("refusals.py", "__init__.py", "engine.py", "writing.py"):
            continue
        calls = [node.func.id for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        assert "four_part_message" not in calls, f"{path.name} builds a refusal itself"


def test_every_raise_in_refusals_py_has_four_parts() -> None:
    """Each refusal refusals.py raises is built by four_part_message, as the Warning is."""
    tree = ast.parse((Path(__file__).parent.parent / editions.CORE / "refusals.py")
                     .read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
            built = node.exc.args[0] if node.exc.args else None
            assert (isinstance(built, ast.Call) and isinstance(built.func, ast.Name)
                    and built.func.id == "four_part_message"), f"line {node.lineno}"
