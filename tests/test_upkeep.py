"""Upkeep and speed: repair_partitions, compute_statistics and explain (map family 8).

Each gives a Statement, run like any other and safe to send again. repair_partitions writes
MSCK REPAIR TABLE, and compute_statistics ANALYZE TABLE ... COMPUTE STATISTICS for one day,
with FOR COLUMNS when asked; both take only one of the user's Saved tables, a Table reference
with location=, which need_saved_table checks for them and for the admin module. explain writes
EXPLAIN before exactly the Hive run would send, takes any Statement since it only reads, and
run gives back its plan as text. Spark Composer's Example database runs an EXPLAIN; sqlglot
Composer's says it can't, and neither runs the other two, its tables being made up and fixed.
"""

from __future__ import annotations

import datetime
import re

import pandas as pd
import pytest

import editions
from conftest import edition, toolbox_module
from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    INSERT_OVERWRITE,
    SELECT,
    WHERE,
    Table,
    between,
    compute_statistics,
    count_rows,
    create_table,
    derived,
    drop_table,
    equals,
    example_database,
    explain,
    export_lineage,
    hive_settings,
    repair_partitions,
    run,
    set_load_limits,
    show_hive,
    statement,
    to_hive,
    unchecked_hive,
)

job_runs = example_database.job_runs
BASE = "/data/your_team/tables"
DAILY_RUNS = Table("mart.daily_runs", columns={"job_id": "bigint", "runs": "bigint",
                                               "dt": "string"},
                   date_partition="dt", key=["job_id"], location=BASE)
REGION_RUNS = Table("mart.region_runs", columns={"job_id": "bigint", "region": "string",
                                                 "runs": "bigint", "dt": "string"},
                    date_partition="dt", location=BASE, partitioned_by=["region"])
COMPACT = Table("mart.compact_runs", columns={"run_id": "bigint", "day": "string"},
                date_partition="day", date_format="%Y%m%d", location=BASE)
UNDATED = Table("mart.job_names", columns={"job_id": "bigint", "job_name": "string"},
                date_partition=None, location=BASE)


def one_day():
    return statement(SELECT(job_runs.run_id), FROM(job_runs),
                     WHERE(equals(job_runs.dt, "2026-09-24")))


def recording(answer=None):
    """A send that keeps each Hive it is given, and answers with `answer`."""
    sent = []

    def send(hive):
        sent.append(hive)
        return pd.DataFrame() if answer is None else answer
    return send, sent


# --- repair_partitions ----------------------------------------------------------------------


def test_repair_partitions_writes_msck_repair_table() -> None:
    assert to_hive(repair_partitions(DAILY_RUNS)) == "MSCK REPAIR TABLE mart.daily_runs"
    assert to_hive(repair_partitions(REGION_RUNS)) == "MSCK REPAIR TABLE mart.region_runs"


def test_repair_partitions_is_sent_as_written_and_again() -> None:
    send, sent = recording()
    for _ in range(2):
        run(repair_partitions(DAILY_RUNS), send=send)
    assert sent == ["MSCK REPAIR TABLE mart.daily_runs"] * 2


def test_repair_partitions_refuses_a_table_with_no_partitions() -> None:
    with pytest.raises(ValueError, match=r"repair_partitions\(job_names\): mart.job_names has "
                                         r"no Date partition"):
        repair_partitions(UNDATED)


# --- compute_statistics ---------------------------------------------------------------------


def test_compute_statistics_counts_one_day() -> None:
    assert to_hive(compute_statistics(DAILY_RUNS, "2026-09-24")) == (
        "ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24') COMPUTE STATISTICS")


def test_compute_statistics_counts_each_column_but_the_partitions_when_asked() -> None:
    assert to_hive(compute_statistics(REGION_RUNS, "2026-09-24", columns=True)) == (
        "ANALYZE TABLE mart.region_runs PARTITION(dt = '2026-09-24', region) "
        "COMPUTE STATISTICS FOR COLUMNS job_id, runs")
    assert to_hive(compute_statistics(REGION_RUNS, "2026-09-24", columns=["runs"])) == (
        "ANALYZE TABLE mart.region_runs PARTITION(dt = '2026-09-24', region) "
        "COMPUTE STATISTICS FOR COLUMNS runs")


def test_compute_statistics_writes_the_day_as_the_table_does() -> None:
    assert to_hive(compute_statistics(COMPACT, datetime.date(2026, 9, 24))) == (
        "ANALYZE TABLE mart.compact_runs PARTITION(day = '20260924') COMPUTE STATISTICS")


def test_compute_statistics_of_a_table_with_no_date_partition_takes_no_day() -> None:
    assert to_hive(compute_statistics(UNDATED, columns=True)) == (
        "ANALYZE TABLE mart.job_names COMPUTE STATISTICS FOR COLUMNS job_id, job_name")


def test_compute_statistics_puts_an_awkward_column_in_backticks() -> None:
    odd = Table("mart.odd", columns={"select": "string", "dt": "string"},
                date_partition="dt", location=BASE)
    assert to_hive(compute_statistics(odd, "2026-09-24", columns=True)).endswith(
        "FOR COLUMNS `select`")


def test_compute_statistics_needs_the_day() -> None:
    with pytest.raises(TypeError, match=r"compute_statistics\(daily_runs\) needs the day"):
        compute_statistics(DAILY_RUNS)


@pytest.mark.parametrize("day", [["2026-09-23", "2026-09-24"], ("2026-09-24",)])
def test_compute_statistics_takes_one_day(day) -> None:
    with pytest.raises(TypeError, match="one day at a time") as refused:
        compute_statistics(DAILY_RUNS, day)
    assert "for day in" in str(refused.value)


def test_compute_statistics_refuses_a_day_written_another_way() -> None:
    with pytest.raises(ValueError, match="writes days like '2026-09-24'"):
        compute_statistics(DAILY_RUNS, "20260924")


def test_compute_statistics_refuses_a_day_for_a_table_with_no_date_partition() -> None:
    with pytest.raises(ValueError, match="has no Date partition") as refused:
        compute_statistics(UNDATED, "2026-09-24")
    assert "compute_statistics(job_names)" in str(refused.value)


@pytest.mark.parametrize(("columns", "says"), [
    (["job_idd"], "job_idd isn't one of its columns"),
    (["dt"], "dt is a Partition"),
    ("yes", "yes isn't one of its columns"),
    (1, "columns=1) isn't True or a list"),
    ([], "columns=[]) names no column"),
])
def test_compute_statistics_refuses_columns_it_cant_count(columns, says) -> None:
    with pytest.raises((TypeError, ValueError), match=re.escape(says)):
        compute_statistics(DAILY_RUNS, "2026-09-24", columns=columns)


# --- Only the user's Saved tables -----------------------------------------------------------


@pytest.mark.parametrize("make", [repair_partitions,
                                  lambda t: compute_statistics(t, "2026-09-24")])
def test_upkeep_refuses_a_table_that_isnt_one_of_your_saved_tables(make) -> None:
    with pytest.raises(ValueError, match="job_runs isn't one of your Saved tables") as refused:
        make(job_runs)
    assert "location=" in str(refused.value)


@pytest.mark.parametrize("make", [repair_partitions,
                                  lambda t: compute_statistics(t, "2026-09-24")])
def test_upkeep_refuses_what_isnt_a_table_reference(make) -> None:
    runs = derived("runs", one_day())
    for given in ("mart.daily_runs", runs):
        with pytest.raises(TypeError, match="Pass a Table reference"):
            make(given)


def test_need_saved_table_gives_back_a_saved_table() -> None:
    need_saved_table = toolbox_module("tables").need_saved_table
    assert need_saved_table(DAILY_RUNS, "admin.drop_days") is DAILY_RUNS
    with pytest.raises(ValueError, match=r"admin.drop_days\(job_runs\): ops.job_runs isn't"):
        need_saved_table(job_runs, "admin.drop_days")


# --- explain --------------------------------------------------------------------------------


def test_explain_writes_explain_before_the_hive_run_sends() -> None:
    s = one_day()
    assert to_hive(explain(s)) == "EXPLAIN " + to_hive(s)
    assert to_hive(explain(s)).splitlines()[0] == "EXPLAIN SELECT"
    set_load_limits(rows=100)
    assert to_hive(explain(s)) == "EXPLAIN " + to_hive(s)
    assert "LIMIT" in to_hive(explain(s))  # the automatic LIMIT run adds


def test_explain_explains_a_write_and_a_derived_table() -> None:
    write = statement(INSERT_OVERWRITE(DAILY_RUNS),
                      SELECT(job_runs.job_id, AS(count_rows(), "runs")), FROM(job_runs),
                      WHERE(equals(job_runs.dt, "2026-09-24")), GROUP_BY(job_runs.job_id))
    assert to_hive(explain(write)) == "EXPLAIN " + to_hive(write)
    runs = derived("runs", one_day())
    reading = statement(SELECT(runs.run_id), FROM(runs))
    assert to_hive(explain(reading)).startswith("EXPLAIN WITH runs AS (")


def test_show_hive_prints_an_explain_with_its_semicolon(capsys) -> None:
    show_hive(explain(one_day()))
    assert capsys.readouterr().out.startswith("EXPLAIN SELECT\n")


def test_explain_refuses_what_to_hive_refuses() -> None:
    set_load_limits(dates=7)
    long = statement(SELECT(job_runs.run_id), FROM(job_runs),
                     WHERE(between(job_runs.dt, "2026-01-01", "2026-09-24")))
    with pytest.raises(Exception, match="dates") as refused:
        explain(long)
    assert "What happened:" in str(refused.value)


@pytest.mark.parametrize(("given", "says"), [
    (lambda: "SELECT 1", "isn't a Statement"),
    (lambda: [one_day()], "one at a time"),
    (lambda: unchecked_hive("SELECT 1"), 'unchecked_hive("EXPLAIN '),
    (lambda: hive_settings("map_joins"), "Session settings have no plan"),
    (lambda: create_table(DAILY_RUNS), "isn't a query or a write"),
    (lambda: drop_table(DAILY_RUNS), "isn't a query or a write"),
    (lambda: repair_partitions(DAILY_RUNS), "isn't a query or a write"),
    (lambda: explain(one_day()), "isn't a query or a write"),
])
def test_explain_refuses_what_has_no_plan_to_show(given, says) -> None:
    with pytest.raises((TypeError, ValueError), match=re.escape(says)):
        explain(given())


def test_run_gives_back_the_plan_as_text() -> None:
    hive_plan = pd.DataFrame({"Explain": ["STAGE DEPENDENCIES:", "  Stage-0 is a root stage",
                                          ""]})
    send, sent = recording(hive_plan)
    plan = run(explain(one_day()), send=send)
    assert sent == [to_hive(explain(one_day()))]
    assert plan == "STAGE DEPENDENCIES:\n  Stage-0 is a root stage"
    assert isinstance(plan, str)
    spark_plan = pd.DataFrame({"plan": ["== Physical Plan ==\n*(1) Project [a]\n\n"]})
    assert run(explain(one_day()), send=recording(spark_plan)[0]) == (
        "== Physical Plan ==\n*(1) Project [a]")


def test_run_refuses_a_plan_that_isnt_a_dataframe() -> None:
    with pytest.raises(TypeError, match="DataFrame"):
        run(explain(one_day()), send=lambda hive: ["STAGE DEPENDENCIES:"])


def test_export_lineage_draws_no_upkeep(tmp_path) -> None:
    for s in (explain(one_day()), repair_partitions(DAILY_RUNS),
              compute_statistics(DAILY_RUNS, "2026-09-24")):
        with pytest.raises(TypeError, match="isn't a Statement that reads a table"):
            export_lineage(s, to=tmp_path / "upkeep.html")


# --- Reading each back, and the Example database ------------------------------------------


@pytest.mark.parametrize("make", [
    lambda: repair_partitions(REGION_RUNS),
    lambda: compute_statistics(REGION_RUNS, "2026-09-24", columns=True),
    lambda: explain(one_day()),
])
def test_each_reads_back_as_itself(make) -> None:
    text = to_hive(make())
    assert toolbox_module("writing").read_back(text) == text


def test_an_upkeep_statement_that_doesnt_read_back_is_caught() -> None:
    writing = toolbox_module("writing")
    garbled = "ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24) COMPUTE STATISTICS"
    assert writing.read_back(garbled) != garbled


def test_the_example_database_refuses_to_repair_or_count() -> None:
    for s in (repair_partitions(DAILY_RUNS), compute_statistics(DAILY_RUNS, "2026-09-24")):
        with pytest.raises(ValueError, match="can't be written to"):
            run(s, send=example_database.send)


@pytest.mark.needs_example_database
def test_spark_composers_example_database_explains_and_sqlglot_composers_cant() -> None:
    if edition() is editions.SPARK_COMPOSER:
        plan = run(explain(one_day()), send=example_database.send)
        assert plan.splitlines()[0] == "== Physical Plan =="
        return
    with pytest.raises(RuntimeError, match="its executor has no EXPLAIN"):
        run(explain(one_day()), send=example_database.send)
