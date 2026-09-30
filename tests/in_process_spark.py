"""A Spark in pytest's own Python, for the tests that ask Spark itself how it reads the Hive.

The rest of the suite holds no Spark: the Example database runs its own in a second Python.
Spark Composer's acceptance tests need Spark's parser, its keywords and its functions, so they
build one here, set up as the Example database's is, with every file it writes in pytest's
temporary folder. A module that builds one stops it when it ends.
"""

from __future__ import annotations

import os
import re
import signal
from pathlib import Path
from unittest import mock

import editions
import hive_corpus

# The folder the in-process Spark writes to, the same for the whole run: the Java Spark runs
# on starts with the first Spark, and keeps the folder it started with.
_FOLDER: dict = {}


def spark_folder(tmp_path_factory) -> Path:
    if "folder" not in _FOLDER:
        folder = tmp_path_factory.mktemp("in_process_spark")
        for name in ("warehouse", "local", "tmp", "conf", "java-tmp", "derby", "hive"):
            (folder / name).mkdir()
        _FOLDER["folder"] = folder
    return _FOLDER["folder"]


def in_process_spark(folder: Path, **settings):
    """A Spark in this Python, set up as the Example database's is, `settings` on top."""
    from pyspark.sql import SparkSession
    from sql_composer import engine

    builder = SparkSession.builder
    for key, value in {**engine._settings(folder), **settings}.items():
        builder = builder.config(key, value)
    # pyspark takes over Ctrl+C for its Spark, and keeps it after that Spark stops, which turns
    # a later test's interrupt into an error of its own: this Python keeps its own.
    interrupt = signal.getsignal(signal.SIGINT)
    # The first Spark starts the Java, which takes this Python's environment as it is then.
    with mock.patch.dict(os.environ, engine._environment(folder), clear=True):
        session = builder.getOrCreate()
    signal.signal(signal.SIGINT, interrupt)
    return session


def spark_says(error: Exception) -> str:
    """The first line of what Spark said, without Java's stack of calls."""
    return str(error).strip().splitlines()[0] if str(error).strip() else type(error).__name__


# --- The Hive in a golden corpus ---------------------------------------------------------------

# The words a piece of Hive starts with; a part that starts otherwise is a Toolbox refusal.
_HIVE = ("SELECT", "WITH", "INSERT", "CREATE", "DROP", "DESCRIBE", "SHOW")
# Where one command the warehouse was sent starts, within a part of a warehouse case.
_COMMAND = re.compile(r"\n(?=(?:DESCRIBE|SHOW|SELECT|WITH)\b)")


def hive_texts(edition: editions.Edition) -> list[tuple[str, str]]:
    """Each piece of Hive an Edition's golden holds, as (where it is, its text).

    Where it is names the case and the part, such as "gen:17 Statement 1"; a warehouse case's
    parts are the commands each warehouse function sent. A refusal in their place is left out.
    """
    golden = hive_corpus.cases_in(hive_corpus.golden_path(edition).read_text(encoding="utf-8"))
    found = []
    for case_id, block in golden.items():
        for part in re.split(r"\n(?=-- )", block)[1:]:
            name, _, text = part.removeprefix("-- ").partition("\n")
            if name.endswith(": to_hive"):
                found.append((f"{case_id} {name.removesuffix(': to_hive')}", text.strip()))
            elif case_id.startswith("warehouse:"):
                found += [(f"{case_id} {name} {n}", command.strip())
                          for n, command in enumerate(_COMMAND.split(text.strip()), 1)]
    return [(where, text) for where, text in found if text.startswith(_HIVE)]


# The queries Spark refuses as it should, by their case in the golden, with what it says.
# hive_function writes a call as given, and Spark reads date_format's pattern YYYY, the year a
# week belongs to, as a pattern it no longer takes; sqlglot's rewrite to yyyy changes what the
# pattern means (the hive_function row of DECLARED_DIFFERENCES).
REFUSED = {"edge:hive_function:date_format": "DATETIME_PATTERN_RECOGNITION"}


def wide_table():
    """The table the corpus's width cases read, with a key column as long as each needs."""
    from sql_composer import Table

    keys = {key for _, text in hive_texts(editions.SPARK_COMPOSER)
            for key in re.findall(r"\bwide\.(kx+)\b", text)}
    return Table("ops.wide", columns={**dict.fromkeys(sorted(keys), "string"), "v": "bigint",
                                      "dt": "string"}, date_partition="dt")


_TABLE_READ = re.compile(r"\b(?:FROM|JOIN)\s+(`?\w+`?\.`?\w+`?)")


def tables_read(text: str) -> set[str]:
    """The tables a query reads, by the names it gives them, as ops.jobs."""
    return set(_TABLE_READ.findall(text))


def queries(edition: editions.Edition) -> list[tuple[str, str]]:
    """Each query an Edition's golden holds, as hive_texts gives it: its SELECTs and WITHs."""
    from sql_composer.example_database import _is_query

    return [(where, text) for where, text in hive_texts(edition) if _is_query(text)]
