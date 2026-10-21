"""events_per_job_day - one row per job and day: its events, runs and minutes.

Why: mart.job_day_facts saves these numbers, and mart.team_days' notebook checks a day from
them too, and writing them once here means the two always count them the same way.

A run's minutes are the minutes since it started, on the event that ends it: finish or fail,
which ops.job_events' Alias ends_a_run names. A day with no run ending has 0 minutes, not
NULL.
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, Table, between, count_rows, derived, equals,
    fill_null, statement, sum_of,
)
from references.ops__job_events import ends_a_run, job_events  # ends_a_run: an Alias


def events_per_job_day(first_day: str, last_day: str) -> Table:
    """One row per job and day from first_day to last_day: its events, runs and minutes.

    The Date partition, dt, is kept in GROUP_BY, so each day's numbers stay apart when
    first_day and last_day are days apart, and in SELECT, so a Statement that reads this can
    join each row to another table on its day, and by_day can cut it into one write per day.
    """
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
