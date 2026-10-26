"""Keep a long list and a lookup as constants, and an if/else chain as one CASE.

Why: a list or a lookup pasted into each Statement, as hand-written Hive often has them, must
be found and changed in every one, where a constant at the top of the script, named for what
it holds, is changed once.
"""

from sqlglot_composer import (
    AS, FROM, SELECT, WHERE, Statement, between, example_database, first_match, is_in, mapped,
    more_than, statement,
)

job_runs = example_database.job_runs

FIRST_DAY = "2026-09-23"
LAST_DAY = "2026-09-24"

# The jobs this report watches, by job_id. However long the list grows, it is written once.
WATCHED_JOBS = [1, 2]
# A label for each status a run can have.
STATUS_LABELS = {"SUCCESS": "passed", "FAILED": "failed", "TEST": "test run"}


def runs_of_watched_jobs() -> Statement:
    """Runs of the watched jobs: is_in takes the list kept in WATCHED_JOBS (IN a list)."""
    return statement(
        SELECT(job_runs.run_id, job_runs.job_id),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY), is_in(job_runs.job_id, WATCHED_JOBS)),
    )


def labelled_runs() -> Statement:
    """Each watched run's status as a label, and its length in words (CASE ... WHEN ...).

    mapped looks each status up in STATUS_LABELS. A run still going has no status (NULL),
    which matches no key, so it gets otherwise=, as any status the dict doesn't hold would; to
    give NULL a label of its own, mapped's docstring fills it in first, with fill_null.
    first_match tries its conditions in order and
    gives the value of the first that holds: a run of 40 minutes is "long", though it is more
    than 10 minutes too.

    Before, as Hive written by hand, the lookup and the chain read as below, with the list
    pasted in where WATCHED_JOBS goes; project.convert(...) writes them as this function does:

        CASE status WHEN 'SUCCESS' THEN 'passed' WHEN 'FAILED' THEN 'failed'
                    WHEN 'TEST' THEN 'test run' ELSE 'still running' END AS outcome,
        CASE WHEN duration_mins > 30 THEN 'long' WHEN duration_mins > 10 THEN 'medium'
             ELSE 'short' END AS length
        ... WHERE job_id IN (1, 2)
    """
    return statement(
        SELECT(
            job_runs.run_id,
            AS(mapped(job_runs.status, STATUS_LABELS, otherwise="still running"), "outcome"),
            AS(first_match([(more_than(job_runs.duration_mins, 30), "long"),
                            (more_than(job_runs.duration_mins, 10), "medium")],
                           otherwise="short"), "length"),
        ),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY), is_in(job_runs.job_id, WATCHED_JOBS)),
    )
