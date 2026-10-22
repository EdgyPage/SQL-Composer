"""The opt-outs no other test or doc passed, each shown doing what its docstring says.

tests/repo/test_dead_code.py holds that every keyword of a public function is passed somewhere:
these are the ones that weren't, each beside what it lets through. Each calls its function by
name, as that test reads calls by the name called.
"""

from __future__ import annotations

import warnings

import pytest

from sqlglot_composer import (
    ANTI_JOIN,
    CROSS_JOIN,
    EXCEPT,
    FROM,
    FULL_JOIN,
    INSERT_INTO,
    INTERSECT,
    JOIN,
    SELECT,
    SEMI_JOIN,
    UNION,
    WHERE,
    Clause,
    GuardRefused,
    LoadRefused,
    Statement,
    Table,
    average_of,
    equals,
    min_of,
    set_load_limits,
    statement,
    to_hive,
)
from sqlglot_composer.example_database import job_events, job_runs, jobs

job_teams = Table("mart.job_teams", columns={"job_id": "bigint", "team": "string"},
                  key=["job_id"], location="/data/your_team/mart.db/job_teams")
ON_EVENTS = equals(job_events.job_id, jobs.job_id)


def reading(join: Clause) -> Statement:
    return statement(SELECT(jobs.job_id), FROM(jobs), join)


def test_a_semi_join_reads_every_partition_only_when_it_says_so() -> None:
    with pytest.raises(LoadRefused):
        reading(SEMI_JOIN(job_events, ON=ON_EVENTS))
    assert "LEFT SEMI JOIN ops.job_events" in to_hive(
        reading(SEMI_JOIN(job_events, ON=ON_EVENTS, reads_all_partitions=True)))


def test_an_anti_join_reads_every_partition_only_when_it_says_so() -> None:
    with pytest.raises(LoadRefused):
        reading(ANTI_JOIN(job_events, ON=ON_EVENTS))
    assert "LEFT JOIN ops.job_events" in to_hive(
        reading(ANTI_JOIN(job_events, ON=ON_EVENTS, reads_all_partitions=True)))


def test_a_cross_join_reads_every_partition_only_when_it_says_so() -> None:
    with pytest.raises(LoadRefused):
        reading(CROSS_JOIN(job_runs))
    assert "CROSS JOIN ops.job_runs AS job_runs" in to_hive(
        reading(CROSS_JOIN(job_runs, reads_all_partitions=True)))


def test_a_full_join_off_the_key_warns_unless_many_matches_says_it_means_to() -> None:
    on = equals(job_runs.job_id, jobs.job_id)
    with pytest.warns(UserWarning, match="FULL_JOIN"):
        reading(FULL_JOIN(job_runs, ON=on, reads_all_partitions=True))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        reading(FULL_JOIN(job_runs, ON=on, reads_all_partitions=True, many_matches=True))


def test_unproven_key_is_true_or_false() -> None:
    with pytest.raises(ValueError, match="unproven_key= is True or False"):
        INSERT_INTO(job_teams, unproven_key="yes")


def test_insert_into_lets_an_unproven_key_through_only_when_it_says_so() -> None:
    rows = [SELECT(jobs.job_id, jobs.team), FROM(job_runs),
            JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
            WHERE(equals(job_runs.dt, "2026-09-24"))]
    with pytest.raises(GuardRefused, match="unproven_key=True"):
        statement(INSERT_INTO(job_teams), *rows)
    assert to_hive(statement(INSERT_INTO(job_teams, unproven_key=True), *rows)).startswith(
        "INSERT INTO mart.job_teams\nSELECT")


EVERY = statement(SELECT(jobs.job_id), FROM(jobs))
DATA = statement(SELECT(jobs.job_id), FROM(jobs), WHERE(equals(jobs.team, "data")))


def test_union_drops_its_automatic_limit_only_when_it_says_so() -> None:
    set_load_limits(rows=100)
    assert to_hive(UNION(EVERY, DATA)).endswith("LIMIT 100")
    assert "LIMIT" not in to_hive(UNION(EVERY, DATA, returns_all_rows=True))


def test_intersect_drops_its_automatic_limit_only_when_it_says_so() -> None:
    set_load_limits(rows=100)
    assert to_hive(INTERSECT(EVERY, DATA)).endswith("LIMIT 100")
    assert "LIMIT" not in to_hive(INTERSECT(EVERY, DATA, returns_all_rows=True))


def test_except_drops_its_automatic_limit_only_when_it_says_so() -> None:
    set_load_limits(rows=100)
    assert to_hive(EXCEPT(EVERY, DATA)).endswith("LIMIT 100")
    assert "LIMIT" not in to_hive(EXCEPT(EVERY, DATA, returns_all_rows=True))


def test_average_of_a_column_that_doesnt_add_up_needs_adds_up() -> None:
    with pytest.raises(GuardRefused, match="adds_up=True"):
        average_of(job_runs.avg_retry_secs)
    assert repr(average_of(job_runs.avg_retry_secs, adds_up=True)) == (
        "AVG(job_runs.avg_retry_secs)")


def test_min_of_counts_only_the_rows_where_picks() -> None:
    failed = min_of(job_runs.duration_mins, where=equals(job_runs.status, "FAILED"))
    assert repr(failed) == ("MIN(CASE WHEN job_runs.status = 'FAILED' THEN "
                            "job_runs.duration_mins END)")
