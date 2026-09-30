"""What Spark Composer runs on: the pyspark it needs, and the Spark its Example database uses.

`__init__.py` calls `check_installed()` as soon as it knows the folder is whole, before it
imports any other file. It reads pyspark's version without starting Spark, so importing Spark
Composer starts nothing, not even the Java that Spark itself runs on. The Example database hands
`run_query` a query's Hive and its tables, and gets back the query's column names and rows.

The Example database's Spark runs in a second Python, in the background, never in your
notebook's own. A Python holds only one Spark, and SparkSession.builder.getOrCreate() hands back
whichever is already there. If the Example database started its Spark in your notebook, it
would run on your own `spark`, or leave its made-up tables in the `spark` you get later. Running
apart, it never touches your `spark`, and it never sees your tables.

The first query takes about 15 seconds, while it starts that second Python in a temporary folder
of its own; later queries take about a second. Your notebook talks to it over a connection only
this computer can reach (127.0.0.1), locked with a new random key each time. It stops, and its
folder is deleted, when your kernel stops or restarts. If the kernel was killed too suddenly to
tidy up, the next Spark the Example database starts, in any notebook, deletes the folder.
"""

from __future__ import annotations

import atexit
import contextlib
import functools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import NoReturn

if __package__:
    # Run as a script, this file is the Example database's Spark process, which needs neither.
    from . import _four_part_message as four_part_message
    from . import _stop

TOOLBOX_VERSION = "2.1"

_LOWEST = (3, 5, 0)
_BELOW = (4, 1, 0)
_NEWEST_TESTED = (4, 0, 4)
# The Javas both supported Sparks run on: Spark 4 needs 17 or newer, and a Java newer than 21
# stops the Hadoop inside Spark from starting.
_JAVA_NEEDED = 17
_JAVA_NEWEST = 21


# --- pyspark ----------------------------------------------------------------------------


def _dotted(numbers):
    return ".".join(str(n) for n in numbers)


def _numbers(text):
    found = re.match(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(n) for n in found.groups()) if found else None


_IN_RANGE = f'"pyspark>={_dotted(_LOWEST)},<{_dotted(_BELOW)}"'
_NO_INSTALLING = "If you can't install packages, ask whoever looks after your environment."


def check_installed():
    """Refuse a pyspark outside the supported range."""
    try:
        import pyspark
    except ImportError:
        pyspark = None
    if pyspark is None:
        _stop(
            what="Spark Composer needs pyspark, and this Python can't import it.",
            why="Spark Composer is the Edition for a notebook that runs Spark, and it is "
            "checked only there: the Hive it writes is meant for spark.sql(...), and its "
            "Example database runs on Spark too.",
            fix="In a notebook that runs Spark, install pyspark from a notebook cell with %pip "
            f"install {_IN_RANGE}, then restart the kernel. {_NO_INSTALLING} Without Spark, "
            "use SQL Composer, the Edition that needs none.",
        )
    found = getattr(pyspark, "__version__", "unknown")
    version = _numbers(found)
    if version is None or not _LOWEST <= version < _BELOW:
        _stop(
            what=f"Spark Composer needs pyspark {_dotted(_LOWEST)} or newer, below "
            f"{_dotted(_BELOW)}, and this Python has pyspark {found}.",
            why="Spark Composer is checked only on that range of pyspark. Another Spark can "
            "read the same Hive differently, so a Statement could come out wrong without "
            "anything saying so.",
            fix="Use a notebook whose Spark is in that range, or ask whoever looks after "
            "your environment for one. Installing pyspark yourself may not change the Spark "
            "that runs your Hive.",
        )
    if version > _NEWEST_TESTED:
        print(f"Note: pyspark {found} is newer than any version Spark Composer was tested on "
              f"({_dotted(_NEWEST_TESTED)}). Nothing is refused; if a result looks wrong, tell "
              "whoever looks after the Toolbox.")


# --- The Example database's Spark: what it needs -----------------------------------------


def _java() -> tuple[str | None, str]:
    """The java program Spark would run, or None and why there is none."""
    home = os.environ.get("JAVA_HOME")
    if home:
        program = Path(home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        if program.is_file():
            return str(program), ""
        return None, f"JAVA_HOME is {home}, which has no bin{os.sep}{program.name} in it"
    program = shutil.which("java")
    return program, "no java program was found (JAVA_HOME isn't set, and none is on PATH)"


@functools.cache
def _java_version(program: str) -> int | None:
    """A java program's main version, such as 17, or None when it doesn't say."""
    try:
        said = subprocess.run([program, "-version"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    found = re.search(r'version "(\d+)(?:\.(\d+))?', said.stderr + said.stdout)
    if found is None:
        return None
    # Java 8 and older call themselves 1.8 and so on.
    return int(found[2]) if found[1] == "1" and found[2] else int(found[1])


# The Javas both supported Sparks run on, and how to point this Python at one, to paste into the
# notebook; no restart is needed.
_JAVAS = f"Java {_JAVA_NEEDED} to {_JAVA_NEWEST}"
_POINT_AT_JAVA = ('import os; os.environ["JAVA_HOME"] = r"<the Java\'s folder, the one with '
                  'bin in it>". No restart is needed.')
# The characters Spark's Windows launcher can't take in the temporary folder's path.
_LAUNCHER_CANT_TAKE = "&()!^"


def _lacking() -> tuple[str, str] | None:
    """What the Example database's Spark lacks here, and how to give it that, or None."""
    return _spark_home_lacking() or _temporary_folder_lacking() or _java_lacking()


def _spark_home_lacking() -> tuple[str, str] | None:
    spark_home = os.environ.get("SPARK_HOME")
    if not spark_home:
        return None
    programs = Path(spark_home) / "bin"
    if (programs / "spark-submit").is_file() or (programs / "spark-submit.cmd").is_file():
        return None
    return (f"can't start: SPARK_HOME is {spark_home}, which has no Spark in it",
            "Set SPARK_HOME to the folder of a Spark install, the one with bin in it, or take "
            'it away so pyspark uses the Spark it comes with: import os; '
            'os.environ.pop("SPARK_HOME"). Your own spark, already running, isn\'t changed, '
            "and no restart is needed.")


def _java_lacking() -> tuple[str, str] | None:
    program, missing = _java()
    needs = f"needs {_JAVAS}"
    install = (f"Install Java {_JAVA_NEEDED}, then set JAVA_HOME to its folder: "
               f"{_POINT_AT_JAVA} If you can't install it, ask whoever looks after your "
               "environment.")
    if program is None:
        found = f"{needs}, and {missing}"
        if os.environ.get("JAVA_HOME"):
            return found, (f"Set JAVA_HOME to the folder of your {_JAVAS}: {_POINT_AT_JAVA} "
                           f"If you have none, install Java {_JAVA_NEEDED} first.")
        return found, install
    version = _java_version(program)
    if version is not None and _JAVA_NEEDED <= version <= _JAVA_NEWEST:
        return None
    which = "doesn't say its version" if version is None else f"is Java {version}"
    return f"{needs}, and {program} {which}", install


def _temporary_folder_lacking() -> tuple[str, str] | None:
    folder = _temporary_folder()
    if os.name != "nt" or not set(folder) & set(_LAUNCHER_CANT_TAKE):
        return None
    return (f"can't start: the path of the temporary folder, {folder}, has one of "
            f"{' '.join(_LAUNCHER_CANT_TAKE)} in it, which Spark's Windows launcher can't take",
            "Point TEMP and TMP at a folder whose path has none of them, such as C:\\Temp, "
            "then restart the kernel.")


def example_database_cannot_run() -> str | None:
    """Why the Example database can't run a query here, or None when it can.

    It looks again each time, so setting JAVA_HOME or SPARK_HOME in the notebook is enough.
    """
    lacking = _lacking()
    return None if lacking is None else f"the Example database's Spark {lacking[0]}"


# --- The Example database's Spark: its own process, from your side -----------------------

# How long its Spark may take to start, and to answer one query.
_START_SECONDS = 180
_QUERY_SECONDS = 300
# How often a wait looks at whether the process is still there, in seconds.
_LOOK_EVERY = 0.2
# How long deleting a folder keeps trying while a Spark that has just stopped lets go of its
# files, which takes about a second.
_DELETE_SECONDS = 10
# What a kernel started by spark-submit, or a Spark machine, carries, which would make the
# process join that kernel's Spark, read its settings, or put its files elsewhere.
_NOT_PASSED_ON = ("PYSPARK_GATEWAY_PORT", "PYSPARK_GATEWAY_SECRET", "PYSPARK_SUBMIT_ARGS",
                  "HADOOP_CONF_DIR", "YARN_CONF_DIR", "_PYSPARK_DRIVER_CONN_INFO_PATH",
                  "SPARK_CONNECT_MODE", "SPARK_REMOTE", "SPARK_LOCAL_DIRS",
                  "SPARK_EXECUTOR_DIRS", "LOCAL_DIRS")
# Values Spark must read back as they were written, checked once its Spark starts.
_ESCAPING_CHECK = ("it's", "C:\\temp\\", "two\nlines", "tab\there", "back\rspace", "50%_off",
                   "`name`", 'say "hi"', "-- not a comment", "; not a second statement",
                   "caf\u00e9 \u2603")
# Each Example database Spark's folder in the temporary folder, and the file in it that the
# notebook's Python which started it holds locked while that Python lives.
_FOLDER_PREFIX = "spark_composer_example_database_"
_IN_USE = "in-use"
# How old a folder with nothing holding it must be before it is deleted as left over.
_LEFT_OVER_SECONDS = 60
# Where the log of a Spark that couldn't start is kept, once its folder is deleted.
_FAILED_START_LOG = "spark_composer_failed_start.log"

# The running Spark: its process, the listener it connected to, its connection, its folder,
# its log, and the folder's lock.
_SPARK: dict = {}
# One query at a time: a reply goes to whoever asked, even with queries from several threads.
_ONE_AT_A_TIME = threading.Lock()


class _Gone(Exception):
    """The process, or the Java its Spark runs on, has stopped: this Spark can't answer."""


def run_query(text: str, tables: dict) -> tuple[list, list]:
    """Run a query's Hive on the Example database's Spark: its column names, and its rows.

    `tables` maps each table's short name to its Table reference and its rows. Its Spark starts
    on the first query, and again if it has stopped; a query its stopped Spark couldn't answer
    is sent once more to the new one.
    """
    lacking = _lacking()
    if lacking is not None:
        what, fix = lacking
        raise RuntimeError(four_part_message(
            what=f"The Example database's Spark {what}.",
            why="The Example database runs each query on that Spark, so example_database.send "
            "can't give a DataFrame here. to_hive(...) still writes every Statement's Hive.",
            fix=fix,
            opt_out=None,
        ))
    with _ONE_AT_A_TIME:
        reply = _answer(text, tables)
    if "refused" in reply:
        raise RuntimeError(_refused(reply["refused"]))
    return reply["columns"], [tuple(row) for row in reply["rows"]]


def _answer(text: str, tables: dict) -> dict:
    """The reply to a query, starting a Spark first, and again if the one there has stopped."""
    for attempt in (1, 2):
        process = _SPARK.get("process")
        if process is None or process.poll() is not None:
            _stop_spark()
            _start_spark(tables)
        try:
            return _ask(text)
        except _Gone:
            _stop_spark(wait=False)
            if attempt == 2:
                _stopped()
    raise AssertionError  # the loop returns or raises


def _first_line(said: str) -> str:
    """What Spark said, cut to the sentences that name the problem, with no full stop.

    It leaves out Spark's SQLSTATE, the place in the Hive, and Spark's advice to change its
    settings or use its try_ functions, which the Example database's Spark doesn't take.
    """
    lines = said.strip().splitlines() or ["(Spark said nothing)"]
    first = re.sub(r"\s*SQLSTATE:.*$", "", lines[0])
    first = re.sub(r"[.;\s]*;\s*line \d+ pos \d+.*$", "", first)
    kept = [sentence for sentence in re.split(r"(?<=\.)\s+(?=[A-Z\[])", first)
            if "spark.sql." not in sentence and "try_" not in sentence]
    return " ".join(kept).rstrip(" ;.") or first.rstrip(" ;.")


def _refused(said: str) -> str:
    """Spark's refusal of a query, with what Spark said about it."""
    return four_part_message(
        what=f"Spark couldn't run this Hive on the Example database: {_first_line(said)}.",
        why="At work Spark refuses the same Hive or, set up less strictly, quietly gives None "
        "where this one stopped, so the Statement needs changing either way.",
        fix="Spark's message names the problem: usually a table, column or hive_function(...) "
        "name spelt wrong (print a Table reference, such as example_database.jobs, to see its "
        "columns), or a value of the wrong type, such as text given where a date goes. If "
        "neither, and statement(...) built the Hive, please report it with the Statement to "
        "whoever looks after the Toolbox.",
        opt_out=None,
    )


def _start_spark(tables: dict) -> None:
    """Start a Spark in a new temporary folder, make its tables, and check its escaping.

    Interrupted, as by a notebook's Interrupt button, it stops that Spark, which would otherwise
    give its answers to the queries after.
    """
    from multiprocessing.connection import Listener

    _delete_left_over()
    print("Note: starting the Example database's Spark: this query takes about 15 seconds, "
          "later ones about a second.", file=sys.stderr)
    try:
        folder = Path(tempfile.mkdtemp(prefix=_FOLDER_PREFIX, dir=_temporary_folder()))
        # Held for as long as this Spark runs, so no other Python deletes its folder.
        _SPARK.update(folder=folder, lock=_hold(folder / _IN_USE))
        for name in ("warehouse", "local", "tmp", "conf") + (() if os.name == "nt" else
                                                             ("java-tmp",)):
            (folder / name).mkdir()
        key = os.urandom(32)
        _SPARK["listener"] = listener = Listener(("127.0.0.1", 0), authkey=key)
        # The process writes to it while it runs; _stop_spark closes it once the process stops.
        _SPARK["log"] = log = open(folder / "spark.log", "w", encoding="utf-8")
        _SPARK["process"] = process = subprocess.Popen(
            [sys.executable, "-B", str(Path(__file__).resolve())], cwd=folder,
            env=_environment(folder), stdin=subprocess.PIPE, stdout=log,
            stderr=subprocess.STDOUT, text=True, start_new_session=os.name != "nt")
        process.stdin.write(json.dumps({"address": list(listener.address), "key": key.hex(),
                                        "settings": _settings(folder)}) + "\n")
        process.stdin.flush()
        _connect(listener)
        _make_tables(tables)
        _check_escaping()
    except _Gone:
        _not_started("stopped before it started")
    except KeyboardInterrupt:
        _stop_spark(wait=False)
        raise


def _make_tables(tables: dict) -> None:
    for name, (table, rows) in tables.items():
        reply = _ask(_table_hive(name, table._columns, rows))
        if "refused" in reply:
            said = _first_line(reply["refused"])
            _toolbox_failed(f"couldn't make its table {name}: {said}.")


def _connect(listener) -> None:
    """Wait for the process to connect back and its Spark to start, within _START_SECONDS."""
    deadline = time.monotonic() + _START_SECONDS
    accepted: dict = {}
    threading.Thread(target=_accept, args=(listener, accepted), daemon=True).start()
    while "connection" not in accepted:
        _still_starting(deadline)
        time.sleep(_LOOK_EVERY)
    listener.close()
    _SPARK["connection"] = connection = accepted["connection"]
    try:
        while not connection.poll(_LOOK_EVERY):
            _still_starting(deadline)
        started = connection.recv()
    except (EOFError, OSError):
        _not_started("stopped before it started")
    if "stopped" in started:
        _not_started("couldn't start")


def _accept(listener, accepted: dict) -> None:
    """Take the process's connection back, passing over any other that knocks first.

    It ends when the start gives up and closes the listener.
    """
    while True:
        try:
            accepted["connection"] = listener.accept()
            return
        except Exception:  # noqa: BLE001 - a knock with the wrong key, or a closed listener
            if _SPARK.get("listener") is not listener:
                return
            time.sleep(_LOOK_EVERY / 4)


def _still_starting(deadline: float) -> None:
    """Stop waiting for a start when the process has stopped, or at the deadline."""
    if _SPARK["process"].poll() is not None:
        _not_started("stopped before it started")
    if time.monotonic() > deadline:
        _not_started(f"didn't start within {_START_SECONDS} seconds", busy=True)


def _not_started(what: str, busy: bool = False) -> NoReturn:
    """Stop the Spark that couldn't start, keep its log, and say so, with its last line."""
    log, last = _keep_log()
    _stop_spark(wait=False)
    said = f" The last thing it wrote: {last}" if last else " It wrote nothing."
    raise RuntimeError(four_part_message(
        what=f"The Example database's Spark {what}.{said}",
        why="The Example database runs each query on that Spark, so none can run until one "
        "starts. to_hive(...) still writes every Statement's Hive.",
        fix="A busy computer can take longer: close other programs, then run the query again."
        if busy else "Run the query again: another Spark starts. If it fails the same way, "
        f"show its log, {log}, to whoever looks after your environment.",
        opt_out=None,
    ))


def _keep_log() -> tuple[Path, str]:
    """Copy the log of a Spark that couldn't start out of its folder; give its last line."""
    kept = Path(_temporary_folder()) / _FAILED_START_LOG
    log = _SPARK.get("log")
    if log is None:
        return kept, ""
    log.flush()
    with contextlib.suppress(OSError):
        shutil.copyfile(log.name, kept)
    lines = [line.strip() for line in Path(log.name).read_text(
        encoding="utf-8", errors="replace").splitlines() if line.strip()]
    return kept, lines[-1] if lines else ""


def _toolbox_failed(what: str) -> NoReturn:
    """Stop a Spark that refused the Toolbox's own start, and say it is the Toolbox's bug."""
    _stop_spark()
    raise RuntimeError(four_part_message(
        what=f"The Example database's Spark {what}",
        why="This is a bug in the Toolbox, not in your Statement: the Hive that Spark refused "
        "is the Toolbox's own, so no query can run on the Example database here.",
        fix="Please report this message to whoever looks after the Toolbox, with its pyspark "
        f"version, {_pyspark_version()}. to_hive(...) still writes every Statement's Hive.",
        opt_out=None,
    ))


def _pyspark_version() -> str:
    import pyspark

    return getattr(pyspark, "__version__", "unknown")


def _ask(sql: str) -> dict:
    """Send one piece of Hive and wait for the reply: its columns and rows, or Spark's refusal.

    When the process or its Java has stopped, it raises _Gone. When the answer doesn't come in
    time, or the wait is interrupted, the Spark is stopped, so its answer can't reach the next
    query.
    """
    connection, process = _SPARK["connection"], _SPARK["process"]
    deadline = time.monotonic() + _QUERY_SECONDS
    try:
        connection.send(sql)
        while not connection.poll(_LOOK_EVERY):
            if process.poll() is not None:
                raise _Gone
            if time.monotonic() > deadline:
                _stop_spark(wait=False)
                _too_slow()
        reply = connection.recv()
    except (EOFError, OSError) as error:
        raise _Gone from error
    except KeyboardInterrupt:
        _stop_spark(wait=False)
        raise
    if "stopped" in reply:
        raise _Gone
    return reply


def _stopped() -> NoReturn:
    """Say that the Spark stopped twice in a row, so the query got no answer."""
    raise RuntimeError(four_part_message(
        what="The Example database's Spark stopped while it had the query, and so did another "
        "one started for it.",
        why="Its Spark is gone, so the query got no answer.",
        fix="Run the query again: another Spark starts. If it stops the same way, show this "
        "message to whoever looks after your environment.",
        opt_out=None,
    ))


def _too_slow() -> NoReturn:
    """Say that a query took longer than _QUERY_SECONDS, so its Spark was stopped."""
    raise RuntimeError(four_part_message(
        what=f"The Example database's Spark didn't answer within {_QUERY_SECONDS} seconds.",
        why="Its answer would have come to the next query instead, so that Spark was stopped.",
        fix="A query that runs for minutes is too big for the Example database, whose tables "
        "hold a few rows each: check it for a JOIN with no ON, then run it again.",
        opt_out=None,
    ))


def _check_escaping() -> None:
    """Stop unless Spark reads every value of _ESCAPING_CHECK back as it was written."""
    from .trees import string
    from .writing import hive_text

    written = ", ".join(f"{hive_text(string(value))} AS v{i}"
                        for i, value in enumerate(_ESCAPING_CHECK))
    reply = _ask(f"SELECT {written}")
    if "refused" in reply:
        _toolbox_failed("refused the Toolbox's own check of how it reads text: "
                        f"{_first_line(reply['refused'])}.")
    wrong = [f"{wrote!r} came back as {read!r}"
             for wrote, read in zip(_ESCAPING_CHECK, reply["rows"][0]) if wrote != read]
    if wrong:
        _stop_spark()
        raise RuntimeError(four_part_message(
            what="The Example database's Spark reads text differently from how the Toolbox "
            f"writes it: {'; '.join(wrong)}.",
            why="Its answers could be wrong without anything saying so, so it isn't used: "
            "every query here stops the same way. to_hive(...) still writes every Statement's "
            "Hive.",
            fix="Tell whoever looks after the Toolbox that pyspark "
            f"{_pyspark_version()} reads these values differently.",
            opt_out=None,
        ))


def _table_hive(name: str, columns: dict, rows: list) -> str:
    """The Hive that makes one Example database table on its Spark, typed as written.

    Spark calls a table made this way a global temporary view.
    """
    from .trees import Node
    from .writing import hive_text

    # A name is written as the writer writes any name, a table's as a column's.
    names = {column: hive_text(Node("Column", name=column)) for column in columns}
    typed = ", ".join(f"CAST({names[column]} AS {kind}) AS {names[column]}"
                      for column, kind in columns.items())
    values = ", ".join("(" + ", ".join(_value(value) for value in row) + ")" for row in rows)
    return (f"CREATE OR REPLACE GLOBAL TEMP VIEW {hive_text(Node('Column', name=name))} AS "
            f"SELECT {typed} FROM VALUES {values} AS t({', '.join(names.values())})")


def _value(value) -> str:
    from .trees import number, string
    from .writing import hive_text

    if value is None:
        return "NULL"
    if isinstance(value, str):
        return hive_text(string(value))
    return hive_text(number(repr(value), is_float=isinstance(value, float)))


def _temporary_folder() -> str:
    """The temporary folder, by a path with no space where Windows can give one.

    Spark's Windows launcher writes a stray file beside a folder whose path has a space, so
    there the folder's short name is used, as C:\\Users\\JOHNSM~1\\... for
    C:\\Users\\John Smith.
    """
    base = tempfile.gettempdir()
    if os.name != "nt" or " " not in base:
        return base
    import ctypes

    size = ctypes.windll.kernel32.GetShortPathNameW(base, None, 0)
    short = ctypes.create_unicode_buffer(size)
    if size and ctypes.windll.kernel32.GetShortPathNameW(base, short, size):
        return short.value
    return base


def _environment(folder: Path) -> dict:
    """The process's environment: yours, less a kernel's Spark, with its own folders and UTC."""
    environment = {key: value for key, value in os.environ.items()
                   if key not in _NOT_PASSED_ON}
    for name in ("TMP", "TEMP", "TMPDIR"):
        environment[name] = str(folder / "tmp")
    environment.update(SPARK_CONF_DIR=str(folder / "conf"), SPARK_LOCAL_IP="127.0.0.1",
                       PYSPARK_PYTHON=sys.executable, TZ="UTC")
    program, _ = _java()
    if program is not None and not os.environ.get("JAVA_HOME"):
        environment["JAVA_HOME"] = str(Path(program).resolve().parent.parent)
    return environment


def _settings(folder: Path) -> dict:
    """Its Spark: one core, no catalog on disk, and every file in its own folder."""
    posix = folder.as_posix()
    settings = {
        "spark.master": "local[1]", "spark.app.name": "spark_composer_example_database",
        "spark.sql.catalogImplementation": "in-memory", "spark.sql.globalTempDatabase": "ops",
        "spark.sql.shuffle.partitions": "1", "spark.default.parallelism": "1",
        "spark.ui.enabled": "false", "spark.ui.showConsoleProgress": "false",
        "spark.sql.session.timeZone": "UTC", "spark.driver.memory": "512m",
        "spark.driver.host": "127.0.0.1", "spark.driver.bindAddress": "127.0.0.1",
        "spark.sql.warehouse.dir": f"{posix}/warehouse", "spark.local.dir": f"{posix}/local",
        "spark.sql.execution.arrow.pyspark.enabled": "false",
        "spark.sql.runSQLOnFiles": "false",
        "spark.sql.ansi.enabled": "true", "spark.sql.parser.escapedStringLiterals": "false",
    }
    # Java takes its temporary folder from TMP on Windows, where the launcher would mangle a
    # path with a letter outside English in this setting; elsewhere it needs telling.
    if os.name != "nt":
        settings["spark.driver.extraJavaOptions"] = f'-Djava.io.tmpdir="{posix}/java-tmp"'
    return settings


def _stop_spark(wait: bool = True) -> None:
    """Stop the Spark, if one runs, and delete its folder.

    With wait, the process is told to stop its Spark, and is given time to; without, the
    process and everything it started, its Spark's Java included, are killed at once.
    """
    connection, process = _SPARK.pop("connection", None), _SPARK.pop("process", None)
    if connection is not None:
        with contextlib.suppress(OSError):
            if wait:
                connection.send(None)
        connection.close()
    if process is not None:
        _end(process, wait)
    for name in ("listener", "log", "lock"):
        held = _SPARK.pop(name, None)
        if held is not None:
            held.close()
    folder = _SPARK.pop("folder", None)
    if folder is not None:
        _remove(folder, tries=int(_DELETE_SECONDS / _LOOK_EVERY))


def _end(process: subprocess.Popen, wait: bool) -> None:
    """End the process: with wait, by letting it stop; without, or if it doesn't, by force.

    Forced, everything it started goes with it.
    """
    if wait:
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.wait(30)
    if process.poll() is None:
        _kill_everything_started_by(process)
    with contextlib.suppress(OSError):
        process.stdin.close()
    with contextlib.suppress(subprocess.TimeoutExpired):
        process.wait(30)


def _kill_everything_started_by(process: subprocess.Popen) -> None:
    """Kill a process and every process it started.

    On Windows those are the tree of its children; elsewhere the process leads a session of
    its own, which they are in.
    """
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)],
                       capture_output=True, check=False)
    else:
        import signal

        with contextlib.suppress(OSError):
            os.killpg(process.pid, signal.SIGKILL)
    with contextlib.suppress(OSError):
        process.kill()


atexit.register(_stop_spark)


# --- The Example database's Spark: its folder ------------------------------------------------


def _hold(path: Path):
    """Open `path` and lock it, until it is closed or this Python stops."""
    held = open(path, "a+b")
    try:
        held.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(held.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        held.close()
        raise
    return held


def _remove(folder: Path, tries: int = 1) -> None:
    """Delete a Spark's folder, its in-use file last, trying `tries` times.

    A Spark lets go of its files about a second after it stops, so the tries are _LOOK_EVERY
    apart. Until everything else is gone the folder keeps its in-use file, so a later start can
    finish the job.
    """
    for attempt in range(tries):
        for part in _parts(folder):
            if part.is_dir():
                shutil.rmtree(part, ignore_errors=True)
            elif part.name != _IN_USE:
                _unlink(part)
        if {part.name for part in _parts(folder)} <= {_IN_USE}:
            _unlink(folder / _IN_USE)
            with contextlib.suppress(OSError):
                folder.rmdir()
        if not folder.exists() or attempt + 1 == tries:
            return
        time.sleep(_LOOK_EVERY)


def _parts(folder: Path) -> list[Path]:
    """What is in a folder, or nothing when another Python has just deleted it."""
    try:
        return list(folder.iterdir())
    except OSError:
        return []


def _unlink(path: Path) -> None:
    with contextlib.suppress(OSError):
        path.unlink()


def _delete_left_over() -> None:
    """Delete the folders of Example database Sparks whose notebook's Python has stopped.

    The Python that starts a Spark holds its folder's in-use file locked while it lives, and the
    lock goes with it, however it stops: a folder whose lock can be taken, and that is over a
    minute old, is left over. Taking the lock only tests it; it is given up at once.
    """
    now = time.time()
    for folder in Path(_temporary_folder()).glob(f"{_FOLDER_PREFIX}*"):
        in_use = folder / _IN_USE
        try:
            if now - in_use.stat().st_mtime < _LEFT_OVER_SECONDS:
                continue
            _hold(in_use).close()
        except OSError:
            continue
        _remove(folder)


# --- The process itself: one private Spark, answering until told to stop -----------------


def _serve() -> None:
    """Start a Spark with the settings sent on stdin, then answer each piece of Hive sent.

    Whatever goes wrong with a query goes back to be shown, unless the Java its Spark runs on
    has gone: then it says it has stopped, and stops, and the next query starts another Spark.
    It stops when told to (None), when the connection closes, and, once its Spark has started,
    at once when your Python stops, even mid-query: its pipe to this process's stdin closes
    then.
    """
    from multiprocessing.connection import Client

    config = json.loads(sys.stdin.readline())
    connection = Client(tuple(config["address"]), authkey=bytes.fromhex(config["key"]))
    try:
        from pyspark.sql import SparkSession

        builder = SparkSession.builder
        for key, value in config["settings"].items():
            builder = builder.config(key, value)
        spark = builder.getOrCreate()
    except Exception as error:  # noqa: BLE001 - a Spark that can't start says why, and stops
        connection.send({"stopped": f"{type(error).__name__}: {error}"})
        raise
    # Only once its Spark has started: on Windows, a thread waiting on stdin stops Spark
    # from starting the Java it runs on.
    threading.Thread(target=_stop_with_your_python, daemon=True).start()
    connection.send({"started": True})
    while True:
        try:
            sql = connection.recv()
        except (EOFError, OSError):
            break
        if sql is None:
            break
        try:
            frame = spark.sql(sql)
            reply = {"columns": list(frame.columns),
                     "rows": [tuple(row) for row in frame.collect()]}
        except Exception as error:  # noqa: BLE001 - shown, unless its Java has gone
            if _java_gone(error):
                connection.send({"stopped": f"{type(error).__name__}: {error}"})
                break
            reply = {"refused": _what_spark_said(error)}
        connection.send(reply)
    spark.stop()
    connection.close()


def _java_gone(error: Exception) -> bool:
    """Whether an error says the Java this Spark runs on has gone, rather than a query failed.

    Py4J, which pyspark talks to that Java through, raises a Py4JNetworkError, or the
    connection's own error, when it can't reach it.
    """
    names = {kind.__name__ for kind in type(error).__mro__}
    return "Py4JNetworkError" in names or isinstance(error, (ConnectionError, EOFError))


def _stop_with_your_python() -> None:
    """Exit as soon as your Python stops, however it stopped, taking this Spark with it.

    Your Python's end of the pipe to this process's stdin closes when it stops, and the Java
    this Spark runs on follows this process within a second.
    """
    sys.stdin.read()
    os._exit(0)


def _what_spark_said(error: Exception) -> str:
    """What a failed query's error says: its Java cause's message, when it has one.

    A refusal pyspark doesn't turn into its own error, such as one raised while Spark runs the
    query, holds Spark's reason in the Java exception at the root of it. An error Python raises
    while turning Spark's rows into Python values says what it is.
    """
    cause = getattr(error, "java_exception", None)
    try:
        while cause is not None and cause.getCause() is not None:
            cause = cause.getCause()
        if cause is not None:
            said = (cause.getMessage() or "").strip()
            name = cause.getClass().getSimpleName()
            return said if said.startswith("[") else ": ".join(filter(None, (name, said)))
    except Exception:  # noqa: BLE001 - Java can't say more; Python's text says enough
        pass
    if hasattr(error, "getErrorClass") or hasattr(error, "getCondition"):
        return str(error)
    return f"{type(error).__name__}: {error}"


if __name__ == "__main__":
    _serve()
