"""Spark Composer's Example database runs each query on a Spark of its own, in its own process.

That Spark runs what sqlglot's executor can't, row_number, NEXT_DAY and TRUNC, so the Worked
examples SQL Composer can only show in pandas are run here and checked against their pandas
twins. These also hold:

- what Python type each kind of column comes back as;
- what the Example database says when Java, Spark or a usable temporary folder is missing,
  when Spark refuses a query, and when Python can't hold what Spark gives back;
- that your Python holds no Spark afterwards;
- that its Spark, and everything started for it, ends however it is stopped: told to, killed,
  interrupted as it starts or mid-query, killed from outside, stopped by the query it runs,
  or left behind by a Python that was killed or stopped mid-query; and that a stray
  connection doesn't hold up a start.
"""

from __future__ import annotations

import _thread
import os
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


@pytest.mark.skipif(os.name != "nt", reason="only Spark's Windows launcher can't take these")
def test_a_temporary_folder_the_windows_launcher_cant_take_is_named(monkeypatch) -> None:
    monkeypatch.setattr(tempfile, "tempdir", "C:\\Users\\Tom&Jerry\\Temp")
    reason = engine.example_database_cannot_run()
    assert ("the temporary folder Python uses, C:\\Users\\Tom&Jerry\\Temp, has & in its path"
            in reason)
    with pytest.raises(RuntimeError, match=r"tempfile\.tempdir = "):
        example_database.send("SELECT job_id FROM ops.jobs")


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
], ids=["suggestion naming a try_ column", "setting advice", "3.5.0 setting advice",
        "3.5.0 place in the Hive"])
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
    # A Java error pyspark leaves as one, from a function Spark calls on each row.
    ("SELECT java_method('java.lang.Integer', 'parseInt', job_name) AS n FROM ops.jobs",
     "NumberFormatException"),
], ids=["ansi", "java"])
def test_a_query_spark_refuses_while_running_it_is_answered_and_its_spark_goes_on(
        sql: str, said: str) -> None:
    _count_jobs()
    process = engine._SPARK["process"]
    with pytest.raises(RuntimeError) as refused:
        example_database.send(sql)
    assert f"Spark couldn't run this Hive on the Example database: {said}" in str(refused.value)
    assert engine._SPARK["process"] is process, "a query Spark refused stopped its Spark"


@pytest.mark.needs_example_database
def test_a_value_python_cant_hold_is_said_so_and_its_spark_goes_on() -> None:
    _count_jobs()
    process = engine._SPARK["process"]
    with pytest.raises(RuntimeError, match="Python can't hold a value it gave back: "
                       "ValueError: year 10001"):
        example_database.send("SELECT make_date(10001, 1, 1) AS d FROM ops.jobs")
    assert engine._SPARK["process"] is process, "a value Python can't hold stopped its Spark"


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
    """Every process whose command line names a Spark's folder: its Java and launchers do."""
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
    for cmdline in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            words = cmdline.read_bytes().split(b"\0")
        except OSError:
            continue
        if any(folder.name.encode() in word for word in words):
            found.append((int(cmdline.parent.name), words[0].decode(errors="replace")))
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


class _FoldersMade:
    """The folders the Example database makes while this is in use."""

    def __init__(self, monkeypatch) -> None:
        self.made: list[Path] = []
        real = tempfile.mkdtemp

        def noting(*args, **kwargs) -> str:
            self.made.append(Path(real(*args, **kwargs)))
            return str(self.made[-1])

        monkeypatch.setattr(engine.tempfile, "mkdtemp", noting)


@pytest.mark.needs_example_database
def test_your_python_holds_no_spark_and_your_folder_gets_no_files() -> None:
    from pyspark import SparkContext

    run(_both_days(job_runs.run_id), send=example_database.send)
    assert SparkContext._active_spark_context is None
    assert [name for name in ("spark-warehouse", "metastore_db", "derby.log")
            if (Path.cwd() / name).exists()] == []


@pytest.mark.needs_example_database
def test_stopping_its_spark_leaves_nothing() -> None:
    _count_jobs()
    folder = engine._SPARK["folder"]
    engine._stop_spark()
    _nothing_left_of(folder)


@pytest.mark.needs_example_database
def test_a_killed_spark_process_starts_again() -> None:
    before = _count_jobs()
    engine._SPARK["process"].kill()
    engine._SPARK["process"].wait(60)
    assert _count_jobs() == before


@pytest.mark.needs_example_database
def test_a_spark_whose_java_was_killed_answers_the_next_query_from_a_new_one() -> None:
    _count_jobs()
    folder = engine._SPARK["folder"]
    javas = [pid for pid, name in _processes_naming(folder) if name.lower().startswith("java")]
    assert javas, "the Spark's Java wasn't found"
    for pid in javas:
        os.kill(pid, signal.SIGTERM if os.name == "nt" else signal.SIGKILL)
    assert _count_jobs() == [4]
    _nothing_left_of(folder)


@pytest.mark.needs_example_database
def test_a_query_that_stops_its_spark_says_so() -> None:
    _count_jobs()
    with pytest.raises(RuntimeError, match="the query itself seems to stop Spark"):
        example_database.send("SELECT java_method('java.lang.System', 'exit', 0) AS bye")
    assert _count_jobs() == [4]


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
    assert _count_jobs() == [4]


@pytest.mark.needs_example_database
@pytest.mark.parametrize("after", [0.5, 1.0, 1.5, 2.0, 3.0])
def test_an_interrupted_start_leaves_nothing(monkeypatch, after: float) -> None:
    engine._stop_spark()
    folders = _FoldersMade(monkeypatch)
    interrupt = threading.Timer(after, _thread.interrupt_main)
    interrupt.start()
    try:
        with pytest.raises(KeyboardInterrupt):
            example_database.send("SELECT job_id FROM ops.jobs")
    finally:
        interrupt.cancel()
    assert folders.made
    _nothing_left_of(folders.made[0])


@pytest.mark.needs_example_database
@pytest.mark.parametrize("after", [1.0, 2.0])
def test_a_spark_process_killed_as_it_starts_leaves_nothing(monkeypatch,
                                                             after: float) -> None:
    engine._stop_spark()
    folders = _FoldersMade(monkeypatch)

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
    _nothing_left_of(folders.made[0])


@pytest.mark.needs_example_database
@pytest.mark.parametrize("says", [False, True],
                         ids=["knocks and goes", "stays and says nothing"])
def test_a_stray_connection_doesnt_hold_up_a_start(says: bool) -> None:
    engine._stop_spark()
    strays = []

    def knock() -> None:
        for _ in range(400):
            server = engine._SPARK.get("server")
            if server is not None:
                stray = socket.create_connection(server.getsockname())
                if says:
                    strays.append(stray)
                else:
                    stray.close()
                return
            time.sleep(0.02)

    knocker = threading.Thread(target=knock)
    knocker.start()
    try:
        assert _count_jobs() == [4]
    finally:
        knocker.join()
        for stray in strays:
            stray.close()


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
    script = _OTHER_PYTHON.format(root=str(ROOT), tools=str(ROOT / "tools"), then=(
        "import threading, time\n"
        f"example_database.send({'SELECT job_id FROM ops.jobs'!r})\n"
        'print("FOLDER", engine._SPARK["folder"], flush=True)\n'
        "slow = 'SELECT sum(a.id * b.id) AS s FROM range(60000) a CROSS JOIN range(60000) b'\n"
        "threading.Thread(target=example_database.send, args=(slow,), daemon=True).start()\n"
        "time.sleep(2)\n"
        "sys.exit(0)"))
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
