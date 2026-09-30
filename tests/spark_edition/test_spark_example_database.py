"""Spark Composer's Example database runs each query on a Spark of its own, in its own process.

That Spark runs what sqlglot's executor can't, row_number, NEXT_DAY and TRUNC, so the Worked
examples SQL Composer can only show in pandas are run here and checked against their pandas
twins. These also hold what Python type each kind of column comes back as, what the Example
database says when Java or Spark is missing or Spark refuses a query, that your Python holds no
Spark afterwards, and that its Spark stops cleanly however it is stopped: told to, killed,
interrupted mid-query, or left behind by a killed Python.
"""

from __future__ import annotations

import _thread
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pandas as pd
import pytest

from sql_composer import (
    AS,
    FROM,
    SELECT,
    WHERE,
    between,
    engine,
    example_database,
    month_start,
    run,
    statement,
    week_start,
)
from sql_composer.example_database import job_runs
from statements import latest_and_top_n, regrouping

ROOT = Path(__file__).resolve().parents[2]


def _both_days(*outputs):
    """A Statement of some columns on both of the Example database's days."""
    return statement(SELECT(*outputs), FROM(job_runs),
                     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")))


def _rows(frame) -> list[tuple]:
    """A result's rows in one order: a Statement with no ORDER_BY may give them in any."""
    return sorted(frame.itertuples(index=False, name=None))


# --- What sqlglot's executor can't run --------------------------------------------------------


@pytest.mark.needs_example_database
@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="ticket 25 of the PySpark work writes week_start as CAST(... AS "
                   "STRING), so Spark gives the week as text, as pandas does; until then "
                   "NEXT_DAY gives a DATE")
def test_the_regrouping_hive_gives_the_same_numbers_as_pandas() -> None:
    careless = run(regrouping.careless(adds_up=True), send=example_database.send)
    fixed = run(regrouping.fixed(), send=example_database.send)
    assert careless.to_dict("records") == regrouping.careless_in_pandas().to_dict("records")
    assert fixed.to_dict("records") == regrouping.fixed_in_pandas().to_dict("records")


@pytest.mark.needs_example_database
@pytest.mark.parametrize("name", ["fixed", "top_runs_per_job"])
def test_row_number_runs_and_gives_the_pandas_result(name: str) -> None:
    result = run(getattr(latest_and_top_n, name)(), send=example_database.send)
    in_pandas = getattr(latest_and_top_n, f"{name}_in_pandas")()
    assert list(result.columns) == list(in_pandas.columns)
    assert _rows(result) == _rows(in_pandas)


@pytest.mark.needs_example_database
def test_week_start_and_month_start_give_the_days_pandas_gives() -> None:
    s = _both_days(job_runs.dt, AS(week_start(job_runs.dt), "week"),
                   AS(month_start(job_runs.dt), "month"))
    result = run(s, send=example_database.send)
    days = pd.to_datetime(result.dt)
    monday = days - pd.to_timedelta(days.dt.weekday, unit="D")
    assert list(result.week.astype(str)) == list(monday.dt.strftime("%Y-%m-%d"))
    assert list(result.month.astype(str)) == list(days.dt.strftime("%Y-%m-01"))


# --- What comes back --------------------------------------------------------------------------


@pytest.mark.needs_example_database
def test_each_kind_of_column_comes_back_as_the_python_type_pandas_shows() -> None:
    s = _both_days(job_runs.run_id, job_runs.status, job_runs.duration_mins,
                   job_runs.avg_retry_secs, job_runs.dt)
    first = run(s, send=example_database.send).iloc[0].to_dict()
    assert {name: type(value) for name, value in first.items()} == {
        "run_id": int, "status": str, "duration_mins": int, "avg_retry_secs": float,
        "dt": str,
    }


@pytest.mark.needs_example_database
@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="ticket 25 of the PySpark work writes week_start and month_start as "
                   "CAST(... AS STRING); until then NEXT_DAY and TRUNC give a date, as their "
                   "docstrings say")
def test_week_start_and_month_start_come_back_as_text() -> None:
    s = _both_days(AS(week_start(job_runs.dt), "week"), AS(month_start(job_runs.dt), "month"))
    first = run(s, send=example_database.send).iloc[0].to_dict()
    assert {name: type(value) for name, value in first.items()} == {"week": str, "month": str}


# --- What the Example database says -----------------------------------------------------------


def test_a_java_home_that_holds_no_java_is_named(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JAVA_HOME", str(tmp_path))
    reason = engine.example_database_cannot_run()
    assert f"JAVA_HOME is {tmp_path}, which has no bin" in reason
    with pytest.raises(RuntimeError) as refused:
        example_database.send("SELECT job_id FROM ops.jobs")
    message = str(refused.value)
    assert "The Example database's Spark needs Java 17 or newer, and JAVA_HOME is " in message
    assert 'Set JAVA_HOME to the folder of a Java 17 or newer' in message


def test_a_spark_home_that_holds_no_spark_is_named(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SPARK_HOME", str(tmp_path))
    reason = engine.example_database_cannot_run()
    assert f"SPARK_HOME is {tmp_path}, which has no Spark in it" in reason
    with pytest.raises(RuntimeError, match=r'os\.environ\.pop\("SPARK_HOME"\)'):
        example_database.send("SELECT job_id FROM ops.jobs")


@pytest.mark.needs_example_database
def test_a_query_spark_refuses_shows_the_first_line_of_what_spark_said() -> None:
    with pytest.raises(RuntimeError) as refused:
        example_database.send("SELECT nope FROM ops.jobs")
    message = str(refused.value)
    assert "Spark couldn't run this Hive on the Example database: [UNRESOLVED_COLUMN" in message
    assert "Project" not in message, "Spark's plan of the query was shown"
    assert "SQLSTATE" not in message


@pytest.mark.needs_example_database
@pytest.mark.parametrize(("sql", "said"), [
    # ANSI's division by zero, raised while Spark runs the query, not while it reads it.
    ("SELECT sum(duration_mins) / 0 AS x FROM ops.job_runs", "[DIVIDE_BY_ZERO]"),
    # A Java error pyspark leaves as one, from a function Spark calls on each row.
    ("SELECT java_method('java.lang.Integer', 'parseInt', job_name) AS n FROM ops.jobs",
     "NumberFormatException"),
], ids=["ansi", "java"])
def test_a_query_spark_refuses_while_running_it_is_answered_and_its_spark_goes_on(
        sql: str, said: str) -> None:
    example_database.send("SELECT job_id FROM ops.jobs")
    process = engine._SPARK["process"]
    with pytest.raises(RuntimeError) as refused:
        example_database.send(sql)
    assert f"Spark couldn't run this Hive on the Example database: {said}" in str(refused.value)
    assert engine._SPARK["process"] is process, "a query Spark refused stopped its Spark"


# --- Its own process -------------------------------------------------------------------------


@pytest.mark.needs_example_database
def test_your_python_holds_no_spark_and_your_folder_gets_no_files() -> None:
    from pyspark import SparkContext

    run(_both_days(job_runs.run_id), send=example_database.send)
    assert SparkContext._active_spark_context is None
    assert [name for name in ("spark-warehouse", "metastore_db", "derby.log")
            if (Path.cwd() / name).exists()] == []


@pytest.mark.needs_example_database
def test_a_stopped_spark_starts_again() -> None:
    s = _both_days(job_runs.run_id)
    before = run(s, send=example_database.send)
    engine._SPARK["process"].kill()
    engine._SPARK["process"].wait(60)
    assert run(s, send=example_database.send).equals(before)


@pytest.mark.needs_example_database
def test_an_interrupted_query_leaves_no_answer_for_the_next_one() -> None:
    example_database.send("SELECT job_id FROM ops.jobs")
    slow = "SELECT sum(a.id * b.id) AS s FROM range(60000) a CROSS JOIN range(60000) b"
    # What a notebook's Interrupt button does, two seconds into a query that takes longer.
    interrupt = threading.Timer(2, _thread.interrupt_main)
    interrupt.start()
    try:
        with pytest.raises(KeyboardInterrupt):
            example_database.send(slow)
    finally:
        interrupt.cancel()
    assert list(example_database.send("SELECT count(*) AS jobs FROM ops.jobs").jobs) == [4]


@pytest.mark.needs_example_database
def test_stopping_its_spark_deletes_its_folder() -> None:
    run(_both_days(job_runs.run_id), send=example_database.send)
    folder = engine._SPARK["folder"]
    engine._stop_spark()
    assert not folder.exists()


# A Python that imports Spark Composer, then runs what it is given and waits.
_OTHER_PYTHON = """
import sys
sys.path[:0] = [{root!r}, {tools!r}]
import editions
editions.use(editions.SPARK_COMPOSER)
from pathlib import Path
from sql_composer import engine, example_database
{then}
sys.stdin.read()
"""


def _other_python(then: str) -> subprocess.Popen:
    script = _OTHER_PYTHON.format(root=str(ROOT), tools=str(ROOT / "tools"), then=then)
    return subprocess.Popen([sys.executable, "-c", script], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, text=True)


def _first_line_starting(child: subprocess.Popen, mark: str) -> str | None:
    for line in child.stdout:
        if line.startswith(mark):
            return line.removeprefix(mark).strip()
    return None


def _made_old(folder: Path) -> None:
    """Make a folder look older than a left-over folder must be."""
    old = time.time() - 2 * engine._LEFT_OVER_SECONDS
    os.utime(folder / engine._IN_USE, (old, old))


@pytest.mark.needs_example_database
def test_the_folder_of_a_killed_python_is_deleted_at_the_next_start() -> None:
    folder = None
    with _other_python('example_database.send("SELECT job_id FROM ops.jobs")\n'
                       'print("FOLDER", engine._SPARK["folder"], flush=True)') as child:
        try:
            said = _first_line_starting(child, "FOLDER ")
            folder = Path(said) if said else None
        finally:
            child.kill()
    assert folder is not None, "the killed Python's Example database didn't start"
    assert folder.exists(), "killed, it had no chance to delete its folder"
    _made_old(folder)
    for _ in range(60):  # its Spark stops within seconds of its Python
        engine._delete_left_over()
        if not folder.exists():
            break
        time.sleep(0.5)
    assert not folder.exists()


def test_a_folder_a_live_python_holds_is_left_alone() -> None:
    import tempfile

    folder = Path(tempfile.mkdtemp(prefix=engine._FOLDER_PREFIX,
                                   dir=engine._temporary_folder()))
    (folder / engine._IN_USE).touch()
    with _other_python(f'held = engine._hold(Path({str(folder / engine._IN_USE)!r}))\n'
                       'print("HELD", flush=True)') as child:
        try:
            assert _first_line_starting(child, "HELD") is not None
            _made_old(folder)
            engine._delete_left_over()
            assert folder.exists(), "the folder of a live Python was deleted"
        finally:
            child.kill()
    _made_old(folder)
    engine._delete_left_over()
    assert not folder.exists(), "once its Python stopped, the folder was left over"
