"""Spark Composer's Example database runs each query on a Spark of its own, in its own process.

That Spark runs what sqlglot's executor can't, row_number, NEXT_DAY and TRUNC, so the Worked
examples SQL Composer can only show in pandas are run here and checked against their pandas
twins. These also hold what Python type each kind of column comes back as, what the Example
database says when there is no Java or Spark refuses a query, that your Python holds no Spark
afterwards, and that a stopped Spark starts again and leaves no folder behind, even when its
Python was killed.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
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

ROOT = Path(__file__).resolve().parents[2]
runs_a_query = pytest.mark.needs_example_database


def _both_days(*outputs):
    return statement(SELECT(*outputs), FROM(job_runs), WHERE(last_n_days(job_runs.dt, 2)))


def _rows(frame) -> list[tuple]:
    """A result's rows in one order: a Statement with no ORDER_BY may give them in any."""
    return sorted(frame.itertuples(index=False, name=None))


# --- What sqlglot's executor can't run --------------------------------------------------------


@runs_a_query
@pytest.mark.xfail(strict=True, reason="ticket 25 of the PySpark work writes week_start as "
                   "CAST(... AS STRING), so Spark gives the week as text, as pandas does; "
                   "until then NEXT_DAY gives a DATE")
def test_the_regrouping_hive_gives_the_same_numbers_as_pandas() -> None:
    careless = run(regrouping.careless(adds_up=True), send=example_database.send)
    fixed = run(regrouping.fixed(), send=example_database.send)
    assert careless.to_dict("records") == regrouping.careless_in_pandas().to_dict("records")
    assert fixed.to_dict("records") == regrouping.fixed_in_pandas().to_dict("records")


@runs_a_query
@pytest.mark.parametrize("name", ["fixed", "top_runs_per_job"])
def test_row_number_runs_and_gives_the_pandas_result(name: str) -> None:
    result = run(getattr(latest_and_top_n, name)(), send=example_database.send)
    in_pandas = getattr(latest_and_top_n, f"{name}_in_pandas")()
    assert list(result.columns) == list(in_pandas.columns)
    assert _rows(result) == _rows(in_pandas)


@runs_a_query
def test_week_start_and_month_start_give_the_days_pandas_gives() -> None:
    s = _both_days(job_runs.dt, AS(week_start(job_runs.dt), "week"),
                   AS(month_start(job_runs.dt), "month"))
    result = run(s, send=example_database.send)
    days = pd.to_datetime(result.dt)
    monday = days - pd.to_timedelta(days.dt.weekday, unit="D")
    assert list(result.week.astype(str)) == list(monday.dt.strftime("%Y-%m-%d"))
    assert list(result.month.astype(str)) == list(days.dt.strftime("%Y-%m-01"))


# --- What comes back --------------------------------------------------------------------------


@runs_a_query
def test_each_kind_of_column_comes_back_as_the_python_type_pandas_shows() -> None:
    s = _both_days(job_runs.run_id, job_runs.status, job_runs.duration_mins,
                   job_runs.avg_retry_secs, job_runs.dt)
    first = run(s, send=example_database.send).iloc[0].to_dict()
    assert {name: type(value) for name, value in first.items()} == {
        "run_id": int, "status": str, "duration_mins": int, "avg_retry_secs": float,
        "dt": str,
    }


@runs_a_query
@pytest.mark.xfail(strict=True, reason="ticket 25 of the PySpark work writes week_start and "
                   "month_start as CAST(... AS STRING); until then NEXT_DAY and TRUNC give a "
                   "date, as their docstrings say")
def test_week_start_and_month_start_come_back_as_text() -> None:
    s = _both_days(AS(week_start(job_runs.dt), "week"), AS(month_start(job_runs.dt), "month"))
    first = run(s, send=example_database.send).iloc[0].to_dict()
    assert {name: type(value) for name, value in first.items()} == {"week": str, "month": str}


# --- What the Example database says ------------------------------------------------------------


def test_a_java_home_that_holds_no_java_is_named(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JAVA_HOME", str(tmp_path))
    assert f"JAVA_HOME is {tmp_path}, which holds no bin" in engine.example_database_cannot_run()
    with pytest.raises(RuntimeError) as refused:
        example_database.send("SELECT job_id FROM ops.jobs")
    message = str(refused.value)
    assert "The Example database can't run a query here: " in message
    assert "set JAVA_HOME to its folder" in message


@runs_a_query
def test_a_query_spark_refuses_shows_the_first_line_of_what_spark_said() -> None:
    with pytest.raises(RuntimeError) as refused:
        example_database.send("SELECT nope FROM ops.jobs")
    message = str(refused.value)
    assert "Spark couldn't run this Hive on the Example database: [UNRESOLVED_COLUMN" in message
    assert "Project" not in message, "Spark's plan of the query was shown"


# --- Its own process -------------------------------------------------------------------------


@runs_a_query
def test_your_python_holds_no_spark_and_your_folder_gets_no_files() -> None:
    from pyspark import SparkContext

    run(_both_days(job_runs.run_id), send=example_database.send)
    assert SparkContext._active_spark_context is None
    assert [name for name in ("spark-warehouse", "metastore_db", "derby.log")
            if (Path.cwd() / name).exists()] == []


@runs_a_query
def test_a_stopped_spark_starts_again() -> None:
    s = _both_days(job_runs.run_id)
    before = run(s, send=example_database.send)
    engine._SPARK["process"].kill()
    engine._SPARK["process"].wait(60)
    assert run(s, send=example_database.send).equals(before)


@runs_a_query
def test_stopping_its_spark_deletes_its_folder() -> None:
    run(_both_days(job_runs.run_id), send=example_database.send)
    folder = engine._SPARK["folder"]
    engine._stop_spark()
    assert not folder.exists()


# A Python that starts the Example database's Spark, says where its folder is, and waits.
_KILLED = """
import sys
sys.path[:0] = [{root!r}, {tools!r}]
import editions
editions.use(editions.SPARK_COMPOSER)
from sql_composer import engine, example_database
example_database.send("SELECT job_id FROM ops.jobs")
print("FOLDER", engine._SPARK["folder"], flush=True)
sys.stdin.read()
"""


@runs_a_query
def test_the_folder_of_a_killed_python_is_deleted_at_the_next_start() -> None:
    script = _KILLED.format(root=str(ROOT), tools=str(ROOT / "tools"))
    folder = None
    with subprocess.Popen([sys.executable, "-c", script], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, text=True) as child:
        try:
            for line in child.stdout:
                if line.startswith("FOLDER "):
                    folder = Path(line.removeprefix("FOLDER ").strip())
                    break
        finally:
            child.kill()
    assert folder is not None, "the killed Python's Example database didn't start"
    assert folder.exists(), "killed, it had no chance to delete its folder"
    # Only a folder over a minute old is taken as left over; this one is made to look it.
    old = time.time() - 120
    os.utime(folder / "in-use", (old, old))
    for _ in range(60):  # its Spark stops within seconds of its Python
        engine._delete_left_over()
        if not folder.exists():
            break
        time.sleep(0.5)
    assert not folder.exists()
