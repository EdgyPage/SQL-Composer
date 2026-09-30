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
import socket
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
# The Javas the Example database's Spark starts on: both supported Sparks document Java 17,
# and Spark 4.0 documents 21 as well; the Hadoop inside Spark can't start on Java 23 or newer.
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


# The java program's name, in JAVA_HOME's bin folder.
_JAVA_PROGRAM = "java.exe" if os.name == "nt" else "java"


def _java() -> tuple[str | None, str]:
    """The java program Spark would run, or None and why there is none."""
    home = os.environ.get("JAVA_HOME")
    if home:
        program = Path(home) / "bin" / _JAVA_PROGRAM
        if program.is_file():
            return str(program), ""
        return None, f"JAVA_HOME is {home}, which has no bin{os.sep}{_JAVA_PROGRAM} in it"
    program = shutil.which("java")
    return program, "no java program was found (JAVA_HOME isn't set, and none is on PATH)"


# What each java program said of itself, by its path and when that last changed. A Java that
# couldn't say is asked again next time: what stopped it may have gone.
_JAVAS_ASKED: dict = {}


def _java_said(program: str) -> tuple[int | None, str | None, str]:
    """A java program's main version, such as 17, its own folder, and what stopped it saying.

    The version is None when it doesn't say one. Its folder is the Java's own, even when the
    program found is a script that runs it.
    """
    try:
        asked = (program, os.stat(program).st_mtime_ns)
    except OSError as error:
        return None, None, str(error)
    if asked not in _JAVAS_ASKED:
        said = _ask_java(program)
        if said[0] is None:
            return said
        _JAVAS_ASKED[asked] = said
    return _JAVAS_ASKED[asked]


def _ask_java(program: str) -> tuple[int | None, str | None, str]:
    try:
        # Its settings name its folder; -XX:-UsePerfData leaves no file in the temporary folder.
        done = subprocess.run([program, "-XX:-UsePerfData", "-XshowSettings:properties",
                               "-version"], capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return None, None, "it didn't answer within 60 seconds"
    except OSError as error:
        return None, None, str(error)
    said = done.stderr + done.stdout
    version = re.search(r'version "(\d+)(?:\.(\d+))?', said)
    if version is None:
        lines = [line.strip() for line in said.splitlines()
                 if line.strip() and not line.startswith("Picked up")]
        return None, None, ". ".join(line.rstrip(".") for line in lines[:2])
    home = re.search(r"^\s*java\.home = (.+?)\s*$", said, re.MULTILINE)
    # Java 8 and older call themselves 1.8 and so on.
    number = int(version[2]) if version[1] == "1" and version[2] else int(version[1])
    return number, home[1] if home else None, ""


# The Javas the Example database's Spark starts on, and how to point this Python at one, to paste
# into the notebook; no restart is needed.
_JAVAS = f"Java {_JAVA_NEEDED} to {_JAVA_NEWEST}"
_POINT_AT_JAVA = ('import os; os.environ["JAVA_HOME"] = r"<the Java\'s folder, the one with '
                  'bin in it>". No restart is needed.')
# What the script that starts Spark on Windows can't take in the temporary folder's path.
_LAUNCHER_CANT_TAKE = "&()!^;,= "


def _lacking() -> tuple[str, str] | None:
    """What the Example database's Spark lacks here, and how to give it that, or None."""
    return _spark_home_lacking() or _temporary_folder_lacking() or _java_lacking()


def _spark_home_lacking() -> tuple[str, str] | None:
    spark_home = os.environ.get("SPARK_HOME")
    if not spark_home:
        return None
    programs = Path(spark_home) / "bin"
    pyspark = _pyspark_version()
    if not ((programs / "spark-submit").is_file() or (programs / "spark-submit.cmd").is_file()):
        holds = "which has no Spark in it"
    else:
        found, wanted = _spark_in(Path(spark_home)), _numbers(pyspark)
        # Only a Spark that plainly isn't pyspark's own is refused: a work Spark's jars may be
        # named in ways this doesn't know.
        if found is None or wanted is None or found[:2] == wanted[:2]:
            return None
        holds = f"which holds Spark {_dotted(found)}, and this Python's pyspark is {pyspark}"
    return (f"can't start: SPARK_HOME is {spark_home}, {holds}",
            f"Set SPARK_HOME to the folder of a Spark {pyspark} install, the one with bin in "
            "it, or take it away so pyspark uses the Spark it comes with: import os; "
            'os.environ.pop("SPARK_HOME"). Your own `spark`, already running, isn\'t changed, '
            "and no restart is needed.")


def _spark_in(folder: Path) -> tuple | None:
    """The version of the Spark a folder holds, by its core jar, or None when that isn't found."""
    for jar in sorted((folder / "jars").glob("spark-core_*.jar")):
        found = re.match(r"spark-core_[\d.]+-(\d+\.\d+\.\d+)", jar.name)
        if found:
            return _numbers(found[1])
    return None


def _temporary_folder_lacking() -> tuple[str, str] | None:
    """On Windows, a temporary folder whose path the script that starts Spark can't take."""
    if os.name != "nt":
        return None
    # The path Spark is given: the folder's short name, which has no space, where Windows has one.
    path = _temporary_folder()
    characters = " ".join(char for char in _LAUNCHER_CANT_TAKE if char != " " and char in path)
    named = " and ".join(filter(None, (characters, "a space" if " " in path else "")))
    if not named:
        return None
    return (f"can't start: the temporary folder Python uses, {tempfile.gettempdir()}, has "
            f"{named} in its path, which the script that starts Spark on Windows can't take",
            "Make a folder whose path has only letters, digits, - and _ in it, such as "
            "C:\\Temp, and point Python at it: import tempfile; tempfile.tempdir = "
            'r"C:\\Temp". No restart is needed.')


def _java_lacking() -> tuple[str, str] | None:
    program, missing = _java()
    needs = f"needs {_JAVAS}"
    install = (f"Install Java {_JAVA_NEEDED}, then set JAVA_HOME to its folder: "
               f"{_POINT_AT_JAVA} If you can't install it, ask whoever looks after your "
               "environment.")
    if program is None:
        found = f"{needs}, and {missing}"
        if os.environ.get("JAVA_HOME"):
            return found, (f"Set JAVA_HOME to the folder of a {_JAVAS} you have: "
                           f"{_POINT_AT_JAVA} If you have none, install Java {_JAVA_NEEDED} "
                           "first.")
        return found, install
    version, _, said = _java_said(program)
    if version is not None and _JAVA_NEEDED <= version <= _JAVA_NEWEST:
        return None
    if version is None:
        return (f"{needs}, and {program} didn't say which Java it is"
                + (f": it said {said.rstrip('.')}" if said else ""),
                f"Run {program} -version in a terminal to see what stops it, or point this "
                f"Python at another {_JAVAS}: {_POINT_AT_JAVA}")
    return f"{needs}, and {program} is Java {version}", install


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
# files, which takes about a second, and how long a stop waits for the process to stop its
# Spark.
_DELETE_SECONDS = 10
_STOP_SECONDS = 15
# What a kernel started by spark-submit, or a Spark machine, carries, which would make the
# process join that kernel's Spark, read its settings or its Hadoop's, or put its files
# elsewhere.
_NOT_PASSED_ON = ("PYSPARK_GATEWAY_PORT", "PYSPARK_GATEWAY_SECRET", "PYSPARK_SUBMIT_ARGS",
                  "HADOOP_CONF_DIR", "YARN_CONF_DIR", "SPARK_DIST_CLASSPATH",
                  "_PYSPARK_DRIVER_CONN_INFO_PATH", "SPARK_CONNECT_MODE", "SPARK_REMOTE",
                  "SPARK_LOCAL_DIRS", "SPARK_EXECUTOR_DIRS", "LOCAL_DIRS")
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
# Java is told its temporary folder where TMP doesn't tell it: everywhere but Windows.
_JAVA_TMP = os.name != "nt"
# The process runs apart from your Python's console: on Windows with a hidden console of its
# own, so no window opens and Ctrl+C in yours doesn't reach its Java; elsewhere in a session
# of its own, which is ended as a whole.
_APART = ({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt"
          else {"start_new_session": True})

# The running Spark: its process; on Windows, the job holding everything the process starts;
# the socket it connects back to and the key it proves; its connection; its folder, its log and
# the folder's lock; and "ready" once it has started, made its tables and checked its escaping.
_SPARK: dict = {}
# One query at a time: a reply goes to whoever asked, even with queries from several threads.
_ONE_AT_A_TIME = threading.Lock()
# Set as this Python stops, so no Spark is started while it does.
_STOPPING = threading.Event()
# One stop at a time, so a stop from another thread can't take half of what this one ends.
_ONE_STOP_AT_A_TIME = threading.Lock()


class _Gone(Exception):
    """The process, or its Spark, has stopped: this Spark can't answer."""


def run_query(text: str, tables: dict) -> tuple[list, list]:
    """Run a query's Hive on the Example database's Spark: its column names, and its rows.

    `tables` maps each table's short name to its Table reference and its rows. Its Spark starts
    on the first query, and again if it has stopped; a query whose Spark stopped under it is
    given once to a new one.
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
    if "unheld" in reply:
        raise RuntimeError(_unheld(reply["unheld"]))
    return reply["columns"], [tuple(row) for row in reply["rows"]]


def _answer(text: str, tables: dict) -> dict:
    """The reply to a query, starting a Spark first, and again if the one there stops.

    While your Python stops, no Spark is started, and the one there is left for the stop that
    is under way to end.
    """
    for _ in range(2):
        if _STOPPING.is_set():
            _python_stopping()
        process = _SPARK.get("process")
        if not _SPARK.get("ready") or process is None or process.poll() is not None:
            _stop_spark()
            _start_spark(tables)
        try:
            return _ask(text)
        except _Gone:
            if not _STOPPING.is_set():
                _stop_spark(wait=False)
    # Outside the except, so the message stands alone in the traceback.
    _stopped_twice()


def _spark_says(said: str) -> str:
    """The part of Spark's message that names the problem, with no full stop at its end.

    It is the message's first line, less its SQLSTATE, the place in the Hive, and Spark's
    advice to change one of its settings or to use one of its try_ functions: the Example
    database's Spark takes no settings, and the Toolbox wraps none of Spark's try_ functions.
    """
    lines = said.strip().splitlines() or ["(Spark said nothing)"]
    first = re.sub(r"\s*SQLSTATE:.*$", "", lines[0])
    first = re.sub(r"[.;\s]*;\s*line \d+ pos \d+.*$", "", first)
    first = re.sub(r"[,;]?\s*(?:please |if necessary )?set ['\"]?spark\.sql\.[\w.]+['\"]?"
                   r"[^.]*\.?", "", first, flags=re.IGNORECASE)
    kept = [sentence for sentence in re.split(r"(?<=\.)\s+(?=[A-Z\[])", first)
            if not re.search(r"[`']try_", sentence)]
    return " ".join(kept).rstrip(" ;.,") or first.rstrip(" ;.,")


def _refused(said: str) -> str:
    """Spark's refusal of a query, with what Spark said about it."""
    return four_part_message(
        what=f"Spark couldn't run this Hive on the Example database: {_spark_says(said)}.",
        why="Your warehouse's Spark would refuse this Hive too. For a few mistakes, such as "
        "text where a date goes, a Spark set up less strictly gives None instead of refusing: "
        "a wrong answer with no error. Either way, the Statement needs changing.",
        fix="Spark's message names the problem: usually a table, column or hive_function(...) "
        "name spelt wrong (print a Table reference, such as example_database.jobs, to see its "
        "columns), a value of the wrong type, such as text given where a date goes, or a "
        "calculation with no answer, such as dividing by zero. If none of these, and "
        "statement(...) built the Hive, please report it with the Statement to whoever looks "
        "after the Toolbox.",
        opt_out=None,
    )


def _unheld(said: str) -> str:
    """What Spark gave back that Python couldn't take."""
    return four_part_message(
        what="The Example database's Spark ran this Hive, but Python couldn't take what it gave "
        f"back: {said.rstrip('.')}.",
        why="Python needs every value to make the DataFrame, so none can be made.",
        fix="Change the Statement so it gives back plain numbers, text, dates and times. "
        "Python's dates end at the year 9999, and on Windows it can't take a time before 1970.",
        opt_out=None,
    )


def _python_stopping() -> NoReturn:
    """Say that no query runs while your Python stops."""
    raise RuntimeError(four_part_message(
        what="The Example database runs no query while your Python is stopping.",
        why="Its Spark is stopped along with your Python, so this query got no answer.",
        fix="None is needed: run the query again once your kernel has started again.",
        opt_out=None,
    ))


def _start_spark(tables: dict) -> None:
    """Start a Spark in a new temporary folder, make its tables, and check its escaping.

    Interrupted, as by a notebook's Interrupt button, it stops that Spark, which would otherwise
    give its answers to the queries after, and keeps its log. A Spark is used only once all this
    is done: one left half started is stopped at the next query.
    """
    if _STOPPING.is_set():
        _python_stopping()
    _delete_left_over()
    print("Note: starting the Example database's own Spark, apart from yours. This query takes "
          "about 15 seconds, later ones about a second.", file=sys.stderr)
    try:
        _launch()
        _connect()
        _make_tables(tables)
        _check_escaping()
    except _Gone:
        _not_started("quit while it was starting")
    except KeyboardInterrupt:
        _interrupted()
        raise
    _SPARK["ready"] = True


def _interrupted() -> None:
    """Stop a Spark whose start was interrupted, keeping its log, in case the start hung."""
    kept = _keep(_end_and_read_log(wait=False))
    _stop_spark(wait=False)
    if kept is not None:
        print(f"Note: the Example database's Spark was stopped as it started. What it wrote is "
              f"in {kept}.", file=sys.stderr)


def _launch() -> None:
    """Start the process in a new folder, with everything it starts held so it can be ended."""
    folder = Path(tempfile.mkdtemp(prefix=_FOLDER_PREFIX, dir=_temporary_folder()))
    # Held for as long as this Spark runs, so no other Python deletes its folder.
    _SPARK.update(folder=folder, lock=_hold(folder / _IN_USE))
    for name in ("warehouse", "local", "tmp", "conf") + (("java-tmp",) if _JAVA_TMP else ()):
        (folder / name).mkdir()
    key = os.urandom(32)
    _SPARK["listener"] = listener = socket.create_server(("127.0.0.1", 0))
    listener.settimeout(_LOOK_EVERY)
    # The process writes to it while it runs; _stop_spark closes it once the process stops.
    _SPARK["log"] = log = open(folder / "spark.log", "w", encoding="utf-8")
    _SPARK["process"] = process = subprocess.Popen(
        [sys.executable, "-B", str(Path(__file__).resolve())], cwd=folder,
        env=_environment(folder), stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT,
        text=True, **_APART)
    # Before the process is told anything, so everything it starts is held too.
    _SPARK["job"] = _job_holding(process)
    _SPARK["key"] = key
    try:
        process.stdin.write(json.dumps({"address": list(listener.getsockname()),
                                        "key": key.hex(), "settings": _settings(folder)}) + "\n")
        process.stdin.flush()
    except OSError as error:  # it has stopped already
        raise _Gone from error


def _make_tables(tables: dict) -> None:
    for name, (table, rows) in tables.items():
        reply = _ask(_table_hive(name, table._columns, rows))
        if "refused" in reply:
            _toolbox_failed(f"couldn't make its table {name}: {_spark_says(reply['refused'])}.")


def _connect() -> None:
    """Wait for the process to connect back and its Spark to start, within _START_SECONDS."""
    deadline = time.monotonic() + _START_SECONDS
    accepted: dict = {}
    listener = _SPARK["listener"]
    threading.Thread(target=_accept, args=(listener, _SPARK["key"], accepted),
                     daemon=True).start()
    while "connection" not in accepted:
        _still_starting(deadline)
        time.sleep(_LOOK_EVERY)
    listener.close()
    _SPARK["connection"] = connection = accepted["connection"]
    try:
        while not connection.poll(_LOOK_EVERY):
            _still_starting(deadline)
        started = connection.recv()
    except (EOFError, OSError) as error:
        raise _Gone from error
    if "stopped" in started:
        raise _Gone


def _accept(listener: socket.socket, key: bytes, accepted: dict) -> None:
    """Take the process's connection back, checking each that comes on a thread of its own.

    So a connection that comes first and says nothing, or has the wrong key, holds nothing up.
    It ends when the start closes the socket.
    """
    while "connection" not in accepted:
        try:
            knocking, _ = listener.accept()
        except TimeoutError:
            continue
        except OSError:
            return
        threading.Thread(target=_check_key, args=(knocking, key, accepted),
                         daemon=True).start()


def _check_key(knocking: socket.socket, key: bytes, accepted: dict) -> None:
    """Keep a connection that proves it has the key; close any other."""
    from multiprocessing.connection import Connection, answer_challenge, deliver_challenge

    knocking.setblocking(True)
    connection = Connection(knocking.detach())
    try:
        deliver_challenge(connection, key)
        answer_challenge(connection, key)
    except Exception:  # noqa: BLE001 - not the process: no key, or no answer at all
        connection.close()
        return
    if accepted.setdefault("connection", connection) is not connection:
        connection.close()


def _still_starting(deadline: float) -> None:
    """Stop waiting for a start when the process has stopped, or at the deadline."""
    if _SPARK["process"].poll() is not None:
        raise _Gone
    if time.monotonic() > deadline:
        _not_started(f"didn't start within {_START_SECONDS} seconds", busy=True)


def _not_started(what: str, busy: bool = False) -> NoReturn:
    """End the Spark that couldn't start, keep its log, and say so, with what most likely says
    why."""
    log_text = _end_and_read_log(wait=not busy)
    kept = _keep(log_text)
    _stop_spark(wait=False)
    last = _last_words(log_text)
    said = (f" What it wrote that most likely says why: {last.rstrip('.')}." if last
            else " It wrote nothing that says why." if log_text.strip() else " It wrote nothing.")
    spark_home = os.environ.get("SPARK_HOME")
    started = f" It was started from the Spark in SPARK_HOME, {spark_home}." if spark_home else ""
    show = (f"show its log, {kept}, to whoever looks after your environment" if kept
            else "tell whoever looks after your environment")
    raise RuntimeError(four_part_message(
        what=f"The Example database's Spark {what}.{said}{started}",
        why="The Example database runs each query on that Spark, so none can run until one "
        "starts. to_hive(...) still writes every Statement's Hive.",
        fix=("A busy computer can take longer: close other programs, then run the query again."
             if busy else "Run the query again: another Spark starts.")
        + f" If it fails the same way, {show}.",
        opt_out=None,
    )) from None


def _end_and_read_log(wait: bool) -> str:
    """End the process and all it started, so its log is whole, then read the log.

    With wait, the process is first given time to finish writing, as one that has just said it
    quit needs.
    """
    process = _SPARK.pop("process", None)
    if process is not None:
        _end(process, _SPARK.pop("job", None), wait)
    log = _SPARK.get("log")
    if log is None:
        return ""
    log.flush()
    return Path(log.name).read_text(encoding="utf-8", errors="replace")


def _keep(log_text: str) -> Path | None:
    """Keep a failed start's log in the temporary folder, under this user's own name."""
    user = re.sub(r"\W", "_", os.environ.get("USERNAME") or os.environ.get("USER") or "you")
    kept = Path(_temporary_folder()) / f"spark_composer_failed_start_{user}.log"
    try:
        kept.write_text(log_text, encoding="utf-8")
    except OSError:
        return None
    return kept


# The lines a start writes that say nothing about why it failed: what Spark and Java write as
# a start goes well, the lines around a Python traceback, and pyspark's own word that the Java
# quit, which the message says already.
_ROUTINE = re.compile(r'\d\d/\d\d/\d\d \S+ (WARN|INFO)|\{"ts"|Using Spark\'s|Setting default|'
                      r"To adjust|WARNING:|Picked up _?JAVA|Traceback|During handling|"
                      r"The above exception|.*\[JAVA_GATEWAY_EXITED\]")
# A line that names an error, as Java's and Python's errors do.
_AN_ERROR = re.compile(r"(Exception|Error)\b")


def _last_words(log_text: str) -> str:
    """The line of a failed start's log that most likely says why, or "" when none does.

    Of the lines that are neither routine nor part of a list of calls, as an indented line of a
    Java or Python traceback is, it is the last that names an error, such as a Java exception at
    the root of it; else the last of them, such as the launcher's own complaint.
    """
    telling = [line.strip().removeprefix(": ") for line in log_text.splitlines()
               if line.strip() and not line[0].isspace() and not _ROUTINE.match(line)]
    errors = [line for line in telling if _AN_ERROR.search(line)]
    return (errors or telling or [""])[-1]


def _toolbox_failed(what: str) -> NoReturn:
    """Stop a Spark that refused the Toolbox's own start, and say it is the Toolbox's bug."""
    _stop_spark()
    raise RuntimeError(four_part_message(
        what=f"The Example database's Spark {what}",
        why="This is a bug in the Toolbox, not in your Statement: the Hive that Spark refused "
        "is the Toolbox's own, so no query can run on the Example database here.",
        fix="Please report this message to whoever looks after the Toolbox, with the pyspark "
        f"version this Python has, {_pyspark_version()}. to_hive(...) still writes every "
        "Statement's Hive.",
        opt_out=None,
    ))


def _pyspark_version() -> str:
    import pyspark

    return getattr(pyspark, "__version__", "unknown")


def _ask(sql: str) -> dict:
    """Send one piece of Hive and wait for the reply: its columns and rows, or what went wrong.

    When the process, or its Spark, has stopped, it raises _Gone. When the answer doesn't come
    in time, or the wait is interrupted, the Spark is stopped, so its answer can't reach the next
    query.
    """
    connection, process = _SPARK.get("connection"), _SPARK.get("process")
    if connection is None or process is None:  # a stop from another thread has just ended it
        raise _Gone
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


def _stopped_twice() -> NoReturn:
    """Say that the query stopped its Spark, and a second one given it again."""
    raise RuntimeError(four_part_message(
        what="The Example database's Spark stopped while running this query. A new Spark was "
        "given the query again, and it stopped too, so the query itself seems to stop Spark.",
        why="The query got no answer, so no DataFrame can be made. The next query starts "
        "another Spark.",
        fix="Change the query. If statement(...) built it, show it to whoever looks after the "
        "Toolbox.",
        opt_out=None,
    ))


def _too_slow() -> NoReturn:
    """Say that a query took longer than _QUERY_SECONDS, so its Spark was stopped."""
    raise RuntimeError(four_part_message(
        what=f"The Example database's Spark didn't answer within {_QUERY_SECONDS} seconds.",
        why="A late answer would have been given to your next query instead, so that Spark was "
        "stopped. The next query starts another.",
        fix="The Example database's tables hold a few rows each, so a query on them takes "
        "about a second; one that runs for minutes joins more rows than it means to. Check its "
        "JOINs and CROSS_JOINs, then run it again.",
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
                        f"{_spark_says(reply['refused'])}.")
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
    C:\\Users\\John Smith. A folder given as relative is taken from where this Python runs.
    """
    base = os.path.abspath(tempfile.gettempdir())
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
        # The Java's own folder, which a script found on PATH in its place doesn't show:
        # Spark's Windows launcher can't run a java that is a script.
        _, home, _ = _java_said(program)
        if home:
            environment["JAVA_HOME"] = home
    return environment


def _settings(folder: Path) -> dict:
    """Its Spark: one core, no catalog on disk, and every file in its own folder, on this
    computer's own disk."""
    posix = folder.as_posix()
    settings = {
        "spark.master": "local[1]", "spark.app.name": "spark_composer_example_database",
        "spark.sql.catalogImplementation": "in-memory", "spark.sql.globalTempDatabase": "ops",
        "spark.sql.shuffle.partitions": "1", "spark.default.parallelism": "1",
        "spark.ui.enabled": "false", "spark.ui.showConsoleProgress": "false",
        "spark.sql.session.timeZone": "UTC", "spark.driver.memory": "512m",
        "spark.driver.host": "127.0.0.1", "spark.driver.bindAddress": "127.0.0.1",
        "spark.sql.warehouse.dir": f"{posix}/warehouse", "spark.local.dir": f"{posix}/local",
        "spark.hadoop.fs.defaultFS": "file:///",
        "spark.sql.execution.arrow.pyspark.enabled": "false",
        "spark.sql.runSQLOnFiles": "false",
        "spark.sql.ansi.enabled": "true", "spark.sql.parser.escapedStringLiterals": "false",
    }
    # Java takes its temporary folder from TMP on Windows, where the launcher would mangle a
    # path with a letter outside English in this setting. -XX:-UsePerfData stops Java leaving
    # a file in the system's temporary folder as it is ended.
    if _JAVA_TMP:
        settings["spark.driver.extraJavaOptions"] = (f'-Djava.io.tmpdir="{posix}/java-tmp" '
                                                     "-XX:-UsePerfData")
    return settings


def _stop_spark(wait: bool = True) -> None:
    """Stop the Spark, if one runs, and delete its folder.

    With wait, the process is told to stop its Spark, and is given time to; either way,
    everything it started, its Spark's Java included, is ended after.
    """
    with _ONE_STOP_AT_A_TIME:
        _stop_what_runs(wait)


def _stop_what_runs(wait: bool) -> None:
    _SPARK.pop("ready", None)
    connection, process = _SPARK.pop("connection", None), _SPARK.pop("process", None)
    job = _SPARK.pop("job", None)
    if connection is not None:
        with contextlib.suppress(OSError):
            if wait:
                connection.send(None)
        connection.close()
    if process is not None:
        _end(process, job, wait)
    elif job is not None:
        _close_job(job)
    for name in ("listener", "log", "lock"):
        held = _SPARK.pop(name, None)
        if held is not None:
            held.close()
    _SPARK.pop("key", None)
    folder = _SPARK.pop("folder", None)
    if folder is not None:
        _remove(folder, tries=int(_DELETE_SECONDS / _LOOK_EVERY))


def _end(process: subprocess.Popen, job, wait: bool) -> None:
    """End the process and everything it started, and let go of its job: with wait, after
    letting it stop."""
    if wait:
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.wait(_STOP_SECONDS)
    _kill_everything_started_by(process, job)
    with contextlib.suppress(OSError):
        process.stdin.close()
    with contextlib.suppress(subprocess.TimeoutExpired):
        process.wait(30)
    if job is not None:
        _close_job(job)


def _kill_everything_started_by(process: subprocess.Popen, job) -> None:
    """Kill a process and every process it started, even one it is starting as they die.

    On Windows they are all in the job that holds the process; elsewhere they are all in the
    session the process leads.
    """
    if job is not None:
        _terminate_job(job)
    elif os.name == "nt":
        # Without a job, as where Windows wouldn't give one, the tree of its children.
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)],
                       capture_output=True, check=False)
    else:
        import signal

        with contextlib.suppress(OSError):
            os.killpg(process.pid, signal.SIGKILL)
    with contextlib.suppress(OSError):
        process.kill()


def _stop_as_python_stops() -> None:
    """Stop the Spark as this Python stops: at once, if another thread's query holds it."""
    _STOPPING.set()
    _stop_spark(wait=not _ONE_AT_A_TIME.locked())


atexit.register(_stop_as_python_stops)


# --- The Example database's Spark: the Windows job that holds its processes -------------------

# On Windows, a job holds the process and every process it starts; ending the job ends them
# all, and so does this Python stopping, however it stops, since the job goes with its handle.
_JOB_LIMIT_KILL_ON_CLOSE = 0x2000
_JOB_EXTENDED_LIMITS = 9
_PROCESS_SET_QUOTA_AND_TERMINATE = 0x0101


@functools.cache
def _kernel32():
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    kernel32.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                                 wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    kernel32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    return kernel32


def _job_limits():
    """The job's limits, as Windows lays them out, set to end every process in the job as
    its last handle closes."""
    import ctypes
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [("user_time", ctypes.c_int64), ("job_user_time", ctypes.c_int64),
                    ("flags", wintypes.DWORD), ("min_working_set", ctypes.c_size_t),
                    ("max_working_set", ctypes.c_size_t), ("process_limit", wintypes.DWORD),
                    ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                    ("scheduling", wintypes.DWORD)]

    class Extended(ctypes.Structure):
        _fields_ = [("basic", Basic), ("io", ctypes.c_ulonglong * 6),
                    ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                    ("peak_process_memory", ctypes.c_size_t),
                    ("peak_job_memory", ctypes.c_size_t)]

    limits = Extended()
    limits.basic.flags = _JOB_LIMIT_KILL_ON_CLOSE
    return limits


def _job_holding(process: subprocess.Popen):
    """On Windows, a new job holding the process; elsewhere None."""
    if os.name != "nt":
        return None
    import ctypes

    kernel32 = _kernel32()
    job = kernel32.CreateJobObjectW(None, None)
    limits = _job_limits()
    kernel32.SetInformationJobObject(job, _JOB_EXTENDED_LIMITS, ctypes.byref(limits),
                                     ctypes.sizeof(limits))
    handle = kernel32.OpenProcess(_PROCESS_SET_QUOTA_AND_TERMINATE, False, process.pid)
    held = kernel32.AssignProcessToJobObject(job, handle)
    kernel32.CloseHandle(handle)
    if not held:
        kernel32.CloseHandle(job)
        return None
    return job


def _terminate_job(job) -> None:
    _kernel32().TerminateJobObject(job, 1)


def _close_job(job) -> None:
    _terminate_job(job)
    _kernel32().CloseHandle(job)


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
    lock goes with it, however it stops.
    """
    now = time.time()
    for folder in Path(_temporary_folder()).glob(f"{_FOLDER_PREFIX}*"):
        if _left_over(folder, now):
            _remove(folder)


def _left_over(folder: Path, now: float) -> bool:
    """Whether a Spark's folder is over a minute old and no Python holds it.

    A folder with no in-use file is left over too, as when a Python stopped between making the
    folder and that file. Taking the lock only tests it; it is given up at once.
    """
    in_use = folder / _IN_USE
    try:
        if not in_use.exists():
            return now - folder.stat().st_mtime >= _LEFT_OVER_SECONDS
        if now - in_use.stat().st_mtime < _LEFT_OVER_SECONDS:
            return False
        _hold(in_use).close()
    except OSError:
        return False
    return True


# --- The process itself: one private Spark, answering until told to stop -----------------


# What the process sends your Python: {"started": True} once its Spark has started; for each
# piece of Hive, {"columns": [...], "rows": [...]}, {"refused": what Spark said} or {"unheld":
# what Python said}; and {"stopped": True} when its Spark has gone, after which it stops. Your
# Python sends it each piece of Hive, and None to stop.


def _serve() -> None:
    """Start a Spark with the settings sent on stdin, then answer each piece of Hive sent.

    A query Spark refuses, or whose values Python can't take, is answered so, unless its Spark
    has gone, its Java unreachable or its SparkContext stopped: then it says it has stopped,
    and stops, and your Python gives the query once to a new Spark. It stops when told to
    (None), when the connection closes, and at once when your Python stops, even mid-query: its
    pipe to this process's stdin closes then. On Windows it watches that pipe only once its
    Spark has started; until then the job that holds it ends it with your Python.
    """
    import traceback
    from multiprocessing.connection import Client

    config = json.loads(sys.stdin.readline())
    connection = Client(tuple(config["address"]), authkey=bytes.fromhex(config["key"]))
    # On Windows, a thread waiting on stdin stops Spark from starting the Java it runs on.
    if os.name != "nt":
        _watch_your_python()
    try:
        from pyspark import java_gateway
        from pyspark.sql import SparkSession

        # pyspark 3.5.0 and 4.0.4 both start Spark's launcher through this name.
        java_gateway.Popen = _Launcher
        builder = SparkSession.builder
        for key, value in config["settings"].items():
            builder = builder.config(key, value)
        spark = builder.getOrCreate()
    except Exception:  # noqa: BLE001 - a Spark that can't start says why in its log, and stops
        traceback.print_exc()
        sys.stdout.flush()
        connection.send({"stopped": True})
        return
    if os.name == "nt":
        _watch_your_python()
    connection.send({"started": True})
    while True:
        try:
            sql = connection.recv()
        except (EOFError, OSError):
            break
        if sql is None:
            break
        reply = _run(spark, sql)
        connection.send(reply)
        if "stopped" in reply:
            break
    spark.stop()
    connection.close()


def _run(spark, sql: str) -> dict:
    """What running one piece of Hive gives: its columns and rows, or what went wrong."""
    try:
        frame = spark.sql(sql)
        return {"columns": list(frame.columns), "rows": [tuple(row) for row in frame.collect()]}
    except Exception as error:  # noqa: BLE001 - every failure is answered
        names = {kind.__name__ for kind in type(error).__mro__}
        # A query that stops Spark, such as one that ends its Java, fails with an error of its
        # own as Spark shuts down; Spark's being gone is what matters.
        if not _still_there(spark):
            return {"stopped": True}
        # What Spark's Java refused, which pyspark raises as a CapturedException, or leaves as
        # the Java error it is. pyspark's other errors are its own, raised in this Python.
        if "CapturedException" in names or getattr(error, "java_exception", None) is not None:
            return {"refused": _what_spark_said(error)}
        # Py4J, which pyspark talks to its Java through, raises its own errors, or the
        # connection's, when that Java has gone.
        if "Py4JError" in names or isinstance(error, (ConnectionError, EOFError)):
            return {"stopped": True}
        return {"unheld": f"{type(error).__name__}: {error}"}


def _still_there(spark) -> bool:
    """Whether this Spark still runs: its Java answers, and hasn't stopped its SparkContext.

    It asks through a private part of pyspark, there in 3.5.0 and 4.0.4 alike.
    """
    try:
        return not spark.sparkContext._jsc.sc().isStopped()
    except Exception:  # noqa: BLE001 - its Java can't answer
        return False


def _watch_your_python() -> None:
    threading.Thread(target=_stop_with_your_python, daemon=True).start()


def _stop_with_your_python() -> None:
    """Exit as soon as your Python stops, however it stopped, taking this Spark with it.

    Your Python's end of the pipe to this process's stdin closes when it stops, and the Java
    this Spark runs on follows this process within a second.
    """
    sys.stdin.read()
    os._exit(0)


class _Launcher(subprocess.Popen):
    """Spark's launcher as pyspark starts it, never taken for still running once it has quit.

    pyspark waits for its launcher to start the Java its Spark runs on, and takes an exit code
    of 0 for still running. Spark's Windows launcher quits with 0 when that Java can't start,
    so pyspark would wait for ever; this gives 1 instead, and pyspark says the Java quit.
    """

    def poll(self):
        code = super().poll()
        return 1 if code == 0 else code


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
            said = (cause.getMessage() or "").strip()
            name = cause.getClass().getSimpleName()
            return said if said.startswith("[") else ": ".join(filter(None, (name, said)))
    except Exception:  # noqa: BLE001 - Java can't say more; Python's text says enough
        pass
    return str(error)


if __name__ == "__main__":
    _serve()
