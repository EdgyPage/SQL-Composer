"""Upkeep and speed: repair_partitions, compute_statistics and explain (map family 8).

Each gives a Statement, run like any other and safe to send again. repair_partitions writes
MSCK REPAIR TABLE, for any partitioned table, and compute_statistics ANALYZE TABLE ...
COMPUTE STATISTICS for a whole table or the Partitions partition= names, with FOR COLUMNS when
asked; both take only one of the user's Saved tables, a Table reference with location=, which
need_saved_table checks for them and for the admin module. explain writes
EXPLAIN before exactly the Hive run would send, takes any Statement since it only reads, and
run gives back its plan as text. The Example database says it can't explain, and runs neither of
the other two, its tables being made up and fixed.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from conftest import toolbox_module
from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    INSERT_OVERWRITE,
    SELECT,
    UNION_ALL,
    WHERE,
    Column,
    Statement,
    Table,
    admin,
    compute_statistics,
    count_rows,
    create_table,
    derived,
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
BASE = "/data/your_team/mart.db"
DAILY_RUNS = Table("mart.daily_runs", columns={"job_id": "bigint", "runs": "bigint",
                                               "dt": "string"},
                   partitioned_by=["dt"], key=["job_id", "dt"], location=f"{BASE}/daily_runs")
REGION_RUNS = Table("mart.region_runs", columns={"job_id": "bigint", "runs": "bigint",
                                                 "region": "string", "dt": "string"},
                    partitioned_by=["region", "dt"], location=f"{BASE}/region_runs")
# Partitioned by region alone: no column of it is a day.
BY_REGION = Table("mart.region_totals", columns={"runs": "bigint", "region": "string"},
                  partitioned_by=["region"], location=f"{BASE}/region_totals")
COMPACT = Table("mart.compact_runs", columns={"run_id": "bigint", "day": "string"},
                partitioned_by=["day"], location=f"{BASE}/compact_runs")
JOB_NAMES = Table("mart.job_names", columns={"job_id": "bigint", "job_name": "string"},
                  location=f"{BASE}/job_names")


def one_day() -> Statement:
    return statement(SELECT(job_runs.run_id), FROM(job_runs),
                     WHERE(equals(job_runs.dt, "2026-09-24")))


def recording(
        answer: pd.DataFrame | None = None) -> tuple[Callable[[str], pd.DataFrame], list[str]]:
    """A query that keeps each Hive it is given, and answers with `answer`."""
    sent = []

    def query(hive: str) -> pd.DataFrame:
        sent.append(hive)
        return pd.DataFrame() if answer is None else answer
    return query, sent


# --- repair_partitions ----------------------------------------------------------------------


def test_repair_partitions_writes_msck_repair_table() -> None:
    assert to_hive(repair_partitions(DAILY_RUNS)) == "MSCK REPAIR TABLE mart.daily_runs"
    assert to_hive(repair_partitions(REGION_RUNS)) == "MSCK REPAIR TABLE mart.region_runs"


def test_repair_partitions_takes_a_table_partitioned_by_region_alone() -> None:
    assert to_hive(repair_partitions(BY_REGION)) == "MSCK REPAIR TABLE mart.region_totals"


def test_repair_partitions_is_sent_to_execute_as_written_and_again() -> None:
    sent = []
    for _ in range(2):
        assert run(repair_partitions(DAILY_RUNS), execute=sent.append) is None
    assert sent == ["MSCK REPAIR TABLE mart.daily_runs"] * 2


def test_repair_partitions_refuses_a_table_with_no_partitions() -> None:
    with pytest.raises(ValueError, match=r"repair_partitions\(job_names\): mart.job_names has "
                                         r"no partitioned_by=, so it has no Partitions to find"):
        repair_partitions(JOB_NAMES)


# --- compute_statistics ---------------------------------------------------------------------


def test_compute_statistics_counts_every_partition_unless_told() -> None:
    assert to_hive(compute_statistics(DAILY_RUNS)) == (
        "ANALYZE TABLE mart.daily_runs PARTITION(dt) COMPUTE STATISTICS")
    assert to_hive(compute_statistics(REGION_RUNS)) == (
        "ANALYZE TABLE mart.region_runs PARTITION(region, dt) COMPUTE STATISTICS")


def test_compute_statistics_counts_the_partitions_it_names() -> None:
    assert to_hive(compute_statistics(DAILY_RUNS, partition={"dt": "2026-09-24"})) == (
        "ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24') COMPUTE STATISTICS")
    assert to_hive(compute_statistics(REGION_RUNS, partition={"region": "EU"})) == (
        "ANALYZE TABLE mart.region_runs PARTITION(region = 'EU', dt) COMPUTE STATISTICS")
    assert to_hive(compute_statistics(
        REGION_RUNS, partition={"region": "EU", "dt": "2026-09-24"})) == (
        "ANALYZE TABLE mart.region_runs PARTITION(region = 'EU', dt = '2026-09-24') "
        "COMPUTE STATISTICS")
    assert to_hive(compute_statistics(BY_REGION, partition={"region": "EU"})) == (
        "ANALYZE TABLE mart.region_totals PARTITION(region = 'EU') COMPUTE STATISTICS")


def test_compute_statistics_counts_each_column_but_the_partitions_when_asked() -> None:
    assert to_hive(compute_statistics(REGION_RUNS, partition={"region": "EU"},
                                      columns=True)) == (
        "ANALYZE TABLE mart.region_runs PARTITION(region = 'EU', dt) "
        "COMPUTE STATISTICS FOR COLUMNS job_id, runs")
    assert to_hive(compute_statistics(REGION_RUNS, columns=["runs"])) == (
        "ANALYZE TABLE mart.region_runs PARTITION(region, dt) "
        "COMPUTE STATISTICS FOR COLUMNS runs")


def test_compute_statistics_takes_columns_as_the_table_s_attributes_or_names() -> None:
    assert to_hive(compute_statistics(REGION_RUNS,
                                      columns=[REGION_RUNS.runs, "job_id"])).endswith(
        "FOR COLUMNS runs, job_id")


def test_compute_statistics_writes_a_value_as_it_is_given() -> None:
    assert to_hive(compute_statistics(COMPACT, partition={"day": "20260924"})) == (
        "ANALYZE TABLE mart.compact_runs PARTITION(day = '20260924') COMPUTE STATISTICS")


def test_compute_statistics_of_an_unpartitioned_table_counts_it_whole() -> None:
    assert to_hive(compute_statistics(JOB_NAMES, columns=True)) == (
        "ANALYZE TABLE mart.job_names COMPUTE STATISTICS FOR COLUMNS job_id, job_name")


def test_compute_statistics_puts_an_awkward_column_in_backticks() -> None:
    odd = Table("mart.odd", columns={"select": "string", "dt": "string"},
                partitioned_by=["dt"], location=f"{BASE}/odd")
    assert to_hive(compute_statistics(odd, partition={"dt": "2026-09-24"},
                                      columns=True)).endswith("FOR COLUMNS `select`")


def test_compute_statistics_refuses_day_naming_partition() -> None:
    with pytest.raises(TypeError) as refused:
        compute_statistics(DAILY_RUNS, day="2026-09-24")
    message = " ".join(str(refused.value).split())
    assert "compute_statistics(...) was given day=, which Toolbox 7.0 replaced." in message
    assert 'Pass partition={...} instead, such as partition={"dt": "2026-09-24"}' in message


def test_compute_statistics_refuses_a_day_where_partition_goes() -> None:
    with pytest.raises(TypeError, match=re.escape(
            "compute_statistics(daily_runs, \"2026-09-24\") wasn't given a dict for "
            "partition=")):
        compute_statistics(DAILY_RUNS, "2026-09-24")


@pytest.mark.parametrize(("t", "partition", "says"), [
    (DAILY_RUNS, {"job_id": 1},
     "compute_statistics(daily_runs, partition=...): \"job_id\" isn't one of mart.daily_runs's "
     "partition columns."),
    (REGION_RUNS, {"dt": "2026-09-24"},
     "compute_statistics(region_runs, partition=...) names dt, but not the partition columns "
     "before it: mart.region_runs is partitioned by region, dt."),
    (REGION_RUNS, {"region": None},
     "compute_statistics(region_runs, partition=...): the value of region is None."),
    (JOB_NAMES, {"job_id": 1},
     "compute_statistics(job_names, partition=...): mart.job_names has no partitioned_by=, "
     "and was given partition=[\"job_id\"]."),
], ids=["not a partition column", "skips the leading columns", "no value", "unpartitioned"])
def test_compute_statistics_refuses_partitions_it_cant_name(
        t: Table, partition: dict[str, object], says: str) -> None:
    with pytest.raises(ValueError) as refused:
        compute_statistics(t, partition=partition)
    assert says in " ".join(str(refused.value).split())


@pytest.mark.parametrize(("columns", "says"), [
    (["job_idd"], "job_idd isn't one of daily_runs's columns"),
    (["dt"], "dt is a partition column"),
    ("yes", "yes isn't one of daily_runs's columns"),
    ([job_runs.job_id], "job_runs.job_id isn't one of daily_runs's columns"),
    (1, "columns=1) isn't True or a list"),
    ([], "columns=[]) isn't True or a list"),
])
def test_compute_statistics_refuses_columns_it_cant_count(
        columns: list[str] | list[Column] | str | int, says: str) -> None:
    with pytest.raises((TypeError, ValueError), match=re.escape(says)):
        compute_statistics(DAILY_RUNS, columns=columns)


# --- Only the user's Saved tables -----------------------------------------------------------


@pytest.mark.parametrize("make", [repair_partitions, compute_statistics])
def test_upkeep_refuses_a_table_that_isnt_one_of_your_saved_tables(
        make: Callable[[Table], Statement]) -> None:
    with pytest.raises(ValueError, match="was given ops.job_runs, which isn't one of your "
                                         "Saved tables") as refused:
        make(job_runs)
    assert "location=" in str(refused.value)


@pytest.mark.parametrize("make", [repair_partitions, compute_statistics])
def test_upkeep_refuses_what_isnt_a_table_reference(
        make: Callable[[object], Statement]) -> None:
    runs = derived("runs", one_day())
    for given in ("mart.daily_runs", runs):
        with pytest.raises(TypeError, match="Pass a Table reference"):
            make(given)


def test_need_saved_table_gives_back_a_saved_table() -> None:
    need_saved_table = toolbox_module("tables").need_saved_table
    assert need_saved_table(DAILY_RUNS, "compute_statistics(...)") is DAILY_RUNS
    with pytest.raises(ValueError, match=re.escape(
            "compute_statistics(...) was given ops.job_runs, which isn't one of your Saved")):
        need_saved_table(job_runs, "compute_statistics(...)")


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
                      SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
                      FROM(job_runs), WHERE(equals(job_runs.dt, "2026-09-24")),
                      GROUP_BY(job_runs.dt, job_runs.job_id))
    assert to_hive(explain(write)) == "EXPLAIN " + to_hive(write)
    runs = derived("runs", one_day())
    reading = statement(SELECT(runs.run_id), FROM(runs))
    assert to_hive(explain(reading)).startswith("EXPLAIN WITH runs AS (")


def test_explain_explains_a_stack() -> None:
    earlier = statement(SELECT(job_runs.run_id), FROM(job_runs),
                        WHERE(equals(job_runs.dt, "2026-09-23")))
    stack = UNION_ALL(one_day(), earlier)
    assert to_hive(explain(stack)) == "EXPLAIN " + to_hive(stack)


def test_show_hive_prints_an_explain_with_its_semicolon(
        capsys: pytest.CaptureFixture[str]) -> None:
    show_hive(explain(one_day()))
    assert capsys.readouterr().out.startswith("EXPLAIN SELECT\n")


def test_explain_explains_a_read_of_every_partition_when_it_says_so() -> None:
    whole = statement(SELECT(job_runs.run_id), FROM(job_runs, reads_all_partitions=True))
    assert to_hive(explain(whole)) == "EXPLAIN " + to_hive(whole)


@pytest.mark.parametrize(("given", "says"), [
    (lambda: "SELECT 1", "isn't a Statement"),
    (lambda: [one_day()], "one at a time"),
    (lambda: unchecked_hive("SELECT 1", returns_rows=True), 'unchecked_hive("EXPLAIN '),
    (lambda: hive_settings("map_joins"), "Session settings have no plan"),
    (lambda: create_table(DAILY_RUNS), "isn't a query or a write"),
    (lambda: admin.drop_table(DAILY_RUNS), "an Admin statement, which isn't a query"),
    (lambda: repair_partitions(DAILY_RUNS), "isn't a query or a write"),
    (lambda: explain(one_day()), "isn't a query or a write"),
])
def test_explain_refuses_what_has_no_plan_to_show(
        given: Callable[[], object], says: str) -> None:
    with pytest.raises((TypeError, ValueError), match=re.escape(says)):
        explain(given())


def test_run_gives_back_the_plan_as_text() -> None:
    hive_plan = pd.DataFrame({"Explain": ["STAGE DEPENDENCIES:", "  Stage-0 is a root stage",
                                          ""]})
    query, sent = recording(hive_plan)
    plan = run(explain(one_day()), query=query)
    assert sent == [to_hive(explain(one_day()))]
    assert plan == "STAGE DEPENDENCIES:\n  Stage-0 is a root stage"
    assert isinstance(plan, str)
    one_row_plan = pd.DataFrame({"plan": ["== Physical Plan ==\n*(1) Project [a]\n\n"]})
    assert run(explain(one_day()), query=recording(one_row_plan)[0]) == (
        "== Physical Plan ==\n*(1) Project [a]")


def test_run_refuses_a_plan_that_isnt_a_dataframe() -> None:
    with pytest.raises(TypeError, match="DataFrame"):
        run(explain(one_day()), query=lambda hive: ["STAGE DEPENDENCIES:"])


def test_export_lineage_draws_no_upkeep(tmp_path: Path) -> None:
    for s in (explain(one_day()), repair_partitions(DAILY_RUNS),
              compute_statistics(DAILY_RUNS)):
        with pytest.raises(TypeError, match="isn't a Statement that reads a table"):
            export_lineage(s, to=tmp_path / "upkeep.html")


# --- Reading each back, and the Example database ------------------------------------------


@pytest.mark.parametrize("make", [
    lambda: repair_partitions(REGION_RUNS),
    lambda: compute_statistics(REGION_RUNS, partition={"region": "EU"}, columns=True),
    lambda: compute_statistics(REGION_RUNS, partition={"region": "EU", "dt": "2026-09-24"}),
    lambda: explain(one_day()),
])
def test_each_reads_back_as_itself(make: Callable[[], Statement]) -> None:
    text = to_hive(make())
    assert toolbox_module("writing").read_back(text) == text


def test_an_upkeep_statement_that_doesnt_read_back_is_caught() -> None:
    writing = toolbox_module("writing")
    garbled = "ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24) COMPUTE STATISTICS"
    assert writing.read_back(garbled) != garbled


def test_repair_and_count_go_to_execute_which_the_example_database_only_prints(
        capsys: pytest.CaptureFixture[str]) -> None:
    for s in (repair_partitions(DAILY_RUNS), compute_statistics(DAILY_RUNS)):
        with pytest.raises(TypeError, match=r"run needs execute=, and wasn't given it\."):
            run(s, query=example_database.query)
        assert run(s, execute=example_database.execute) is None
        assert capsys.readouterr().out == f"execute: {to_hive(s)}\n"


@pytest.mark.needs_example_database
def test_the_example_database_says_it_cant_explain() -> None:
    with pytest.raises(RuntimeError, match="its executor has no EXPLAIN"):
        run(explain(one_day()), query=example_database.query)
