"""Partitions: the Load limit on reading a partitioned table, and writing into one.

A read of a table with partitioned_by= must filter at least one of its partition columns, of
whatever kind they are, or it is refused, with reads_all_partitions=True as the opt-out; an
unpartitioned table is never limited. A write into a partitioned table fills PARTITION(<its
columns>) from the rows, or names the first of them with partition={...}.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    INSERT_INTO,
    INSERT_OVERWRITE,
    JOIN,
    LEFT_JOIN,
    SELECT,
    WHERE,
    Condition,
    GuardRefused,
    LoadRefused,
    Statement,
    Table,
    all_of,
    any_of,
    at_least,
    at_most,
    between,
    compute_statistics,
    count_rows,
    derived,
    equals,
    is_in,
    is_not_in,
    is_null,
    last_n_days,
    less_than,
    more_than,
    not_equals,
    show_hive,
    statement,
    to_hive,
)
from sqlglot_composer.example_database import job_runs, jobs, region_costs

sales = Table("ops.sales", columns={"order_id": "bigint", "amount": "int", "region": "string",
                                    "day": "string"},
              partitioned_by=["region"], key=["order_id"])
"""A table partitioned by region alone: no column of it is a day to the Toolbox."""

orders = Table("ops.orders", columns={"order_id": "bigint", "customer": "string"},
               key=["order_id"])
"""An unpartitioned table."""

region_runs = Table("mart.region_runs",
                    columns={"job_id": "bigint", "runs": "bigint", "region": "string",
                             "dt": "string"},
                    partitioned_by=["region", "dt"], key=["job_id", "region", "dt"],
                    location="/data/your_team/mart.db/region_runs")
"""A Saved table partitioned by region, then dt."""

ON_ORDER = equals(sales.order_id, orders.order_id)
TWO_DAYS = between(job_runs.dt, "2026-09-23", "2026-09-24")


def reading(*conditions: Condition) -> Statement:
    return statement(SELECT(sales.order_id), FROM(sales), WHERE(*conditions))


def refusal(make: Callable[[], object]) -> str:
    """The text of the Load limit `make` is refused by, on one line."""
    with pytest.raises(LoadRefused) as refused:
        make()
    return " ".join(str(refused.value).split())


# --- Reads: what filters a partition column --------------------------------------------------


@pytest.mark.parametrize("condition", [
    pytest.param(lambda: equals(sales.region, "EU"), id="equals"),
    pytest.param(lambda: at_least(sales.region, "EU"), id="at_least"),
    pytest.param(lambda: at_most(sales.region, "EU"), id="at_most"),
    pytest.param(lambda: more_than(sales.region, "EU"), id="more_than"),
    pytest.param(lambda: less_than(sales.region, "EU"), id="less_than"),
    pytest.param(lambda: between(sales.region, "A", "M"), id="between"),
    pytest.param(lambda: is_in(sales.region, ["EU", "US"]), id="is_in"),
    pytest.param(lambda: any_of(equals(sales.region, "EU"), equals(sales.region, "US")),
                 id="any_of_where_every_part_filters_it"),
    pytest.param(lambda: all_of(equals(sales.amount, 5), equals(sales.region, "EU")),
                 id="all_of_with_a_part_that_filters_it"),
    pytest.param(lambda: all_of(between(sales.region, "A", "M"),
                                not_equals(sales.region, "EU")),
                 id="a_range_with_a_value_left_out"),
])
def test_a_filter_on_the_partition_column_lets_a_read_through(
        condition: Callable[[], Condition]) -> None:
    assert "sales.region" in to_hive(reading(condition()))


@pytest.mark.parametrize("condition", [
    pytest.param(lambda: not_equals(sales.region, "EU"), id="not_equals_alone"),
    pytest.param(lambda: is_not_in(sales.region, ["EU", "US"]), id="is_not_in"),
    pytest.param(lambda: is_null(sales.region), id="is_null"),
    pytest.param(lambda: equals(sales.amount, 5), id="another_column"),
    pytest.param(lambda: last_n_days(sales.day, 2), id="a_date_column_it_isnt_partitioned_by"),
    pytest.param(lambda: any_of(equals(sales.region, "EU"), equals(sales.amount, 5)),
                 id="any_of_over_different_columns"),
])
def test_a_read_that_filters_no_partition_column_is_refused(
        condition: Callable[[], Condition]) -> None:
    said = refusal(lambda: reading(condition()))
    assert ("FROM(sales) reads ops.sales, but filters none of its partition columns: "
            "region.") in said


def test_a_read_with_no_where_is_refused_with_its_fix_and_opt_out() -> None:
    said = refusal(lambda: statement(SELECT(sales.order_id), FROM(sales)))
    assert "filters none of its partition columns: region." in said
    assert "Usual fix: Filter one of them in WHERE, as in WHERE(equals(sales.region, ...))" in said
    assert "Opt-out: FROM(sales, reads_all_partitions=True)" in said


def test_reads_all_partitions_opts_out() -> None:
    hive = to_hive(statement(SELECT(sales.order_id), FROM(sales, reads_all_partitions=True)))
    assert hive == "SELECT\n  sales.order_id\nFROM ops.sales AS sales"


def test_an_unpartitioned_table_is_never_limited() -> None:
    assert to_hive(statement(SELECT(orders.customer), FROM(orders))).endswith(
        "FROM ops.orders AS orders")
    statement(SELECT(sales.amount, orders.customer), FROM(sales), JOIN(orders, ON=ON_ORDER),
              WHERE(equals(sales.region, "EU")))


@pytest.mark.parametrize("condition", [
    pytest.param(lambda: equals(region_costs.region, "eu"), id="its_first"),
    pytest.param(lambda: equals(region_costs.dt, "20260911"), id="its_second"),
])
def test_a_table_partitioned_by_two_columns_needs_one_of_them_filtered(
        condition: Callable[[], Condition]) -> None:
    statement(SELECT(region_costs.job_id), FROM(region_costs), WHERE(condition()))
    said = refusal(lambda: statement(SELECT(region_costs.job_id), FROM(region_costs)))
    assert "filters none of its partition columns: region, dt." in said


def test_a_value_is_compared_with_a_date_column_as_it_is_written() -> None:
    """No date format is checked: region_costs' dt is written like 20260911, job_runs' like
    2026-09-11, and each is compared with the text given."""
    assert repr(equals(region_costs.dt, "20260911")) == "region_costs.dt = '20260911'"
    assert repr(equals(job_runs.dt, "2026-9-24")) == "job_runs.dt = '2026-9-24'"


def test_last_n_days_on_a_partition_column_filters_it() -> None:
    hive = to_hive(statement(SELECT(job_runs.run_id), FROM(job_runs),
                             WHERE(last_n_days(job_runs.dt, 2))))
    assert "job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'" in hive


def test_a_derived_table_filters_its_own_reads() -> None:
    europe = derived("europe", statement(SELECT(sales.order_id, sales.amount), FROM(sales),
                                         WHERE(equals(sales.region, "EU"))))
    assert "sales.region = 'EU'" in to_hive(statement(SELECT(europe.amount), FROM(europe)))
    said = refusal(lambda: derived("every_sale", statement(SELECT(sales.order_id),
                                                           FROM(sales))))
    assert "FROM(sales) reads ops.sales" in said


# --- Reads: joins ----------------------------------------------------------------------------


def test_a_joined_table_is_filtered_in_where_or_in_its_on() -> None:
    statement(SELECT(orders.customer, sales.amount), FROM(orders), JOIN(sales, ON=ON_ORDER),
              WHERE(equals(sales.region, "EU")))
    statement(SELECT(orders.customer, sales.amount), FROM(orders),
              JOIN(sales, ON=all_of(ON_ORDER, equals(sales.region, "EU"))))


def test_a_joined_table_with_no_filter_is_refused_naming_its_join() -> None:
    said = refusal(lambda: statement(SELECT(orders.customer, sales.amount), FROM(orders),
                                     JOIN(sales, ON=ON_ORDER)))
    assert "JOIN(sales, ON=...) reads ops.sales, but filters none of its partition columns" in said
    assert "Opt-out: JOIN(sales, ON=..., reads_all_partitions=True)" in said
    statement(SELECT(orders.customer, sales.amount), FROM(orders),
              JOIN(sales, ON=ON_ORDER, reads_all_partitions=True))


def test_a_left_joined_table_is_filtered_inside_its_own_on() -> None:
    statement(SELECT(orders.customer, sales.amount), FROM(orders),
              LEFT_JOIN(sales, ON=all_of(ON_ORDER, equals(sales.region, "EU"))))
    said = refusal(lambda: statement(SELECT(orders.customer, sales.amount), FROM(orders),
                                     LEFT_JOIN(sales, ON=ON_ORDER)))
    assert "LEFT_JOIN(sales, ON=...) reads ops.sales" in said
    assert "Filter one of them inside ON=, as in ON=all_of(equals(...), equals(sales.region, " \
        "...))" in said
    assert "Opt-out: LEFT_JOIN(sales, ON=..., reads_all_partitions=True)" in said
    statement(SELECT(orders.customer, sales.amount), FROM(orders),
              LEFT_JOIN(sales, ON=ON_ORDER, reads_all_partitions=True))


def test_a_left_joined_table_filtered_in_where_is_the_left_join_guards_to_refuse() -> None:
    with pytest.raises(GuardRefused, match="a condition on sales, which LEFT_JOIN brought in"):
        statement(SELECT(orders.customer, sales.amount), FROM(orders),
                  LEFT_JOIN(sales, ON=ON_ORDER), WHERE(equals(sales.region, "EU")))
    statement(SELECT(orders.customer, sales.amount), FROM(orders),
              LEFT_JOIN(sales, ON=ON_ORDER, keeps_only_matches=True),
              WHERE(equals(sales.region, "EU")))


def test_a_filter_in_a_joins_on_doesnt_filter_the_from_table() -> None:
    said = refusal(lambda: statement(
        SELECT(orders.customer, sales.amount), FROM(sales),
        LEFT_JOIN(orders, ON=all_of(ON_ORDER, equals(sales.region, "EU")))))
    assert "FROM(sales) reads ops.sales" in said


# --- Writes: Partitions filled from the rows -------------------------------------------------


def runs_by_region(**write: object) -> Statement:
    """Each job's runs in each region on two days, written into region_runs, its SELECT in an
    order of its own."""
    return statement(
        INSERT_OVERWRITE(region_runs, **write),
        SELECT(job_runs.dt, jobs.region, job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
        WHERE(TWO_DAYS), GROUP_BY(job_runs.job_id, jobs.region, job_runs.dt))


def test_a_write_fills_every_partition_column_from_the_rows_putting_them_last() -> None:
    assert to_hive(runs_by_region()).splitlines()[:6] == [
        "INSERT OVERWRITE TABLE mart.region_runs PARTITION(region, dt)",
        "SELECT",
        "  job_runs.job_id,",
        "  COUNT(*) AS runs,",
        "  jobs.region,",
        "  job_runs.dt",
    ]


@pytest.mark.parametrize("write", [INSERT_OVERWRITE, INSERT_INTO])
def test_show_hive_prints_the_session_setting_a_dynamic_write_needs(
        write: Callable[..., object]) -> None:
    s = statement(write(region_runs),
                  SELECT(job_runs.job_id, AS(count_rows(), "runs"), jobs.region, job_runs.dt),
                  FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                  WHERE(TWO_DAYS), GROUP_BY(job_runs.job_id, jobs.region, job_runs.dt))
    lines = show_hive(s).splitlines()
    assert lines[:3] == [
        '-- The Session setting "dynamic_partitions": this write fills region, dt from its rows.',
        "SET hive.exec.dynamic.partition=true;",
        "SET hive.exec.dynamic.partition.mode=nonstrict;",
    ]
    assert lines[3] == to_hive(s).splitlines()[0]
    assert not to_hive(s).startswith("SET")


def test_a_dynamic_write_leaving_out_a_partition_column_is_refused() -> None:
    with pytest.raises(GuardRefused, match=r"INSERT_OVERWRITE\(region_runs\): it leaves out "
                                           r"region\."):
        statement(INSERT_OVERWRITE(region_runs),
                  SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
                  FROM(job_runs), WHERE(TWO_DAYS), GROUP_BY(job_runs.job_id, job_runs.dt))


def test_a_write_into_a_partitioned_table_someone_else_owns_is_refused() -> None:
    # ADR 0007: only your own Saved tables are written. A write into someone else's
    # partitioned table would replace, or add to, Partitions that are theirs; ops.job_runs
    # has partitioned_by= and no location=.
    for write in (INSERT_OVERWRITE, INSERT_INTO):
        with pytest.raises(ValueError, match=r"was given ops.job_runs, which isn't one of your "
                           "Saved tables: its Table reference has no location="):
            write(job_runs)
        with pytest.raises(ValueError, match="isn't one of your Saved tables"):
            write(job_runs, partition={"dt": "2026-09-24"})


# --- Writes: partition={...} -----------------------------------------------------------------


def europe(**write: object) -> Statement:
    """Each job's runs on two days, written into region_runs' Partition region = 'EU'."""
    return statement(
        INSERT_OVERWRITE(region_runs, partition={"region": "EU"}, **write),
        SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
        FROM(job_runs), WHERE(TWO_DAYS), GROUP_BY(job_runs.job_id, job_runs.dt))


def test_partition_names_its_columns_values_and_select_leaves_them_out() -> None:
    lines = to_hive(europe()).splitlines()
    assert lines[:5] == [
        "INSERT OVERWRITE TABLE mart.region_runs PARTITION(region = 'EU', dt)",
        "SELECT",
        "  job_runs.job_id,",
        "  COUNT(*) AS runs,",
        "  job_runs.dt",
    ]
    assert show_hive(europe()).splitlines()[0] == (
        '-- The Session setting "dynamic_partitions": this write fills dt from its rows.')


def test_a_write_naming_every_partition_column_needs_no_session_setting() -> None:
    s = statement(INSERT_INTO(region_runs, partition={"region": "EU", "dt": "2026-09-24"}),
                  SELECT(job_runs.job_id, AS(count_rows(), "runs")), FROM(job_runs),
                  WHERE(equals(job_runs.dt, "2026-09-24")), GROUP_BY(job_runs.job_id))
    assert show_hive(s).splitlines()[0] == (
        "INSERT INTO mart.region_runs PARTITION(region = 'EU', dt = '2026-09-24')")


def test_a_column_partition_names_is_selected_as_an_extra_column() -> None:
    with pytest.raises(GuardRefused, match="it also selects region"):
        statement(INSERT_OVERWRITE(region_runs, partition={"region": "EU"}),
                  SELECT(job_runs.job_id, AS(count_rows(), "runs"), jobs.region, job_runs.dt),
                  FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                  WHERE(TWO_DAYS), GROUP_BY(job_runs.job_id, jobs.region, job_runs.dt))


@pytest.mark.parametrize(("partition", "error", "said"), [
    pytest.param({"job_id": 1}, ValueError,
                 "names 'job_id', which isn't a partition column of mart.region_runs",
                 id="a_column_it_isnt_partitioned_by"),
    pytest.param({"dt": "2026-09-24"}, ValueError,
                 "names dt, but not region, which comes before it in mart.region_runs's "
                 "partitioned_by (region, dt)", id="not_its_first_columns"),
    pytest.param({"region": None}, ValueError, "gives region None", id="none"),
    pytest.param({"region": job_runs.status}, ValueError, "gives region job_runs.status",
                 id="a_column"),
    pytest.param({}, TypeError, "partition= is a dict of partition columns and their values",
                 id="an_empty_dict"),
    pytest.param(["region"], TypeError, "partition= is a dict", id="not_a_dict"),
])
@pytest.mark.parametrize("call", [INSERT_OVERWRITE, INSERT_INTO, compute_statistics])
def test_partition_refuses_what_doesnt_name_its_first_columns_values(
        call: Callable[..., object], partition: object, error: type[Exception],
        said: str) -> None:
    # A write and compute_statistics check partition= alike, with the same refusals.
    with pytest.raises(error) as refused:
        call(region_runs, partition=partition)
    assert said in " ".join(str(refused.value).split())
    assert f"{call.__name__}(region_runs, partition=" in str(refused.value)


@pytest.mark.parametrize("call", [INSERT_OVERWRITE, INSERT_INTO, compute_statistics])
def test_partition_on_an_unpartitioned_table_is_refused(call: Callable[..., object]) -> None:
    saved = Table("mart.job_teams", columns={"job_id": "bigint", "team": "string"},
                  location="/data/your_team/mart.db/job_teams")
    with pytest.raises(ValueError) as refused:
        call(saved, partition={"team": "data"})
    message = " ".join(str(refused.value).split())
    assert (f"{call.__name__}(job_teams, partition=...): mart.job_teams isn't partitioned."
            in message)
    assert f"Leave partition= out, as in {call.__name__}(job_teams)" in message


# --- Writes: the Key -------------------------------------------------------------------------


def test_a_partition_column_partition_names_is_left_out_of_the_key() -> None:
    """region_runs' Key is job_id, region and dt: with region named, GROUP_BY job_id and dt
    shows it."""
    assert to_hive(europe()).startswith("INSERT OVERWRITE TABLE mart.region_runs")


def test_the_rest_of_the_key_must_still_be_shown() -> None:
    with pytest.raises(GuardRefused) as refused:
        statement(INSERT_OVERWRITE(region_runs, partition={"region": "EU"}),
                  SELECT(job_runs.job_id, AS(job_runs.duration_mins, "runs"), job_runs.dt),
                  FROM(job_runs), WHERE(TWO_DAYS))
    said = " ".join(str(refused.value).split())
    assert "has a Key (job_id, region, dt) of its own" in said
    assert "nothing makes its rows one for each job_id, dt." in said
    assert "Opt-out: INSERT_OVERWRITE(region_runs, unproven_key=True)" in said
