"""What Spark Composer runs on: the pyspark it needs, and the Spark its Example database uses.

`__init__.py` calls `check_installed()` as soon as it knows the folder is whole, before it imports
any other file. It reads pyspark's version without starting Spark, so importing Spark Composer
starts nothing, not even the Java that Spark itself runs on. The Example database hands
`run_query` a query's Hive and its tables, and gets back the query's column names and rows.

The Example database's Spark runs in a second Python of its own, in the background, never in
yours. A Python holds only one Spark, and SparkSession.builder.getOrCreate() gives back the one
it holds: started in your notebook, the Example database would run on your own `spark`, or your
own getOrCreate() would later give you the Example database's Spark, with its made-up tables. So your `spark` never sees ops.jobs, and the Example database never sees your tables.

The first query starts that second Python, in a temporary folder of its own, which takes about
15 seconds; later queries take about a second. Your Python talks to it over a connection only
this computer can reach (127.0.0.1), locked with a new random key each time. It stops, and its
folder is deleted, when your kernel stops or restarts, or at the next start if the kernel was
stopped too suddenly to tidy up.
"""

from __future__ import annotations

import atexit
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


# --- pyspark ------------------------------------------------------------------------------------


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
            why="Spark Composer is the Edition for a notebook that runs Spark, and it is checked "
            "only there: the Hive it writes is meant for spark.sql(...), and its Example "
            "database runs on Spark too.",
            fix="In a notebook that runs Spark, install pyspark from a notebook cell with %pip "
            f"install {_IN_RANGE}, then restart the kernel. {_NO_INSTALLING} Without Spark, use "
            "SQL Composer, the Edition that needs none.",
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


# --- The Example database's Spark: the Java it runs on -------------------------------------


def _java() -> tuple[str | None, str]:
    """The java program Spark would run, or None, and where it was looked for."""
    home = os.environ.get("JAVA_HOME")
    if home:
        program = Path(home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        found = str(program) if program.is_file() else None
        return found, f"JAVA_HOME is {home}, which holds no bin{os.sep}{program.name}"
    return shutil.which("java"), "neither JAVA_HOME nor PATH leads to a java program"


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


def example_database_cannot_run() -> str | None:
    """Why the Example database can't run a query here, or None when it can.

    It looks again each time, so setting JAVA_HOME in the notebook is enough.
    """
    program, looked = _java()
    needs = f"the Example database's Spark needs Java {_JAVA_NEEDED} or newer"
    if program is None:
        return f"{needs}, and {looked}"
    version = _java_version(program)
    if version is None:
        return f"{needs}, and {program} doesn't say its version"
    if version < _JAVA_NEEDED:
        return f"{needs}, and {program} is Java {version}"
    return None


# --- The Example database's Spark: its own process, from your side -----------------------

# How long its Spark may take to start, and to answer one query.
_START_SECONDS = 180
_QUERY_SECONDS = 300
# What a kernel started by spark-submit carries, which would make the process join that kernel's
# Spark rather than start its own, or read its settings.
_NOT_PASSED_ON = ("PYSPARK_GATEWAY_PORT", "PYSPARK_GATEWAY_SECRET", "PYSPARK_SUBMIT_ARGS",
                  "HADOOP_CONF_DIR", "YARN_CONF_DIR", "_PYSPARK_DRIVER_CONN_INFO_PATH",
                  "SPARK_CONNECT_MODE", "SPARK_REMOTE")
# Values Spark must read back as they were written, checked once its Spark starts.
_ESCAPING_CHECK = ("it's", "C:\\temp\\", "two\nlines", "tab\there", "back\rspace", "50%_off",
                   "`name`", 'say "hi"', "-- not a comment", "; not a second statement",
                   "caf\u00e9 \u2603")
# Each Example database Spark's folder in the temporary folder, and the file in it that its
# Python holds locked while it lives.
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
    reason = example_database_cannot_run()
    if reason is not None:
        raise RuntimeError(four_part_message(
            what=f"The Example database can't run a query here: {reason}.",
            why="It runs each query on a Spark of its own, which runs on Java, so "
            "example_database.send can't give a DataFrame. to_hive(...) still writes every "
            "Statement's Hive.",
            fix=f"Install Java {_JAVA_NEEDED} or newer, then set JAVA_HOME to its folder, the "
            "one that holds bin: in the notebook, os.environ[\"JAVA_HOME\"] = that folder. No "
            "restart is needed. If you can't install it, ask whoever looks after your "
            "environment; meanwhile the Example gallery shows each Worked example's result.",
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


def _refused(said: str) -> str:
    """Spark's refusal of a query, with the first line of what Spark said."""
    first = said.strip().splitlines()[0] if said.strip() else said
    return four_part_message(
        what=f"Spark couldn't run this Hive on the Example database: {first}",
        why="The Example database runs your Hive on a real Spark, which checks every name and "
        "type as your warehouse's Spark would.",
        fix="Check the names in Spark's message against the Example database's tables "
        "(ops.jobs, ops.job_runs and ops.run_alerts) and any hive_function(...) name. If every "
        "name is right and statement(...) built the Hive, please report it with the Statement "
        "to whoever looks after the Toolbox: the Toolbox may have written Hive Spark can't "
        "read.",
        opt_out=None,
    )


def _start_spark(tables: dict) -> None:
    """Start a Spark in a new temporary folder, make its tables, and check its escaping."""
    from multiprocessing.connection import Listener

    _delete_left_over()
    # On stderr, which a notebook shows, so it stays out of a doctest's or the gallery's output.
    print("Note: starting the Example database's Spark, which takes about 15 seconds, once "
          "for each Python.", file=sys.stderr)
    folder = Path(tempfile.mkdtemp(prefix=_FOLDER_PREFIX))
    _SPARK.update(folder=folder, lock=_hold(folder / _IN_USE))
    for name in ("warehouse", "local", "java-tmp", "derby", "tmp", "conf"):
        (folder / name).mkdir()
    key = os.urandom(32)
    listener = Listener(("127.0.0.1", 0), authkey=key)
    # Closed by _stop_spark, which the process outlives.
    log = open(folder / "spark.log", "w", encoding="utf-8")  # noqa: SIM115
    _SPARK["log"] = log
    _SPARK["process"] = subprocess.Popen(
        [sys.executable, "-B", str(Path(__file__).resolve())], cwd=folder,
        env=_environment(folder), stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT,
        text=True)
    _SPARK["process"].stdin.write(json.dumps({"address": list(listener.address),
                                              "key": key.hex(),
                                              "settings": _settings(folder)}) + "\n")
    _SPARK["process"].stdin.flush()
    _connect(listener)
    for name, (table, rows) in tables.items():
        if "refused" in _ask(_view(name, table._columns, rows)):
            _failed(f"couldn't make its table {name}")
    _check_escaping()


def _connect(listener) -> None:
    """Wait for the process to connect back and its Spark to start, within _START_SECONDS."""
    accepted = {}
    waiting = threading.Thread(target=lambda: accepted.update(connection=listener.accept()),
                               daemon=True)
    waiting.start()
    waiting.join(_START_SECONDS)
    listener.close()
    if "connection" not in accepted:
        _failed(f"didn't start within {_START_SECONDS} seconds")
    _SPARK["connection"] = connection = accepted["connection"]
    try:
        if not connection.poll(_START_SECONDS):
            _failed(f"didn't start within {_START_SECONDS} seconds")
        started = connection.recv()
    except (EOFError, OSError):
        _failed("couldn't start")
    if "stopped" in started:
        _failed(f"couldn't start: {started['stopped']}")


def _failed(what: str) -> NoReturn:
    """Stop the Spark, and say what went wrong, with the last lines it wrote."""
    last = _log_tail()
    _stop_spark()
    raise RuntimeError(four_part_message(
        what=f"The Example database's Spark {what}.",
        why="Every query on the Example database runs on that Spark, so none can run until "
        "another one starts.",
        fix="Run the query again: another Spark starts. If it fails again, the last lines its "
        "Spark wrote, below, usually name the cause. Often it is SPARK_HOME or JAVA_HOME "
        "naming a folder that isn't there, or security software stopping programs on this "
        "computer from connecting to each other.",
        opt_out=None,
    ) + f"\n\nThe last lines its Spark wrote:\n{last}")


def _log_tail() -> str:
    log = _SPARK.get("log")
    if log is None:
        return "(nothing)"
    log.flush()
    lines = Path(log.name).read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-30:]) or "(nothing)"


def _ask(sql: str) -> dict:
    """Send one piece of Hive and wait for the reply: its columns and rows, or Spark's refusal.

    When the process stops or doesn't answer, it is stopped, and _failed says so.
    """
    connection = _SPARK["connection"]
    try:
        connection.send(sql)
        if not connection.poll(_QUERY_SECONDS):
            _failed(f"didn't answer within {_QUERY_SECONDS} seconds")
        reply = connection.recv()
    except (EOFError, OSError):
        _failed("stopped")
    if "stopped" in reply:
        _failed(f"stopped: {reply['stopped']}")
    return reply


def _check_escaping() -> None:
    """Stop unless Spark reads every value of _ESCAPING_CHECK back as it was written."""
    from .trees import string
    from .writing import hive_text

    written = ", ".join(f"{hive_text(string(value))} AS v{i}"
                        for i, value in enumerate(_ESCAPING_CHECK))
    reply = _ask(f"SELECT {written}")
    if "refused" in reply:
        _stop_spark()
        raise RuntimeError(_refused(reply["refused"]))
    wrong = [f"{wrote!r} came back as {read!r}"
             for wrote, read in zip(_ESCAPING_CHECK, reply["rows"][0]) if wrote != read]
    if wrong:
        _stop_spark()
        raise RuntimeError(four_part_message(
            what="The Example database's Spark reads values differently from how the Toolbox "
            f"writes them: {'; '.join(wrong)}.",
            why="Its answers could be wrong without anything saying so.",
            fix="Tell whoever looks after the Toolbox, with this Python's pyspark version.",
            opt_out=None,
        ))


def _view(name: str, columns: dict, rows: list) -> str:
    """The Hive that makes one table a global temporary view of its rows, typed as written."""
    from .trees import Node
    from .writing import hive_text

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
    return {
        "spark.master": "local[1]", "spark.app.name": "spark_composer_example_database",
        "spark.sql.catalogImplementation": "in-memory", "spark.sql.globalTempDatabase": "ops",
        "spark.sql.shuffle.partitions": "1", "spark.default.parallelism": "1",
        "spark.ui.enabled": "false", "spark.ui.showConsoleProgress": "false",
        "spark.sql.session.timeZone": "UTC", "spark.driver.memory": "512m",
        "spark.driver.host": "127.0.0.1", "spark.driver.bindAddress": "127.0.0.1",
        "spark.sql.warehouse.dir": f"{posix}/warehouse", "spark.local.dir": f"{posix}/local",
        "spark.driver.extraJavaOptions":
            f'-Djava.io.tmpdir="{posix}/java-tmp" -Dderby.system.home="{posix}/derby"',
        "spark.sql.execution.arrow.pyspark.enabled": "false",
        "spark.sql.runSQLOnFiles": "false",
        "spark.sql.ansi.enabled": "true", "spark.sql.parser.escapedStringLiterals": "false",
    }


def _stop_spark() -> None:
    """Stop the Spark, if one runs, and delete its folder."""
    connection, process = _SPARK.pop("connection", None), _SPARK.pop("process", None)
    if connection is not None:
        try:
            connection.send(None)
        except OSError:
            pass
        connection.close()
    if process is not None:
        try:
            process.stdin.close()
            process.wait(30)
        except (OSError, subprocess.TimeoutExpired):
            process.kill()
            process.wait(30)
    for name in ("log", "lock"):
        held = _SPARK.pop(name, None)
        if held is not None:
            held.close()
    folder = _SPARK.pop("folder", None)
    if folder is not None:
        _delete(folder)


def _delete(folder: Path) -> None:
    """Delete a Spark's folder, once its Spark lets go of its files: about a second."""
    for _ in range(50):
        shutil.rmtree(folder, ignore_errors=True)
        if not folder.exists():
            return
        time.sleep(0.2)


def _hold(path: Path):
    """Open `path` and lock it, for as long as this Python lives or until it is closed."""
    held = open(path, "a+b")  # noqa: SIM115 - held for the folder's life
    held.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(held.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    return held


def _delete_left_over() -> None:
    """Delete the folders of Example database Sparks whose Python stopped without deleting them.

    A Python holds its folder's in-use file locked while it lives, and the lock goes with it,
    however it stops: a folder whose lock can be taken, and that is over a minute old, is left
    over.
    """
    now = time.time()
    for folder in Path(tempfile.gettempdir()).glob(f"{_FOLDER_PREFIX}*"):
        in_use = folder / _IN_USE
        try:
            if now - in_use.stat().st_mtime < _LEFT_OVER_SECONDS:
                continue
            held = _hold(in_use)
        except OSError:
            continue
        # The in-use file goes last, so a folder whose Spark still holds a file is tried again
        # at the next start.
        with held:
            for part in folder.iterdir():
                if part.is_dir():
                    shutil.rmtree(part, ignore_errors=True)
                elif part.name != _IN_USE:
                    _unlink(part)
        if [part.name for part in folder.iterdir()] == [_IN_USE]:
            _unlink(in_use)
            shutil.rmtree(folder, ignore_errors=True)


def _unlink(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


atexit.register(_stop_spark)


# --- The process itself: one private Spark, answering until told to stop -----------------


def _serve() -> None:
    """Start a Spark with the settings sent on stdin, then answer each piece of Hive sent.

    A refusal from Spark goes back to be shown. Anything else means this Spark can't go on,
    so it says so and stops, and the next query starts another. It stops too when told to
    (None), or when the connection closes, however your Python stopped.
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
        except PySparkException as error:
            reply = {"refused": str(error)}
        except Exception as error:  # noqa: BLE001 - this Spark can't go on
            connection.send({"stopped": f"{type(error).__name__}: {str(error)[:3000]}"})
            break
        connection.send(reply)
    spark.stop()
    connection.close()


if __name__ == "__main__":
    _serve()
