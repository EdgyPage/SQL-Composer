# SQL Composer 2.1, exported 2026-09-29 12:54 - generated from dev, do not edit
"""SQL Composer: write Hive SQL as Python, one clause function per SQL clause.

Import everything from here, never from a file inside the folder:

    from sql_composer import statement, SELECT, AS, FROM, WHERE, GROUP_BY, to_hive, run

To update, delete the `sql_composer` folder, copy in the new one and restart the kernel. The
folder checks itself when imported. If a file is missing, extra, or from another version or
export, or if this Python or its sqlglot won't work with it, it stops and says what happened,
why it matters and the usual fix.

TOOLBOX_VERSION is the feature number, raised only when a big feature lands. VERSION is the
full text, which also says when this copy was exported.

>>> TOOLBOX_VERSION
'2.1'
>>> VERSION
'SQL Composer 2.1, ...'
"""

from __future__ import annotations

import os
import re
import sys

TOOLBOX_VERSION = "2.1"

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


def _four_part_message(what: str, why: str, fix: str, opt_out: str | None) -> str:
    """The one shape every refusal and Warning message has, and every import stop too.

    It lives here, not in refusals.py, because the import self-check needs it before any
    other file in the folder can be trusted, or even found.
    """
    if opt_out is None:
        opt_out = "none - this one can't be switched off."
    return (
        f"\n  What happened:  {what}"
        f"\n  Why it matters: {why}"
        f"\n  Usual fix:      {fix}"
        f"\n  Opt-out:        {opt_out}"
    )


def _stop(what, why, fix):
    """Stop the import with the four-part message. No import stop can be switched off."""
    raise ImportError("sql_composer stopped on import:"
                      + _four_part_message(what=what, why=why, fix=fix, opt_out=None))


def _check_python():
    if sys.version_info[:2] < _PYTHON_NEEDED:
        _stop(
            what="SQL Composer needs Python 3.11 or newer, and this is Python "
            + ".".join(str(n) for n in sys.version_info[:3]) + ".",
            why="SQL Composer is tested only on Python 3.11 and newer, and parts of it may not "
            "work on an older one.",
            fix="Choose a Python 3.11 or newer kernel (Kernel > Change Kernel in JupyterLab), "
            "or ask whoever looks after your environment to add one.",
        )


def _version_of(path):
    with open(path, encoding="utf-8") as file:
        found = re.search(r'^TOOLBOX_VERSION = "([^"]*)"', file.read(), re.MULTILINE)
    return found.group(1) if found else None


def _stamp_of(path):
    """The export stamp on line 1, or None.

    The export writes it as a `# ...` comment in a .py file and as `<!-- ... -->` in any
    other, since a `#` line in Markdown is a heading.
    """
    with open(path, encoding="utf-8", errors="replace") as file:
        first = file.readline().strip()
    start, end = ("# ", "") if path.endswith(".py") else ("<!-- ", " -->")
    stamp = first[len(start):len(first) - len(end)]
    if first.startswith(start) and first.endswith(end) and stamp.startswith("SQL Composer "):
        return stamp
    return None


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
            _stop(
                what=f"{', '.join(extra)} {'is' if len(extra) == 1 else 'are'} in the "
                f"sql_composer folder, but not part of SQL Composer {TOOLBOX_VERSION}.",
                why="A file left over from an earlier Toolbox version can still be imported, "
                "and would quietly run old code. A script of your own inside the folder would "
                "be deleted with it at the next update.",
                fix="Move any of your own scripts out first: they sit beside the sql_composer "
                "folder, never inside it. Then delete the sql_composer folder, and copy the "
                f"whole folder in again from the {TOOLBOX_VERSION} download.",
            )
        if missing:
            _stop(
                what=f"{', '.join(missing)} {'is' if len(missing) == 1 else 'are'} missing "
                "from the sql_composer folder.",
                why=f"Every file of SQL Composer {TOOLBOX_VERSION} is needed: a missing .py "
                "file would make a part of it fail later, far from the cause, and a missing "
                "examples.html or CHANGES.md leaves you without the Example gallery or the "
                "change notes.",
                fix="Delete the sql_composer folder, then copy the whole folder in again from "
                f"the {TOOLBOX_VERSION} download.",
            )
    python_files = [name for name in present if name.endswith(".py")]
    for name in python_files:
        version = _version_of(os.path.join(_HERE, name))
        if version != TOOLBOX_VERSION:
            _stop(
                what=f"{name} is from "
                + (f"Toolbox version {version}" if version else "another Toolbox version")
                + f", and __init__.py is from {TOOLBOX_VERSION}.",
                why="Files from different Toolbox versions weren't written to work together, "
                "so a Statement could fail or come out wrong.",
                fix="Delete the sql_composer folder, then copy the whole folder in again from "
                "one download.",
            )
    stamps = {
        name: _stamp_of(os.path.join(_HERE, name))
        for name in present if os.path.isfile(os.path.join(_HERE, name))
    }
    if len(set(stamps.values())) > 1:
        odd = sorted(name for name, stamp in stamps.items() if stamp != stamps["__init__.py"])
        _stop(
            what=f"{', '.join(odd)} came from a different export than __init__.py.",
            why="Two exports of the same Toolbox version can differ, so the code, the Example "
            "gallery and the change notes in this folder may not match each other.",
            fix="Delete the sql_composer folder, then copy the whole folder in again from one "
            "download.",
        )


def _dotted(numbers):
    return ".".join(str(n) for n in numbers)


def _numbers(text):
    found = re.match(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(n) for n in found.groups()) if found else None


_IN_RANGE = f'"sqlglot>={_dotted(_SQLGLOT_LOWEST)},<{_dotted(_SQLGLOT_BELOW)}"'
_NO_INSTALLING = "If you can't install packages, ask whoever looks after your environment."


def _check_sqlglot():
    """Refuse a sqlglot outside the supported range, or one that behaves differently."""
    try:
        import sqlglot
    except ImportError:
        _stop(
            what="SQL Composer needs sqlglot, and this Python can't import it.",
            why="SQL Composer writes every Statement as Hive through sqlglot, and reads the "
            "Hive back to check it, so it can't build anything without it.",
            fix=f"Install sqlglot from a notebook cell with %pip install {_IN_RANGE}, then "
            f"restart the kernel. {_NO_INSTALLING}",
        )
    found = getattr(sqlglot, "__version__", "unknown")
    version = _numbers(found)
    if version is None or not _SQLGLOT_LOWEST <= version < _SQLGLOT_BELOW:
        _stop(
            what=f"SQL Composer needs sqlglot {_dotted(_SQLGLOT_LOWEST)} or newer, below "
            f"{_dotted(_SQLGLOT_BELOW)}, and this Python has sqlglot {found}.",
            why="SQL Composer is checked only on that range of sqlglot. Another sqlglot can "
            "write Hive differently, so a Statement could come out wrong without anything "
            "saying so.",
            fix="Install a sqlglot in that range from a notebook cell with %pip install "
            f"{_IN_RANGE}, then restart the kernel. {_NO_INSTALLING}",
        )
    problems = _sqlglot_behaviour()
    if problems:
        _stop(
            what=f"sqlglot {found} is in the supported range, but behaves differently: "
            + "; ".join(problems) + ". Nothing has been built or sent.",
            why="SQL Composer relies on this behaviour to write Hive safely, so a Statement "
            "could come out wrong.",
            fix="Install again the sqlglot SQL Composer is tested on, from a notebook cell "
            f'with %pip install --force-reinstall "sqlglot=={_dotted(_SQLGLOT_NEWEST_TESTED)}", '
            f"then restart the kernel. {_NO_INSTALLING}",
        )
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
    # Built the way drop_table builds it: sqlglot 30 renamed a DROP's `this` to `tables`.
    if "tables" in exp.Drop.arg_types:
        drop = exp.Drop(kind="TABLE", tables=[exp.table_("t", db="db")], exists=True)
    else:
        drop = exp.Drop(kind="TABLE", this=exp.table_("t", db="db"), exists=True)
    if drop.sql("hive") != "DROP TABLE IF EXISTS db.t":
        problems.append("DROP TABLE drops its table name")
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
    return stamp.split(" - ")[0]


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
    INSERT_INTO,
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
    drop_table,
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
    "drop_table",
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
    "INSERT_INTO",
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
