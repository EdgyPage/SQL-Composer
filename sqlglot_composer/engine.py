"""What sqlglot Composer runs on: the sqlglot it needs.

`__init__.py` calls `check_installed()` as soon as it knows the folder is whole, before it
imports any other file. This file imports sqlglot only inside its functions, so it can be
imported to check sqlglot before sqlglot is trusted.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, NoReturn

from . import _stop as _core_stop

if TYPE_CHECKING:
    # Only for hints: sqlglot is imported inside the functions, once it is checked.
    from sqlglot import exp


def _stop_import(what: str, why: str, fix: str) -> NoReturn:
    """Stop the Toolbox's import, named by its own folder, with the four-part message.

    Not refusals.refuse, whose message isn't headed by the folder's name, as every import stop
    is."""
    _core_stop(what, why, fix, folder=__name__.split(".")[0])


# The supported range: 30.19.0, where the executor dev's Example database runs on first counts
# COUNT(DISTINCT ...) right, up to (not including) 31. CI runs the pin, _NEWEST_TESTED.
_LOWEST = (30, 19, 0)
_BELOW = (31, 0, 0)
_NEWEST_TESTED = (30, 23, 0)


# --- sqlglot --------------------------------------------------------------------------------


def _dotted(numbers: tuple[int, ...]) -> str:
    return ".".join(str(n) for n in numbers)


def _numbers(text: str) -> tuple[int, ...] | None:
    found = re.match(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(n) for n in found.groups()) if found else None


# Where sqlglot is missing or out of the range, the one the Toolbox is tested on.
_INSTALL_TESTED = ("Install the sqlglot sqlglot Composer is tested on from a notebook cell "
                   f'with %pip install "sqlglot=={_dotted(_NEWEST_TESTED)}", then restart '
                   "the kernel.")
_NO_INSTALLING = "If you can't install packages, ask whoever looks after your environment."


def check_installed() -> None:
    """Refuse a sqlglot outside the supported range, or one that behaves differently."""
    try:
        import sqlglot
    except ImportError:
        sqlglot = None
    if sqlglot is None:
        _stop_import(
            what="sqlglot Composer needs sqlglot, and this Python can't import it.",
            why="sqlglot Composer writes every Statement as Hive through sqlglot, and reads "
            "the Hive back to check it, so it can't build anything without it.",
            fix=f"{_INSTALL_TESTED} {_NO_INSTALLING}",
        )
    found = getattr(sqlglot, "__version__", "unknown")
    version = _numbers(found)
    if version is None or not _LOWEST <= version < _BELOW:
        _stop_import(
            what=f"sqlglot Composer needs sqlglot {_dotted(_LOWEST)} or newer, below "
            f"{_dotted(_BELOW)}, and this Python has sqlglot {found}.",
            why="sqlglot Composer works only with that range of sqlglot, and is tested on "
            f"{_dotted(_NEWEST_TESTED)}. Another sqlglot can write Hive differently, so a "
            "Statement could come out wrong without anything saying so.",
            fix=f"{_INSTALL_TESTED} {_NO_INSTALLING}",
        )
    problems = _sqlglot_behaviour()
    if problems:
        _stop_import(
            what=f"sqlglot {found} is in the supported range, but behaves differently: "
            + "; ".join(problems) + ". Nothing has been built or sent.",
            why="sqlglot Composer relies on this behaviour to write Hive safely, so a "
            "Statement could come out wrong.",
            fix="Install again the sqlglot version that sqlglot Composer is tested on, from "
            "a notebook cell with %pip install --force-reinstall "
            f'"sqlglot=={_dotted(_NEWEST_TESTED)}", then restart the kernel. '
            f"{_NO_INSTALLING}",
        )
    if version > _NEWEST_TESTED:
        print(f"Note: sqlglot {found} is newer than any version sqlglot Composer was tested on "
              f"({_dotted(_NEWEST_TESTED)}). Its behaviour checks passed.")


def _sqlglot_behaviour() -> list[str]:
    from sqlglot import exp
    from sqlglot.errors import OptimizeError, UnsupportedError
    from sqlglot.optimizer.qualify import qualify

    # Written the way the Toolbox writes, now that the sqlglot it needs is known to be here.
    from .trees import Node
    from .writing import sql_text, to_sqlglot

    def written(tree: exp.Expression) -> str:
        try:
            return sql_text(tree)
        except UnsupportedError:
            return ""  # a sqlglot that can no longer write it behaves differently too

    problems = []
    if written(exp.convert("O'Brien\\")) != "'O\\'Brien\\\\'":
        problems.append("Hive string escaping has changed")
    table = exp.table_("t", db="db")
    table.set("partition", exp.Partition(
        expressions=[exp.column("dt").eq(exp.Literal.string("2026-01-01"))]))
    insert = exp.Insert(this=table, expression=exp.select("a").from_("s"), overwrite=True)
    if "PARTITION(dt = '2026-01-01')" not in written(insert):
        problems.append("INSERT OVERWRITE drops its PARTITION")
    if written(to_sqlglot(Node("Drop", target=Node("Table", db="db", name="t")))) != (
            "DROP TABLE IF EXISTS db.t"):
        problems.append("DROP TABLE drops its table name")
    try:
        qualify(exp.select("nope").from_("t"), schema={"t": {"a": "INT"}}, dialect="hive")
        problems.append("qualify no longer refuses an unknown column")
    except OptimizeError:
        pass
    return problems
