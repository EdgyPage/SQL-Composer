"""Spark Composer's Example database runs what sqlglot's executor can't on the intermediate tables.

The newest snapshot per key with row_number, and week and month rollups with week_start and
month_start, which the intermediate how-tos show, each checked against pandas.
"""

from __future__ import annotations

import pandas as pd
import pytest

from conftest import example_rows
from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    SELECT,
    WHERE,
    count_rows,
    derived,
    descending,
    equals,
    example_database,
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
