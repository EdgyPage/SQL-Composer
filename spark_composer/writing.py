"""How Spark Composer writes a Statement as Hive text, with no package but Python's own.

The other files build a Statement's parts as the Toolbox's own tree (trees.py). This file writes
them out as the same Hive SQL Composer writes, checks the text, and says how a table is
described. Each Edition of the Toolbox writes Hive its own way behind these same function names.
"""

from __future__ import annotations

from .refusals import four_part_message
from .trees import Node, plain_name

TOOLBOX_VERSION = "2.1"


def _not_yet() -> RuntimeError:
    return RuntimeError(four_part_message(
        what="Spark Composer can't write Hive yet.",
        why="Its writer is built in a later step of the PySpark work.",
        fix="Use SQL Composer for now.",
        opt_out=None,
    ))


def hive_text(node: Node) -> str:
    """A part of a Statement, held in the Toolbox's own tree (trees.py), as Hive on one line."""
    raise _not_yet()


def hive_statement(node: Node) -> str:
    """A whole Statement's tree as the Hive to_hive gives: laid out over several lines."""
    raise _not_yet()


def read_back(text: str) -> str:
    """The Hive, checked. to_hive compares the two, to check its own Hive."""
    raise _not_yet()


def function_adds_rows_up(name: str, args: list[Node], call: str) -> bool:
    """Whether hive_function(name, *args) adds rows up.

    It raises TypeError when the function doesn't take this many arguments.
    """
    raise _not_yet()


def hive_type(text: str) -> str:
    """A column's type for CREATE TABLE; raises when it isn't one."""
    raise _not_yet()


def _table_name(name: str) -> str:
    """A table's full name, each part in backticks where it needs them."""
    return ".".join(part if plain_name(part) else "`" + part.replace("`", "``") + "`"
                    for part in name.split("."))


def describe_text(name: str) -> str:
    """The DESCRIBE command for one table."""
    return f"DESCRIBE {_table_name(name)}"


def show_partitions_text(name: str) -> str:
    """The SHOW PARTITIONS command for one table."""
    return f"SHOW PARTITIONS {_table_name(name)}"
