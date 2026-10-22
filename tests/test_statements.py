"""How a Statement is written, checked and turned into Hive, seen through the public names."""

from __future__ import annotations

import datetime
import re
import warnings
from collections.abc import Callable

import numpy as np
import pandas as pd
import pytest

from sqlglot_composer import (
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
    Statement,
    Table,
    all_columns,
    any_of,
    between,
    count_distinct,
    count_rows,
    create_table,
    derived,
    descending,
    equals,
    explain,
    first_look,
    hive_function,
    hive_settings,
    is_in,
    last_n_days,
    row_number,
    run_execute,
    run_query,
    set_load_limits,
    statement,
    sum_of,
    to_hive,
    week_start,
)
from sqlglot_composer import admin, writing
from sqlglot_composer.trees import HIVE_FUNCTION_ARGUMENTS
from sqlglot_composer.example_database import job_runs, jobs, run_alerts

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
def test_python_operators_that_would_mislead_are_refused(write: Callable[[], object],
                                                         points_to: str) -> None:
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
                   partitioned_by=["dt"])
    at = datetime.datetime(2026, 9, 24, 13, 5)
    assert repr(equals(events.at, at)) == "events.at = '2026-09-24 13:05:00'"
    assert repr(last_n_days(events.at, 2)) == (
        "events.at >= '2026-09-23' AND events.at < '2026-09-25'")


def test_a_partition_column_of_dates_is_compared_as_written() -> None:
    """No column is a day to the Toolbox: a value is written into the Hive as it is given, and
    the day helpers read the column as it is."""
    compact = Table("ops.compact", columns={"n": "int", "day": "string"},
                    partitioned_by=["day"])
    assert repr(equals(compact.day, "20260924")) == "compact.day = '20260924'"
    assert repr(equals(compact.day, datetime.date(2026, 9, 24))) == "compact.day = '2026-09-24'"
    assert repr(last_n_days(compact.day, 2)) == "compact.day BETWEEN '2026-09-23' AND '2026-09-24'"
    assert repr(week_start(compact.day)) == (
        "CAST(NEXT_DAY(DATE_ADD(compact.day, 7 * -1), 'MO') AS STRING)")


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
    with pytest.raises(TypeError, match=r"hive_function\('regexp_extract', \.\.\.\)"):
        hive_function("regexp_extract", jobs.team)


@pytest.mark.parametrize(("call", "said"), [
    (lambda: hive_function("upper", jobs.team, jobs.team),
     "gives upper 2 arguments, and upper takes 1 argument."),
    (lambda: hive_function("length", jobs.team, 2), "and length takes 1 argument."),
    (lambda: hive_function("regexp_extract", jobs.team), "and regexp_extract takes 2 to 3"),
    (lambda: hive_function("concat_ws", "-"), "gives concat_ws 1 argument, and concat_ws takes "
     "2 or more arguments."),
])
def test_hive_function_counts_arguments_by_the_list_in_trees(call: Callable[[], object],
                                                             said: str) -> None:
    with pytest.raises(TypeError, match=re.escape(said)):
        call()


@pytest.mark.parametrize(("name", "count"), [
    (name, count) for name, (fewest, most) in sorted(HIVE_FUNCTION_ARGUMENTS.items())
    for count in range(fewest, (fewest + 2 if most is None else most) + 1)])
def test_hive_function_writes_every_count_the_shared_list_lets_through(name: str,
                                                                       count: int) -> None:
    """So a call the Toolbox writes, Hive runs."""
    call = hive_function(name, *[job_runs.status] * count)
    to_hive(statement(SELECT(AS(call, "x")), FROM(job_runs), WHERE(DAYS)))


def test_hive_function_counts_min_and_max_as_one_argument() -> None:
    """With two, sqlglot Composer's sqlglot writes GREATEST, which doesn't turn rows into one."""
    with pytest.raises(TypeError, match=re.escape("gives max 2 arguments, and max takes 1")):
        hive_function("max", job_runs.run_id, job_runs.duration_mins)


@pytest.mark.parametrize("name", ["lag", "RANK", "row_number"])
def test_hive_function_refuses_a_function_that_needs_a_window(name: str) -> None:
    with pytest.raises(ValueError, match=re.escape(
            f"hive_function({name!r}, ...) calls {name}, which works only over a window")):
        hive_function(name, jobs.team)


@pytest.mark.parametrize(("name", "instead"), [
    ("lag", "lag(column, over=window(...))"), ("rank", "rank(over=window(...))"),
    ("ntile", "ntile(parts, over=window(...))"), ("row_number", "row_number(over=window(...))")])
def test_the_window_refusal_names_the_toolbox_function_that_writes_over(name: str,
                                                                        instead: str) -> None:
    with pytest.raises(ValueError, match=re.escape(f"Use {instead}, which writes OVER")):
        hive_function(name, jobs.team)


def test_the_window_refusal_says_pandas_for_a_window_function_the_toolbox_lacks() -> None:
    with pytest.raises(ValueError, match="work it out in pandas"):
        hive_function("percent_rank")


@pytest.mark.parametrize("name", ["first", "count_if", "any_value", "collect_set", "SUM"])
def test_hive_function_knows_the_functions_that_add_rows_up(name: str) -> None:
    """A function that adds rows up needs GROUP_BY beside a column, as count_rows() does."""
    with pytest.raises(GuardRefused, match="counts or adds up rows and has no GROUP_BY"):
        statement(SELECT(jobs.region, AS(hive_function(name, jobs.team), "x")), FROM(jobs))


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
    from sqlglot_composer import at_least

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


def test_first_look_on_an_unpartitioned_table() -> None:
    assert to_hive(first_look(jobs)).endswith("FROM ops.jobs AS jobs\nLIMIT 20")


def test_first_look_reads_every_partition_of_a_partitioned_table() -> None:
    hive = to_hive(first_look(job_runs))
    assert hive.endswith("  job_runs.dt\nFROM ops.job_runs AS job_runs\nLIMIT 20")
    assert "WHERE" not in hive
    assert hive.count("job_runs.") == len(job_runs._columns)


def test_a_reserved_word_as_a_name_is_quoted() -> None:
    odd = Table("ops.odd", columns={"user": "string", "select": "int"})
    hive = to_hive(statement(SELECT(odd.user, AS(getattr(odd, "select"), "order")), FROM(odd)))
    assert "odd.`user`" in hive and "AS `order`" in hive


# --- Derived tables -----------------------------------------------------------------------


def per_run() -> Table:
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
                  partitioned_by=["dt"], location="/data/your_team/mart.db/daily")
    write = statement(INSERT_OVERWRITE(daily), SELECT(AS(count_rows(), "runs"), job_runs.dt),
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
    partitioned_by=["dt"],
    location="/data/your_team/mart.db/daily_runs",
)


def backfill() -> Statement:
    return statement(
        INSERT_OVERWRITE(daily_runs),
        SELECT(job_runs.dt, AS(sum_of(job_runs.duration_mins), "minutes"), job_runs.job_id,
               AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(DAYS),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    )


def test_a_write_selects_in_the_saved_tables_order_its_partition_columns_last() -> None:
    lines = to_hive(backfill()).splitlines()
    assert lines[0] == "INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt)"
    assert lines[1:6] == ["SELECT", "  job_runs.job_id,", "  COUNT(*) AS runs,",
                          "  SUM(job_runs.duration_mins) AS minutes,", "  job_runs.dt"]


def test_a_write_never_gets_the_automatic_limit() -> None:
    set_load_limits(rows=10)
    assert "LIMIT" not in to_hive(backfill())


def test_a_write_may_read_every_partition_when_it_says_so() -> None:
    everything = statement(
        INSERT_OVERWRITE(daily_runs),
        SELECT(AS(sum_of(job_runs.duration_mins), "minutes"), job_runs.job_id,
               AS(count_rows(), "runs"), job_runs.dt),
        FROM(job_runs, reads_all_partitions=True),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    )
    hive = to_hive(everything)
    assert hive.startswith("INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt)\n")
    assert "WHERE" not in hive


def adding_a_day(day: str = "2026-09-24") -> Statement:
    return statement(
        INSERT_INTO(daily_runs, partition={"dt": day}),
        SELECT(job_runs.job_id, AS(count_rows(), "runs"),
               AS(sum_of(job_runs.duration_mins), "minutes")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, day)),
        GROUP_BY(job_runs.job_id),
    )


def test_insert_into_adds_to_the_partition_it_names() -> None:
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
               AS(sum_of(job_runs.duration_mins), "minutes"), job_runs.dt),
        FROM(job_runs), WHERE(DAYS), GROUP_BY(job_runs.dt, job_runs.job_id),
    )
    assert to_hive(two_days).splitlines()[0] == "INSERT INTO mart.daily_runs PARTITION(dt)"
    # ops.jobs is unpartitioned and has no location=: written whole, someone else's table
    # would lose every row, so it is refused.
    with pytest.raises(ValueError, match="isn't one of your Saved tables"):
        INSERT_INTO(jobs)
    with pytest.raises(ValueError, match="write"):
        derived("added", adding_a_day())


def test_a_statement_has_one_write_at_most() -> None:
    with pytest.raises(ValueError, match="has INSERT_OVERWRITE and INSERT_INTO, but a Statement has only one INSERT clause"):
        statement(INSERT_OVERWRITE(daily_runs), INSERT_INTO(daily_runs),
                  SELECT(job_runs.job_id), FROM(job_runs), WHERE(DAYS))


def test_a_write_from_an_unpartitioned_table_names_its_partition_or_fills_it_from_the_rows(
) -> None:
    per_day = Table("mart.per_day", columns={"jobs": "bigint", "dt": "string"},
                    partitioned_by=["dt"], location="/data/your_team/mart.db/per_day")
    named = statement(INSERT_OVERWRITE(per_day, partition={"dt": "2026-09-24"}),
                      SELECT(AS(count_rows(), "jobs")), FROM(jobs))
    assert to_hive(named) == (
        "INSERT OVERWRITE TABLE mart.per_day PARTITION(dt = '2026-09-24')\n"
        "SELECT\n"
        "  COUNT(*) AS jobs\n"
        "FROM ops.jobs AS jobs")
    per_team = Table("mart.per_team", columns={"jobs": "bigint", "team": "string"},
                     partitioned_by=["team"], key=["team"],
                     location="/data/your_team/mart.db/per_team")
    filled = statement(INSERT_OVERWRITE(per_team), SELECT(jobs.team, AS(count_rows(), "jobs")),
                       FROM(jobs), GROUP_BY(jobs.team))
    assert to_hive(filled) == (
        "INSERT OVERWRITE TABLE mart.per_team PARTITION(team)\n"
        "SELECT\n"
        "  COUNT(*) AS jobs,\n"
        "  jobs.team\n"
        "FROM ops.jobs AS jobs\n"
        "GROUP BY\n"
        "  jobs.team")


# --- to_hive and the load limits ----------------------------------------------------------


def test_to_hive_stops_on_hive_that_doesnt_read_back_the_same(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(writing, "read_back", lambda text: text + " ")
    with pytest.raises(RuntimeError, match="bug in the Toolbox, not in your Statement: "
                       "nothing was sent"):
        to_hive(statement(SELECT(jobs.team), FROM(jobs)))


def test_set_load_limits_refuses_nonsense_and_returns_what_is_in_force() -> None:
    with pytest.raises(ValueError):
        set_load_limits(rows=-1)
    with pytest.raises(TypeError, match="set_load_limits was given dates=, which Toolbox 7.0 "
                       "took out."):
        set_load_limits(dates=1)
    assert set_load_limits(rows=5) == {"rows": 5}
    assert set_load_limits() == {"rows": None}


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


# --- run_query and run_execute: you pick the call ---------------------------------------------

saved_runs = Table("mart.saved_runs", columns={"job_id": "bigint", "dt": "string"},
                   partitioned_by=["dt"], location="/data/your_team/mart.db/saved_runs")


def recording() -> tuple[Callable[[str], pd.DataFrame], Callable[[str], None],
                         list[tuple[str, str]]]:
    """A query and an execute that keep each Hive they are given, with which of them it went
    to: the query gives back one line of a plan, the execute nothing."""
    sent = []

    def query(hive: str) -> pd.DataFrame:
        sent.append(("query", hive))
        return pd.DataFrame({"plan": ["STAGE DEPENDENCIES:"]})

    def execute(hive: str) -> None:
        sent.append(("execute", hive))

    return query, execute, sent


def one_day_read() -> Statement:
    return statement(SELECT(job_runs.run_id), FROM(job_runs),
                     WHERE(equals(job_runs.dt, "2026-09-24")))


def test_run_query_sends_a_read_to_query_and_gives_back_its_rows() -> None:
    query, _, sent = recording()
    rows = run_query(one_day_read(), query)
    assert rows["plan"].tolist() == ["STAGE DEPENDENCIES:"]
    assert sent == [("query", to_hive(one_day_read()))]


def test_run_query_takes_query_by_name_too() -> None:
    query, _, sent = recording()
    run_query(one_day_read(), query=query)
    assert sent == [("query", to_hive(one_day_read()))]


def test_run_query_sends_explain_to_query_and_gives_back_the_plan() -> None:
    query, _, sent = recording()
    assert run_query(explain(one_day_read()), query) == "STAGE DEPENDENCIES:"
    assert sent == [("query", to_hive(explain(one_day_read())))]


@pytest.mark.parametrize("make", [
    pytest.param(backfill, id="write"),
    pytest.param(lambda: create_table(saved_runs), id="create_table"),
    pytest.param(lambda: admin.drop_table(saved_runs), id="admin_drop_table"),
])
def test_run_execute_sends_what_changes_a_table_to_execute_and_gives_back_none(
        make: Callable[[], Statement]) -> None:
    _, execute, sent = recording()
    assert run_execute(make(), execute) is None
    assert sent == [("execute", to_hive(make()))]


def test_run_execute_sends_each_session_setting_on_its_own() -> None:
    _, execute, sent = recording()
    assert run_execute(hive_settings("dynamic_partitions"), execute) is None
    assert sent == [("execute", "SET hive.exec.dynamic.partition=true"),
                    ("execute", "SET hive.exec.dynamic.partition.mode=nonstrict")]


@pytest.mark.parametrize("make, words", [
    pytest.param(backfill, "a Statement that writes a Saved table", id="write"),
    pytest.param(lambda: create_table(saved_runs), "create_table(...)'s Statement",
                 id="create_table"),
    pytest.param(lambda: admin.drop_table(saved_runs), "an Admin statement", id="admin"),
    pytest.param(lambda: hive_settings("map_joins"), "Session settings", id="settings"),
])
def test_run_query_refuses_what_changes_something_naming_run_execute(
        make: Callable[[], object], words: str) -> None:
    query, _, sent = recording()
    step = make()
    with pytest.raises(ValueError) as refused:
        run_query(step, query)
    message = " ".join(str(refused.value).split())
    assert f"run_query was given {words}" in message
    assert "Send it with run_execute(step, execute)." in message
    assert sent == []


@pytest.mark.parametrize("make, words", [
    pytest.param(one_day_read, "a Statement that reads rows", id="read"),
    pytest.param(lambda: explain(one_day_read()), "explain(...)'s Statement", id="explain"),
])
def test_run_execute_refuses_a_read_naming_run_query(make: Callable[[], Statement],
                                                     words: str) -> None:
    _, execute, sent = recording()
    step = make()
    with pytest.raises(ValueError) as refused:
        run_execute(step, execute)
    message = " ".join(str(refused.value).split())
    assert f"run_execute was given {words}" in message
    assert "Send it with run_query(step, query), which gives back its rows." in message
    assert sent == []


@pytest.mark.parametrize("call, other, instead", [
    pytest.param(run_query, "execute", "run_execute", id="run_query"),
    pytest.param(run_execute, "query", "run_query", id="run_execute"),
])
def test_each_refuses_the_other_call_by_name_naming_the_function_that_takes_it(
        call: Callable[..., object], other: str, instead: str) -> None:
    query, execute, sent = recording()
    with pytest.raises(TypeError) as refused:
        call(one_day_read(), **{other: query if other == "query" else execute})
    message = str(refused.value)
    assert f"{call.__name__} was given {other}=, your other call." in message
    assert f"call {instead}(s, {other}) instead." in message
    assert sent == []


@pytest.mark.parametrize("call, needed", [(run_query, "query"), (run_execute, "execute")])
def test_each_refuses_a_missing_call_naming_it(call: Callable[..., object],
                                               needed: str) -> None:
    step = one_day_read() if needed == "query" else backfill()
    with pytest.raises(TypeError) as refused:
        call(step)
    message = str(refused.value)
    assert f"{call.__name__} needs {needed}=, and wasn't given it." in message
    assert f"from warehouse import {needed}" in message


def test_run_query_refuses_send_naming_query() -> None:
    sent = []
    with pytest.raises(TypeError) as refused:
        run_query(one_day_read(), send=sent.append)
    message = str(refused.value)
    assert "run_query was given send=, which Toolbox 7.0 replaced." in message
    assert "Pass query= instead, imported with from warehouse import query, execute." in message
    assert "CHANGES.md" in message
    assert sent == []


def test_run_query_refuses_a_keyword_it_doesnt_take() -> None:
    query, _, sent = recording()
    with pytest.raises(TypeError) as refused:
        run_query(one_day_read(), query, querry=query)
    message = str(refused.value)
    assert "run_query was given querry=, which it doesn't take." in message
    assert "It takes s and query=, and nothing else." in message
    assert sent == []
