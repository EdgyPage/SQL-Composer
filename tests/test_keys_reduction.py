"""Keys' reduction: a Key less each column the others decide, tried from the last.

These pin the Keys statement_keys(...) finds where that reduction runs: a SELECT_DISTINCT's
columns, a GROUP_BY's, and a table's Key widened by its joins. They were written before the two
copies of the loop became one, to hold its answers as they were, the odd ones too: a Key that
names a column twice, and two columns that decide each other.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from sqlglot_composer import (
    AS,
    CROSS_JOIN,
    FROM,
    GROUP_BY,
    JOIN,
    LEFT_JOIN,
    SELECT,
    SELECT_DISTINCT,
    WHERE,
    Condition,
    Statement,
    Table,
    all_of,
    count_rows,
    equals,
    statement,
)
from sqlglot_composer.clauses import Clause
from sqlglot_composer.example_database import job_owners, job_runs, jobs, run_alerts
from sqlglot_composer.keys import statement_keys

DAY = "2026-09-24"

twice = Table("mart.twice", columns={"run_id": "bigint", "job_id": "bigint"},
              key=["run_id", "run_id"])
pair = Table("mart.pair", columns={"run_id": "bigint", "job_id": "bigint", "note": "string"},
             key=["run_id", "job_id"])
loop = Table("mart.loop", columns={"run_id": "bigint", "job_id": "bigint"},
             key=["run_id", "job_id", "run_id"])
# Joined on loop's run_id and job_id, each by its own Key: so loop's run_id decides its job_id
# through by_run, and its job_id decides its run_id through by_job.
by_run = Table("mart.by_run", columns={"run_id": "bigint", "job_id": "bigint"}, key=["run_id"])
by_job = Table("mart.by_job", columns={"run_id": "bigint", "job_id": "bigint"}, key=["job_id"])


def runs_on_the_day() -> Condition:
    return equals(job_runs.dt, DAY)


def both_on_the_day() -> Clause:
    return WHERE(equals(job_runs.dt, DAY), equals(run_alerts.dt, DAY))


# Each case: a Statement, and the Keys found for it, each (names, why, instead), then
# where they were lost.
CASES: dict[str, tuple[Callable[[], Statement],
                       tuple[list[tuple[list[str], str, str]], str | None]]] = {
    # SELECT_DISTINCT: its columns, less each one the others decide.
    "distinct, the Key first": (lambda: statement(
        SELECT_DISTINCT(job_runs.run_id, job_runs.job_id, job_runs.status), FROM(job_runs),
        WHERE(runs_on_the_day())),
        ([(["run_id"], "SELECT_DISTINCT makes one row for each different run_id",
           "not one for each")], None)),
    "distinct, the Key last": (lambda: statement(
        SELECT_DISTINCT(job_runs.job_id, job_runs.status, job_runs.run_id), FROM(job_runs),
        WHERE(runs_on_the_day())),
        ([(["run_id"], "SELECT_DISTINCT makes one row for each different run_id",
           "not one for each")], None)),
    "distinct, no Key among them": (lambda: statement(
        SELECT_DISTINCT(job_runs.job_id, job_runs.status), FROM(job_runs),
        WHERE(runs_on_the_day())),
        ([(["job_id", "status"], "SELECT_DISTINCT makes one row for each different job_id, "
           "status", "not one for each")], None)),
    "distinct, a calculation the Key decides": (lambda: statement(
        SELECT_DISTINCT(job_runs.run_id, AS(job_runs.duration_mins + 1, "plus")),
        FROM(job_runs), WHERE(runs_on_the_day())),
        ([(["run_id"], "SELECT_DISTINCT makes one row for each different run_id",
           "not one for each")], None)),
    "distinct, a column held to one value": (lambda: statement(
        SELECT_DISTINCT(job_runs.job_id, job_runs.dt), FROM(job_runs),
        WHERE(runs_on_the_day())),
        ([(["job_id"], "SELECT_DISTINCT makes one row for each different job_id",
           "not one for each")], None)),
    "distinct, two columns set equal": (lambda: statement(
        SELECT_DISTINCT(jobs.job_id, AS(job_runs.job_id, "run_job")), FROM(job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)), WHERE(runs_on_the_day())),
        ([(["job_id"], "SELECT_DISTINCT makes one row for each different job_id",
           "not one for each")], None)),
    "distinct, through a join": (lambda: statement(
        SELECT_DISTINCT(job_runs.run_id, job_runs.job_id, run_alerts.alert_id),
        FROM(run_alerts), JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
        both_on_the_day()),
        ([(["alert_id"], "SELECT_DISTINCT makes one row for each different alert_id",
           "not one for each")], None)),
    "distinct, through a LEFT_JOIN": (lambda: statement(
        SELECT_DISTINCT(job_runs.run_id, jobs.team), FROM(job_runs),
        LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)), WHERE(runs_on_the_day())),
        ([(["run_id"], "SELECT_DISTINCT makes one row for each different run_id",
           "not one for each")], None)),
    # GROUP_BY: its columns SELECT returns, less each one the others decide.
    "group, a column held to one value": (lambda: statement(
        SELECT(job_runs.job_id, job_runs.dt, AS(count_rows(), "runs")), FROM(job_runs),
        WHERE(runs_on_the_day()), GROUP_BY(job_runs.job_id, job_runs.dt)),
        ([(["job_id"], "GROUP_BY makes one row for each job_id, dt, with dt held to one value",
           "not one for each")], None)),
    "group, the Key first": (lambda: statement(
        SELECT(job_runs.run_id, job_runs.job_id, AS(count_rows(), "n")), FROM(job_runs),
        WHERE(runs_on_the_day()), GROUP_BY(job_runs.run_id, job_runs.job_id)),
        ([(["run_id"], "GROUP_BY makes one row for each run_id", "not one for each")], None)),
    "group, the Key last": (lambda: statement(
        SELECT(job_runs.job_id, job_runs.run_id, AS(count_rows(), "n")), FROM(job_runs),
        WHERE(runs_on_the_day()), GROUP_BY(job_runs.job_id, job_runs.run_id)),
        ([(["run_id"], "GROUP_BY makes one row for each run_id", "not one for each")], None)),
    "group, a column SELECT leaves out that the Key decides": (lambda: statement(
        SELECT(job_runs.run_id, AS(count_rows(), "n")), FROM(job_runs),
        WHERE(runs_on_the_day()), GROUP_BY(job_runs.run_id, job_runs.job_id)),
        ([(["run_id"], "GROUP_BY makes one row for each run_id", "not one for each")], None)),
    "group, a column SELECT leaves out that nothing decides": (lambda: statement(
        SELECT(job_runs.job_id, AS(count_rows(), "n")), FROM(job_runs),
        WHERE(runs_on_the_day()), GROUP_BY(job_runs.job_id, job_runs.status)),
        ([], "GROUP_BY groups by job_runs.status, which SELECT leaves out")),
    "group, one column twice": (lambda: statement(
        SELECT(job_runs.job_id, AS(count_rows(), "n")), FROM(job_runs),
        WHERE(runs_on_the_day()), GROUP_BY(job_runs.job_id, job_runs.job_id)),
        ([(["job_id"], "GROUP_BY makes one row for each job_id", "not one for each")], None)),
    "group, a calculation the Key decides": (lambda: statement(
        SELECT(job_runs.run_id, AS(job_runs.duration_mins + 1, "plus"), AS(count_rows(), "n")),
        FROM(job_runs), WHERE(runs_on_the_day()),
        GROUP_BY(job_runs.run_id, job_runs.duration_mins + 1)),
        ([(["run_id"], "GROUP_BY makes one row for each run_id", "not one for each")], None)),
    "group, one calculation twice": (lambda: statement(
        SELECT(job_runs.job_id, AS(job_runs.duration_mins + 1, "plus"), AS(count_rows(), "n")),
        FROM(job_runs), WHERE(runs_on_the_day()),
        GROUP_BY(job_runs.job_id, job_runs.duration_mins + 1, job_runs.duration_mins + 1)),
        ([(["job_id", "plus", "plus"], "GROUP_BY makes one row for each job_id, plus, plus",
           "not one for each")], None)),
    # A table's Key, widened by each join that can repeat its rows.
    "rows, the Key": (lambda: statement(
        SELECT(job_runs.run_id, job_runs.job_id), FROM(job_runs), WHERE(runs_on_the_day())),
        ([(["run_id"], "job_runs' rows are told apart by run_id", "not by")], None)),
    "rows, a join that repeats them": (lambda: statement(
        SELECT(job_runs.run_id, run_alerts.alert_id), FROM(job_runs),
        JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id), many_matches=True),
        both_on_the_day()),
        ([(["alert_id"], "JOIN(run_alerts, ON=...) can match several run_alerts rows to one "
           "row", "")], None)),
    "rows, a join that keeps them": (lambda: statement(
        SELECT(run_alerts.alert_id, job_runs.status), FROM(run_alerts),
        JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)), both_on_the_day()),
        ([(["alert_id"], "run_alerts' rows are told apart by alert_id", "not by")], None)),
    "rows, a CROSS_JOIN": (lambda: statement(
        SELECT(job_runs.run_id, jobs.job_id), FROM(job_runs), CROSS_JOIN(jobs),
        WHERE(runs_on_the_day())),
        ([(["run_id", "job_id"], "CROSS_JOIN(jobs) pairs each row with every jobs row", "")],
         None)),
    "rows, a CROSS_JOIN whose Key SELECT leaves out": (lambda: statement(
        SELECT(job_runs.run_id), FROM(job_runs), CROSS_JOIN(jobs), WHERE(runs_on_the_day())),
        ([], "CROSS_JOIN(jobs) pairs each row with every jobs row")),
    "rows, a Key that names a column twice": (lambda: statement(
        SELECT(twice.run_id, twice.job_id), FROM(twice)),
        ([(["run_id"], "twice's rows are told apart by run_id, run_id", "not by")], None)),
    "rows, a Key that names a column twice, joined": (lambda: statement(
        SELECT(twice.run_id, run_alerts.alert_id), FROM(twice),
        JOIN(run_alerts, ON=equals(run_alerts.run_id, twice.run_id), many_matches=True),
        WHERE(equals(run_alerts.dt, DAY))),
        ([(["alert_id"], "JOIN(run_alerts, ON=...) can match several run_alerts rows to one "
           "row", "")], None)),
    "rows, a Key column a join decides": (lambda: statement(
        SELECT(pair.run_id, pair.job_id, pair.note), FROM(pair),
        JOIN(job_runs, ON=all_of(equals(job_runs.run_id, pair.run_id),
                                 equals(job_runs.job_id, pair.job_id))),
        WHERE(runs_on_the_day())),
        ([(["run_id"], "pair's rows are told apart by run_id, job_id", "not by")], None)),
    "rows, a Key of two": (lambda: statement(SELECT(pair.run_id, pair.job_id), FROM(pair)),
        ([(["run_id", "job_id"], "pair's rows are told apart by run_id, job_id", "not by")],
         None)),
    "rows, a Key column SELECT leaves out": (lambda: statement(
        SELECT(pair.run_id), FROM(pair)),
        ([], "pair's rows are told apart by run_id, job_id, and SELECT leaves out "
         "pair.job_id")),
    "rows, a Key column held to one value": (lambda: statement(
        SELECT(job_owners.job_id, job_owners.owner), FROM(job_owners),
        WHERE(equals(job_owners.dt, DAY))),
        ([(["job_id"], "job_owners' rows are told apart by job_id, dt, with dt held to one "
           "value", "not by")], None)),
    "rows, the first table's Key left out after a join": (lambda: statement(
        SELECT(job_runs.run_id, job_runs.job_id, AS(jobs.job_id, "any_job")),
        FROM(run_alerts), JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
        CROSS_JOIN(jobs), both_on_the_day()),
        ([], "run_alerts' rows are told apart by alert_id, and SELECT leaves out "
         "run_alerts.alert_id")),
    "rows, a Key twice over two columns that decide each other": (lambda: statement(
        SELECT(loop.run_id, loop.job_id), FROM(loop),
        JOIN(by_run, ON=all_of(equals(by_run.run_id, loop.run_id),
                               equals(by_run.job_id, loop.job_id))),
        JOIN(by_job, ON=all_of(equals(by_job.job_id, loop.job_id),
                               equals(by_job.run_id, loop.run_id)))),
        ([(["job_id"], "loop's rows are told apart by run_id, job_id, run_id", "not by")],
         None)),
}


def _answer(s: Statement) -> tuple[list[tuple[list[str], str, str]], str | None]:
    keys = statement_keys(s)
    return [(found.names, found.why, found.instead) for found in keys.found], keys.lost


@pytest.mark.parametrize("case", CASES)
def test_the_keys_found_are_as_they_were(case: str) -> None:
    make, answer = CASES[case]
    assert _answer(make()) == answer
