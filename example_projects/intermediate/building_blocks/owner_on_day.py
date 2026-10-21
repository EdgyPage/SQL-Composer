"""owner_on_day - the team that owned each job on each day, joined as of that day.

Why: mart.job_day_facts saves each job's day beside its team then, and mart.team_days'
notebook checks a day the same way, so both look the team up alike.

ops.job_owners holds a snapshot a day: each job's team and owner that day. A job can change
teams, so a row is joined to the snapshot of its own day, not the newest.
"""

from sqlglot_composer import LEFT_JOIN, Clause, Column, all_of, between, equals
from references.ops__job_owners import job_owners


def owner_on_day(job_id_column: Column, day_column: Column, first_day: str,
                 last_day: str) -> Clause:
    """LEFT_JOIN ops.job_owners on the job and the day, so job_owners.team is the team then.

    job_id_column and day_column are the reading Statement's columns, such as events.job_id
    and events.dt; first_day and last_day are the days it reads, written like "2026-09-24".
    Every read of a table must bound its Date partition at both ends, a joined table's too, so
    they bound job_owners here, in ON=. by_day leaves a joined table's bound as written, and
    the match on the day keeps each row to its own day's snapshot.

    It is a LEFT_JOIN, so a row whose day has no snapshot yet keeps its numbers, with a NULL
    team, rather than being dropped. ON= names job_owners' whole key, the job and the day, so
    each row matches one snapshot row at most, and nothing is counted twice.
    """
    return LEFT_JOIN(
        job_owners,
        ON=all_of(equals(job_owners.job_id, job_id_column), equals(job_owners.dt, day_column),
                  between(job_owners.dt, first_day, last_day)),
    )
