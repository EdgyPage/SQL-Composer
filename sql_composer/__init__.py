# SQL Composer 2.0, exported 2026-09-25 20:11 - generated from dev, do not edit
"""SQL Composer: write Hive SQL as Python, one clause function per SQL clause.

Import everything from here, never from a file inside the folder:

    from sql_composer import statement, SELECT, AS, FROM, WHERE, GROUP_BY, to_hive, run

To update, delete the `sql_composer` folder, copy in the new one and restart the kernel. The
folder checks itself when imported, and stops with a plain message if a file is missing,
extra, or from another version.

TOOLBOX_VERSION is the feature number, raised only when a big feature lands. VERSION is the
full text, which also says when this copy was exported.

>>> TOOLBOX_VERSION
'2.0'
>>> VERSION
'SQL Composer 2.0, ...'
"""

from __future__ import annotations

import os
import re
import sys

TOOLBOX_VERSION = "2.0"

# The export script writes the Toolbox's file list here. On dev it is None, and the checks
# for missing and extra files are skipped.
_FILES = [
    "CHANGES.md",
    "__init__.py",
    "calculations.py",
    "clauses.py",
    "conditions.py",
    "example_database.py",
    "examples.html",
    "lineage.py",
    "refusals.py",
    "running.py",
    "tables.py",
]

_PYTHON_NEEDED = (3, 11)
_SQLGLOT_LOWEST = (25, 24, 2)
_SQLGLOT_BELOW = (31, 0, 0)
_SQLGLOT_NEWEST_TESTED = (30, 19, 0)

_HERE = os.path.dirname(os.path.abspath(__file__))


def _stop(message):
    raise ImportError("sql_composer stopped on import: " + message)


def _check_python():
    if sys.version_info[:2] < _PYTHON_NEEDED:
        _stop(
            "it needs Python 3.11 or newer, and this is Python "
            + ".".join(str(n) for n in sys.version_info[:3])
            + "."
        )


def _version_of(path):
    with open(path, encoding="utf-8") as file:
        found = re.search(r'^TOOLBOX_VERSION = "([^"]*)"', file.read(), re.MULTILINE)
    return found.group(1) if found else None


def _stamp_of(path):
    with open(path, encoding="utf-8") as file:
        first = file.readline().strip()
    return first if first.startswith("# SQL Composer") else None


def _check_files():
    """Stop if the pasted folder is missing a file, has an extra one, or mixes versions."""
    present = sorted(
        name for name in os.listdir(_HERE)
        if name != "__pycache__" and not name.startswith(".")
    )
    if _FILES is not None:
        extra = [name for name in present if name not in _FILES]
        missing = [name for name in _FILES if name not in present]
        if extra:
            _stop(f"{', '.join(extra)} isn't part of SQL Composer {TOOLBOX_VERSION}. Delete the "
                  "sql_composer folder and copy in the new one whole.")
        if missing:
            _stop(f"{', '.join(missing)} is missing. Copy it in from the {TOOLBOX_VERSION} "
                  "download.")
    python_files = [name for name in present if name.endswith(".py")]
    for name in python_files:
        version = _version_of(os.path.join(_HERE, name))
        if version != TOOLBOX_VERSION:
            _stop(f"sql_composer {TOOLBOX_VERSION}: {name} is from {version or 'another version'}"
                  f" - paste it again from the {TOOLBOX_VERSION} download.")
    stamps = {name: _stamp_of(os.path.join(_HERE, name)) for name in python_files}
    if len(set(stamps.values())) > 1:
        odd = sorted(name for name, stamp in stamps.items() if stamp != stamps["__init__.py"])
        _stop(f"{', '.join(odd)} came from a different export than __init__.py - paste the "
              "whole folder again from one download.")


def _dotted(numbers):
    return ".".join(str(n) for n in numbers)


def _numbers(text):
    found = re.match(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(n) for n in found.groups()) if found else None


def _check_sqlglot():
    """Refuse a sqlglot outside the supported range, or one that behaves differently."""
    try:
        import sqlglot
    except ImportError:
        _stop("it needs the sqlglot library, and this Python can't import it.")
    found = getattr(sqlglot, "__version__", "unknown")
    version = _numbers(found)
    if version is None or not _SQLGLOT_LOWEST <= version < _SQLGLOT_BELOW:
        _stop(f"it needs sqlglot {_dotted(_SQLGLOT_LOWEST)} or newer, below "
              f"{_dotted(_SQLGLOT_BELOW)}, and this Python has sqlglot {found}.")
    problems = _sqlglot_behaviour()
    if problems:
        _stop(f"sqlglot {found} is in the supported range but behaves differently: "
              + "; ".join(problems) + ". Nothing has been built or sent.")
    if version > _SQLGLOT_NEWEST_TESTED:
        print(f"Note: sqlglot {found} is newer than any version SQL Composer was tested on "
              f"({_dotted(_SQLGLOT_NEWEST_TESTED)}). Its behaviour checks passed.")


def _sqlglot_behaviour():
    from sqlglot import exp
    from sqlglot.errors import OptimizeError
    from sqlglot.optimizer.qualify import qualify

    problems = []
    if exp.convert("O'Brien\\").sql("hive") != "'O\\'Brien\\\\'":
        problems.append("Hive string escaping has changed")
    table = exp.table_("t", db="db")
    table.set("partition", exp.Partition(
        expressions=[exp.column("dt").eq(exp.Literal.string("2026-01-01"))]))
    insert = exp.Insert(this=table, expression=exp.select("a").from_("s"), overwrite=True)
    if "PARTITION(dt = '2026-01-01')" not in insert.sql("hive"):
        problems.append("INSERT OVERWRITE drops its PARTITION")
    try:
        qualify(exp.select("nope").from_("t"), schema={"t": {"a": "INT"}}, dialect="hive")
        problems.append("qualify no longer refuses an unknown column")
    except OptimizeError:
        pass
    return problems


def _version_text():
    stamp = _stamp_of(os.path.join(_HERE, "__init__.py"))
    if stamp is None:
        return f"SQL Composer {TOOLBOX_VERSION}, not exported (dev)"
    return stamp[2:].split(" - ")[0]


_check_python()
_check_files()
_check_sqlglot()

VERSION = _version_text()

from . import example_database  # noqa: E402
from .calculations import (  # noqa: E402
    average_of,
    count_distinct,
    count_rows,
    descending,
    fill_null,
    hive_function,
    if_else,
    max_of,
    min_of,
    month_start,
    row_number,
    sum_of,
    week_start,
)
from .clauses import (  # noqa: E402
    AS,
    CROSS_JOIN,
    FROM,
    GROUP_BY,
    HAVING,
    INSERT_OVERWRITE,
    JOIN,
    LEFT_JOIN,
    LIMIT,
    ORDER_BY,
    SELECT,
    SELECT_DISTINCT,
    WHERE,
    derived,
    statement,
)
from .conditions import (  # noqa: E402
    all_of,
    any_of,
    at_least,
    at_most,
    between,
    contains,
    equals,
    is_in,
    is_not_in,
    is_not_null,
    is_null,
    last_n_days,
    less_than,
    more_than,
    not_equals,
    starts_with,
)
from .lineage import export_lineage  # noqa: E402
from .refusals import GuardRefused, LoadRefused  # noqa: E402
from .running import by_day, run, set_load_limits, to_hive  # noqa: E402
from .tables import (  # noqa: E402
    Table,
    all_columns,
    check_key,
    check_table_reference,
    create_table,
    first_look,
    write_table_reference,
)

# Every public name, grouped by the file it lives in.
__all__ = [
    # __init__.py
    "TOOLBOX_VERSION",
    "VERSION",
    # tables.py
    "Table",
    "write_table_reference",
    "first_look",
    "check_key",
    "check_table_reference",
    "create_table",
    "all_columns",
    # clauses.py
    "SELECT",
    "SELECT_DISTINCT",
    "AS",
    "FROM",
    "JOIN",
    "LEFT_JOIN",
    "CROSS_JOIN",
    "WHERE",
    "GROUP_BY",
    "HAVING",
    "ORDER_BY",
    "LIMIT",
    "INSERT_OVERWRITE",
    "statement",
    "derived",
    # conditions.py
    "equals",
    "not_equals",
    "is_null",
    "is_not_null",
    "at_least",
    "at_most",
    "more_than",
    "less_than",
    "between",
    "last_n_days",
    "is_in",
    "is_not_in",
    "contains",
    "starts_with",
    "any_of",
    "all_of",
    # calculations.py
    "count_rows",
    "count_distinct",
    "sum_of",
    "average_of",
    "min_of",
    "max_of",
    "if_else",
    "fill_null",
    "week_start",
    "month_start",
    "row_number",
    "descending",
    "hive_function",
    # running.py
    "to_hive",
    "run",
    "by_day",
    "set_load_limits",
    # refusals.py
    "GuardRefused",
    "LoadRefused",
    # lineage.py
    "export_lineage",
    # example_database.py
    "example_database",
]
