"""The Style B prototype's Statements, rewritten against the real Toolbox.

"Build the Toolbox core" is done when the Statements of `prototype/statement-styles`
(`b_clause_functions/`) can be written with the real Toolbox. They are rewritten here on the
Example database, with its Building blocks as plain functions, and the Hive they emit is
checked in full. `pitfall.py` now stops at SELECT instead of reaching pandas as `_c1`.
"""

from __future__ import annotations

import pytest

from sql_composer import (
    AS,
    FROM,
    GROUP_BY,
    JOIN,
    SELECT,
    WHERE,
    GuardRefused,
    count_rows,
    derived,
    descending,
    equals,
    last_n_days,
    not_equals,
    row_number,
    statement,
    to_hive,
    week_start,
)
from sql_composer.example_database import job_runs as runs
from sql_composer.example_database import jobs

# --- Level 1: the Building blocks (blocks.py) ------------------------------------------------


def failed_runs():
    """Filter: only runs that ended in failure."""
    return equals(runs.status, "FAILED")


def active_jobs():
    """Filter: jobs outside the web team (the prototype's is_active and sandbox filter)."""
    return [not_equals(jobs.team, "web"), not_equals(jobs.region, "NYC")]


def run_to_job():
    """Join: how a run finds its job."""
    return equals(runs.job_id, jobs.job_id)


def latest_run_per_job(days):
    """Sub-query: each job's most recent run in the last `days` days."""
    ranked = derived("ranked", statement(
        SELECT(runs.job_id, runs.status, runs.run_id,
               AS(row_number(PARTITION_BY=runs.job_id, ORDER_BY=descending(runs.run_id)),
                  "rn")),
        FROM(runs),
        WHERE(last_n_days(runs.dt, days)),
    ))
    return derived("latest", statement(
        SELECT(ranked.job_id, ranked.status, ranked.run_id),
        FROM(ranked),
        WHERE(equals(ranked.rn, 1)),
    ))


# --- Level 2: the Statements -----------------------------------------------------------------


def test_failed_by_week() -> None:
    week = week_start(runs.dt)
    failed_by_week = statement(
        SELECT(AS(week, "week"), jobs.region, AS(count_rows(), "failed_runs")),
        FROM(runs),
        JOIN(jobs, ON=run_to_job()),
        WHERE(failed_runs(), last_n_days(runs.dt, 30)),
        GROUP_BY("week", jobs.region),
    )
    assert to_hive(failed_by_week) == """\
SELECT
  NEXT_DAY(DATE_ADD(job_runs.dt, 7 * -1), 'MO') AS week,
  jobs.region,
  COUNT(*) AS failed_runs
FROM ops.job_runs AS job_runs
JOIN ops.jobs AS jobs
  ON job_runs.job_id = jobs.job_id
WHERE
  job_runs.status = 'FAILED' AND job_runs.dt BETWEEN '2026-08-26' AND '2026-09-24'
GROUP BY
  NEXT_DAY(DATE_ADD(job_runs.dt, 7 * -1), 'MO'),
  jobs.region"""


def test_failures_by_team() -> None:
    failures_by_team = statement(
        SELECT(jobs.team, AS(count_rows(), "failed_runs")),
        FROM(runs),
        JOIN(jobs, ON=run_to_job()),
        WHERE(failed_runs(), active_jobs(), last_n_days(runs.dt, 7)),
        GROUP_BY(jobs.team),
    )
    assert to_hive(failures_by_team) == """\
SELECT
  jobs.team,
  COUNT(*) AS failed_runs
FROM ops.job_runs AS job_runs
JOIN ops.jobs AS jobs
  ON job_runs.job_id = jobs.job_id
WHERE
  job_runs.status = 'FAILED'
  AND jobs.team <> 'web'
  AND jobs.region <> 'NYC'
  AND job_runs.dt BETWEEN '2026-09-18' AND '2026-09-24'
GROUP BY
  jobs.team"""


def test_currently_failing() -> None:
    latest = latest_run_per_job(days=7)
    currently_failing = statement(
        SELECT(latest.job_id, jobs.job_name, latest.run_id),
        FROM(latest),
        JOIN(jobs, ON=equals(latest.job_id, jobs.job_id)),
        WHERE(equals(latest.status, "FAILED")),
    )
    assert to_hive(currently_failing) == """\
WITH ranked AS (
  SELECT
    job_runs.job_id,
    job_runs.status,
    job_runs.run_id,
    ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id DESC) AS rn
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-18' AND '2026-09-24'
), latest AS (
  SELECT
    ranked.job_id,
    ranked.status,
    ranked.run_id
  FROM ranked
  WHERE
    ranked.rn = 1
)
SELECT
  latest.job_id,
  jobs.job_name,
  latest.run_id
FROM latest
JOIN ops.jobs AS jobs
  ON latest.job_id = jobs.job_id
WHERE
  latest.status = 'FAILED'"""


def test_the_pitfall_now_stops_at_select() -> None:
    with pytest.raises(GuardRefused, match="no name: COUNT"):
        statement(
            SELECT(jobs.region, count_rows()),
            FROM(runs),
            JOIN(jobs, ON=run_to_job()),
            WHERE(failed_runs(), last_n_days(runs.dt, 7)),
            GROUP_BY(jobs.region),
        )
