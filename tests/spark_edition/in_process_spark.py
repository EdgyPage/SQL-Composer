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
from typing import NamedTuple
from unittest import mock

import editions
import hive_corpus

# Spark can't make a database, or a Hive table, on Windows without winutils.
ON_WINDOWS = os.name == "nt"
NEEDS_WINUTILS = ("Spark can't make a database on Windows without winutils, so this runs on "
                  "Linux, as in CI")

# The folder the in-process Spark writes to, the same for the whole run: the Java Spark runs
# on starts with the first Spark, and keeps the folder it started with.
_FOLDER: dict = {}


def spark_folder(tmp_path_factory) -> Path:
    """The in-process Spark's folder, with the folders the Example database's settings name,
    and Derby's and Hive's."""
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


def parse(spark, text: str) -> None:
    """Have Spark's parser read a piece of Hive, without running it."""
    spark._jsparkSession.sessionState().sqlParser().parsePlan(text)


def spark_says(error: Exception) -> str:
    """The first line of what Spark said, without Java's stack of calls."""
    return str(error).strip().splitlines()[0] if str(error).strip() else type(error).__name__


# --- The Hive in a golden corpus ---------------------------------------------------------------


class Hive(NamedTuple):
    """One piece of Hive in a golden: its case, the part of the case it is, and its text."""

    case: str
    part: str
    text: str

    @property
    def where(self) -> str:
        return f"{self.case} {self.part}"


# The words a piece of Hive starts with; a part that starts otherwise is a Toolbox refusal.
_HIVE_STARTS = ("SELECT", "WITH", "INSERT", "CREATE", "DROP", "DESCRIBE", "SHOW")
# Where one command the warehouse was sent starts, within a part of a warehouse case.
_COMMAND = re.compile(r"\n(?=(?:DESCRIBE|SHOW|SELECT|WITH)\b)")


def hive_texts(edition: editions.Edition) -> list[Hive]:
    """Each piece of Hive an Edition's golden holds.

    A warehouse case's parts are the commands that write_table_reference, check_table_reference
    and check_key each sent. A refusal in a piece of Hive's place is left out.
    """
    golden = hive_corpus.cases_in(hive_corpus.golden_path(edition).read_text(encoding="utf-8"))
    found = []
    for case, block in golden.items():
        for part in re.split(r"\n(?=-- )", block)[1:]:
            name, _, text = part.removeprefix("-- ").partition("\n")
            if name.endswith(": to_hive"):
                found.append(Hive(case, name.removesuffix(": to_hive"), text.strip()))
            elif case.startswith("warehouse:"):
                found += [Hive(case, f"{name} {n}", command.strip())
                          for n, command in enumerate(_COMMAND.split(text.strip()), 1)]
    return [hive for hive in found if hive.text.startswith(_HIVE_STARTS)]


# The queries Spark refuses as it should, by their case in the golden, with what it says.
# hive_function writes a call as given, and Spark reads date_format's pattern YYYY, the year a
# week belongs to, as a pattern it no longer takes; sqlglot's rewrite to yyyy changes what the
# pattern means (the hive_function row of DECLARED_DIFFERENCES).
REFUSED = {"edge:hive_function:date_format": "DATETIME_PATTERN_RECOGNITION"}


def queries(edition: editions.Edition) -> list[Hive]:
    """Each query an Edition's golden holds: its SELECTs and WITHs."""
    from composer_core.example_database import _is_query

    return [hive for hive in hive_texts(edition) if _is_query(hive.text)]


_TABLE_READ = re.compile(r"\b(?:FROM|JOIN)\s+(`?\w+`?\.`?\w+`?)")


def tables_read(text: str) -> set[str]:
    """The tables a query reads, by the names it gives them, as ops.jobs."""
    return set(_TABLE_READ.findall(text))


def wide_table():
    """The table the corpus's width cases read, with a key column as long as each needs."""
    from sql_composer import Table

    keys = {key for hive in hive_texts(editions.SPARK_COMPOSER)
            for key in re.findall(r"\bwide\.(kx+)\b", hive.text)}
    return Table("ops.wide", columns={**dict.fromkeys(sorted(keys), "string"), "v": "bigint",
                                      "dt": "string"}, date_partition="dt")
