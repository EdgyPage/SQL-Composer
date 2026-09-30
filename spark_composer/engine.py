"""What Spark Composer runs on: the pyspark it needs, and the Spark its Example database uses.

`__init__.py` calls `check_installed()` as soon as it knows the folder is whole, before it imports
any other file. It reads pyspark's version without starting Spark, so importing Spark Composer
starts nothing, not even the Java that Spark itself runs on. The Example database hands
`run_query` a query's Hive and its tables, and gets back the query's column names and rows.

The Example database's Spark runs in a helper of its own, never in your Python: a Spark started
in your Python would either hand the Example database your own Spark, or tie the Spark you start
later to the Example database's. So the first query starts this very file as a script, in a
temporary folder of its own, and the two talk over a local connection with a random key. The
helper stops when your Python does.
"""

from __future__ import annotations

import atexit
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

if __package__:
    # Run as a script, this file is the Example database's helper, which needs none of these.
    from . import _four_part_message as four_part_message
    from . import _stop
    from .trees import number, string
    from .writing import hive_text

TOOLBOX_VERSION = "2.1"

_LOWEST = (3, 5, 0)
_BELOW = (4, 1, 0)
_NEWEST_TESTED = (4, 0, 4)
# The oldest Java that both supported Sparks run on.
_JAVA = 17


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

# What example_database_cannot_run found, so Java is asked only once.
_FOUND: dict = {}


def _java() -> str | None:
    """The java program Spark would run: JAVA_HOME's, else the first on PATH, else None."""
    home = os.environ.get("JAVA_HOME")
    if home:
        program = Path(home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        return str(program) if program.is_file() else None
    return shutil.which("java")


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
    """Why the Example database can't run a query here, or None when it can."""
    if "reason" not in _FOUND:
        program = _java()
        version = None if program is None else _java_version(program)
        needs = f"the Example database's Spark needs Java {_JAVA} or newer"
        if program is None:
            _FOUND["reason"] = f"{needs}, and this computer has none"
        elif version is None:
            _FOUND["reason"] = f"{needs}, and {program} doesn't say its version"
        elif version < _JAVA:
            _FOUND["reason"] = f"{needs}, and {program} is Java {version}"
        else:
            _FOUND["reason"] = None
    return _FOUND["reason"]


# --- The Example database's Spark: the helper, from your side --------------------------------

# How long the helper's Spark may take to start, and to answer one query.
_START_SECONDS = 180
_QUERY_SECONDS = 300
# What a kernel started by spark-submit carries, which would make the helper join that kernel's
# Spark rather than start its own, or read its settings.
_NOT_PASSED_ON = ("PYSPARK_GATEWAY_PORT", "PYSPARK_GATEWAY_SECRET", "PYSPARK_SUBMIT_ARGS",
                  "HADOOP_CONF_DIR", "YARN_CONF_DIR", "_PYSPARK_DRIVER_CONN_INFO_PATH",
                  "SPARK_CONNECT_MODE", "SPARK_REMOTE")
# Values Spark must read back as they were written, checked once the helper starts.
_ESCAPING_CHECK = ("it's", "C:\\temp\\", "two\nlines", "tab\there", "back\rspace", "50%_off",
                   "`name`", 'say "hi"', "-- not a comment", "; not a second statement",
                   "caf\u00e9 \u2603")

# The running helper: its process, its connection, its folder and its log.
_HELPER: dict = {}


def run_query(text: str, tables: dict) -> tuple[list, list]:
    """Run a query's Hive on the Example database's Spark: its column names, and its rows.

    `tables` maps each table's short name to its Table reference and its rows. The helper starts
    on the first query, and again if it has stopped.
    """
    reason = example_database_cannot_run()
    if reason is not None:
        raise RuntimeError(four_part_message(
            what="The Example database can't run a query here.",
            why=f"The Example database runs on a Spark of its own, and {reason}.",
            fix=f"Install Java {_JAVA}, or see the Hive with to_hive(...) and run it with your "
            "own send.",
            opt_out=None,
        ))
    process = _HELPER.get("process")
    if process is None or process.poll() is not None:
        _stop_helper()
        _start_helper(tables)
    reply = _ask({"collect": text})
    if "error" in reply:
        raise RuntimeError(four_part_message(
            what="Spark couldn't run this Hive on the Example database.",
            why=f"Spark said: {reply['error']}",
            fix="If it is Hive Spark should run, please report it with the Statement that made "
            "it: the Toolbox may have written something Spark can't read.",
            opt_out=None,
        ))
    return reply["columns"], [tuple(row) for row in reply["rows"]]


def _start_helper(tables: dict) -> None:
    """Start the helper in a new temporary folder, make its tables, and check its escaping."""
    from multiprocessing.connection import Listener

    folder = Path(tempfile.mkdtemp(prefix="spark_composer_example_database_"))
    for name in ("warehouse", "local", "java-tmp", "derby", "tmp", "conf"):
        (folder / name).mkdir()
    key = os.urandom(32)
    listener = Listener(("127.0.0.1", 0), authkey=key)
    # Closed by _stop_helper, which the helper outlives.
    log = open(folder / "helper.log", "w", encoding="utf-8")  # noqa: SIM115
    process = subprocess.Popen(
        [sys.executable, "-B", str(Path(__file__).resolve())], cwd=folder,
        env=_environment(folder), stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT,
        text=True)
    _HELPER.update(process=process, folder=folder, log=log)
    process.stdin.write(json.dumps({"address": list(listener.address), "key": key.hex(),
                                    "settings": _settings(folder)}) + "\n")
    process.stdin.flush()
    accepted = {}
    waiting = threading.Thread(target=lambda: accepted.update(connection=listener.accept()),
                               daemon=True)
    waiting.start()
    waiting.join(_START_SECONDS)
    listener.close()
    if "connection" not in accepted:
        _failed(f"didn't start within {_START_SECONDS} seconds")
    _HELPER["connection"] = accepted["connection"]
    for name, (table, rows) in tables.items():
        if "error" in _ask({"run": _view(name, table._columns, rows)}):
            _failed(f"couldn't make its table {name}")
    _check_escaping()


def _failed(what: str) -> None:
    """Stop the helper, and say what went wrong with the last lines its Spark wrote."""
    last = _log_tail()
    _stop_helper()
    raise RuntimeError(four_part_message(
        what=f"The Example database's Spark {what}.",
        why=f"The last lines it wrote were:\n{last}",
        fix=f"Check that Java {_JAVA} is installed and that nothing blocks a local connection "
        "on 127.0.0.1, then run the query again: a new Spark starts.",
        opt_out=None,
    ))


def _log_tail() -> str:
    log = _HELPER.get("log")
    if log is None:
        return "(nothing)"
    log.flush()
    lines = Path(log.name).read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-20:]) or "(nothing)"


def _ask(command: dict) -> dict:
    """Send the helper one command and wait for its reply."""
    connection = _HELPER["connection"]
    try:
        connection.send(command)
        if not connection.poll(_QUERY_SECONDS):
            _failed(f"didn't answer within {_QUERY_SECONDS} seconds")
        return connection.recv()
    except (EOFError, OSError):
        _failed("stopped")
    raise AssertionError  # _failed always raises


def _check_escaping() -> None:
    """Stop unless Spark reads every value of _ESCAPING_CHECK back as it was written."""
    written = ", ".join(f"{hive_text(string(value))} AS v{i}"
                        for i, value in enumerate(_ESCAPING_CHECK))
    reply = _ask({"collect": f"SELECT {written}"})
    read = tuple(reply.get("rows", [()])[0]) if "rows" in reply else None
    if read != _ESCAPING_CHECK:
        _stop_helper()
        raise RuntimeError(four_part_message(
            what="The Example database's Spark reads values differently from how the Toolbox "
            "writes them.",
            why=f"The Toolbox wrote {_ESCAPING_CHECK!r}, and Spark read {read!r}, so its "
            "answers could be wrong without anything saying so.",
            fix="Tell whoever looks after the Toolbox, with this Python's pyspark version.",
            opt_out=None,
        ))


def _view(name: str, columns: dict, rows: list) -> str:
    """The Hive that makes one table a global temporary view of its rows, typed as written."""
    listed = ", ".join(f"`{column}`" for column in columns)
    typed = ", ".join(f"CAST(`{column}` AS {kind}) AS `{column}`"
                      for column, kind in columns.items())
    values = ", ".join("(" + ", ".join(_value(value) for value in row) + ")" for row in rows)
    return (f"CREATE OR REPLACE GLOBAL TEMP VIEW `{name}` AS SELECT {typed} "
            f"FROM VALUES {values} AS t({listed})")


def _value(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return hive_text(string(value))
    return hive_text(number(repr(value), is_float=isinstance(value, float)))


def _environment(folder: Path) -> dict:
    """The helper's environment: yours, less a kernel's Spark, with its own folders and UTC."""
    environment = {key: value for key, value in os.environ.items()
                   if key not in _NOT_PASSED_ON}
    for name in ("TMP", "TEMP", "TMPDIR"):
        environment[name] = str(folder / "tmp")
    environment.update(SPARK_CONF_DIR=str(folder / "conf"), SPARK_LOCAL_IP="127.0.0.1",
                       PYSPARK_PYTHON=sys.executable, TZ="UTC")
    program = _java()
    if program is not None and not os.environ.get("JAVA_HOME"):
        environment["JAVA_HOME"] = str(Path(program).resolve().parent.parent)
    return environment


def _settings(folder: Path) -> dict:
    """The helper's Spark: one core, no catalog on disk, and every file in its own folder."""
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


def _stop_helper() -> None:
    """Stop the helper, if one runs, and delete its folder."""
    connection, process = _HELPER.pop("connection", None), _HELPER.pop("process", None)
    if connection is not None:
        try:
            connection.send({"exit": True})
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
    log = _HELPER.pop("log", None)
    if log is not None:
        log.close()
    folder = _HELPER.pop("folder", None)
    if folder is not None:
        _delete(folder)


def _delete(folder: Path) -> None:
    """Delete the helper's folder, once its Spark lets go of its files: about a second."""
    for _ in range(50):
        shutil.rmtree(folder, ignore_errors=True)
        if not folder.exists():
            return
        time.sleep(0.2)


atexit.register(_stop_helper)


# --- The helper itself: one private Spark, answering until told to stop ---------------------


def _serve() -> None:
    """Start a Spark with the settings sent on stdin; answer each command until told to stop."""
    from multiprocessing.connection import Client

    config = json.loads(sys.stdin.readline())
    connection = Client(tuple(config["address"]), authkey=bytes.fromhex(config["key"]))
    from pyspark.sql import SparkSession

    builder = SparkSession.builder
    for key, value in config["settings"].items():
        builder = builder.config(key, value)
    spark = builder.getOrCreate()
    while True:
        try:
            command = connection.recv()
        except EOFError:
            break
        if "exit" in command:
            break
        try:
            frame = spark.sql(command.get("collect") or command["run"])
            rows = [tuple(row) for row in frame.collect()]
            reply = {"columns": list(frame.columns), "rows": rows}
        except Exception as error:  # noqa: BLE001 - every failure goes back to be shown
            reply = {"error": f"{type(error).__name__}: {str(error)[:3000]}"}
        connection.send(reply)
    spark.stop()
    connection.close()


if __name__ == "__main__":
    _serve()
