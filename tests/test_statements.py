"""How a Statement is written, checked and turned into Hive, seen through the public names."""

from __future__ import annotations

import datetime
import warnings

import numpy as np
import pandas as pd
import pytest

from sql_composer import (
    AS,
    FROM,
    GROUP_BY,
    HAVING,
    INSERT_INTO,
    INSERT_OVERWRITE,
    JOIN,
    LIMIT,
    ORDER_BY,
    SELECT,
    SELECT_DISTINCT,
    WHERE,
    GuardRefused,
    LoadRefused,
    Table,
    all_columns,
    any_of,
    between,
    by_day,
    count_distinct,
    count_rows,
    derived,
    descending,
    equals,
    first_look,
    hive_function,
    is_in,
    last_n_days,
    row_number,
    set_load_limits,
    statement,
    sum_of,
    to_hive,
    week_start,
)
from sql_composer import running
from sql_composer.example_database import job_runs, jobs, run_alerts

DAYS = between(job_runs.dt, "2026-09-23", "2026-09-24")


# --- Columns ------------------------------------------------------------------------------


def test_a_typo_in_a_column_fails_with_the_column_list() -> None:
    with pytest.raises(AttributeError, match="Did you mean 'status'"):
        job_runs.stauts
    assert not hasattr(job_runs, "stauts")
    assert "status" in dir(job_runs)


@pytest.mark.parametrize(
    ("write", "points_to"),
    [
        (lambda: job_runs.status == "FAILED", "equals"),
        (lambda: job_runs.status != "FAILED", "not_equals"),
        (lambda: job_runs.duration_mins > 5, "more_than"),
        (lambda: job_runs.duration_mins <= 5, "at_most"),
        (lambda: equals(jobs.team, "a") & equals(jobs.team, "b"), "all_of"),
        (lambda: equals(jobs.team, "a") | equals(jobs.team, "b"), "any_of"),
        (lambda: bool(job_runs.status), "equals"),
    ],
)
def test_python_operators_that_would_mislead_are_refused(write, points_to) -> None:
    with pytest.raises(TypeError, match=points_to):
        write()


def test_arithmetic_comes_out_bracketed() -> None:
    minutes, retries = job_runs.duration_mins, job_runs.avg_retry_secs
    assert repr((minutes + 1) / 2) == "(job_runs.duration_mins + 1) / 2"
    assert repr(minutes / (retries + 1)) == "job_runs.duration_mins / (job_runs.avg_retry_secs + 1)"
    assert repr(60 * minutes - 1) == "(60 * job_runs.duration_mins) - 1"
    assert repr(-minutes) == "0 - job_runs.duration_mins"


def test_a_division_does_not_add_up() -> None:
    with pytest.raises(GuardRefused, match="which is a division"):
        sum_of(job_runs.duration_mins / 60)


def test_arithmetic_refuses_what_isnt_a_number() -> None:
    with pytest.raises(TypeError, match="needs a number"):
        job_runs.duration_mins + "5"


# --- Values -------------------------------------------------------------------------------


def test_a_value_of_the_wrong_type_for_a_typed_column_is_refused() -> None:
    with pytest.raises(TypeError, match="a string column"):
        equals(job_runs.dt, 20260925)
    with pytest.raises(TypeError, match="a int column"):
        equals(job_runs.duration_mins, "30")


def test_numpy_and_pandas_values_become_plain_values() -> None:
    assert repr(equals(job_runs.duration_mins, np.int64(30))) == "job_runs.duration_mins = 30"
    assert repr(equals(job_runs.status, np.str_("FAILED"))) == "job_runs.status = 'FAILED'"
    midnight = pd.Timestamp("2026-09-24")
    assert repr(equals(job_runs.dt, midnight)) == "job_runs.dt = '2026-09-24'"
    assert repr(is_in(job_runs.run_id, np.array([95, 96]))) == "job_runs.run_id IN (95, 96)"


def test_a_missing_pandas_value_counts_as_none() -> None:
    with pytest.raises(GuardRefused, match="is_null"):
        equals(job_runs.dt, pd.NaT)


def test_a_timestamp_column_keeps_the_time_of_day() -> None:
    events = Table("ops.events", columns={"at": "timestamp", "dt": "string"},
                   date_partition="dt")
    at = datetime.datetime(2026, 9, 24, 13, 5)
    assert repr(equals(events.at, at)) == "events.at = '2026-09-24 13:05:00'"
    assert repr(last_n_days(events.at, 2)) == (
        "events.at >= '2026-09-23' AND events.at < '2026-09-25'")


def test_a_date_partition_in_another_format_is_written_in_that_format() -> None:
    compact = Table("ops.compact", columns={"n": "int", "day": "string"},
                    date_partition="day", date_format="%Y%m%d")
    assert repr(equals(compact.day, datetime.date(2026, 9, 24))) == "compact.day = '20260924'"
    assert repr(last_n_days(compact.day, 2)) == "compact.day BETWEEN '20260923' AND '20260924'"
    assert repr(week_start(compact.day)) == (
        "NEXT_DAY(DATE_ADD(FROM_UNIXTIME(UNIX_TIMESTAMP(compact.day, 'yyyyMMdd'), "
        "'yyyy-MM-dd'), 7 * -1), 'MO')")


def test_between_refuses_days_in_the_wrong_order() -> None:
    with pytest.raises(ValueError, match="starts after it ends"):
        between(job_runs.dt, "2026-09-24", "2026-09-01")


def test_is_in_needs_a_non_empty_list() -> None:
    with pytest.raises(ValueError, match="empty"):
        is_in(job_runs.status, [])
    with pytest.raises(TypeError, match="list of values"):
        is_in(job_runs.status, "FAILED")


def test_hive_function_refuses_a_name_that_isnt_a_plain_name() -> None:
    with pytest.raises(ValueError, match="plain"):
        hive_function("upper(x); drop table y; --", jobs.team)
    with pytest.raises(TypeError, match="don't fit"):
        hive_function("regexp_extract", jobs.team)


def test_hive_function_output_reads_back_the_same_on_every_version() -> None:
    days = hive_function("datediff", job_runs.dt, "2026-09-01")
    to_hive(statement(SELECT(AS(days, "days")), FROM(job_runs), WHERE(DAYS)))


# --- statement(...) -----------------------------------------------------------------------


def test_clauses_must_come_in_sql_order() -> None:
    with pytest.raises(ValueError, match="SQL order"):
        statement(FROM(jobs), SELECT(jobs.team))
    with pytest.raises(ValueError, match="one WHERE"):
        statement(SELECT(jobs.team), FROM(jobs), WHERE(equals(jobs.team, "a")),
                  WHERE(equals(jobs.team, "b")))
    with pytest.raises(ValueError, match="no FROM"):
        statement(SELECT(jobs.team))
    with pytest.raises(TypeError, match="isn't a clause"):
        statement(SELECT(jobs.team), FROM(jobs), equals(jobs.team, "a"))


def test_a_column_of_a_table_the_statement_doesnt_read_is_refused() -> None:
    with pytest.raises(ValueError, match="doesn't read"):
        statement(SELECT(jobs.team, job_runs.status), FROM(jobs))


def test_the_same_table_twice_needs_a_second_name() -> None:
    with pytest.raises(ValueError, match="AS"):
        statement(SELECT(job_runs.run_id), FROM(job_runs),
                  JOIN(job_runs, ON=equals(job_runs.run_id, job_runs.run_id), many_matches=True),
                  WHERE(DAYS))
    earlier = AS(job_runs, "earlier")
    with pytest.raises(LoadRefused, match=r"JOIN\(earlier, ON=\.\.\.\)"):
        statement(SELECT(job_runs.run_id), FROM(job_runs),
                  JOIN(earlier, ON=equals(earlier.run_id, job_runs.run_id)), WHERE(DAYS))
    hive = to_hive(statement(
        SELECT(job_runs.run_id, AS(earlier.status, "earlier_status")),
        FROM(job_runs),
        JOIN(earlier, ON=equals(earlier.run_id, job_runs.run_id)),
        WHERE(DAYS, between(earlier.dt, "2026-09-23", "2026-09-24")),
    ))
    assert "JOIN ops.job_runs AS earlier" in hive


def test_select_refuses_two_columns_with_one_name() -> None:
    with pytest.raises(ValueError, match="more than one column called job_id"):
        SELECT(job_runs.job_id, jobs.job_id)


def test_select_refuses_a_table_or_a_condition() -> None:
    with pytest.raises(TypeError, match="all_columns"):
        SELECT(jobs)
    with pytest.raises(TypeError, match="if_else"):
        SELECT(equals(jobs.team, "web"))


def test_where_refuses_a_count_and_points_to_having() -> None:
    from sql_composer import at_least

    with pytest.raises(ValueError, match="HAVING"):
        statement(SELECT(jobs.team), FROM(jobs), WHERE(at_least(count_rows(), 2)))
    statement(SELECT(jobs.team), FROM(jobs), GROUP_BY(jobs.team),
              HAVING(at_least(count_rows(), 2)))


def test_group_by_an_unknown_output_name_is_refused() -> None:
    with pytest.raises(ValueError, match="no column called 'wek'"):
        statement(SELECT(AS(week_start(job_runs.dt), "week")), FROM(job_runs), WHERE(DAYS),
                  GROUP_BY("wek"))


def test_a_calculation_made_from_grouped_columns_needs_no_group_of_its_own() -> None:
    statement(SELECT(AS(hive_function("upper", jobs.team), "team")), FROM(jobs),
              GROUP_BY(jobs.team))


def test_all_columns_expands_to_the_explicit_list() -> None:
    hive = to_hive(statement(SELECT(all_columns(jobs)), FROM(jobs)))
    assert "*" not in hive
    assert "jobs.region" in hive


def test_first_look_on_a_table_with_no_date_partition() -> None:
    assert to_hive(first_look(jobs)).endswith("FROM ops.jobs AS jobs\nLIMIT 20")


def test_a_reserved_word_as_a_name_is_quoted() -> None:
    odd = Table("ops.odd", columns={"user": "string", "select": "int"}, date_partition=None)
    hive = to_hive(statement(SELECT(odd.user, AS(getattr(odd, "select"), "order")), FROM(odd)))
    assert "odd.`user`" in hive and "AS `order`" in hive


# --- Derived tables -----------------------------------------------------------------------


def per_run():
    return derived("alerts_per_run", statement(
        SELECT(run_alerts.run_id, AS(count_rows(), "alerts"),
               AS(count_distinct(run_alerts.severity), "severities")),
        FROM(run_alerts),
        WHERE(between(run_alerts.dt, "2026-09-23", "2026-09-24")),
        GROUP_BY(run_alerts.run_id),
    ))


def test_a_derived_tables_columns_are_checked() -> None:
    with pytest.raises(AttributeError, match="alerts_per_run has no column 'alert'"):
        per_run().alert


def test_a_derived_distinct_count_does_not_add_up() -> None:
    with pytest.raises(GuardRefused, match="a distinct count"):
        sum_of(per_run().severities)
    sum_of(per_run().alerts)


def test_derived_tables_become_ctes_each_after_the_ones_it_reads() -> None:
    first = per_run()
    busy = derived("busy_runs", statement(
        SELECT(first.run_id, first.alerts),
        FROM(first),
        WHERE(equals(first.alerts, 3)),
    ))
    hive = to_hive(statement(
        SELECT(job_runs.run_id, busy.alerts),
        FROM(job_runs),
        JOIN(busy, ON=equals(busy.run_id, job_runs.run_id)),
        WHERE(DAYS),
    ))
    assert hive.index("WITH alerts_per_run AS") < hive.index("busy_runs AS (")
    assert hive.count("alerts_per_run AS (") == 1


def test_two_different_derived_tables_with_one_name_are_refused() -> None:
    other = AS(derived("alerts_per_run", statement(SELECT(jobs.job_id), FROM(jobs))), "other")
    first = per_run()
    with pytest.raises(ValueError, match="two different Derived tables"):
        statement(SELECT(first.run_id), FROM(first),
                  JOIN(other, ON=equals(other.job_id, first.run_id), many_matches=True))


def test_a_derived_table_keeps_its_sources_key_when_it_only_filters() -> None:
    failed = derived("failed", statement(SELECT(job_runs.run_id, job_runs.status),
                                         FROM(job_runs), WHERE(DAYS)))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        JOIN(failed, ON=equals(failed.run_id, run_alerts.run_id))
    teams = derived("teams", statement(SELECT_DISTINCT(jobs.team), FROM(jobs)))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        JOIN(teams, ON=equals(teams.team, jobs.team))


def test_a_write_cant_be_a_derived_table() -> None:
    daily = Table("mart.daily", columns={"runs": "bigint", "dt": "string"},
                  date_partition="dt")
    write = statement(INSERT_OVERWRITE(daily), SELECT(AS(count_rows(), "runs")),
                      FROM(job_runs), WHERE(equals(job_runs.dt, "2026-09-24")),
                      GROUP_BY(job_runs.dt))
    with pytest.raises(ValueError, match="write"):
        derived("daily", write)


def test_latest_row_per_key_with_row_number() -> None:
    ranked = derived("ranked", statement(
        SELECT(job_runs.job_id, job_runs.status,
               AS(row_number(PARTITION_BY=job_runs.job_id,
                             ORDER_BY=descending(job_runs.run_id)), "rn")),
        FROM(job_runs),
        WHERE(DAYS),
    ))
    latest = statement(SELECT(ranked.job_id, ranked.status), FROM(ranked),
                       WHERE(equals(ranked.rn, 1)))
    assert "ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id DESC)" \
        in to_hive(latest)


# --- Writing a Saved table ----------------------------------------------------------------

daily_runs = Table(
    "mart.daily_runs",
    columns={"job_id": "bigint", "runs": "bigint", "minutes": "bigint", "dt": "string"},
    date_partition="dt",
)


def backfill():
    return statement(
        INSERT_OVERWRITE(daily_runs),
        SELECT(AS(sum_of(job_runs.duration_mins), "minutes"), job_runs.job_id,
               AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(DAYS),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    )


def test_a_write_selects_in_the_saved_tables_order() -> None:
    (first, _) = by_day(backfill())
    lines = to_hive(first).splitlines()
    assert lines[0] == "INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt = '2026-09-23')"
    assert lines[1:5] == ["SELECT", "  job_runs.job_id,", "  COUNT(*) AS runs,",
                          "  SUM(job_runs.duration_mins) AS minutes"]


def test_a_write_never_gets_the_automatic_limit() -> None:
    set_load_limits(rows=10)
    (first, _) = by_day(backfill())
    assert "LIMIT" not in to_hive(first)


def test_a_write_with_no_bound_on_its_day_is_refused() -> None:
    unbounded = statement(
        INSERT_OVERWRITE(daily_runs),
        SELECT(AS(sum_of(job_runs.duration_mins), "minutes"), job_runs.job_id,
               AS(count_rows(), "runs")),
        FROM(job_runs, reads_all_partitions=True),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    )
    with pytest.raises(ValueError, match="the day to write isn't known"):
        to_hive(unbounded)


def adding_a_day(day="2026-09-24"):
    return statement(
        INSERT_INTO(daily_runs),
        SELECT(job_runs.job_id, AS(count_rows(), "runs"),
               AS(sum_of(job_runs.duration_mins), "minutes")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, day)),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    )


def test_insert_into_adds_to_the_day_it_reads() -> None:
    lines = to_hive(adding_a_day()).splitlines()
    assert lines[0] == "INSERT INTO mart.daily_runs PARTITION(dt = '2026-09-24')"
    assert lines[1:3] == ["SELECT", "  job_runs.job_id,"]


def test_insert_into_keeps_every_rule_of_a_write() -> None:
    with pytest.raises(GuardRefused, match=r"INSERT_INTO\(daily_runs\): it leaves out minutes"):
        statement(INSERT_INTO(daily_runs), SELECT(job_runs.job_id, AS(count_rows(), "runs")),
                  FROM(job_runs), WHERE(DAYS), GROUP_BY(job_runs.dt, job_runs.job_id))
    two_days = statement(
        INSERT_INTO(daily_runs),
        SELECT(job_runs.job_id, AS(count_rows(), "runs"),
               AS(sum_of(job_runs.duration_mins), "minutes")),
        FROM(job_runs), WHERE(DAYS), GROUP_BY(job_runs.dt, job_runs.job_id),
    )
    with pytest.raises(GuardRefused, match=r"INSERT_INTO\(daily_runs\) covers 2 days"):
        to_hive(two_days)
    assert [to_hive(day).splitlines()[0][-13:] for day in by_day(two_days)] == [
        "'2026-09-23')", "'2026-09-24')"]
    with pytest.raises(ValueError, match="needs a Saved table with a Date partition"):
        INSERT_INTO(jobs)
    with pytest.raises(ValueError, match="write"):
        derived("added", adding_a_day())


def test_a_statement_has_one_write_at_most() -> None:
    with pytest.raises(ValueError, match="has INSERT_OVERWRITE and INSERT_INTO, but a Statement has only one INSERT clause"):
        statement(INSERT_OVERWRITE(daily_runs), INSERT_INTO(daily_runs),
                  SELECT(job_runs.job_id), FROM(job_runs), WHERE(DAYS))


def test_a_write_from_a_table_with_no_date_partition_says_so() -> None:
    per_team = Table("mart.per_team", columns={"jobs": "bigint", "dt": "string"},
                     date_partition="dt")
    s = statement(INSERT_OVERWRITE(per_team), SELECT(AS(count_rows(), "jobs")), FROM(jobs))
    with pytest.raises(ValueError, match="reads ops.jobs, which has no Date partition") as refused:
        to_hive(s)
    assert "None" not in str(refused.value)


# --- by_day -------------------------------------------------------------------------------


def test_by_day_follows_from_down_through_derived_tables() -> None:
    ranked = derived("per_day", statement(
        SELECT(job_runs.dt, job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(last_n_days(job_runs.dt, 2), equals(job_runs.status, "SUCCESS")),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    ))
    s = statement(SELECT(ranked.dt, ranked.runs), FROM(ranked), WHERE(equals(ranked.runs, 1)))
    days = by_day(s)
    assert len(days) == 2
    second = to_hive(days[1])
    assert "job_runs.dt = '2026-09-24'" in second
    assert "BETWEEN" not in second
    assert "job_runs.status = 'SUCCESS'" in second


def test_by_day_refuses_a_derived_table_that_picks_rows_across_days() -> None:
    ranked = derived("ranked", statement(
        SELECT(job_runs.job_id, AS(row_number(PARTITION_BY=job_runs.job_id,
                                              ORDER_BY=descending(job_runs.run_id)), "rn")),
        FROM(job_runs),
        WHERE(DAYS),
    ))
    s = statement(SELECT(ranked.job_id), FROM(ranked), WHERE(equals(ranked.rn, 1)))
    with pytest.raises(GuardRefused, match=r"derived\('ranked', \.\.\.\)"):
        by_day(s)


def test_by_day_needs_a_bounded_date_partition() -> None:
    with pytest.raises(ValueError, match="no bounded Date partition"):
        by_day(statement(SELECT(jobs.team), FROM(jobs)))


def test_by_day_splits_a_list_of_days() -> None:
    s = statement(SELECT(job_runs.run_id), FROM(job_runs),
                  WHERE(is_in(job_runs.dt, ["2026-09-24", "2026-09-20"])))
    assert [to_hive(d).splitlines()[-1].strip() for d in by_day(s)] == [
        "job_runs.dt = '2026-09-20'", "job_runs.dt = '2026-09-24'"]


# --- to_hive and the load limits ----------------------------------------------------------


def test_to_hive_stops_on_hive_that_doesnt_read_back_the_same(monkeypatch) -> None:
    written = iter(["SELECT 1", "SELECT 2"])
    monkeypatch.setattr(running, "hive_text", lambda tree, pretty=False: next(written))
    with pytest.raises(RuntimeError, match="bug in the Toolbox"):
        to_hive(statement(SELECT(jobs.team), FROM(jobs)))


def test_set_load_limits_refuses_nonsense_and_returns_what_is_in_force() -> None:
    with pytest.raises(ValueError):
        set_load_limits(rows=-1)
    with pytest.raises(ValueError):
        set_load_limits(dates=True)
    assert set_load_limits(rows=5) == {"rows": 5, "dates": None}
    assert set_load_limits() == {"rows": None, "dates": None}


def test_the_automatic_limit_never_goes_inside_a_derived_table() -> None:
    set_load_limits(rows=7)
    teams = derived("teams", statement(SELECT_DISTINCT(jobs.team), FROM(jobs)))
    hive = to_hive(statement(SELECT(teams.team), FROM(teams)))
    assert hive.count("LIMIT 7") == 1 and hive.endswith("LIMIT 7")


def test_a_bound_inside_an_any_of_counts_when_every_branch_bounds() -> None:
    both_days = any_of(equals(job_runs.dt, "2026-09-23"), equals(job_runs.dt, "2026-09-24"))
    statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(both_days))


def test_order_by_an_output_name_with_a_limit() -> None:
    hive = to_hive(statement(SELECT(jobs.team, AS(count_rows(), "job_count")), FROM(jobs),
                             GROUP_BY(jobs.team), ORDER_BY(descending("job_count"), jobs.team),
                             LIMIT(2)))
    assert "ORDER BY\n  job_count DESC,\n  jobs.team ASC\nLIMIT 2" in hive
