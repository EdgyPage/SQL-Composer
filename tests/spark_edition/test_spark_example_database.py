"""Spark Composer's Example database runs each query on a Spark of its own, in its own process.

That Spark runs what sqlglot's executor can't, row_number, NEXT_DAY and TRUNC, so the Worked
examples SQL Composer can only show in pandas are run here and checked against their pandas
twins. These also hold:

- what Python type each kind of column comes back as;
- what the Example database says when Java, Spark or a usable temporary folder is missing,
  when its Spark can't start, when Spark refuses a query, and when Python can't take what
  Spark gives back;
- that your Python holds no Spark afterwards, and that its Spark reads nothing of a kernel's
  own Spark or Hadoop settings;
- that its Spark, and everything started for it, ends however it is stopped: told to, killed,
  interrupted as it starts or mid-query, killed from outside, stopped by the query it runs,
  or left behind by a Python that was killed or stopped mid-query; that a Spark left half
  started isn't used; and that a stray connection doesn't hold up a start.
"""

from __future__ import annotations

import _thread
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
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


def _count_jobs() -> list:
    return list(example_database.send("SELECT count(*) AS jobs FROM ops.jobs").jobs)


# What _count_jobs() gives: the Example database's jobs table holds four jobs.
_EVERY_JOB = [4]


@pytest.fixture
def own_temporary_folder(monkeypatch, tmp_path) -> Path:
    """A temporary folder of the test's own, so a failed start's kept log stays out of yours."""
    folder = tmp_path / "temp"
    folder.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(folder))
    return folder


def _kept_logs(folder: Path) -> list[Path]:
    return list(folder.glob("spark_composer_failed_start_*.log"))


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


# --- What the Example database says when it can't start ---------------------------------------


def test_a_java_home_that_holds_no_java_is_named(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JAVA_HOME", str(tmp_path))
    reason = engine.example_database_cannot_run()
    assert f"JAVA_HOME is {tmp_path}, which has no bin" in reason
    with pytest.raises(RuntimeError) as refused:
        example_database.send("SELECT job_id FROM ops.jobs")
    message = str(refused.value)
    assert "The Example database's Spark needs Java 17 to 21, and JAVA_HOME is " in message
    assert "Set JAVA_HOME to the folder of a Java 17 to 21 you have" in message


@pytest.mark.parametrize("folders", [[], ["bin"]], ids=["no bin", "a bin with no spark-submit"])
def test_a_spark_home_that_holds_no_spark_is_named(monkeypatch, tmp_path, folders) -> None:
    for folder in folders:
        (tmp_path / folder).mkdir()
    monkeypatch.setenv("SPARK_HOME", str(tmp_path))
    reason = engine.example_database_cannot_run()
    assert f"SPARK_HOME is {tmp_path}, which has no Spark in it" in reason
    with pytest.raises(RuntimeError, match=r'os\.environ\.pop\("SPARK_HOME"\)'):
        example_database.send("SELECT job_id FROM ops.jobs")


def test_a_spark_home_holding_another_spark_is_named(monkeypatch, tmp_path) -> None:
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / ("spark-submit.cmd" if os.name == "nt" else "spark-submit")).touch()
    (tmp_path / "jars").mkdir()
    (tmp_path / "jars" / "spark-core_2.12-3.4.1.jar").touch()
    monkeypatch.setenv("SPARK_HOME", str(tmp_path))
    reason = engine.example_database_cannot_run()
    assert (f"SPARK_HOME is {tmp_path}, which holds Spark 3.4.1, and this Python's pyspark is "
            in reason)


@pytest.mark.skipif(os.name != "nt", reason="only Spark's Windows launcher can't take these")
@pytest.mark.parametrize(("folder", "named"), [
    ("C:\\Users\\Tom&Jerry\\Temp", "&"),
    ("C:\\Users\\a;b\\Temp", ";"),
    # A folder Windows gives no short name, as on a drive where it makes none.
    ("C:\\No Such Folder\\Temp", "a space"),
], ids=["&", ";", "a space with no short name"])
def test_a_temporary_folder_the_windows_launcher_cant_take_is_named(monkeypatch, folder: str,
                                                                    named: str) -> None:
    monkeypatch.setattr(tempfile, "tempdir", folder)
    reason = engine.example_database_cannot_run()
    assert f"the temporary folder Python uses, {folder}, has {named} in its path" in reason
    with pytest.raises(RuntimeError, match=r"tempfile\.tempdir = "):
        example_database.send("SELECT job_id FROM ops.jobs")


@pytest.mark.needs_example_database
def test_a_java_that_couldnt_say_its_version_is_asked_again(monkeypatch) -> None:
    monkeypatch.setattr(engine, "_JAVAS_ASKED", {})  # as in a Python that hasn't asked yet
    monkeypatch.setenv("JAVA_TOOL_OPTIONS", "-Xmx1m")  # too little memory for Java to start
    reason = engine.example_database_cannot_run()
    assert ("didn't say which Java it is: it said Error occurred during initialization of VM"
            in reason)
    monkeypatch.delenv("JAVA_TOOL_OPTIONS")
    assert engine.example_database_cannot_run() is None


# --- What the Example database says when its Spark can't start -------------------------------


@pytest.mark.parametrize(("log", "said"), [
    ("Launcher: the Java it runs could not start.\n"
     "Traceback (most recent call last):\n"
     '  File "engine.py", line 1004, in _serve\n'
     "    spark = builder.getOrCreate()\n"
     "pyspark.errors.exceptions.base.PySparkRuntimeError: [JAVA_GATEWAY_EXITED] Java gateway "
     "process exited before sending its port number.\n",
     "Launcher: the Java it runs could not start."),
    ("26/09/30 04:32:01 WARN Utils: Your hostname resolves to a loopback address\n"
     "26/09/30 04:32:01 ERROR SparkContext: Error initializing SparkContext.\n"
     "java.net.BindException: Address already in use: bind\n"
     "\tat java.base/sun.nio.ch.Net.bind0(Native Method)\n"
     "\tat java.base/java.lang.Thread.run(Thread.java:840)\n"
     "Traceback (most recent call last):\n"
     '  File "engine.py", line 1004, in _serve\n'
     "py4j.protocol.Py4JJavaError: An error occurred while calling "
     "None.org.apache.spark.api.java.JavaSparkContext.\n"
     ": java.net.BindException: Address already in use: bind\n"
     "\tat java.base/sun.nio.ch.Net.bind0(Native Method)\n"
     "\t... 20 more\n",
     "java.net.BindException: Address already in use: bind"),
    ("Picked up JAVA_TOOL_OPTIONS: -Dfile.encoding=UTF-8\n"
     "Traceback (most recent call last):\n"
     '  File "engine.py", line 1004, in _serve\n'
     "TypeError: 'JavaPackage' object is not callable\n",
     "TypeError: 'JavaPackage' object is not callable"),
    ('Exception in thread "Thread-1" java.lang.OutOfMemoryError: Cannot reserve 4096 bytes\n'
     "\tat java.base/java.nio.Bits.reserveMemory(Bits.java:178)\n",
     'Exception in thread "Thread-1" java.lang.OutOfMemoryError: Cannot reserve 4096 bytes'),
    ("WARNING: Using incubator modules: jdk.incubator.vector\n"
     "Using Spark's default log4j profile: org/apache/spark/log4j2-defaults.properties\n"
     "26/09/30 04:32:01 WARN Shell: Did not find winutils.exe\n", ""),
], ids=["the launcher's own complaint", "a Java error, under its stack and a traceback",
        "a Python error, under a Java notice", "a Java error with no traceback",
        "only what a start that goes well writes"])
def test_a_failed_starts_log_is_cut_to_what_most_likely_says_why(log: str, said: str) -> None:
    assert engine._last_words(log) == said


@pytest.mark.needs_example_database
def test_a_launcher_that_quits_without_starting_java_is_said_to_have_quit(
        monkeypatch, tmp_path, own_temporary_folder) -> None:
    # What Spark's Windows launcher does when the Java it runs can't start: it says why, and
    # quits as though all went well.
    home = tmp_path / "spark"
    (home / "bin").mkdir(parents=True)
    (home / "jars").mkdir()
    (home / "jars" / f"spark-core_2.13-{engine._pyspark_version()}.jar").touch()
    if os.name == "nt":
        (home / "bin" / "spark-submit.cmd").write_text(
            "@echo off\necho Launcher: the Java it runs could not start.\nexit /b 0\n")
    else:
        launcher = home / "bin" / "spark-submit"
        launcher.write_text("#!/bin/sh\necho 'Launcher: the Java it runs could not start.'\n"
                            "exit 0\n")
        launcher.chmod(0o755)
    monkeypatch.setenv("SPARK_HOME", str(home))
    engine._stop_spark()
    started = time.monotonic()
    with pytest.raises(RuntimeError) as quit_:
        example_database.send("SELECT job_id FROM ops.jobs")
    took = time.monotonic() - started
    message = str(quit_.value)
    assert ("quit while it was starting. What it wrote that most likely says why: Launcher: the "
            "Java it runs could not start." in message)
    assert f"It was started from the Spark in SPARK_HOME, {home}." in message
    assert f"show its log, {_kept_logs(own_temporary_folder)[0]}, to whoever" in message
    assert took < 60, f"it took {took:.0f} seconds to see the launcher had quit"


# --- What the Example database says when a query goes wrong -----------------------------------


@pytest.mark.parametrize(("said", "shown"), [
    ("[UNRESOLVED_COLUMN.WITH_SUGGESTION] A column with name `avg_retry` cannot be resolved. "
     "Did you mean one of the following? [`avg_retry_secs`, `run_id`]. SQLSTATE: 42703; line 1 "
     "pos 7;\n'Project ['avg_retry]",
     "[UNRESOLVED_COLUMN.WITH_SUGGESTION] A column with name `avg_retry` cannot be resolved. "
     "Did you mean one of the following? [`avg_retry_secs`, `run_id`]"),
    ("[DIVIDE_BY_ZERO] Division by zero. Use `try_divide` to tolerate divisor being 0 and "
     'return NULL instead. If necessary set "spark.sql.ansi.enabled" to "false" to bypass this '
     "error.", "[DIVIDE_BY_ZERO] Division by zero"),
    ("Max iterations (100) reached for batch Resolution, please set "
     "'spark.sql.analyzer.maxIterations' to a larger value.",
     "Max iterations (100) reached for batch Resolution"),
    ("[UNRESOLVED_COLUMN] ... one of the following? [`team`, `job_id`].; line 1 pos 7",
     "[UNRESOLVED_COLUMN] ... one of the following? [`team`, `job_id`]"),
    ("[ARITHMETIC_OVERFLOW] integer overflow. Use 'try_multiply' to tolerate overflow and "
     'return NULL instead. If necessary set "spark.sql.ansi.enabled" to "false" to bypass this '
     "error. SQLSTATE: 22003", "[ARITHMETIC_OVERFLOW] integer overflow"),
], ids=["suggestion naming a try_ column", "setting advice", "3.5.0 setting advice",
        "3.5.0 place in the Hive", "try_ advice in single quotes"])
def test_what_spark_says_is_cut_to_what_names_the_problem(said: str, shown: str) -> None:
    assert engine._spark_says(said) == shown


@pytest.mark.needs_example_database
def test_a_query_spark_refuses_shows_what_spark_said() -> None:
    with pytest.raises(RuntimeError) as refused:
        example_database.send("SELECT nope FROM ops.jobs")
    message = str(refused.value)
    what = next(line for line in message.splitlines() if "What happened:" in line)
    assert "Spark couldn't run this Hive on the Example database: [UNRESOLVED_COLUMN" in what
    assert "Project" not in message, "Spark's plan of the query was shown"
    assert "SQLSTATE" not in message
    assert not what.endswith("..")


@pytest.mark.needs_example_database
@pytest.mark.parametrize(("sql", "said"), [
    # ANSI's division by zero, raised while Spark runs the query, not while it reads it.
    ("SELECT sum(duration_mins) / 0 AS x FROM ops.job_runs", "[DIVIDE_BY_ZERO]"),
    # ANSI's overflow, whose advice names a try_ function in single quotes.
    ("SELECT duration_mins * 2147483647 AS x FROM ops.job_runs",
     "[ARITHMETIC_OVERFLOW] integer overflow."),
    # A Java error pyspark leaves as one, from a function Spark calls on each row.
    ("SELECT java_method('java.lang.Integer', 'parseInt', job_name) AS n FROM ops.jobs",
     "NumberFormatException"),
], ids=["ansi", "ansi overflow", "java"])
def test_a_query_spark_refuses_while_running_it_is_answered_and_its_spark_goes_on(
        sql: str, said: str) -> None:
    _count_jobs()
    process = engine._SPARK["process"]
    with pytest.raises(RuntimeError) as refused:
        example_database.send(sql)
    message = str(refused.value)
    assert f"Spark couldn't run this Hive on the Example database: {said}" in message
    assert "try_" not in message, "Spark's advice to use a function the Toolbox doesn't wrap"
    assert engine._SPARK["process"] is process, "a query Spark refused stopped its Spark"


@pytest.mark.needs_example_database
@pytest.mark.parametrize(("sql", "said"), [
    ("SELECT make_date(10001, 1, 1) AS d FROM ops.jobs", "ValueError: year 10001"),
    # pyspark raises an error of its own as it turns an interval into Python.
    ("SELECT make_interval(1, 2, 3, 4, 5, 6, 7) AS i", ""),
], ids=["a date after 9999", "an interval"])
def test_a_value_python_cant_take_is_said_so_and_its_spark_goes_on(sql: str, said: str) -> None:
    _count_jobs()
    process = engine._SPARK["process"]
    with pytest.raises(RuntimeError, match="Python couldn't take what it gave back: "
                       + re.escape(said)):
        example_database.send(sql)
    assert engine._SPARK["process"] is process, "a value Python can't take stopped its Spark"


# --- One query at a time ----------------------------------------------------------------------


@pytest.mark.needs_example_database
def test_queries_from_two_threads_each_get_their_own_answer() -> None:
    _count_jobs()
    wrong = []

    def ask(start: int) -> None:
        for k in range(start, start + 20):
            got = list(example_database.send(f"SELECT {k} AS k FROM ops.jobs LIMIT 1").k)
            if got != [k]:
                wrong.append((k, got))

    threads = [threading.Thread(target=ask, args=(start,)) for start in (1000, 2000)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert wrong == []


# --- Its own process -------------------------------------------------------------------------


def _processes_naming(folder: Path) -> list[tuple[int, str]]:
    """Every process started for a Spark, and its program's name.

    Its Java and launchers name the Spark's folder on their command lines. Off Windows the
    Spark's own Python, which runs in the folder, is found by that; on Windows a Python still
    running there keeps the folder from being deleted.
    """
    if os.name == "nt":
        listed = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process | Where-Object { $_.Name -ne 'powershell.exe' -and "
             f"$_.CommandLine -like '*{folder.name}*' }} | ForEach-Object "
             "{ \"$($_.ProcessId) $($_.Name)\" }"],
            capture_output=True, text=True).stdout
        return [(int(pid), name) for pid, name in (line.split(" ", 1)
                                                   for line in listed.splitlines() if line)]
    found = []
    for process in Path("/proc").glob("[0-9]*"):
        try:
            words = (process / "cmdline").read_bytes().split(b"\0")
            runs_in = os.readlink(process / "cwd")
        except OSError:
            continue
        if folder.name in runs_in or any(folder.name.encode() in word for word in words):
            found.append((int(process.name), Path(words[0].decode(errors="replace")).name))
    return found


def _nothing_left_of(folder: Path) -> None:
    """Fail unless a Spark's folder is gone and nothing started for it still runs."""
    for _ in range(25):  # killed processes can take a moment to be gone
        left = _processes_naming(folder)
        if not left and not folder.exists():
            return
        time.sleep(0.2)
    assert left == [], "a process started for the Spark still runs"
    assert not folder.exists()


def _note_folders_made(monkeypatch) -> list[Path]:
    """The folders the Example database makes from now on, as it makes them."""
    made: list[Path] = []
    real = tempfile.mkdtemp

    def noting(*args, **kwargs) -> str:
        made.append(Path(real(*args, **kwargs)))
        return str(made[-1])

    monkeypatch.setattr(engine.tempfile, "mkdtemp", noting)
    return made


@pytest.mark.needs_example_database
def test_your_python_holds_no_spark_and_your_folder_gets_no_files() -> None:
    from pyspark import SparkContext

    run(_both_days(job_runs.run_id), send=example_database.send)
    assert SparkContext._active_spark_context is None
    assert [name for name in ("spark-warehouse", "metastore_db", "derby.log")
            if (Path.cwd() / name).exists()] == []


@pytest.mark.needs_example_database
def test_a_kernels_hadoop_settings_dont_reach_its_spark(monkeypatch, tmp_path) -> None:
    # What a kernel started by spark-submit, on a Spark that brings no Hadoop of its own, carries.
    (tmp_path / "core-site.xml").write_text(
        "<configuration><property><name>fs.defaultFS</name>"
        "<value>nowhere://warehouse-at-work/</value></property></configuration>")
    monkeypatch.setenv("SPARK_DIST_CLASSPATH", str(tmp_path))
    engine._stop_spark()
    assert _count_jobs() == _EVERY_JOB


@pytest.mark.needs_example_database
def test_a_java_found_through_a_script_on_path_starts_its_spark(monkeypatch, tmp_path) -> None:
    # As a version manager puts a script named java first on PATH, in place of the Java.
    java, _ = engine._java()
    if os.name == "nt":
        (tmp_path / "java.bat").write_text(f'@"{java}" %*\n')
    else:
        (tmp_path / "java").write_text(f'#!/bin/sh\nexec "{java}" "$@"\n')
        (tmp_path / "java").chmod(0o755)
    monkeypatch.delenv("JAVA_HOME", raising=False)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    assert Path(engine._java()[0]).parent == tmp_path
    engine._stop_spark()
    assert _count_jobs() == _EVERY_JOB


@pytest.mark.needs_example_database
def test_a_relative_temporary_folder_is_taken_from_where_your_python_runs(monkeypatch,
                                                                         tmp_path) -> None:
    (tmp_path / "temp").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(tempfile, "tempdir", "temp")
    engine._stop_spark()
    try:
        assert _count_jobs() == _EVERY_JOB
    finally:
        engine._stop_spark()


@pytest.mark.needs_example_database
def test_stopping_its_spark_leaves_nothing() -> None:
    _count_jobs()
    folder = engine._SPARK["folder"]
    engine._stop_spark()
    _nothing_left_of(folder)


@pytest.mark.needs_example_database
def test_a_killed_spark_process_starts_again() -> None:
    _count_jobs()
    engine._SPARK["process"].kill()
    engine._SPARK["process"].wait(60)
    assert _count_jobs() == _EVERY_JOB


@pytest.mark.needs_example_database
def test_a_spark_whose_java_was_killed_answers_the_next_query_from_a_new_one() -> None:
    _count_jobs()
    folder = engine._SPARK["folder"]
    javas = [pid for pid, name in _processes_naming(folder) if name.lower().startswith("java")]
    assert javas, "the Spark's Java wasn't found"
    for pid in javas:
        # Windows has no SIGKILL: there os.kill ends a process at once, whatever the signal.
        os.kill(pid, signal.SIGTERM if os.name == "nt" else signal.SIGKILL)
    assert _count_jobs() == _EVERY_JOB
    _nothing_left_of(folder)


@pytest.mark.needs_example_database
def test_a_query_that_stops_its_spark_says_so() -> None:
    _count_jobs()
    with pytest.raises(RuntimeError, match="so the query itself seems to stop Spark"):
        example_database.send("SELECT java_method('java.lang.System', 'exit', 0) AS bye")
    assert _count_jobs() == _EVERY_JOB


@pytest.mark.needs_example_database
def test_an_interrupted_query_leaves_no_answer_for_the_next_one() -> None:
    _count_jobs()
    slow = "SELECT sum(a.id * b.id) AS s FROM range(60000) a CROSS JOIN range(60000) b"
    # What a notebook's Interrupt button does, two seconds into a query that takes longer.
    interrupt = threading.Timer(2, _thread.interrupt_main)
    interrupt.start()
    try:
        with pytest.raises(KeyboardInterrupt):
            example_database.send(slow)
    finally:
        interrupt.cancel()
    assert _count_jobs() == _EVERY_JOB


@pytest.mark.needs_example_database
@pytest.mark.parametrize("after", [0.5, 1.0, 1.5, 2.0, 3.0])
def test_an_interrupted_start_leaves_nothing_but_its_log(monkeypatch, own_temporary_folder,
                                                         after: float) -> None:
    engine._stop_spark()
    made = _note_folders_made(monkeypatch)
    interrupt = threading.Timer(after, _thread.interrupt_main)
    interrupt.start()
    try:
        with pytest.raises(KeyboardInterrupt):
            example_database.send("SELECT job_id FROM ops.jobs")
    finally:
        interrupt.cancel()
    assert made
    _nothing_left_of(made[0])
    assert _kept_logs(own_temporary_folder), "the interrupted start's log wasn't kept"


@pytest.mark.needs_example_database
def test_a_spark_left_half_started_is_not_used(monkeypatch) -> None:
    engine._stop_spark()
    real_still_starting = engine._still_starting

    def second_interrupt() -> None:
        raise KeyboardInterrupt

    def interrupted_once_connected(deadline: float) -> None:
        # A first Interrupt once the process has connected, before its Spark says it started,
        # and a second as the first one's stop begins, so that stop never happens.
        if "connection" in engine._SPARK:
            monkeypatch.setattr(engine, "_interrupted", second_interrupt)
            raise KeyboardInterrupt
        real_still_starting(deadline)

    monkeypatch.setattr(engine, "_still_starting", interrupted_once_connected)
    with pytest.raises(KeyboardInterrupt):
        example_database.send("SELECT job_id FROM ops.jobs")
    monkeypatch.undo()
    half_started = engine._SPARK["folder"]
    assert list(example_database.send("SELECT 'B' AS b").b) == ["B"]
    _nothing_left_of(half_started)


@pytest.mark.needs_example_database
@pytest.mark.parametrize("after", [1.0, 2.0])
def test_a_spark_process_killed_as_it_starts_leaves_nothing(monkeypatch, own_temporary_folder,
                                                             after: float) -> None:
    engine._stop_spark()
    made = _note_folders_made(monkeypatch)

    def kill_it() -> None:
        while engine._SPARK.get("process") is None:
            time.sleep(0.01)
        time.sleep(after)
        engine._SPARK["process"].kill()

    killer = threading.Thread(target=kill_it, daemon=True)
    killer.start()
    with pytest.raises(RuntimeError, match="quit while it was starting"):
        example_database.send("SELECT job_id FROM ops.jobs")
    killer.join()
    _nothing_left_of(made[0])


@pytest.mark.needs_example_database
@pytest.mark.parametrize("says", [False, True],
                         ids=["knocks and goes", "stays and says nothing"])
def test_a_stray_connection_doesnt_hold_up_a_start(says: bool) -> None:
    engine._stop_spark()
    knocked = threading.Event()
    strays = []

    def knock() -> None:
        for _ in range(400):
            listener = engine._SPARK.get("listener")
            if listener is not None:
                stray = socket.create_connection(listener.getsockname())
                knocked.set()
                if says:
                    strays.append(stray)
                else:
                    stray.close()
                return
            time.sleep(0.02)

    knocker = threading.Thread(target=knock)
    knocker.start()
    try:
        assert _count_jobs() == _EVERY_JOB
    finally:
        knocker.join()
        for stray in strays:
            stray.close()
    assert knocked.is_set(), "no stray connection was made while the Spark started"


# --- Folders and Pythons --------------------------------------------------------------------

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


def _other_python_script(then: str) -> str:
    return _OTHER_PYTHON.format(root=str(ROOT), tools=str(ROOT / "tools"), then=then)


def _other_python(then: str) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-c", _other_python_script(then)],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)


def _first_line_starting(child: subprocess.Popen, mark: str) -> str | None:
    for line in child.stdout:
        if line.startswith(mark):
            return line.removeprefix(mark).strip()
    return None


def _made_old(folder: Path) -> None:
    """Make a folder look older than a left-over folder must be."""
    old = time.time() - 2 * engine._LEFT_OVER_SECONDS
    in_use = folder / engine._IN_USE
    os.utime(in_use if in_use.exists() else folder, (old, old))


def _deleted_as_left_over(folder: Path) -> bool:
    """Whether the next starts' sweep deletes a folder, once what held it lets go."""
    for _ in range(50):  # a killed Python, and a venv's real Python, end a moment after
        engine._delete_left_over()
        if not folder.exists():
            return True
        time.sleep(0.2)
    return False


@pytest.mark.needs_example_database
def test_the_folder_of_a_killed_python_is_deleted_at_the_next_start() -> None:
    folder = None
    with _other_python(f"example_database.send({'SELECT job_id FROM ops.jobs'!r})\n"
                       'print("FOLDER", engine._SPARK["folder"], flush=True)') as child:
        try:
            said = _first_line_starting(child, "FOLDER ")
            folder = Path(said) if said else None
        finally:
            child.kill()
    assert folder is not None, "the killed Python's Example database didn't start"
    assert folder.exists(), "killed, it had no chance to delete its folder"
    _made_old(folder)
    assert _deleted_as_left_over(folder)
    _nothing_left_of(folder)


@pytest.mark.needs_example_database
def test_a_python_that_stops_mid_query_stops_at_once_and_leaves_nothing() -> None:
    script = _other_python_script(
        "import threading, time\n"
        f"example_database.send({'SELECT job_id FROM ops.jobs'!r})\n"
        'print("FOLDER", engine._SPARK["folder"], flush=True)\n'
        "slow = 'SELECT sum(a.id * b.id) AS s FROM range(60000) a CROSS JOIN range(60000) b'\n"
        "threading.Thread(target=example_database.send, args=(slow,), daemon=True).start()\n"
        "time.sleep(2)\n"
        "sys.exit(0)")
    started = time.monotonic()
    done = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                          timeout=180)
    said = [line for line in done.stdout.splitlines() if line.startswith("FOLDER ")]
    assert said, done.stderr
    ended_after = time.monotonic() - started
    _nothing_left_of(Path(said[0].removeprefix("FOLDER ").strip()))
    assert ended_after < 60, f"it took {ended_after:.0f} seconds to stop"


def test_a_folder_a_live_python_holds_is_left_alone() -> None:
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
    assert _deleted_as_left_over(folder), "once its Python stopped, the folder was left over"


def test_a_folder_with_no_in_use_file_is_deleted_once_old() -> None:
    # As a Python leaves one when it stops between making the folder and its in-use file.
    folder = Path(tempfile.mkdtemp(prefix=engine._FOLDER_PREFIX,
                                   dir=engine._temporary_folder()))
    engine._delete_left_over()
    assert folder.exists(), "a folder just made was deleted"
    _made_old(folder)
    assert _deleted_as_left_over(folder)
