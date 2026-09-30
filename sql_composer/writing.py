"""How SQL Composer writes Hive: every step only sqlglot can take.

The other files build a Statement's parts; this file writes them as Hive text with sqlglot,
reads the text back to check it, and builds the pieces sqlglot must build itself: Hive's own
functions, column types, and the commands that describe a table. Each Edition has a file of
this name with the same functions.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel

from .refusals import four_part_message

TOOLBOX_VERSION = "2.1"

_DIALECT = "hive"


def sql_text(tree: exp.Expression, pretty: bool = False) -> str:
    """Write a sqlglot tree as Hive. Nothing else in the Toolbox calls `.sql()`."""
    return tree.sql(dialect=_DIALECT, pretty=pretty, unsupported_level=ErrorLevel.RAISE)


def hive_text(node: exp.Expression, pretty: bool = False) -> str:
    """A Statement, or one part of it, as Hive."""
    return sql_text(node, pretty=pretty)


def read_back(text: str) -> str:
    """The Hive read back and written again, to compare with the Hive as it was written."""
    return sql_text(sqlglot.parse_one(text, read=_DIALECT), pretty=True)


def hive_call(name: str, *arguments: exp.Expression) -> exp.Expression:
    """A call to one of Hive's own functions, as sqlglot builds it."""
    return exp.func(name, *arguments, dialect=_DIALECT)


def read_back_function(name: str, arguments: list, call: str) -> exp.Expression:
    """hive_function's call, built and read back once, or why its arguments don't fit."""
    try:
        tree = hive_call(name, *arguments)
        # Read the call back once, as to_hive's self-check will: a few functions come back in
        # sqlglot's own form (DATEDIFF gains TO_DATE on older sqlglot), which is then stable.
        return sqlglot.parse_one(sql_text(tree), read=_DIALECT)
    except (ValueError, TypeError, sqlglot.errors.ParseError) as error:
        raise TypeError(
            four_part_message(
                what=f"{call} was given {len(arguments)} arguments, which don't fit {name}.",
                why="sqlglot knows this Hive function and couldn't build it from these "
                "arguments.",
                fix=f"Check {name}'s arguments in Hive's documentation.",
                opt_out=None,
            )
        ) from error


def hive_type(text: str) -> exp.DataType:
    """A column's type for CREATE TABLE, as sqlglot reads it; raises when it can't."""
    return exp.DataType.build(text, dialect=_DIALECT)


def describe_text(name: str) -> str:
    """The DESCRIBE command for one table."""
    from .tables import hive_table  # here, not at the top: tables.py imports this file

    return sql_text(exp.Describe(this=hive_table(name)))


def show_partitions_text(name: str) -> str:
    """The SHOW PARTITIONS command for one table."""
    from .tables import hive_table  # here, not at the top: tables.py imports this file

    return sql_text(exp.Command(this="SHOW", expression=exp.Literal.string(
        "PARTITIONS " + sql_text(hive_table(name)))))


def set_part(tree: exp.Expression, part: str, value) -> None:
    """Set a part of a sqlglot tree. sqlglot 30 renamed `from` and `with` to `from_`, `with_`."""
    for key in (part, part + "_"):
        if key in type(tree).arg_types:
            tree.set(key, value)
            return
    raise RuntimeError(f"sql_composer: this sqlglot has no {part!r} on {type(tree).__name__}.")


def drop(table: exp.Table) -> exp.Drop:
    """DROP TABLE IF EXISTS for one table. sqlglot 30 renamed a DROP's `this` to `tables`."""
    if "tables" in exp.Drop.arg_types:
        return exp.Drop(kind="TABLE", tables=[table], exists=True)
    return exp.Drop(kind="TABLE", this=table, exists=True)
