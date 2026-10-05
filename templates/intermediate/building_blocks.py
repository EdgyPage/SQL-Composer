"""Several Building blocks in one file, one of them built from the other two.

Why: blocks about the same table belong together, and a block built from other blocks takes
them as arguments, since a Building block file may import Table references but no other
Building block file.

Copy it to: building_blocks/<TABLE>.py

keys_seen and keys_expected each read one table over the days given: each key and day it has
a row for. keys_missing is built from the two: each key and day that keys_expected lists and
keys_seen doesn't, which SQL calls an anti-join. LEFT_JOIN keeps every expected row, giving
one with no match NULL in the seen columns, and is_null keeps just those. keys_missing takes
the two blocks as arguments rather than building them, so a Statement builds each block once
and hands it to every piece that reads it:

    expected = keys_expected("2026-09-22", "2026-09-24")
    seen = keys_seen("2026-09-22", "2026-09-24")
    missing = keys_missing(expected, seen)
    run(statement(SELECT(all_columns(missing)), FROM(missing)), send=send)

The days live inside the blocks, so keys_missing's ON= needs only the match. Each block keeps
its name whatever the days, so every day's Hive and lineage read alike.

Mirrors example_projects/intermediate/building_blocks/jobs_without_events.py, written as
blocks built from blocks, as how-to 24 does.

Replace each placeholder, brackets and all, wherever it is written:

Fill in:
    <TABLE>: the Table reference of the rows seen, which is also its file's name in
        table_references/, such as job_events.
    <MATCH_COLUMN>: its column holding the key, such as job_id.
    <DATE_PARTITION>: its Date partition, such as dt.
    <EXPECTED_TABLE>: the Table reference listing each key and day that should have rows,
        which is also its file's name in table_references/, such as job_owners.
    <EXPECTED_MATCH_COLUMN>: its column holding the same key, such as job_id.
    <EXPECTED_DATE_PARTITION>: its Date partition, such as dt.
"""

from sqlglot_composer import (
    FROM, LEFT_JOIN, SELECT, SELECT_DISTINCT, WHERE, all_of, between, derived, equals, is_null,
    statement,
)
from table_references.<EXPECTED_TABLE> import <EXPECTED_TABLE>
from table_references.<TABLE> import <TABLE>


def keys_seen(first_day, last_day):
    """Each key and day from first_day to last_day that the table has a row for, once each."""
    return derived("keys_seen", statement(
        SELECT_DISTINCT(<TABLE>.<MATCH_COLUMN>, <TABLE>.<DATE_PARTITION>),  # each pair once
        FROM(<TABLE>),
        WHERE(between(<TABLE>.<DATE_PARTITION>, first_day, last_day)),
    ))


def keys_expected(first_day, last_day):
    """Each key and day from first_day to last_day that should have rows, once each."""
    return derived("keys_expected", statement(
        SELECT_DISTINCT(<EXPECTED_TABLE>.<EXPECTED_MATCH_COLUMN>,
                        <EXPECTED_TABLE>.<EXPECTED_DATE_PARTITION>),
        FROM(<EXPECTED_TABLE>),
        WHERE(between(<EXPECTED_TABLE>.<EXPECTED_DATE_PARTITION>, first_day, last_day)),
    ))


def keys_missing(expected, seen):
    """Each key and day in `expected`, a keys_expected(...), with no row in `seen`, a
    keys_seen(...) over the same days."""
    return derived("keys_missing", statement(
        SELECT(expected.<EXPECTED_MATCH_COLUMN>, expected.<EXPECTED_DATE_PARTITION>),
        FROM(expected),
        LEFT_JOIN(seen, ON=all_of(
            equals(seen.<MATCH_COLUMN>, expected.<EXPECTED_MATCH_COLUMN>),  # the same key
            equals(seen.<DATE_PARTITION>, expected.<EXPECTED_DATE_PARTITION>),  # the same day
        )),
        WHERE(is_null(seen.<MATCH_COLUMN>)),  # no row seen: LEFT_JOIN left it NULL
    ))
