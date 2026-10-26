"""Each misuse a beginner is likely to make is refused with all four parts and no opt-out."""

from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from sqlglot_composer import (
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
    Statement,
    Table,
    all_columns,
    any_of,
    at_least,
    contains,
    count_rows,
    create_table,
    derived,
    descending,
    equals,
    example_database,
    export_lineage,
    first_match,
    hive_function,
    if_else,
    is_in,
    is_null,
    last_n_days,
    mapped,
    run_query, run_execute,
    set_load_limits,
    statement,
    sum_of,
    to_hive,
)
from sqlglot_composer.example_database import job_owners, job_runs, jobs

FAILED = equals(job_runs.status, "FAILED")
# A table whose column's type isn't known, so nothing but its keys says what type they are.
UNTYPED = Table("ops.codes", columns={"code": None})

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
    pytest.param(lambda: JOIN(jobs, ON=equals(jobs.job_id, jobs.job_id)), ValueError,
                 "compares jobs.job_id with jobs.job_id: both sides are tables called jobs",
                 id="join_on_itself"),
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
    # Toolbox 7.2, ticket 04: first_match and mapped.
    pytest.param(lambda: first_match([]), ValueError, "first_match(...) was given an empty list",
                 id="first_match_empty"),
    pytest.param(lambda: first_match((FAILED, "failed")), TypeError,
                 "where a list of (condition, value) pairs goes", id="first_match_one_pair"),
    pytest.param(lambda: first_match([FAILED]), TypeError,
                 'pair 1 is equals(job_runs.status, "FAILED"), which isn\'t a (condition, '
                 "value) pair",
                 id="first_match_not_a_pair"),
    pytest.param(lambda: first_match([(5, "failed")]), TypeError,
                 "pair 1 has 5 where a condition goes", id="first_match_5"),
    pytest.param(lambda: first_match([("failed", FAILED)]), TypeError,
                 "pair 1 has the condition second", id="first_match_swapped"),
    pytest.param(lambda: first_match([(FAILED, FAILED)]), TypeError,
                 "was given equals(job_runs.status, \"FAILED\") as pair 1's value, where a "
                 "value goes", id="first_match_condition_value"),
    pytest.param(lambda: first_match([(FAILED, "failed")], otherwise=FAILED), TypeError,
                 "as otherwise=, where a value goes", id="first_match_condition_otherwise"),
    pytest.param(lambda: first_match([(FAILED, "failed"), (is_null(job_runs.status), 0)]),
                 TypeError, 'gives values whose types don\'t mix: "failed", a string, and 0, '
                 "a number", id="first_match_mixed"),
    pytest.param(lambda: first_match([(FAILED, job_runs.duration_mins)], otherwise="none"),
                 TypeError, "job_runs.duration_mins, an int column", id="first_match_mixed_else"),
    pytest.param(lambda: mapped(job_runs.status, {}), ValueError,
                 "mapped(job_runs.status, ...) was given an empty dict", id="mapped_empty"),
    pytest.param(lambda: mapped(job_runs.status, ["FAILED"]), TypeError,
                 "where a dict of values goes", id="mapped_a_list"),
    pytest.param(lambda: mapped(5, {"a": 1}), TypeError, "where a column goes", id="mapped_5"),
    pytest.param(lambda: mapped(job_runs.job_id, {"one": "nightly"}), TypeError,
                 "compares job_runs.job_id, a bigint column, with 'one'",
                 id="mapped_key_of_another_type"),
    pytest.param(lambda: mapped(UNTYPED.code, {1: "one", "b": "bee"}), TypeError,
                 "gives keys whose types don't mix: 1, a number, and \"b\", a string",
                 id="mapped_keys_mixed"),
    pytest.param(lambda: mapped(job_runs.status, {job_runs.status: "same"}), TypeError,
                 "was given job_runs.status as a key, where a value to look up goes",
                 id="mapped_column_key"),
    pytest.param(lambda: mapped(job_runs.status, {"FAILED": "failed", "TEST": 0}), TypeError,
                 "gives values whose types don't mix", id="mapped_mixed"),
    pytest.param(lambda: mapped(job_runs.status, {"FAILED": FAILED}), TypeError,
                 "where a value goes", id="mapped_condition_value"),
    pytest.param(lambda: descending(5), TypeError, "where a column goes", id="descending_5"),
    pytest.param(lambda: hive_function("drop table", jobs.team), ValueError,
                 "isn't a function name", id="hive_function_name"),
    pytest.param(lambda: to_hive(42), TypeError, "isn't a Statement", id="to_hive_42"),
    pytest.param(lambda: run_query(statement(SELECT(jobs.team), FROM(jobs))), TypeError,
                 "run_query needs query=, and wasn't given it", id="run_query_no_query"),
    pytest.param(lambda: run_query(statement(SELECT(jobs.team), FROM(jobs)), 5), TypeError,
                 "run_query: query= is an int, not a function", id="run_query_5"),
    pytest.param(lambda: job_runs.duration_mins + "a", TypeError, "+ was used with 'a'",
                 id="plus_text"),
    pytest.param(lambda: export_lineage(), TypeError, "was given no Statement",
                 id="lineage_nothing"),
    pytest.param(lambda: export_lineage(5), TypeError, "isn't a Statement", id="lineage_5"),
    pytest.param(lambda: set_load_limits(rows=-1), ValueError, "a limit must be a whole number",
                 id="load_limits_negative"),
    pytest.param(lambda: Table("bad name", columns={"a": "string"}),
                 ValueError, "isn't a table name", id="table_name"),
    pytest.param(lambda: Table("ops.t", columns={"a": "string"}, date_format="%Y%m%d"),
                 TypeError, "was given date_format=, which Toolbox 7.0 replaced",
                 id="table_date_format"),
    pytest.param(lambda: Table("ops.t", columns={"a": "string"}, date_partition="a"),
                 TypeError, "was given date_partition=, which Toolbox 7.0 replaced",
                 id="table_date_partition"),
    pytest.param(lambda: Table("ops.t", columns={"a": "string"}, partitioned_by=5),
                 ValueError, "partitioned_by=5 isn't a list of column names",
                 id="table_partitioned_by_5"),
    pytest.param(lambda: Table("ops.t", columns=["a"]), ValueError,
                 "needs a dict of column names", id="table_columns_list"),
    pytest.param(lambda: Table("ops.t", columns={"a": "string"}, key=["b"]),
                 ValueError, "isn't one of its columns", id="table_key_not_a_column"),
    pytest.param(lambda: Table("ops.t", columns={"a": "string"}, key=5),
                 ValueError, "isn't a list of column names", id="table_key_5"),
    pytest.param(lambda: derived("x", statement(
        INSERT_OVERWRITE(Table("mart.d", columns={"team": "string", "dt": "string"},
                               partitioned_by=["dt"], location="/data/your_team/mart.db/d"),
                         partition={"dt": "2026-09-24"}),
        SELECT(jobs.team), FROM(jobs))),
                 ValueError, "was given a write", id="derived_write"),
    pytest.param(lambda: example_database.query("DESCRIBE ops.nope"), ValueError,
                 "The Example database has no table 'ops.nope'", id="example_database_table"),
    pytest.param(lambda: contains(jobs.team, 5), TypeError, "needs a string to look for",
                 id="contains_5"),
    pytest.param(lambda: equals(jobs.team, ["a", "b"]), TypeError, "isn't a single value",
                 id="equals_a_list"),
    pytest.param(lambda: run_query(teams(), lambda hive: [("data",), ("finance",)]), TypeError,
                 "Your query gave back a list, where a pandas DataFrame goes",
                 id="run_query_list"),
    pytest.param(lambda: run_query(to_hive(teams()), example_database.query), TypeError,
                 "run_query was given 'SELECT", id="run_hive_text"),
]


def teams() -> Statement:
    return statement(SELECT(jobs.team), FROM(jobs))


@pytest.mark.parametrize(("make", "error", "said"), MISUSES)
def test_a_misuse_is_refused_in_four_parts(make: Callable[[], object], error: type[Exception],
                                           said: str) -> None:
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
    folder = Path(__file__).parent.parent / "sqlglot_composer"
    for path in folder.glob("*.py"):
        if path.name in ("refusals.py", "__init__.py", "engine.py", "writing.py"):
            continue
        calls = [node.func.id for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        assert "four_part_message" not in calls, f"{path.name} builds a refusal itself"


def test_every_raise_in_refusals_py_has_four_parts() -> None:
    """Each refusal refusals.py raises is built by four_part_message, as the Warning is."""
    tree = ast.parse((Path(__file__).parent.parent / "sqlglot_composer" / "refusals.py")
                     .read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
            built = node.exc.args[0] if node.exc.args else None
            assert (isinstance(built, ast.Call) and isinstance(built.func, ast.Name)
                    and built.func.id == "four_part_message"), f"line {node.lineno}"


# --- run given what isn't a Statement --------------------------------------------------------


def usual_fix(refused: pytest.ExceptionInfo) -> str:
    """The "Usual fix" line of a refusal."""
    return str(refused.value).split("Usual fix:")[1].split("\n")[0].strip()


def test_where_passes_over_an_empty_list_that_any_of_refuses() -> None:
    """WHERE and any_of check their conditions with one helper, but WHERE flattens first: an
    empty list beside a condition is nothing to WHERE, and no conditions to any_of."""
    failed = equals(jobs.team, "data")
    hive = to_hive(statement(SELECT(jobs.job_id), FROM(jobs), WHERE([], failed)))
    assert "WHERE\n  jobs.team = 'data'" in hive
    with pytest.raises(TypeError, match=r"any_of\(\.\.\.\) was given no conditions"):
        any_of([], failed)


def test_run_query_given_a_derived_table_says_to_wrap_it_in_a_statement() -> None:
    per_team = derived("per_team", teams())
    with pytest.raises(TypeError) as refused:
        run_query(per_team, example_database.query)
    assert "run_query was given derived('per_team'" in str(refused.value)
    assert "statement(SELECT(all_columns(per_team)), FROM(per_team))" in usual_fix(refused)
    # The fix it gives is a Statement that reads the Derived table.
    sent = []
    run_query(statement(SELECT(all_columns(per_team)), FROM(per_team)),
              lambda hive: sent.append(hive) or pd.DataFrame({"team": []}))
    assert sent[0].endswith("FROM per_team")


def test_run_execute_given_a_derived_table_says_to_write_its_rows() -> None:
    """run_execute sends only what changes something, so its fix is a write, not a read it
    would refuse in turn."""
    per_team = derived("per_team", teams())
    with pytest.raises(TypeError) as refused:
        run_execute(per_team, example_database.execute)
    assert usual_fix(refused).endswith(
        "run_execute(statement(INSERT_OVERWRITE(t), SELECT(all_columns(per_team)), "
        "FROM(per_team)), execute), where t is the Saved table to write.")


def test_a_derived_table_with_no_variable_name_is_called_d_in_the_fix() -> None:
    """Its name in the Hive isn't a Python name, so the fix doesn't paste it as one."""
    with pytest.raises(TypeError) as refused:
        run_query(derived("per_team", teams()), example_database.query)
    assert usual_fix(refused).endswith(
        "run_query(statement(SELECT(all_columns(d)), FROM(d)), query), where d is the Derived "
        "table.")


def test_run_query_given_a_list_says_to_send_each_in_turn() -> None:
    steps = [teams(), teams()]
    with pytest.raises(TypeError, match=r"run_query was given \[") as refused:
        run_query(steps, example_database.query)
    assert "for step in steps:" in usual_fix(refused)


# --- what a query gives back -----------------------------------------------------------------


class _OtherLibrarysDataFrame:
    """A DataFrame of a library other than pandas, such as polars'."""


_OtherLibrarysDataFrame.__name__ = "DataFrame"
_OtherLibrarysDataFrame.__module__ = "polars.dataframe.frame"


@pytest.mark.parametrize(("answer", "said"), [
    pytest.param([("data",), ("finance",)], "a list", id="a_list"),
    pytest.param(None, "None", id="none"),
    pytest.param({"team": ["data"]}, "a dict", id="a_dict"),
    pytest.param(_OtherLibrarysDataFrame(), "a polars DataFrame", id="another_librarys_dataframe"),
])
def test_a_query_that_doesnt_give_back_a_dataframe_is_refused(answer: object, said: str) -> None:
    with pytest.raises(TypeError) as refused:
        run_query(teams(), lambda hive: answer)
    message = str(refused.value)
    assert f"Your query gave back {said}, where a pandas DataFrame goes." in message
    assert "pd.DataFrame(rows)" in usual_fix(refused)
    assert "columns=" in usual_fix(refused)


def test_a_write_isnt_refused_for_what_its_execute_gives_back() -> None:
    """A write goes to execute, whose result is never read: run gives back None whatever it
    gave."""
    owners = Table("mart.job_owners", columns=dict(job_owners._columns), partitioned_by=["dt"],
                   location="/data/your_team/mart.db/job_owners")
    assert run_execute(create_table(owners, may_exist=True), lambda hive: "anything") is None


# --- a calculation's name where a column goes ------------------------------------------------


def test_a_calculations_name_in_a_condition_says_to_write_the_calculation() -> None:
    with pytest.raises(TypeError) as refused:
        at_least("runs", 3)
    fix = usual_fix(refused)
    assert "AS(" in fix and "write the calculation itself" in fix


def test_a_text_in_is_null_isnt_taken_for_a_calculations_name() -> None:
    """is_null takes no value, and a count is never NULL, so the hint isn't given there."""
    with pytest.raises(TypeError) as refused:
        is_null("runs")
    assert "AS(" not in usual_fix(refused)
