"""Each job and day with an owner but no event, as a Derived table to read.

Why: a job that didn't run leaves no row to count, so finding it means looking for what is
missing: each job and day in ops.job_owners with no match in ops.job_events.

This is an anti-join. LEFT_JOIN keeps every job and day of job_owners, with NULL in the joined
columns where the job had no event that day, and the WHERE keeps only those rows. The Toolbox
lets that WHERE through, since is_null(...) on a joined column keeps the rows with no match
rather than dropping them.
"""

from sqlglot_composer import (
    FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, all_of, between, derived, equals, is_null,
    statement,
)
from table_references.job_events import job_events
from table_references.job_owners import job_owners


def jobs_without_events(first_day, last_day):
    """One row per job and day from first_day to last_day on which it had no event.

    It first lists each job's days with an event, one row per job and day, so the join
    matches one row at most: joining job_events itself would match each of the day's events.
    """
    event_days = derived(
        "event_days",
        statement(
            SELECT(job_events.job_id, job_events.dt),
            FROM(job_events),
            WHERE(between(job_events.dt, first_day, last_day)),
            GROUP_BY(job_events.job_id, job_events.dt),
        ),
    )
    return derived(
        "jobs_without_events",
        statement(
            SELECT(job_owners.job_id, job_owners.team, job_owners.owner, job_owners.dt),
            FROM(job_owners),
            LEFT_JOIN(event_days, ON=all_of(equals(event_days.job_id, job_owners.job_id),
                                            equals(event_days.dt, job_owners.dt))),
            WHERE(between(job_owners.dt, first_day, last_day), is_null(event_days.job_id)),
        ),
    )
