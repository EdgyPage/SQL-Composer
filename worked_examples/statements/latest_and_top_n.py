"""Latest run per job, and top N per group, with row_number.

Why: to keep whole rows, since max_of on each column can take the status from a different
run than the newest one.
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, all_columns, at_most, between, derived, descending,
    equals, example_database, max_of, row_number, run, statement,
)

job_runs = example_database.job_runs

FIRST_DAY = "2026-09-23"
LAST_DAY = "2026-09-24"


def careless():
    """What most people write first: it runs, and job 2's newest run shows SUCCESS.

    Run 102 is job 2's newest, and it FAILED. max_of(job_runs.status) is the largest status
    in alphabetical order, SUCCESS, from another run. Job 1 shows TEST the same way.
    """
    return statement(
        SELECT(job_runs.job_id, AS(max_of(job_runs.run_id), "run_id"),
               AS(max_of(job_runs.status), "status")),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY)),
        GROUP_BY(job_runs.job_id),
    )


def fixed():
    """Number each job's runs from the newest, then keep number 1: one whole run per job."""
    numbered = derived("numbered", statement(
        SELECT(job_runs.job_id, job_runs.run_id, job_runs.status,
               AS(row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id)),
                  "newest_first")),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY)),
    ))
    return statement(
        SELECT(numbered.job_id, numbered.run_id, numbered.status),
        FROM(numbered),
        WHERE(equals(numbered.newest_first, 1)),
    )


def top_runs_per_job(n=2):
    """The n longest runs of each job: number them from the longest, keep numbers 1 to n."""
    numbered = derived("numbered", statement(
        SELECT(job_runs.job_id, job_runs.run_id, job_runs.duration_mins,
               AS(row_number(PARTITION_BY=job_runs.job_id,
                             ORDER_BY=descending(job_runs.duration_mins)),
                  "longest_first")),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY)),
    ))
    return statement(
        SELECT(numbered.job_id, numbered.run_id, numbered.duration_mins),
        FROM(numbered),
        WHERE(at_most(numbered.longest_first, n)),
    )


def every_run():
    """Every run on both days, read with a Statement the Example database can run."""
    return run(
        statement(SELECT(all_columns(job_runs)), FROM(job_runs),
                  WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY))),
        send=example_database.send,
    )


def fixed_in_pandas():
    """fixed()'s result, computed in pandas, not by running this Hive."""
    newest_first = every_run().sort_values("run_id", ascending=False)
    latest = newest_first.groupby("job_id").head(1)
    return latest[["job_id", "run_id", "status"]].sort_values("job_id").reset_index(drop=True)


def top_runs_per_job_in_pandas(n=2):
    """top_runs_per_job(n)'s result, computed in pandas, not by running this Hive.

    Its rows are in the Example database's order for a Statement with no ORDER_BY: by the first
    column, then the second, and so on.
    """
    longest_first = every_run().sort_values("duration_mins", ascending=False, kind="stable")
    top = longest_first.groupby("job_id").head(n)
    top = top[["job_id", "run_id", "duration_mins"]]
    return top.sort_values(["job_id", "run_id", "duration_mins"]).reset_index(drop=True)
