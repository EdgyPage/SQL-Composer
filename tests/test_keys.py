"""A Saved table's Key is checked before writing (ADR 0005).

A write into a Saved table with a Key is refused unless the Toolbox can see that each row it
writes has a Key of its own: a GROUP_BY over the Key's columns, a SELECT_DISTINCT, a
row_number kept at 1 per Key in a Derived table, or a join that keeps the reading table's Key.
unproven_key=True on the write lets one through. The same reading carries a Derived table's
Key through key-keeping joins and a row_number kept at 1, so the repeated-rows Warning asks
less often.
"""

from __future__ import annotations

import warnings

import pytest

from sqlglot_composer import (
    AS,
    CROSS_JOIN,
    FROM,
    GROUP_BY,
    INSERT_INTO,
    INSERT_OVERWRITE,
    JOIN,
    LEFT_JOIN,
    SELECT,
    SELECT_DISTINCT,
    WHERE,
    GuardRefused,
    Table,
    all_of,
    at_most,
    between,
    by_day,
    count_rows,
    create_table,
    derived,
    descending,
    equals,
    row_number,
    statement,
    sum_of,
    to_hive,
)
from composer_core.example_database import job_owners, job_runs, jobs, run_alerts

DAY = "2026-09-24"
BASE = "/data/your_team/tables"

per_job = Table("mart.per_job", columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
                date_partition="dt", key=["job_id", "dt"], location=BASE)
per_run = Table("mart.per_run", columns={"run_id": "bigint", "job_id": "bigint",
                                         "status": "string", "dt": "string"},
                date_partition="dt", key=["run_id"])
per_run_and_team = Table("mart.per_run_and_team", columns={
    "run_id": "bigint", "team": "string", "dt": "string"}, date_partition="dt", key=["run_id"])
newest_per_job = Table("mart.newest_per_job", columns={
    "job_id": "bigint", "run_id": "bigint", "dt": "string"}, date_partition="dt",
    key=["job_id"])
no_key = Table("mart.no_key", columns={"job_id": "bigint", "status": "string", "dt": "string"},
               date_partition="dt", location=BASE)


def on_the_day():
    return equals(job_runs.dt, DAY)


def numbered_runs():
    """job_runs' runs numbered per job, newest first."""
    return derived("numbered", statement(
        SELECT(job_runs.job_id, job_runs.run_id,
               AS(row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id)),
                  "newest_first")),
        FROM(job_runs), WHERE(on_the_day())))


# --- What proves a Key -----------------------------------------------------------------------


@pytest.mark.parametrize("write", [INSERT_OVERWRITE, INSERT_INTO])
def test_a_group_by_over_the_key_proves_it(write) -> None:
    statement(write(per_job), SELECT(job_runs.job_id, AS(count_rows(), "runs")),
              FROM(job_runs), WHERE(on_the_day()), GROUP_BY(job_runs.job_id))


def test_grouping_by_the_day_written_too_still_proves_it() -> None:
    """The day written is one day, so grouping by it changes nothing."""
    statement(INSERT_OVERWRITE(per_job), SELECT(job_runs.job_id, AS(count_rows(), "runs")),
              FROM(job_runs), WHERE(on_the_day()), GROUP_BY(job_runs.dt, job_runs.job_id))


def test_select_distinct_of_the_key_proves_it() -> None:
    keys = Table("mart.keys", columns={"job_id": "bigint", "dt": "string"},
                 date_partition="dt", key=["job_id"])
    statement(INSERT_OVERWRITE(keys), SELECT_DISTINCT(job_runs.job_id), FROM(job_runs),
              WHERE(on_the_day()))


def test_select_distinct_with_columns_the_key_decides_proves_it() -> None:
    """job_id is decided by run_id, job_runs' Key, so DISTINCT on both is unique by run_id."""
    statement(INSERT_INTO(per_run), SELECT_DISTINCT(job_runs.run_id, job_runs.job_id,
                                                    job_runs.status),
              FROM(run_alerts), JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
              WHERE(equals(run_alerts.dt, DAY), on_the_day()))


def test_reading_the_tables_own_key_proves_it() -> None:
    statement(INSERT_OVERWRITE(per_run), SELECT(job_runs.run_id, job_runs.job_id,
                                                job_runs.status),
              FROM(job_runs), WHERE(on_the_day()))


def test_a_join_on_the_joined_tables_whole_key_keeps_the_key() -> None:
    statement(INSERT_OVERWRITE(per_run_and_team), SELECT(job_runs.run_id, jobs.team),
              FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
              WHERE(on_the_day()))


def test_a_left_join_on_the_joined_tables_whole_key_keeps_the_key() -> None:
    statement(INSERT_OVERWRITE(per_run_and_team), SELECT(job_runs.run_id, jobs.team),
              FROM(job_runs), LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
              WHERE(on_the_day()))


def test_a_joined_tables_day_bounded_to_one_day_needs_no_match() -> None:
    """job_owners' Key is job_id and dt; with dt bounded to one day, job_id alone is enough."""
    owners = Table("mart.owners", columns={"run_id": "bigint", "owner": "string",
                                           "dt": "string"}, date_partition="dt",
                   key=["run_id"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # JOIN can't see WHERE, so it still warns
        statement(INSERT_OVERWRITE(owners), SELECT(job_runs.run_id, job_owners.owner),
                  FROM(job_runs), JOIN(job_owners, ON=equals(job_owners.job_id,
                                                             job_runs.job_id)),
                  WHERE(on_the_day(), equals(job_owners.dt, DAY)))


def test_a_row_number_kept_at_1_proves_its_partition() -> None:
    numbered = numbered_runs()
    statement(INSERT_OVERWRITE(newest_per_job), SELECT(numbered.job_id, numbered.run_id),
              FROM(numbered), WHERE(equals(numbered.newest_first, 1)))


def test_a_write_of_several_days_keeps_the_day_in_its_key() -> None:
    """by_day splits it into one write per day, so a Derived table's day holds one value."""
    per_day = derived("per_day", statement(
        SELECT(job_runs.job_id, job_runs.dt, AS(count_rows(), "runs")), FROM(job_runs),
        WHERE(between(job_runs.dt, "2026-09-23", DAY)), GROUP_BY(job_runs.job_id, job_runs.dt)))
    writes = by_day(statement(INSERT_OVERWRITE(per_job), SELECT(per_day.job_id, per_day.runs),
                              FROM(per_day)))
    assert len(writes) == 2


def test_a_join_that_repeats_rows_still_shows_the_key_when_its_own_key_decides_the_rest() -> None:
    """Each job's owner on each of its runs: the join repeats job_owners' rows, one per run,
    and run_id, job_runs' Key, decides the job_id the two are joined on."""
    run_owner = Table("mart.run_owner", columns={"run_id": "bigint", "owner": "string",
                                                 "dt": "string"},
                      date_partition="dt", key=["run_id", "dt"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        statement(INSERT_OVERWRITE(run_owner), SELECT(job_runs.run_id, job_owners.owner),
                  FROM(job_owners),
                  JOIN(job_runs, ON=equals(job_runs.job_id, job_owners.job_id)),
                  WHERE(equals(job_owners.dt, DAY), on_the_day()))


def test_a_table_with_no_key_is_written_as_before() -> None:
    statement(INSERT_INTO(no_key), SELECT(job_runs.job_id, job_runs.status), FROM(job_runs),
              WHERE(on_the_day()))


def test_a_cross_join_with_one_row_keeps_the_key() -> None:
    total = derived("total", statement(SELECT(AS(sum_of(job_runs.duration_mins), "minutes")),
                                       FROM(job_runs), WHERE(on_the_day())))
    shares = Table("mart.shares", columns={"run_id": "bigint", "minutes": "bigint",
                                           "dt": "string"}, date_partition="dt",
                   key=["run_id"])
    statement(INSERT_OVERWRITE(shares), SELECT(job_runs.run_id, total.minutes), FROM(job_runs),
              CROSS_JOIN(total), WHERE(on_the_day()))


# --- What doesn't, and the refusal -----------------------------------------------------------


def refusal(*clauses) -> str:
    with pytest.raises(GuardRefused) as refused:
        statement(*clauses)
    return " ".join(str(refused.value).split())


@pytest.mark.parametrize("write", [INSERT_OVERWRITE, INSERT_INTO])
def test_a_write_with_no_proof_is_refused_with_its_opt_out(write) -> None:
    said = refusal(write(per_job), SELECT(job_runs.job_id, AS(job_runs.duration_mins, "runs")),
                   FROM(job_runs), WHERE(on_the_day()))
    name = write.__name__
    assert f"What happened: {name}(per_job) can't show that each row it writes has a Key " \
           "(job_id, dt) of its own" in said
    assert ("job_runs' rows are told apart by run_id, and SELECT leaves out job_runs.run_id, so "
            "nothing makes its rows one for each job_id") in said
    assert "Hive never checks a Key" in said
    assert f"Opt-out: {name}(per_job, unproven_key=True)" in said


def test_the_opt_out_lets_the_write_through() -> None:
    s = statement(INSERT_OVERWRITE(per_job, unproven_key=True),
                  SELECT(job_runs.job_id, AS(job_runs.run_id, "runs")), FROM(job_runs),
                  WHERE(on_the_day()))
    assert to_hive(s).startswith("INSERT OVERWRITE TABLE mart.per_job PARTITION(dt = ")


def test_grouping_by_more_than_the_key_is_refused() -> None:
    per_status = Table("mart.per_status", columns={"job_id": "bigint", "status": "string",
                                                   "runs": "bigint", "dt": "string"},
                       date_partition="dt", key=["job_id"])
    said = refusal(INSERT_OVERWRITE(per_status),
                   SELECT(job_runs.job_id, job_runs.status, AS(count_rows(), "runs")),
                   FROM(job_runs), WHERE(on_the_day()), GROUP_BY(job_runs.job_id,
                                                                  job_runs.status))
    assert "GROUP_BY makes one row for each job_id, status, not one for each job_id" in said


def test_grouping_by_a_column_select_leaves_out_is_refused() -> None:
    said = refusal(INSERT_OVERWRITE(per_job), SELECT(job_runs.job_id, AS(count_rows(), "runs")),
                   FROM(job_runs), WHERE(on_the_day()), GROUP_BY(job_runs.job_id,
                                                                  job_runs.status))
    assert "GROUP_BY groups by job_runs.status, which SELECT leaves out" in said


def test_a_join_that_can_repeat_rows_is_named() -> None:
    said = refusal(INSERT_OVERWRITE(per_run_and_team),
                   SELECT(job_runs.run_id, AS(run_alerts.severity, "team")), FROM(job_runs),
                   JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id),
                        many_matches=True),
                   WHERE(on_the_day(), equals(run_alerts.dt, DAY)))
    assert "JOIN(run_alerts, ON=...) can match several run_alerts rows to one row" in said


def test_a_row_number_kept_up_to_2_is_refused() -> None:
    numbered = numbered_runs()
    said = refusal(INSERT_OVERWRITE(newest_per_job), SELECT(numbered.job_id, numbered.run_id),
                   FROM(numbered), WHERE(at_most(numbered.newest_first, 2)))
    assert "numbered's rows are told apart by run_id, not by job_id" in said


def test_a_select_that_leaves_out_part_of_the_key_is_refused() -> None:
    said = refusal(INSERT_OVERWRITE(newest_per_job),
                   SELECT(job_runs.job_id, AS(job_runs.job_id, "run_id")), FROM(job_runs),
                   WHERE(on_the_day()))
    assert "job_runs' rows are told apart by run_id, and SELECT leaves out job_runs.run_id" in said


def test_unproven_key_must_be_true_or_false() -> None:
    with pytest.raises(ValueError, match="unproven_key="):
        INSERT_OVERWRITE(per_job, unproven_key="yes")


# --- A Derived table's Key reaches further ---------------------------------------------------


def joins_quietly(*clauses) -> None:
    """The Statement is built with no repeated-rows Warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        statement(*clauses)


def test_a_derived_tables_key_is_carried_through_a_key_keeping_join() -> None:
    with_team = derived("with_team", statement(
        SELECT(job_runs.run_id, job_runs.job_id, jobs.team), FROM(job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)), WHERE(on_the_day())))
    joins_quietly(SELECT(run_alerts.alert_id, with_team.team), FROM(run_alerts),
                  JOIN(with_team, ON=equals(with_team.run_id, run_alerts.run_id)),
                  WHERE(equals(run_alerts.dt, DAY)))


def test_a_derived_tables_key_is_carried_through_a_row_number_kept_at_1() -> None:
    numbered = numbered_runs()
    newest = derived("newest", statement(SELECT(numbered.job_id, numbered.run_id),
                                         FROM(numbered),
                                         WHERE(equals(numbered.newest_first, 1))))
    joins_quietly(SELECT(jobs.job_name, newest.run_id), FROM(jobs),
                  JOIN(newest, ON=equals(newest.job_id, jobs.job_id)))


def test_the_warning_on_a_derived_table_with_no_key_says_where_it_lost_it() -> None:
    with_alerts = derived("with_alerts", statement(
        SELECT(job_runs.run_id, run_alerts.severity), FROM(job_runs),
        JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id), many_matches=True),
        WHERE(on_the_day(), equals(run_alerts.dt, DAY))))
    with pytest.warns(UserWarning) as warned:
        statement(SELECT(jobs.job_name, with_alerts.severity), FROM(jobs),
                  JOIN(with_alerts, ON=equals(with_alerts.run_id, jobs.job_id)))
    said = " ".join(str(warned[0].message).split())
    assert "JOIN(run_alerts, ON=...) can match several run_alerts rows to one row" in said


def test_an_all_of_with_the_key_keeps_it() -> None:
    joins_quietly(SELECT(job_runs.run_id, jobs.team), FROM(job_runs),
                  JOIN(jobs, ON=all_of(equals(jobs.job_id, job_runs.job_id),
                                       equals(jobs.team, "data"))),
                  WHERE(on_the_day()))


# --- create_table writes the Key into the table ----------------------------------------------


def test_create_table_writes_the_key_as_information_hive_never_checks() -> None:
    assert to_hive(create_table(per_job)) == (
        "CREATE EXTERNAL TABLE mart.per_job (\n"
        "  job_id BIGINT,\n"
        "  runs BIGINT,\n"
        "  PRIMARY KEY (job_id, dt) DISABLE NOVALIDATE\n"
        ")\n"
        "PARTITIONED BY (\n"
        "  dt STRING\n"
        ")\n"
        "STORED AS ORC\n"
        "LOCATION '/data/your_team/tables/mart/per_job'"
    )


def test_create_table_puts_a_key_column_in_backticks_where_hive_needs_them() -> None:
    odd = Table("mart.odd", columns={"select": "string", "dt": "string"}, date_partition="dt",
                key=["select"], location=BASE)
    assert "PRIMARY KEY (`select`) DISABLE NOVALIDATE" in to_hive(create_table(odd))


def test_create_table_of_a_table_with_no_key_writes_none() -> None:
    assert "PRIMARY KEY" not in to_hive(create_table(no_key))
