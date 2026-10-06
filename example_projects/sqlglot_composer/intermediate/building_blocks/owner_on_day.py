# sqlglot Composer 4.0, exported 2026-10-06 00:26 - copy it, then edit your copy
"""A join to the team each job had on each row's day: an as-of lookup.

Why: a job can move team, as report_build moves from data to finance on 2026-09-18, so a
Statement that counts per team must look each job's team up as of each row's day.

ops.job_owners holds a snapshot of every job's team and owner each day, so a job's team on a
day is in that day's snapshot: the join matches the job and the day. A Building block can be a
join as well as a Derived table: this one returns the LEFT_JOIN(...) to put in a Statement,
after its FROM(...).
"""

from sqlglot_composer import LEFT_JOIN, all_of, between, equals
from table_references.job_owners import job_owners


def owner_on_day(job_id_column, day_column, first_day, last_day):
    """LEFT_JOIN ops.job_owners on the job and the day, so job_owners.team is the team then.

    job_id_column and day_column are the reading Statement's columns, such as events.job_id and
    events.dt; first_day and last_day are the days it reads, written like "2026-09-24". Every read of a table must bound its Date partition at
    both ends, a joined table's too, so they bound job_owners here, in ON=. by_day leaves a
    joined table's bound as written, and the match on the day keeps each row to its own day's
    snapshot.

    It is a LEFT_JOIN, so a row whose day has no snapshot yet keeps its numbers, with a NULL
    team, rather than being dropped. ON= names job_owners' whole key, the job and the day, so
    each row matches one snapshot row at most, and nothing is counted twice.
    """
    return LEFT_JOIN(
        job_owners,
        ON=all_of(equals(job_owners.job_id, job_id_column), equals(job_owners.dt, day_column),
                  between(job_owners.dt, first_day, last_day)),
    )
