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
# The oldest Java that both supported Sparks run on.
_JAVA_NEEDED = 17


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


# How to point this Python at a Java, to paste into the notebook; no restart is needed.
_JAVA_HOME_TO = (f"JAVA_HOME to the folder of a Java {_JAVA_NEEDED} or newer, the one with bin "
                 'inside: import os; os.environ["JAVA_HOME"] = r"<that folder>". No restart is '
                 "needed.")


def _lacking() -> tuple[str, str] | None:
    """What the Example database's Spark lacks here, and how to give it that, or None."""
    spark_home = os.environ.get("SPARK_HOME")
    if spark_home and not (Path(spark_home) / "bin").is_dir():
        return (f"can't start: SPARK_HOME is {spark_home}, which has no Spark in it",
                "Set SPARK_HOME to a Spark's folder, or take it away so pyspark uses its own: "
                'import os; os.environ.pop("SPARK_HOME"). No restart is needed.')
    program, missing = _java()
    needs = f"needs Java {_JAVA_NEEDED} or newer"
    if program is None and os.environ.get("JAVA_HOME"):
        return f"{needs}, and {missing}", f"Set {_JAVA_HOME_TO}"
    if program is None:
        return (f"{needs}, and {missing}",
                f"Install Java {_JAVA_NEEDED} or newer, then set {_JAVA_HOME_TO} If you can't "
                "install it, ask whoever looks after your environment.")
    version = _java_version(program)
    if version is None or version < _JAVA_NEEDED:
        which = "doesn't say its version" if version is None else f"is Java {version}"
        return f"{needs}, and {program} {which}", f"Set {_JAVA_HOME_TO}"
    return None


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
# What a kernel started by spark-submit carries, which would make the process join that kernel's
# Spark rather than start its own, or read its settings.
_NOT_PASSED_ON = ("PYSPARK_GATEWAY_PORT", "PYSPARK_GATEWAY_SECRET", "PYSPARK_SUBMIT_ARGS",
                  "HADOOP_CONF_DIR", "YARN_CONF_DIR", "_PYSPARK_DRIVER_CONN_INFO_PATH",
                  "SPARK_CONNECT_MODE", "SPARK_REMOTE")
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

# The running Spark: its process, its connection, its folder, its log, and the folder's lock.
_SPARK: dict = {}


def run_query(text: str, tables: dict) -> tuple[list, list]:
    """Run a query's Hive on the Example database's Spark: its column names, and its rows.

    `tables` maps each table's short name to its Table reference and its rows. Its Spark starts
    on the first query, and again if it has stopped.
    """
    lacking = _lacking()
    if lacking is not None:
        raise RuntimeError(four_part_message(
            what=f"The Example database's Spark {lacking[0]}.",
            why="The Example database runs each query on that Spark, so example_database.send "
            "can't give a DataFrame here. to_hive(...) still writes every Statement's Hive.",
            fix=lacking[1],
            opt_out=None,
        ))
    process = _SPARK.get("process")
    if process is None or process.poll() is not None:
        _stop_spark()
        _start_spark(tables)
    reply = _ask(text)
    if "refused" in reply:
        raise RuntimeError(_refused(reply["refused"]))
    return reply["columns"], [tuple(row) for row in reply["rows"]]


def _first_line(said: str) -> str:
    """The first line of what Spark said, which names the problem, without its SQLSTATE."""
    lines = said.strip().splitlines() or ["(Spark said nothing)"]
    return re.sub(r"\s*SQLSTATE:.*$", "", lines[0]).rstrip(" ;.") + "."


def _refused(said: str) -> str:
    """Spark's refusal of a query, with the first line of what Spark said."""
    return four_part_message(
        what=f"Spark couldn't run this Hive on the Example database: {_first_line(said)}",
        why="Your warehouse's Spark would most likely refuse the same Hive, so the Statement "
        "would fail at work too.",
        fix="Spark's message names the problem: usually a name spelt differently from the "
        "Example database's tables (ops.jobs, ops.job_runs and ops.run_alerts, whose columns "
        "their Table references list), or a value of the wrong type, such as text given to "
        "hive_function(...) where a date goes. If neither, and statement(...) built the Hive, "
        "please report it with the Statement to whoever looks after the Toolbox.",
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
        _SPARK.update(folder=folder, lock=_hold(folder / _IN_USE))
        for name in ("warehouse", "local", "java-tmp", "tmp", "conf"):
            (folder / name).mkdir()
        key = os.urandom(32)
        _SPARK["listener"] = listener = Listener(("127.0.0.1", 0), authkey=key)
        # The process writes to it while it runs; _stop_spark closes it once the process stops.
        _SPARK["log"] = log = open(folder / "spark.log", "w", encoding="utf-8")
        _SPARK["process"] = process = subprocess.Popen(
            [sys.executable, "-B", str(Path(__file__).resolve())], cwd=folder,
            env=_environment(folder), stdin=subprocess.PIPE, stdout=log,
            stderr=subprocess.STDOUT, text=True)
        process.stdin.write(json.dumps({"address": list(listener.address), "key": key.hex(),
                                        "settings": _settings(folder)}) + "\n")
        process.stdin.flush()
        _connect(listener)
        for name, (table, rows) in tables.items():
            reply = _ask(_table_hive(name, table._columns, rows))
            if "refused" in reply:
                said = _first_line(reply["refused"])
                _toolbox_failed(f"couldn't make its table {name}: {said}")
        _check_escaping()
    except KeyboardInterrupt:
        _stop_spark(wait=False)
        raise


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
        _not_started(f"couldn't start: {_first_line(started['stopped'])}")


def _accept(listener, accepted: dict) -> None:
    """Take the process's connection back, unless the start gives up first and closes it."""
    try:
        accepted["connection"] = listener.accept()
    except Exception:  # noqa: BLE001 - a closed listener, or a connection with the wrong key
        pass


def _still_starting(deadline: float) -> None:
    """Stop waiting for a start when the process has stopped, or at the deadline."""
    if _SPARK["process"].poll() is not None:
        _not_started("stopped before it started")
    if time.monotonic() > deadline:
        _not_started(f"didn't start within {_START_SECONDS} seconds", busy=True)


_BUSY = "A busy computer can take longer: close other programs, then run the query again."
_NOT_STARTING = ("Run the query again: another Spark starts. If it fails the same way, show "
                 "this message to whoever looks after your environment: something there stops "
                 "Spark from starting, such as security software that stops programs on this "
                 "computer from connecting to each other.")


def _not_started(what: str, busy: bool = False) -> NoReturn:
    """Stop the Spark that couldn't start, and say so."""
    _stop_spark(wait=False)
    raise RuntimeError(four_part_message(
        what=f"The Example database's Spark {what}.",
        why="The Example database runs each query on that Spark, so none can run until one "
        "starts. to_hive(...) still writes every Statement's Hive.",
        fix=_BUSY if busy else _NOT_STARTING,
        opt_out=None,
    ))


def _toolbox_failed(what: str) -> NoReturn:
    """Stop a Spark that refused the Toolbox's own start, and say it is the Toolbox's bug."""
    _stop_spark()
    raise RuntimeError(four_part_message(
        what=f"The Example database's Spark {what}",
        why="This is a bug in the Toolbox, not in your Statement: the Hive Spark refused is "
        "the Toolbox's own, so no query can run on the Example database here.",
        fix="Please report this message to whoever looks after the Toolbox, with this Python's "
        f"pyspark version, {_pyspark_version()}. to_hive(...) still writes every Statement's "
        "Hive.",
        opt_out=None,
    ))


def _pyspark_version() -> str:
    import pyspark

    return getattr(pyspark, "__version__", "unknown")


def _ask(sql: str) -> dict:
    """Send one piece of Hive and wait for the reply: its columns and rows, or Spark's refusal.

    When the process stops or doesn't answer in time, it is stopped, and that is said. When the
    wait is interrupted, it is stopped too, so its answer can't come to the next query.
    """
    connection, process = _SPARK["connection"], _SPARK["process"]
    deadline = time.monotonic() + _QUERY_SECONDS
    try:
        connection.send(sql)
        while not connection.poll(_LOOK_EVERY):
            if process.poll() is not None:
                _stopped("stopped")
            if time.monotonic() > deadline:
                _stopped(f"didn't answer within {_QUERY_SECONDS} seconds")
        reply = connection.recv()
    except (EOFError, OSError):
        _stopped("stopped")
    except KeyboardInterrupt:
        _stop_spark(wait=False)
        raise
    if "stopped" in reply:
        _stopped(f"stopped: {_first_line(reply['stopped'])}")
    return reply


def _stopped(what: str) -> NoReturn:
    """Stop a Spark that stopped answering, and say so."""
    _stop_spark(wait=False)
    raise RuntimeError(four_part_message(
        what=f"The Example database's Spark {what}.",
        why="The query didn't get an answer, and the queries after it would get the wrong "
        "ones, so that Spark is stopped.",
        fix="Run the query again: another Spark starts. A query that runs for minutes is too "
        "big for the Example database, whose tables hold a few rows each.",
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
        _toolbox_failed(f"refused the Toolbox's own check of how it reads text: "
                        f"{_first_line(reply['refused'])}")
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

    With wait, the process is asked to stop its Spark first; without, it is killed at once, and
    its Spark follows within a second.
    """
    connection, process = _SPARK.pop("connection", None), _SPARK.pop("process", None)
    if connection is not None:
        with contextlib.suppress(OSError):
            if wait:
                connection.send(None)
        connection.close()
    if process is not None:
        try:
            if not wait:
                process.kill()
            process.stdin.close()
            process.wait(30)
        except (OSError, subprocess.TimeoutExpired):
            process.kill()
            process.wait(30)
    for name in ("listener", "log", "lock"):
        held = _SPARK.pop(name, None)
        if held is not None:
            held.close()
    folder = _SPARK.pop("folder", None)
    if folder is not None:
        _remove(folder, tries=50)


atexit.register(_stop_spark)


# --- The Example database's Spark: its folder ------------------------------------------------


def _hold(path: Path):
    """Open `path` and lock it, for as long as this Python lives or until it is closed."""
    # Held open for the folder's life: closing it gives up the lock.
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

    A Spark lets go of its files about a second after it stops, so the tries are a fifth of a
    second apart. Until everything else is gone the folder keeps its in-use file, so a later
    start can finish the job.
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
    minute old, is left over.
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

    A query Spark refuses goes back to be shown. Anything else means this Spark can't go on,
    so it says so and stops, and the next query starts another. It stops when told to (None),
    when the connection closes, and, once its Spark has started, at once when your Python stops,
    even mid-query: its pipe to this process's stdin closes then.
    """
    from multiprocessing.connection import Client

    config = json.loads(sys.stdin.readline())
    connection = Client(tuple(config["address"]), authkey=bytes.fromhex(config["key"]))
    try:
        from pyspark.errors import PySparkException
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
        except Exception as error:  # noqa: BLE001 - a refusal, or a Spark that can't go on
            # A Java error pyspark passes on as it is, from a Java that is still there, has the
            # Java exception with it.
            if not isinstance(error, PySparkException) and not hasattr(error, "java_exception"):
                connection.send({"stopped": f"{type(error).__name__}: {error}"})
                break
            reply = {"refused": _what_spark_said(error)}
        connection.send(reply)
    spark.stop()
    connection.close()


def _stop_with_your_python() -> None:
    """Exit as soon as your Python stops, however it stopped, taking this Spark with it.

    Your Python's end of the pipe to this process's stdin closes when it stops, and the Java
    this Spark runs on follows this process within a second.
    """
    sys.stdin.read()
    os._exit(0)


def _what_spark_said(error: Exception) -> str:
    """What a refused query's error says: its Java cause's message, when it has one.

    A refusal pyspark doesn't turn into its own error, such as one raised while Spark runs the
    query, holds Spark's reason in the Java exception at the root of it.
    """
    cause = getattr(error, "java_exception", None)
    try:
        while cause is not None and cause.getCause() is not None:
            cause = cause.getCause()
        if cause is not None:
            said = cause.getMessage() or ""
            name = cause.getClass().getSimpleName()
            return said if said.startswith("[") else f"{name}: {said}"
    except Exception:  # noqa: BLE001 - Java can't say more; Python's text says enough
        pass
    return str(error)


if __name__ == "__main__":
    _serve()
