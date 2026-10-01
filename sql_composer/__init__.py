"""Write Hive SQL as Python, one clause function per SQL clause.

Import everything from here, never from a file inside the folder:

    from sql_composer import statement, SELECT, AS, FROM, WHERE, GROUP_BY, to_hive, run

To update, delete the `sql_composer` folder, copy in the new one and restart the kernel. The
folder checks itself when imported. If a file is missing, extra, from another version or
export, or from another Toolbox folder, or if this Python can't run the Toolbox, it stops and
says what happened, why it matters and the usual fix.

TOOLBOX_VERSION is the feature number, raised only when a big feature lands. VERSION is the
full text, which also says when this copy was exported.

>>> TOOLBOX_VERSION
'3.1'
>>> VERSION
'SQL Composer 3.1, ...'
"""

from __future__ import annotations

import os
import re
import sys

TOOLBOX_VERSION = "3.1"

# The folder this file belongs in, and the name its export stamps on each of that folder's
# files.
_FOLDER = "sql_composer"
_PRODUCT = "SQL Composer"

# The export script writes the Toolbox's file list here. On dev it is None, and the checks
# for missing and extra files are skipped.
_FILES = None

_PYTHON_NEEDED = (3, 11)

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
    # The folder the import found, which a __init__.py pasted in from another folder can't know.
    raise ImportError(f"{os.path.basename(_HERE)} stopped on import:"
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


# Any Toolbox folder's stamp, such as "SQL Composer 3.1, exported 2026-10-02 14:05 - ...",
# whose first words name the folder its file belongs in.
_STAMP = re.compile(r"(\w+ Composer) \S+, exported ")


def _stamp_of(path):
    """The export stamp on line 1, or None.

    The export writes it as a `# ...` comment in a .py file and as `<!-- ... -->` in any
    other, since a `#` line in Markdown is a heading.
    """
    with open(path, encoding="utf-8", errors="replace") as file:
        first = file.readline().strip()
    start, end = ("# ", "") if path.endswith(".py") else ("<!-- ", " -->")
    stamp = first[len(start):len(first) - len(end)]
    if first.startswith(start) and first.endswith(end) and _STAMP.match(stamp):
        return stamp
    return None


def _home_of(name, stamp):
    """The folder a file belongs in: __init__.py knows its own, and a stamp names any other's.

    None for an unstamped file other than __init__.py.
    """
    if name == "__init__.py":
        return _FOLDER
    if stamp is None:
        return None
    return _STAMP.match(stamp).group(1).lower().replace(" ", "_")


def _check_home(stamps):
    """Stop if a file came from another Toolbox folder than the one it sits in."""
    on_disk = os.path.basename(_HERE)
    homes = {name: _home_of(name, stamp) for name, stamp in stamps.items()}
    # The folder is the Toolbox folder its name and its files' stamps agree on. A folder its
    # files don't name, such as one you renamed, is the one most of its other files' stamps
    # name, so a __init__.py pasted in can't decide it; unstamped, as on dev, __init__.py's.
    stamped = [home for name, home in homes.items() if name != "__init__.py" and home]
    this = on_disk if on_disk in homes.values() else max(stamped, key=stamped.count,
                                                          default=_FOLDER)
    elsewhere = sorted(name for name, home in homes.items() if home not in (None, this))
    if elsewhere:
        home = homes[elsewhere[0]]
        where = f"the {on_disk} folder" + ("" if on_disk == this else f", a copy of {this}")
        _stop(
            what=f"{', '.join(elsewhere)} {'is' if len(elsewhere) == 1 else 'are'} from the "
            f"{home} folder, and this is {where}.",
            why="A folder's files are made to work only with each other: a .py file from "
            "another folder could make a Statement fail or come out wrong, and an "
            "examples.html or CHANGES.md from one may not describe this folder's code.",
            fix=f"Delete the {on_disk} folder, then copy it in again from the {this} folder "
            f"of one download, not from {home}.",
        )


def _check_files():
    """Stop if the pasted folder is missing a file, has an extra one, or mixes versions,
    exports or Toolbox folders."""
    present = sorted(
        name for name in os.listdir(_HERE)
        if name != "__pycache__" and not name.startswith(".")
    )
    stamps = {
        name: _stamp_of(os.path.join(_HERE, name))
        for name in present if os.path.isfile(os.path.join(_HERE, name))
    }
    # First, since a __init__.py from another folder brings that folder's file list and names.
    _check_home(stamps)
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
    if len(set(stamps.values())) > 1:
        odd = sorted(name for name, stamp in stamps.items() if stamp != stamps["__init__.py"])
        _stop(
            what=f"{', '.join(odd)} came from a different export than __init__.py.",
            why="Two exports of the same Toolbox version can differ, so the code, the Example "
            "gallery and the change notes in this folder may not match each other.",
            fix="Delete the sql_composer folder, then copy the whole folder in again from one "
            "download.",
        )


def _version_text():
    stamp = _stamp_of(os.path.join(_HERE, "__init__.py"))
    if stamp is None:
        return f"{_PRODUCT} {TOOLBOX_VERSION}, not exported (dev)"
    return stamp.split(" - ")[0]


_check_python()
_check_files()
# engine.py, one file per Edition, checks what the Edition needs installed. It is imported only
# once the folder is known to be whole.
from . import engine  # noqa: E402

engine.check_installed()

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
