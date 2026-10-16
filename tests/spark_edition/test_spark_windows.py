"""Spark Composer's Example database runs windows, which sqlglot's executor can't.

Each window function's Hive, run on Spark, against the same worked out in pandas from the rows
of the Example database: a running total, a moving average, a group's total beside each row,
rank, dense_rank, ntile, lag, lead, first_value and last_value; and the Hive of a write that
reads earlier days and keeps the one it writes, read on Spark.
"""

from __future__ import annotations

import pandas as pd
import pytest

from conftest import example_rows
from sqlglot_composer import (
    AS,
    FROM,
    SELECT,
    WHERE,
    average_of,
    between,
    count_rows,
    dense_rank,
    derived,
    descending,
    equals,
    example_database,
    first_value,
    lag,
    last_value,
    lead,
    ntile,
    rank,
    row_number,
    run,
    statement,
    sum_of,
    window,
)

events = example_database.job_events
FIRST, LAST = "2026-09-18", "2026-09-24"


def finished() -> pd.DataFrame:
    """The finished runs of the week, in each job's order of days, from the Example rows."""
    rows = example_rows("job_events")
    rows = rows[(rows.event_type == "finish") & rows.dt.between(FIRST, LAST)]
    return rows.sort_values(["job_id", "dt"]).reset_index(drop=True)


@pytest.mark.needs_example_database
def test_each_window_function_gives_what_pandas_gives() -> None:
    by_day = window(PARTITION_BY=events.job_id, ORDER_BY=events.dt)
    s = statement(
        SELECT(events.event_id,
               AS(sum_of(events.minutes, over=window(PARTITION_BY=events.job_id,
                                                     ORDER_BY=events.dt, rows=(None, 0))),
                  "so_far"),
               AS(average_of(events.minutes, over=window(
                   PARTITION_BY=events.job_id, ORDER_BY=events.dt, rows=(-1, 0))), "mean_2"),
               AS(sum_of(events.minutes, over=window(PARTITION_BY=events.job_id)), "total"),
               AS(count_rows(over=window()), "rows"),
               AS(rank(over=window(PARTITION_BY=events.job_id,
                                   ORDER_BY=descending(events.minutes))), "rk"),
               AS(dense_rank(over=window(PARTITION_BY=events.job_id,
                                         ORDER_BY=descending(events.minutes))), "drk"),
               AS(ntile(2, over=by_day), "half"),
               AS(row_number(over=by_day), "rn"),
               AS(lag(events.minutes, over=by_day), "before"),
               AS(lead(events.minutes, over=by_day, ahead=2), "two_after"),
               AS(first_value(events.minutes, over=by_day), "first"),
               AS(last_value(events.minutes, over=by_day), "last")),
        FROM(events),
        WHERE(between(events.dt, FIRST, LAST), equals(events.event_type, "finish")),
    )
    got = run(s, send=example_database.send).set_index("event_id").sort_index()
    rows = finished()
    jobs = rows.groupby("job_id")["minutes"]
    place, sizes = rows.groupby("job_id").cumcount(), jobs.transform("size")
    want = pd.DataFrame({
        "event_id": rows.event_id,
        "so_far": jobs.cumsum(),
        "mean_2": jobs.transform(lambda m: m.rolling(2, min_periods=1).mean()),
        "total": jobs.transform("sum"),
        "rows": len(rows),
        "rk": jobs.rank(method="min", ascending=False),
        "drk": jobs.rank(method="dense", ascending=False),
        # NTILE(2): the first half of each job's runs, one more when they don't split evenly.
        "half": (place >= (sizes + 1) // 2).astype(int) + 1,
        "rn": place + 1,
        "before": jobs.shift(1),
        "two_after": jobs.shift(-2),
        "first": jobs.transform("first"),
        "last": jobs.transform("last"),
    }).set_index("event_id").sort_index()
    for column in want.columns:
        assert got[column].astype(float).fillna(-1).tolist() == pytest.approx(
            want[column].astype(float).fillna(-1).tolist()), column


@pytest.mark.needs_example_database
def test_a_lag_kept_in_the_statement_that_reads_it() -> None:
    with_before = derived("with_before", statement(
        SELECT(events.event_id, events.dt,
               AS(lag(events.minutes, over=window(PARTITION_BY=events.job_id,
                                                  ORDER_BY=events.dt)), "before")),
        FROM(events),
        WHERE(between(events.dt, FIRST, LAST), equals(events.event_type, "finish"))))
    s = statement(SELECT(with_before.event_id, with_before.before), FROM(with_before),
                  WHERE(equals(with_before.dt, LAST)))
    got = run(s, send=example_database.send)
    rows = finished()
    rows["before"] = rows.groupby("job_id")["minutes"].shift(1)
    want = rows[rows.dt == LAST]
    assert dict(zip(got.event_id, got.before)) == dict(zip(want.event_id, want.before))
