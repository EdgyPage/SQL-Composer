"""Spark Composer's Example database runs what sqlglot's executor can't on the intermediate tables.

The newest snapshot per key with row_number, week and month rollups with week_start and
month_start, which the intermediate how-tos show, and rows added up after a LEFT_JOIN to a
column named like one before it, each checked against pandas.
"""

from __future__ import annotations

import pandas as pd
import pytest

from conftest import example_rows
from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    LEFT_JOIN,
    SELECT,
    SELECT_DISTINCT,
    WHERE,
    all_of,
    count_rows,
    derived,
    descending,
    equals,
    example_database,
    is_null,
    last_n_days,
    month_start,
    row_number,
    run,
    statement,
    week_start,
)

events = example_database.job_events
owners = example_database.job_owners


@pytest.mark.needs_example_database
def test_each_jobs_newest_snapshot_with_row_number() -> None:
    numbered = derived("numbered", statement(
        SELECT(owners.job_id, owners.team, owners.dt,
               AS(row_number(PARTITION_BY=owners.job_id, ORDER_BY=descending(owners.dt)),
                  "newest_first")),
        FROM(owners),
        WHERE(last_n_days(owners.dt, 14)),
    ))
    s = statement(SELECT(numbered.job_id, numbered.team), FROM(numbered),
                  WHERE(equals(numbered.newest_first, 1)))
    found = run(s, send=example_database.send).set_index("job_id").team.to_dict()
    rows = example_rows("job_owners")
    newest = rows[rows.dt == rows.dt.max()]
    assert found == newest.set_index("job_id").team.to_dict()


@pytest.mark.needs_example_database
@pytest.mark.parametrize("bucket", [week_start, month_start])
def test_events_per_week_and_per_month(bucket) -> None:
    s = statement(
        SELECT(AS(bucket(events.dt), "starts"), AS(count_rows(), "events")),
        FROM(events),
        WHERE(last_n_days(events.dt, 14)),
        GROUP_BY(bucket(events.dt)),
    )
    found = run(s, send=example_database.send).set_index("starts").events.to_dict()
    days = pd.to_datetime(example_rows("job_events").dt)
    if bucket is week_start:
        starts = days - pd.to_timedelta(days.dt.weekday, unit="D")
    else:
        starts = days.dt.to_period("M").dt.start_time
    assert found == starts.dt.strftime("%Y-%m-%d").value_counts().to_dict()


@pytest.mark.needs_example_database
def test_unfinished_runs_per_job_added_up_after_a_left_join() -> None:
    """sqlglot's executor would give starts.job_id NULL here for each start with no finish,
    so sqlglot Composer refuses it; Spark gets it right."""
    def days_with(event_type: str, name: str):
        return derived(name, statement(
            SELECT_DISTINCT(events.job_id, events.dt),
            FROM(events),
            WHERE(equals(events.event_type, event_type), last_n_days(events.dt, 14)),
        ))

    starts, finishes = days_with("start", "starts"), days_with("finish", "finishes")
    s = statement(
        SELECT(starts.job_id, AS(count_rows(where=is_null(finishes.job_id)), "unfinished")),
        FROM(starts),
        LEFT_JOIN(finishes, ON=all_of(equals(finishes.job_id, starts.job_id),
                                      equals(finishes.dt, starts.dt))),
        GROUP_BY(starts.job_id),
    )
    found = run(s, send=example_database.send).set_index("job_id").unfinished.to_dict()
    rows = example_rows("job_events")[["job_id", "dt", "event_type"]].drop_duplicates()
    started = rows[rows.event_type == "start"][["job_id", "dt"]]
    finished = rows[rows.event_type == "finish"][["job_id", "dt"]].assign(finished=True)
    joined = started.merge(finished, on=["job_id", "dt"], how="left")
    expected = joined.finished.isna().groupby(joined.job_id).sum().to_dict()
    assert found == expected
    assert sorted(found) == [1, 2, 3] and sum(found.values()) == 2
