"""Windows: window(...) passed as over=, and the functions that always take one (map family 6).

A window names the rows a calculation looks across for each row: those sharing its PARTITION_BY
values, in ORDER_BY's order, and with rows= only those near it. sum_of, average_of, count_rows,
min_of and max_of take one as over=; rank, dense_rank, ntile, lag, lead, first_value and
last_value always take one; row_number takes one too, its 4.x keywords still working. A window's
result is filtered only in the Statement that reads its Derived table, and by_day refuses a
window that looks across days.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    HAVING,
    INSERT_OVERWRITE,
    SELECT,
    WHERE,
    Column,
    GuardRefused,
    Table,
    average_of,
    between,
    by_day,
    count_rows,
    dense_rank,
    derived,
    descending,
    equals,
    first_value,
    hive_function,
    lag,
    last_value,
    lead,
    max_of,
    min_of,
    more_than,
    ntile,
    rank,
    row_number,
    statement,
    sum_of,
    to_hive,
    window,
)
from sqlglot_composer.example_database import job_events, job_runs

DAY = "2026-09-24"
BASE = "/data/your_team/tables"
ONE_DAY = equals(job_runs.dt, DAY)
by_job = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id)


def hive_of(column: Column) -> str:
    """The Hive of one calculation on one line, once a Statement over one day of job_runs
    takes it, as to_hive checks it there."""
    to_hive(statement(SELECT(AS(column, "x")), FROM(job_runs), WHERE(ONE_DAY)))
    return repr(column)


# --- What each one writes --------------------------------------------------------------------


@pytest.mark.parametrize(("column", "hive"), [
    pytest.param(lambda: sum_of(job_runs.duration_mins, over=window(PARTITION_BY=job_runs.job_id)),
                 "SUM(job_runs.duration_mins) OVER (PARTITION BY job_runs.job_id)",
                 id="a_groups_total_beside_each_row"),
    pytest.param(lambda: sum_of(job_runs.duration_mins, over=window(
        PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id, rows=(None, 0))),
                 "SUM(job_runs.duration_mins) OVER (PARTITION BY job_runs.job_id ORDER BY "
                 "job_runs.run_id ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)",
                 id="a_running_total"),
    pytest.param(lambda: average_of(job_runs.duration_mins, over=window(
        PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id, rows=(-6, 0))),
                 "AVG(job_runs.duration_mins) OVER (PARTITION BY job_runs.job_id ORDER BY "
                 "job_runs.run_id ASC ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)",
                 id="a_moving_average"),
    pytest.param(lambda: count_rows(over=window()), "COUNT(*) OVER ()", id="count_every_row"),
    pytest.param(lambda: min_of(job_runs.duration_mins, over=window(
        ORDER_BY=job_runs.run_id, rows=(0, 2))),
                 "MIN(job_runs.duration_mins) OVER (ORDER BY job_runs.run_id ASC ROWS BETWEEN "
                 "CURRENT ROW AND 2 FOLLOWING)", id="following_rows"),
    pytest.param(lambda: max_of(job_runs.duration_mins, over=window(
        ORDER_BY=job_runs.run_id, rows=(None, None))),
                 "MAX(job_runs.duration_mins) OVER (ORDER BY job_runs.run_id ASC ROWS BETWEEN "
                 "UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)", id="every_row_in_order"),
    pytest.param(lambda: rank(over=window(PARTITION_BY=job_runs.job_id,
                                          ORDER_BY=descending(job_runs.duration_mins))),
                 "RANK() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.duration_mins "
                 "DESC)", id="rank"),
    pytest.param(lambda: dense_rank(over=by_job),
                 "DENSE_RANK() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC)",
                 id="dense_rank"),
    pytest.param(lambda: ntile(4, over=by_job),
                 "NTILE(4) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC)",
                 id="ntile"),
    pytest.param(lambda: lag(job_runs.duration_mins, over=by_job),
                 "LAG(job_runs.duration_mins, 1) OVER (PARTITION BY job_runs.job_id ORDER BY "
                 "job_runs.run_id ASC)", id="lag"),
    pytest.param(lambda: lead(job_runs.status, over=by_job, ahead=2),
                 "LEAD(job_runs.status, 2) OVER (PARTITION BY job_runs.job_id ORDER BY "
                 "job_runs.run_id ASC)", id="lead"),
    pytest.param(lambda: first_value(job_runs.status, over=by_job),
                 "FIRST_VALUE(job_runs.status) OVER (PARTITION BY job_runs.job_id ORDER BY "
                 "job_runs.run_id ASC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)",
                 id="first_value_over_the_whole_group"),
    pytest.param(lambda: last_value(job_runs.status, over=window(
        PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id, rows=(None, 0))),
                 "LAST_VALUE(job_runs.status) OVER (PARTITION BY job_runs.job_id ORDER BY "
                 "job_runs.run_id ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)",
                 id="last_value_up_to_each_row"),
    pytest.param(lambda: row_number(over=by_job),
                 "ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC)",
                 id="row_number_over_a_window"),
    pytest.param(lambda: row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id),
                 "ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC)",
                 id="row_number_with_its_4x_keywords"),
])
def test_each_window_function_writes_its_hive(column: Callable[[], Column], hive: str) -> None:
    assert hive_of(column()) == hive


def test_lag_takes_how_many_rows_back() -> None:
    assert hive_of(lag(job_runs.duration_mins, over=by_job, back=7)).startswith(
        "LAG(job_runs.duration_mins, 7) OVER")


def test_a_window_shows_how_it_was_written() -> None:
    assert repr(window(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id),
                       rows=(-6, 0))) == ("window(PARTITION_BY=job_runs.job_id, "
                                          "ORDER_BY=descending(job_runs.run_id), rows=(-6, 0))")


# --- What each one refuses -------------------------------------------------------------------


@pytest.mark.parametrize(("make", "said"), [
    pytest.param(lambda: window(PARTITION_BY="job_id"), "names given in SELECT",
                 id="partition_by_a_name"),
    pytest.param(lambda: window(ORDER_BY=descending("runs")), "names given in SELECT",
                 id="order_by_a_name"),
    pytest.param(lambda: window(PARTITION_BY=job_runs.job_id, rows=(-6, 0)),
                 "rows= needs ORDER_BY", id="rows_without_order_by"),
    pytest.param(lambda: window(ORDER_BY=job_runs.run_id, rows=6), "a pair", id="rows_not_a_pair"),
    pytest.param(lambda: window(ORDER_BY=job_runs.run_id, rows=(0, -6)), "comes before",
                 id="rows_back_to_front"),
    pytest.param(lambda: window(ORDER_BY=job_runs.run_id, rows=(-1.5, 0)), "whole numbers",
                 id="rows_not_whole"),
    pytest.param(lambda: window(PARTITION_BY=row_number(over=by_job)), "inside a Window",
                 id="a_window_inside_a_window"),
    pytest.param(lambda: sum_of(job_runs.duration_mins, over=window(
        PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id)), r"rows=\(None, 0\)",
                 id="a_sum_ordered_with_no_rows"),
    pytest.param(lambda: sum_of(job_runs.duration_mins, over=job_runs.job_id),
                 "over= takes window", id="over_not_a_window"),
    pytest.param(lambda: rank(over=window(PARTITION_BY=job_runs.job_id)), "needs ORDER_BY",
                 id="rank_with_no_order"),
    pytest.param(lambda: lag(job_runs.status, over=window(
        ORDER_BY=job_runs.run_id, rows=(-1, 0))), "takes no rows=", id="lag_with_rows"),
    pytest.param(lambda: lag(job_runs.status, over=by_job, back=0), "back=",
                 id="lag_back_zero"),
    pytest.param(lambda: ntile(0, over=by_job), "ntile", id="ntile_zero_groups"),
    pytest.param(lambda: first_value(job_runs.status, over=window(PARTITION_BY=job_runs.job_id)),
                 "needs ORDER_BY", id="first_value_with_no_order"),
    pytest.param(lambda: row_number(over=by_job, PARTITION_BY=job_runs.job_id),
                 "either over=", id="row_number_both_ways"),
    pytest.param(lambda: row_number(), "ORDER_BY", id="row_number_with_nothing"),
    pytest.param(lambda: sum_of(lag(job_runs.duration_mins, over=by_job)), "through a Window",
                 id="a_window_inside_a_sum"),
])
def test_it_refuses(make: Callable[[], object], said: str) -> None:
    with pytest.raises((TypeError, ValueError), match=said):
        make()


@pytest.mark.parametrize("place", ["WHERE", "HAVING"])
def test_a_windows_result_is_filtered_only_through_a_derived_table(place: str) -> None:
    before = lag(job_runs.duration_mins, over=by_job)
    clauses = [WHERE(ONE_DAY, more_than(before, 5))] if place == "WHERE" else [
        WHERE(ONE_DAY), GROUP_BY(job_runs.job_id), HAVING(more_than(before, 5))]
    with pytest.raises(ValueError, match=rf"(?s){place} has LAG\(.*looks across rows.*derived"):
        statement(SELECT(job_runs.job_id), FROM(job_runs), *clauses)


def test_a_window_filtered_in_the_statement_that_reads_it() -> None:
    with_before = derived("with_before", statement(
        SELECT(job_runs.run_id, AS(lag(job_runs.duration_mins, over=by_job), "before")),
        FROM(job_runs), WHERE(ONE_DAY)))
    s = statement(SELECT(with_before.run_id), FROM(with_before),
                  WHERE(more_than(with_before.before, 5)))
    assert "with_before.before > 5" in to_hive(s)


def test_a_grouped_statement_refuses_a_window_over_a_column_it_doesnt_group() -> None:
    with pytest.raises(GuardRefused, match="job_runs.duration_mins"):
        statement(SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins,
                                                    over=window()), "everything")),
                  FROM(job_runs), WHERE(ONE_DAY), GROUP_BY(job_runs.job_id))


def test_a_windows_total_beside_each_row_doesnt_add_up_again() -> None:
    totals = derived("totals", statement(
        SELECT(job_runs.run_id, job_runs.job_id,
               AS(sum_of(job_runs.duration_mins, over=window(PARTITION_BY=job_runs.job_id)),
                  "job_minutes")),
        FROM(job_runs), WHERE(ONE_DAY)))
    with pytest.raises(GuardRefused, match="job_minutes"):
        statement(SELECT(totals.job_id, AS(sum_of(totals.job_minutes), "m")), FROM(totals),
                  GROUP_BY(totals.job_id))


def test_hive_function_points_a_window_function_at_its_toolbox_name() -> None:
    with pytest.raises(ValueError, match=r"lag\(column, over=window\(\.\.\.\)\)"):
        hive_function("lag", job_runs.duration_mins, 1)


# --- Keys ------------------------------------------------------------------------------------

newest_per_job = Table("mart.newest_per_job_w", columns={
    "job_id": "bigint", "run_id": "bigint", "dt": "string"}, date_partition="dt",
    key=["job_id", "dt"], location=BASE)
runs_with_before = Table("mart.runs_with_before", columns={
    "run_id": "bigint", "before": "int", "dt": "string"}, date_partition="dt",
    key=["run_id", "dt"], location=BASE)


def test_a_row_number_over_a_window_kept_at_1_shows_the_key() -> None:
    numbered = derived("numbered", statement(
        SELECT(job_runs.job_id, job_runs.run_id, AS(row_number(over=window(
            PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id))), "newest")),
        FROM(job_runs), WHERE(ONE_DAY)))
    s = statement(INSERT_OVERWRITE(newest_per_job), SELECT(numbered.job_id, numbered.run_id),
                  FROM(numbered), WHERE(equals(numbered.newest, 1)))
    assert "PARTITION(dt = '2026-09-24')" in to_hive(s)


def test_a_rank_kept_at_1_doesnt_show_the_key() -> None:
    ranked = derived("ranked", statement(
        SELECT(job_runs.job_id, job_runs.run_id, AS(rank(over=window(
            PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.duration_mins))),
            "longest")),
        FROM(job_runs), WHERE(ONE_DAY)))
    with pytest.raises(GuardRefused, match="Key"):
        statement(INSERT_OVERWRITE(newest_per_job), SELECT(ranked.job_id, ranked.run_id),
                  FROM(ranked), WHERE(equals(ranked.longest, 1)))


def test_a_lag_keeps_the_rows_and_so_the_from_tables_key() -> None:
    s = statement(INSERT_OVERWRITE(runs_with_before),
                  SELECT(job_runs.run_id, AS(lag(job_runs.duration_mins, over=by_job), "before")),
                  FROM(job_runs), WHERE(ONE_DAY))
    assert "LAG(job_runs.duration_mins, 1) OVER" in to_hive(s)


# --- by_day ----------------------------------------------------------------------------------

events_before = Table("mart.events_before", columns={
    "event_id": "bigint", "minutes": "int", "minutes_before": "int", "dt": "string"},
    date_partition="dt", key=["event_id", "dt"], location=BASE)


def finished_with_the_run_before(first: str, last: str) -> Table:
    """Each finish of job_events between two days, with the minutes of the job's finish
    before it, which may be on an earlier day."""
    return derived("with_before", statement(
        SELECT(job_events.event_id, job_events.dt, job_events.minutes,
               AS(lag(job_events.minutes, over=window(PARTITION_BY=job_events.job_id,
                                                      ORDER_BY=job_events.dt)),
                  "minutes_before")),
        FROM(job_events),
        WHERE(between(job_events.dt, first, last), equals(job_events.event_type, "finish"))))


def test_by_day_refuses_a_window_that_looks_across_days() -> None:
    with_before = finished_with_the_run_before("2026-09-18", "2026-09-24")
    s = statement(SELECT(all_of_with_before(with_before)), FROM(with_before))
    with pytest.raises(GuardRefused, match=r"lag\(.*looks across days") as refused:
        by_day(s)
    message = str(refused.value)
    assert "PARTITION_BY" in message and "the days before it" in message


def all_of_with_before(t: Table) -> list[Column]:
    return [t.event_id, t.dt, t.minutes, t.minutes_before]


@pytest.mark.parametrize("numbering", [
    pytest.param(lambda: row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id),
                 id="its_4x_keywords"),
    pytest.param(lambda: row_number(over=by_job), id="over_a_window"),
])
def test_by_day_says_where_the_day_goes_in_either_form_of_row_number(
        numbering: Callable[[], Column]) -> None:
    s = statement(SELECT(job_runs.run_id, AS(numbering(), "rn")), FROM(job_runs),
                  WHERE(between(job_runs.dt, "2026-09-23", DAY)))
    with pytest.raises(GuardRefused) as refused:
        by_day(s)
    fix = str(refused.value).split("Usual fix:", 1)[1]
    assert "Add job_runs.dt to PARTITION_BY= of row_number(...)" in fix
    assert "window(...) of" not in fix


def test_by_day_splits_a_window_within_each_day() -> None:
    per_day = statement(
        SELECT(job_events.event_id, AS(sum_of(job_events.minutes, over=window(
            PARTITION_BY=[job_events.dt, job_events.job_id])), "job_minutes")),
        FROM(job_events), WHERE(between(job_events.dt, "2026-09-23", DAY)))
    assert len(by_day(per_day)) == 2


def test_a_write_reads_the_earlier_days_and_writes_one() -> None:
    with_before = finished_with_the_run_before("2026-09-17", DAY)
    s = statement(INSERT_OVERWRITE(events_before),
                  SELECT(with_before.event_id, with_before.minutes, with_before.minutes_before),
                  FROM(with_before), WHERE(equals(with_before.dt, DAY)))
    hive = to_hive(s)
    assert "INSERT OVERWRITE TABLE mart.events_before PARTITION(dt = '2026-09-24')" in hive
    assert "job_events.dt BETWEEN '2026-09-17' AND '2026-09-24'" in hive
    assert "with_before.dt = '2026-09-24'" in hive


def test_a_write_still_refuses_several_days_when_nothing_keeps_one() -> None:
    with_before = finished_with_the_run_before("2026-09-17", DAY)
    s = statement(INSERT_OVERWRITE(events_before),
                  SELECT(with_before.event_id, with_before.minutes, with_before.minutes_before),
                  FROM(with_before))
    with pytest.raises(GuardRefused, match="covers 8 days") as refused:
        to_hive(s)
    assert "WHERE(equals(the_derived_table.dt, day))" in str(refused.value)


def test_a_write_with_no_window_still_refuses_several_days_a_step_above_keeps_one_of() -> None:
    # Keeping one day in a step above is the fix for a Window that looks back, and for
    # nothing else: a write with no Window reads the one day it writes, as in 4.x.
    finishes = derived("finishes", statement(
        SELECT(job_events.event_id, job_events.dt, job_events.minutes),
        FROM(job_events),
        WHERE(between(job_events.dt, "2026-09-17", DAY), equals(job_events.event_type, "finish"))))
    s = statement(INSERT_OVERWRITE(events_before),
                  SELECT(finishes.event_id, finishes.minutes,
                         AS(finishes.minutes, "minutes_before")),
                  FROM(finishes), WHERE(equals(finishes.dt, DAY)))
    with pytest.raises(GuardRefused, match="reads 8 days") as refused:
        to_hive(s)
    message = str(refused.value)
    # Its reason is the Window rule, not "every day's rows would land in that one day", which
    # isn't so here: the step above keeps one day.
    assert "keeps one of them with equals(finishes.dt, ...)" in message
    assert "Only a write whose Window looks back" in message
    assert "every day's rows would land" not in message
    assert "WHERE(equals(job_events.dt, day))" in message


def test_a_write_refuses_a_kept_day_its_from_table_doesnt_read() -> None:
    with_before = finished_with_the_run_before("2026-09-17", "2026-09-20")
    s = statement(INSERT_OVERWRITE(events_before),
                  SELECT(with_before.event_id, with_before.minutes, with_before.minutes_before),
                  FROM(with_before), WHERE(equals(with_before.dt, DAY)))
    with pytest.raises(ValueError, match="2026-09-24"):
        to_hive(s)
