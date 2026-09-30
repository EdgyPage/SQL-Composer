"""Spark Composer's Example database runs each query on a Spark of its own, in a helper process.

That Spark runs what sqlglot's executor can't, row_number, NEXT_DAY and TRUNC, so the Worked
examples SQL Composer can only show in pandas are run here and checked against their pandas
twins. These also hold that your Python holds no Spark afterwards, what Python type each kind
of column comes back as, and that a stopped helper starts again.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from sql_composer import (
    AS,
    FROM,
    SELECT,
    WHERE,
    engine,
    example_database,
    last_n_days,
    month_start,
    run,
    statement,
    week_start,
)
from sql_composer.example_database import job_runs
from statements import latest_and_top_n, regrouping

pytestmark = pytest.mark.needs_example_database


@pytest.mark.xfail(strict=True, reason="ticket 25 of the PySpark work writes week_start as "
                   "CAST(... AS STRING), so Spark gives the week as text, as pandas does; "
                   "until then NEXT_DAY gives a DATE")
def test_the_regrouping_hive_gives_the_same_numbers_as_pandas() -> None:
    careless = run(regrouping.careless(adds_up=True), send=example_database.send)
    fixed = run(regrouping.fixed(), send=example_database.send)
    assert careless.to_dict("records") == regrouping.careless_in_pandas().to_dict("records")
    assert fixed.to_dict("records") == regrouping.fixed_in_pandas().to_dict("records")


def _rows(frame) -> list[tuple]:
    """A result's rows in one order: a Statement with no ORDER_BY may give them in any."""
    return sorted(frame.itertuples(index=False, name=None))


@pytest.mark.parametrize("name", ["fixed", "top_runs_per_job"])
def test_row_number_runs_and_gives_the_pandas_result(name: str) -> None:
    result = run(getattr(latest_and_top_n, name)(), send=example_database.send)
    in_pandas = getattr(latest_and_top_n, f"{name}_in_pandas")()
    assert list(result.columns) == list(in_pandas.columns)
    assert _rows(result) == _rows(in_pandas)


def test_each_kind_of_column_comes_back_as_the_python_type_pandas_shows() -> None:
    s = statement(
        SELECT(job_runs.run_id, job_runs.status, job_runs.duration_mins,
               job_runs.avg_retry_secs, job_runs.dt, AS(week_start(job_runs.dt), "week"),
               AS(month_start(job_runs.dt), "month")),
        FROM(job_runs),
        WHERE(last_n_days(job_runs.dt, 2)),
    )
    first = run(s, send=example_database.send).iloc[0].to_dict()
    assert {name: type(value) for name, value in first.items()} == {
        "run_id": int, "status": str, "duration_mins": int, "avg_retry_secs": float,
        "dt": str,
        # Until ticket 25's CAST(... AS STRING), NEXT_DAY and TRUNC give a DATE.
        "week": datetime.date, "month": datetime.date,
    }


def test_your_python_holds_no_spark_and_your_folder_gets_no_files() -> None:
    from pyspark import SparkContext

    run(statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(last_n_days(job_runs.dt, 2))),
        send=example_database.send)
    assert SparkContext._active_spark_context is None
    assert [name for name in ("spark-warehouse", "metastore_db", "derby.log")
            if (Path.cwd() / name).exists()] == []


def test_a_stopped_helper_starts_again() -> None:
    s = statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(last_n_days(job_runs.dt, 2)))
    before = run(s, send=example_database.send)
    engine._HELPER["process"].kill()
    engine._HELPER["process"].wait(60)
    assert run(s, send=example_database.send).equals(before)


def test_stopping_the_helper_deletes_its_folder() -> None:
    run(statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(last_n_days(job_runs.dt, 2))),
        send=example_database.send)
    folder = engine._HELPER["folder"]
    engine._stop_helper()
    assert not folder.exists()
