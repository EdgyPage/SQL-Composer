"""As-of lookups: rows counted by what was true on their day, and newest snapshots.

Why: a snapshot table holds what each key was on each day, such as each job's team, so a row
counts for what was true on its own day only if it is matched to that day's snapshot.

Copy it to: statements/<LOOKED_UP_COLUMN>_as_of_day.py

rows_as_of_their_day(first_day, last_day) joins each row of <TABLE> to the snapshot row with
the same key on the same day, then counts each day's rows per looked-up value. It is a
LEFT_JOIN, so a row whose day has no snapshot yet keeps its count, under a NULL value. The
snapshot's days are bounded in ON=, not in WHERE: a WHERE on the LEFT_JOIN's table would drop
the very rows LEFT_JOIN keeps.

newest_per_key(day) answers a different question: what is each key now? It takes each key's
newest snapshot in the SNAPSHOT_DAYS days up to the day, so a key is still found when the
day's snapshot hasn't come in yet. It numbers each key's snapshots with row_number, newest
first, then keeps number 1. row_number is a window function. If your Example database stops
on it with a message saying its executor has no window functions, run
newest_per_key_by_newest_day(day) there instead: it gives the same rows without one. Your
warehouse runs both.

Mirrors example_projects/intermediate/statements/example_2_owner_as_of.py and its Building
block, example_projects/intermediate/building_blocks/owner_on_day.py.

Replace each placeholder, brackets and all, wherever it is written in the code, then delete
this Fill in: block:

Fill in:
    <TABLE>: the Table reference of the rows to look up for, which is also its file's name in
        table_references/, such as job_events.
    <MATCH_COLUMN>: its column holding the key to look up, such as job_id.
    <DATE_PARTITION>: its Date partition, such as dt.
    <SNAPSHOT>: the snapshot's Table reference, one row per key per day, which is also its
        file's name in table_references/, such as job_owners. Its key is the key column and
        its Date partition, such as key=["job_id", "dt"]: each join names both.
    <SNAPSHOT_MATCH_COLUMN>: the snapshot's column holding the same key, such as job_id.
    <SNAPSHOT_DATE_PARTITION>: the snapshot's Date partition, such as dt.
    <LOOKED_UP_COLUMN>: the snapshot's column to look up, such as team.
    <SNAPSHOT_DAYS>: how many days, up to the day, newest_per_key looks back for a snapshot:
        a number, without quotes, such as 7.
"""

import datetime

from sqlglot_composer import (
    AS, FROM, GROUP_BY, JOIN, LEFT_JOIN, SELECT, WHERE, all_of, between, count_rows, derived,
    descending, equals, max_of, row_number, statement,
)
from table_references.<SNAPSHOT> import <SNAPSHOT>  # the snapshot's Table reference
from table_references.<TABLE> import <TABLE>  # the Table reference of the rows looked up for

SNAPSHOT_DAYS = <SNAPSHOT_DAYS>  # newest_per_key looks this many days back, the day included


def days_before(day, days):
    """The day `days` days before `day`, written the same way: days_before("2026-09-24", 6)
    is "2026-09-18"."""
    return (datetime.date.fromisoformat(day) - datetime.timedelta(days=days)).isoformat()


def rows_as_of_their_day(first_day, last_day):
    """Each day's rows from first_day to last_day, per value looked up as of that day."""
    return statement(
        SELECT(<TABLE>.<DATE_PARTITION>, <SNAPSHOT>.<LOOKED_UP_COLUMN>,
               AS(count_rows(), "row_count")),
        FROM(<TABLE>),
        LEFT_JOIN(<SNAPSHOT>, ON=all_of(  # all_of: every condition in it must hold
            equals(<SNAPSHOT>.<SNAPSHOT_MATCH_COLUMN>, <TABLE>.<MATCH_COLUMN>),  # the same key
            equals(<SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>, <TABLE>.<DATE_PARTITION>),  # same day
            between(<SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>, first_day, last_day),  # its days
        )),
        WHERE(between(<TABLE>.<DATE_PARTITION>, first_day, last_day)),
        GROUP_BY(<TABLE>.<DATE_PARTITION>, <SNAPSHOT>.<LOOKED_UP_COLUMN>),
    )


def newest_per_key(day):
    """Each key's newest snapshot in the SNAPSHOT_DAYS days up to the day.

    Hive can't keep only row number 1 in the SELECT that numbers the rows, so the numbering is
    a Derived table, and the Statement that reads it keeps the rows numbered 1.
    """
    numbered = derived(
        "numbered",
        statement(
            SELECT(<SNAPSHOT>.<SNAPSHOT_MATCH_COLUMN>, <SNAPSHOT>.<LOOKED_UP_COLUMN>,
                   <SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>,
                   AS(row_number(PARTITION_BY=<SNAPSHOT>.<SNAPSHOT_MATCH_COLUMN>,
                                 ORDER_BY=descending(<SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>)),
                      "newest_first")),  # 1 for each key's newest day
            FROM(<SNAPSHOT>),
            WHERE(between(<SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>,
                          days_before(day, SNAPSHOT_DAYS - 1), day)),
        ),
    )
    return statement(
        SELECT(numbered.<SNAPSHOT_MATCH_COLUMN>, numbered.<LOOKED_UP_COLUMN>,
               numbered.<SNAPSHOT_DATE_PARTITION>),
        FROM(numbered),
        WHERE(equals(numbered.newest_first, 1)),
    )


def newest_per_key_by_newest_day(day):
    """The rows newest_per_key gives, worked out without row_number, so every Example database
    runs it.

    It finds each key's newest day with a snapshot, one row per key, then joins that day's
    snapshot back on. ON= names the snapshot's key, the key column and its day, so each key
    matches one snapshot row.
    """
    first_day = days_before(day, SNAPSHOT_DAYS - 1)
    newest = derived(
        "newest",
        statement(
            SELECT(<SNAPSHOT>.<SNAPSHOT_MATCH_COLUMN>,
                   AS(max_of(<SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>), "newest_day")),
            FROM(<SNAPSHOT>),
            WHERE(between(<SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>, first_day, day)),
            GROUP_BY(<SNAPSHOT>.<SNAPSHOT_MATCH_COLUMN>),
        ),
    )
    return statement(
        SELECT(newest.<SNAPSHOT_MATCH_COLUMN>, <SNAPSHOT>.<LOOKED_UP_COLUMN>,
               <SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>),
        FROM(newest),
        JOIN(<SNAPSHOT>, ON=all_of(
            equals(<SNAPSHOT>.<SNAPSHOT_MATCH_COLUMN>, newest.<SNAPSHOT_MATCH_COLUMN>),
            equals(<SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>, newest.newest_day),  # its newest day
            between(<SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>, first_day, day),  # the days read
        )),
    )
