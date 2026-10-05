"""Events, runs and minutes per job and day, as a Derived table to read.

Why: example 2 and example 3's team_day_from_job_events both need these numbers, and writing
them once here means the two can never work them out two different ways.

A run's events are its start, any retries, then its finish or a fail, each with the minutes
since the run started. So the minutes on the event that ends a run are how long the run took.
A run still going at the end of the day has a start and no end yet: it counts as a run, with 0
minutes, until its end event comes in. An event lands in the partition of the day it
happened, so a run that ends on a later day counts its minutes on that later day.
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows, derived, equals, fill_null, is_in,
    statement, sum_of,
)
from table_references.job_events import job_events


def events_per_job_day(first_day, last_day):
    """One row per job and day from first_day to last_day: its events, runs and minutes.

    The Date partition, dt, is kept in GROUP_BY, so each day's numbers stay apart when
    first_day and last_day are days apart, and in SELECT, so a Statement that reads this can
    join each row to another table on its day, and by_day can cut it into one write per day.
    """
    ends_a_run = is_in(job_events.event_type, ["finish", "fail"])
    return derived(
        "events_per_job_day",
        statement(
            SELECT(
                job_events.job_id,
                job_events.dt,
                AS(count_rows(), "events"),
                AS(count_rows(where=equals(job_events.event_type, "start")), "runs"),
                AS(fill_null(sum_of(job_events.minutes, where=ends_a_run), 0), "minutes"),
            ),
            FROM(job_events),
            WHERE(between(job_events.dt, first_day, last_day)),
            GROUP_BY(job_events.job_id, job_events.dt),
        ),
    )
