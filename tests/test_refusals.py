"""Every Guard, Load limit and Warning refuses (or warns), and its opt-out lets the Statement through.

`refusals.py` holds each one as a function named `guard_...`, `load_limit_...` or
`warning_...`. The last test here goes through them all and fails if one has no test named
`test_<function>_refuses` (or `_warns`), or no `test_<function>_opt_out` unless its docstring
says "No opt-out".
"""

from __future__ import annotations

import datetime
import inspect
import sys
import warnings

import pytest

from sql_composer import (
    AS,
    CROSS_JOIN,
    FROM,
    GROUP_BY,
    INSERT_OVERWRITE,
    JOIN,
    LEFT_JOIN,
    LIMIT,
    ORDER_BY,
    SELECT,
    WHERE,
    GuardRefused,
    LoadRefused,
    Table,
    average_of,
    between,
    by_day,
    count_distinct,
    count_rows,
    derived,
    descending,
    equals,
    is_null,
    run,
    set_load_limits,
    statement,
    sum_of,
    to_hive,
)
from sql_composer import refusals
from sql_composer.example_database import job_runs, jobs, run_alerts
from sql_composer.refusals import RepeatedRowsWarning

DAYS = between(job_runs.dt, "2026-09-23", "2026-09-24")

daily_runs = Table(
    "mart.daily_runs",
    columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    date_partition="dt",
)


def rows_of(n: int):
    """A stand-in for `send` that returns n rows, whatever it is sent."""
    return lambda hive: [None] * n


# --- Guards -------------------------------------------------------------------------------


def test_guard_unnamed_calculation_refuses() -> None:
    with pytest.raises(GuardRefused, match=r"no name: COUNT\(\*\)"):
        SELECT(count_rows())


def test_guard_none_in_condition_refuses() -> None:
    with pytest.raises(GuardRefused, match="is_null"):
        equals(job_runs.status, None)


def test_guard_not_a_number_refuses() -> None:
    with pytest.raises(GuardRefused, match="NaN or infinity"):
        equals(job_runs.duration_mins, float("nan"))


def test_guard_control_character_refuses() -> None:
    with pytest.raises(GuardRefused, match="bell"):
        equals(job_runs.status, "FAILED\x07")


def test_guard_time_of_day_refuses() -> None:
    with pytest.raises(GuardRefused, match="time of day"):
        equals(job_runs.dt, datetime.datetime(2026, 9, 24, 13, 5))


def test_guard_unsafe_regrouping_refuses() -> None:
    with pytest.raises(GuardRefused, match="does_not_add_up"):
        sum_of(job_runs.avg_retry_secs)


def daily(calculation) -> Table:
    """A Derived table with one row per day, holding `calculation` as `per_day`."""
    return derived("daily", statement(
        SELECT(job_runs.dt, AS(calculation, "per_day")),
        FROM(job_runs),
        WHERE(DAYS),
        GROUP_BY(job_runs.dt),
    ))


def usual_fix(refused: pytest.ExceptionInfo) -> str:
    """The "Usual fix" line of a refusal."""
    return str(refused.value).split("Usual fix:")[1].split("\n")[0].strip()


def test_guard_unsafe_regrouping_fix_for_a_distinct_count_counts_again() -> None:
    with pytest.raises(GuardRefused) as refused:
        sum_of(daily(count_distinct(job_runs.job_id)).per_day)
    fix = usual_fix(refused)
    assert "count_distinct(...)" in fix
    assert "sum" not in fix and "divide" not in fix


def test_guard_unsafe_regrouping_fix_for_a_distinct_count_says_when_it_applies() -> None:
    """Averaging daily counts may be what was meant, so the fix says which question it answers."""
    with pytest.raises(GuardRefused) as refused:
        average_of(daily(count_distinct(job_runs.job_id)).per_day)
    fix = usual_fix(refused)
    assert fix.startswith("For a count over the whole span")
    assert "adding up" not in fix


def test_guard_unsafe_regrouping_fix_for_an_average_keeps_the_sum_and_the_count() -> None:
    with pytest.raises(GuardRefused) as refused:
        sum_of(daily(average_of(job_runs.duration_mins)).per_day)
    fix = usual_fix(refused)
    assert "sum_of(...)" in fix and "divide" in fix
    # AVG leaves out NULL, so the count to divide by is of the values that aren't NULL.
    assert "count_rows(where=is_not_null(...))" in fix


def test_guard_unsafe_regrouping_fix_for_a_ratio_keeps_both_sides() -> None:
    with pytest.raises(GuardRefused) as refused:
        sum_of(daily(sum_of(job_runs.duration_mins) / count_rows()).per_day)
    fix = usual_fix(refused)
    assert "both sides of the division" in fix
    assert "count_distinct" not in fix


def test_guard_unsafe_regrouping_fix_for_a_listed_column_covers_each_kind() -> None:
    """A column in does_not_add_up could be any of the three, so the fix names each."""
    with pytest.raises(GuardRefused) as refused:
        sum_of(job_runs.avg_retry_secs)
    fix = usual_fix(refused)
    assert "an average or a ratio" in fix and "divide" in fix
    assert "a distinct count" in fix and "count_distinct(...)" in fix
    # Its parts aren't in the table, so the fix goes back to where it was made.
    assert "the table it was made from" in fix


def test_guard_unsafe_regrouping_opt_out() -> None:
    assert repr(sum_of(job_runs.avg_retry_secs, adds_up=True)) == "SUM(job_runs.avg_retry_secs)"


def test_guard_missing_group_by_refuses() -> None:
    with pytest.raises(GuardRefused, match="SELECT has job_runs.job_id, which GROUP_BY leaves"):
        statement(
            SELECT(job_runs.job_id, job_runs.status, AS(count_rows(), "runs")),
            FROM(job_runs),
            WHERE(DAYS),
            GROUP_BY(job_runs.status),
        )


def test_guard_missing_group_by_fix_keeps_whole_rows() -> None:
    """max_of on each column would take each value from a different row, so it isn't offered."""
    with pytest.raises(GuardRefused) as refused:
        statement(
            SELECT(job_runs.job_id, job_runs.status, AS(count_rows(), "runs")),
            FROM(job_runs),
            WHERE(DAYS),
            GROUP_BY(job_runs.job_id),
        )
    fix = usual_fix(refused)
    assert "Add job_runs.status to GROUP_BY" in fix
    assert "row_number(...)" in fix and "derived(...)" in fix
    assert "max_of" not in fix


def test_guard_left_join_then_where_refuses() -> None:
    with pytest.raises(GuardRefused, match="LEFT_JOIN brought in"):
        statement(
            SELECT(jobs.job_name),
            FROM(jobs),
            LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id), many_matches=True),
            WHERE(DAYS),
        )


def test_guard_left_join_then_where_opt_out() -> None:
    statement(
        SELECT(jobs.job_name),
        FROM(jobs),
        LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id), many_matches=True,
                  keeps_only_matches=True),
        WHERE(DAYS),
    )


def test_guard_cross_join_refuses() -> None:
    with pytest.raises(GuardRefused, match=r"JOIN\(jobs\) has no ON="):
        JOIN(jobs)


def test_guard_cross_join_opt_out() -> None:
    other = AS(jobs, "other")
    s = statement(SELECT(jobs.job_name), FROM(jobs), CROSS_JOIN(other))
    assert "CROSS JOIN ops.jobs AS other" in to_hive(s)


def test_guard_order_by_in_derived_table_refuses() -> None:
    inner = statement(SELECT(jobs.job_name), FROM(jobs), ORDER_BY(jobs.job_name,
                                                                   sorts_everything=True))
    with pytest.raises(GuardRefused, match="may not keep the order"):
        derived("sorted_jobs", inner)


def test_guard_write_lines_up_refuses() -> None:
    with pytest.raises(GuardRefused, match="it leaves out runs, and it also selects dt"):
        statement(
            INSERT_OVERWRITE(daily_runs),
            SELECT(job_runs.job_id, job_runs.dt),
            FROM(job_runs),
            WHERE(equals(job_runs.dt, "2026-09-24")),
        )


def test_guard_one_day_per_write_refuses() -> None:
    backfill = statement(
        INSERT_OVERWRITE(daily_runs),
        SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(DAYS),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    )
    with pytest.raises(GuardRefused, match="covers 2 days"):
        to_hive(backfill)


def test_guard_by_day_limit_refuses() -> None:
    top = statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(DAYS),
                    ORDER_BY(descending(job_runs.duration_mins)), LIMIT(10))
    with pytest.raises(GuardRefused, match="this Statement: it has LIMIT 10"):
        by_day(top)


def test_guard_by_day_grouping_refuses() -> None:
    weekly = statement(
        SELECT(job_runs.status, AS(count_distinct(job_runs.job_id), "jobs")),
        FROM(job_runs),
        WHERE(DAYS),
        GROUP_BY(job_runs.status),
    )
    with pytest.raises(GuardRefused, match="without keeping the Date partition job_runs.dt"):
        by_day(weekly)


# --- The Warning --------------------------------------------------------------------------


def test_warning_repeated_rows_warns() -> None:
    with pytest.warns(RepeatedRowsWarning, match="many_matches=True") as caught:
        JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id))
    assert caught[0].filename == __file__, "the warning points at the user's own JOIN line"


def test_warning_repeated_rows_opt_out() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id), many_matches=True)


def test_a_repeated_rows_warning_shows_on_every_join_that_earns_it() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("default")
        for _ in range(3):
            JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id))
    assert len(caught) == 3


def test_a_table_with_no_key_warns_and_says_to_declare_one() -> None:
    no_key = Table("ops.jobs", columns={"job_id": "bigint", "team": "string"},
                   date_partition=None)
    with pytest.warns(RepeatedRowsWarning, match=r"declares no key.*key=\[\.\.\.\]"):
        JOIN(no_key, ON=equals(no_key.job_id, job_runs.job_id))


def test_a_join_on_the_whole_key_does_not_warn() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id))


def test_joining_a_grouped_derived_table_on_its_groups_does_not_warn() -> None:
    per_run = derived("alerts_per_run", statement(
        SELECT(run_alerts.run_id, AS(count_rows(), "alerts")),
        FROM(run_alerts),
        WHERE(between(run_alerts.dt, "2026-09-23", "2026-09-24")),
        GROUP_BY(run_alerts.run_id),
    ))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        JOIN(per_run, ON=equals(per_run.run_id, job_runs.run_id))


# --- Load limits --------------------------------------------------------------------------


def test_load_limit_date_bound_refuses() -> None:
    with pytest.raises(LoadRefused, match=r"FROM\(job_runs\) reads ops.job_runs"):
        statement(SELECT(job_runs.run_id), FROM(job_runs))


def test_load_limit_date_bound_opt_out() -> None:
    s = statement(SELECT(job_runs.run_id), FROM(job_runs, reads_all_partitions=True))
    assert "WHERE" not in to_hive(s)


def test_a_date_bound_inside_left_joins_on_counts() -> None:
    from sql_composer import all_of

    statement(
        SELECT(jobs.job_name),
        FROM(jobs),
        LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id), DAYS),
                  many_matches=True),
    )


def test_a_date_bound_inside_an_or_does_not_count() -> None:
    from sql_composer import any_of

    with pytest.raises(LoadRefused):
        statement(
            SELECT(job_runs.run_id),
            FROM(job_runs),
            WHERE(any_of(DAYS, is_null(job_runs.status))),
        )


def test_load_limit_order_by_refuses() -> None:
    with pytest.raises(LoadRefused, match="ORDER_BY has no LIMIT"):
        statement(SELECT(jobs.job_name), FROM(jobs), ORDER_BY(jobs.job_name))


def test_load_limit_order_by_says_its_opt_out_isnt_for_a_derived_table() -> None:
    with pytest.raises(LoadRefused) as refused:
        statement(SELECT(jobs.job_name), FROM(jobs), ORDER_BY(jobs.job_name))
    assert "Opt-out:        ORDER_BY(..., sorts_everything=True), but not in a Statement you "         "pass to derived(...)" in str(refused.value)


def test_load_limit_order_by_opt_out() -> None:
    statement(SELECT(jobs.job_name), FROM(jobs), ORDER_BY(descending(jobs.job_name),
                                                          sorts_everything=True))


def test_load_limit_rows_refuses() -> None:
    set_load_limits(rows=3)
    s = statement(SELECT(jobs.job_name), FROM(jobs))
    assert to_hive(s).endswith("LIMIT 3")
    with pytest.raises(LoadRefused, match="got back 3 rows"):
        run(s, send=rows_of(3))


def test_load_limit_rows_opt_out() -> None:
    set_load_limits(rows=3)
    s = statement(SELECT(jobs.job_name), FROM(jobs), returns_all_rows=True)
    assert "LIMIT" not in to_hive(s)
    assert len(run(s, send=rows_of(3))) == 3


def test_a_limit_the_user_writes_is_never_refused() -> None:
    set_load_limits(rows=3)
    s = statement(SELECT(jobs.job_name), FROM(jobs), LIMIT(2))
    assert to_hive(s).endswith("LIMIT 2")
    assert len(run(s, send=rows_of(2))) == 2


def test_load_limit_dates_refuses() -> None:
    set_load_limits(dates=1)
    s = statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(DAYS))
    with pytest.raises(LoadRefused, match="reads 2 days of ops.job_runs"):
        to_hive(s)


def test_load_limit_dates_opt_out() -> None:
    set_load_limits(dates=1)
    s = statement(SELECT(job_runs.run_id), FROM(job_runs, reads_all_partitions=True),
                  WHERE(DAYS))
    to_hive(s)
    for day in by_day(statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(DAYS))):
        to_hive(day)


# --- Every one of them is covered ---------------------------------------------------------


REFUSALS = [
    (name, function)
    for name, function in inspect.getmembers(refusals, inspect.isfunction)
    if name.startswith(("guard_", "load_limit_", "warning_"))
]


def test_refusals_are_found() -> None:
    assert len(REFUSALS) >= 15


@pytest.mark.parametrize(("name", "function"), REFUSALS, ids=[n for n, _ in REFUSALS])
def test_every_refusal_has_its_tests(name: str, function) -> None:
    tests = set(dir(sys.modules[__name__]))
    shown = "warns" if name.startswith("warning_") else "refuses"
    assert f"test_{name}_{shown}" in tests
    if "No opt-out" not in (function.__doc__ or ""):
        assert f"test_{name}_opt_out" in tests


def test_one_helper_builds_every_message() -> None:
    source = inspect.getsource(refusals)
    # The mix-ups between the two Editions are TypeErrors, as other misuses are.
    raised = (source.count("raise GuardRefused(") + source.count("raise LoadRefused(")
              + source.count("raise TypeError("))
    built = source.count("four_part_message(\n")
    assert raised + 1 == built  # plus the Warning, which is shown rather than raised
