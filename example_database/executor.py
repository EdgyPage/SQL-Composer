"""The Example database's executor: it runs a query's Hive on sqlglot's own executor.

The Example database hands `run_query` a query's Hive and its tables, and gets back the query's
column names and rows. It is dev's alone, beside the Toolbox, never in it (Toolbox 8.7, ticket
12): the Toolbox sends Hive only to the user's own query and execute. The running itself is
the Toolbox's `hive_executor.run_on_executor`, which the Workbook check runs Hive on too
(Toolbox 8.9, ticket 09); this file gives it the Example database's tables and says, in the
Example database's words, what it couldn't run.
"""

from __future__ import annotations

from typing import NoReturn

import sqlglot
from sqlglot import exp

from sqlglot_composer import engine
from sqlglot_composer.hive_executor import (
    HIVE_DAYS,
    MissingPart,
    NtileWithNoParts,
    executor_counts_right,
    reason_without_place,
    run_on_executor,
)
from sqlglot_composer.refusals import four_part_message, refuse
from sqlglot_composer.shared import in_words
from sqlglot_composer.tables import Table


def _dotted(numbers: tuple[int, ...]) -> str:
    """A version, such as (30, 23, 0), as it is written: 30.23.0."""
    return ".".join(str(n) for n in numbers)


# What to install where the executor counts wrongly: the sqlglot the Toolbox is tested on, or a
# newer one in its range.
INSTALL_NEWER = ("Install a newer sqlglot from a notebook cell with %pip install "
                 f'"sqlglot>={_dotted(engine._PIN)},<{_dotted(engine._BELOW)}", '
                 "then restart the kernel. If you can't install packages, ask whoever looks "
                 "after your environment.")


def _check_executor() -> None:
    """Stop with a plain message when sqlglot's executor would give wrong answers."""
    if executor_counts_right():
        return
    refuse(
        what="The Example database runs queries on sqlglot's own executor, and sqlglot "
        f"{sqlglot.__version__}'s executor counts COUNT(DISTINCT ...) wrong.",
        why="An executor that counts COUNT(DISTINCT ...) wrong says nothing about it.",
        fix=f"{INSTALL_NEWER} Until then the rest of the Toolbox works as usual: to_hive(...) "
        "still shows a Statement's Hive.",
        error=RuntimeError,
    )


def _refuse_missing_part(missing: str, error: Exception | None = None) -> NoReturn:
    """Refuse a query that needs a part of Hive the executor hasn't got, such as TRUNC.

    Raised here, not through refusals.refuse, so that the executor's own `error` stays the
    refusal's cause."""
    raise RuntimeError(four_part_message(
        what=f"The Example database can't run this Hive: its executor has no {missing}.",
        why="The Example database runs Hive on sqlglot's own small executor, which knows only "
        "part of Hive. Hive at work knows all of it.",
        fix="See the Hive with to_hive(...), and run it at work with your own query. Or try "
        "the rest here without that part: in the Statement, or in the original Hive, where "
        "you compare a Statement with one.",
        opt_out=None,
    )) from error


def _refuse_hive_it_cant_run(reason: str,
                             tables: dict[str, tuple[Table, list[tuple[object, ...]]]],
                             error: Exception | None = None) -> NoReturn:
    """Refuse a query sqlglot couldn't read or run, as a warehouse refuses one.

    Raised here, not through refusals.refuse, so that sqlglot's own `error` stays the
    refusal's cause."""
    listed = in_words([f"ops.{name}" for name in tables])
    raise RuntimeError(four_part_message(
        what=f"The Example database couldn't run this Hive: {reason}.",
        why="Most often a table, column or hive_function(...) name is spelt wrong, which your "
        "warehouse would refuse too. Or the Hive uses a part of Hive your warehouse knows but "
        "the Example database's small executor doesn't.",
        fix=f"Check the names: the tables are {listed}, and all_columns(...) of one, such as "
        "all_columns(ops.jobs), lists its columns, as the table alone on a "
        "cell's last line does. If they're right, see the Hive with "
        "to_hive(...), and run it at work with your own query.",
        opt_out=None,
    )) from error


def _refuse_ntile_of_no_parts(parts: int) -> NoReturn:
    """Refuse NTILE given no parts to split each group into, as Hive refuses it."""
    refuse(
        what=f"The Example database can't run this Hive: NTILE({parts}) splits each group "
        "into no parts.",
        why="NTILE numbers the rows of each group from 1 to its number of parts, so it "
        "needs 1 part or more. Hive refuses it too.",
        fix="Give NTILE a number of parts of 1 or more, such as ntile(4, over=...).",
        error=RuntimeError,
    )


def _check_example_tables(tree: exp.Expression,
                          tables: dict[str, tuple[Table, list[tuple[object, ...]]]]) -> None:
    """Refuse a table the query names with a database that isn't one of the Example database's,
    such as mart.jobs, as a warehouse refuses it, before a column of it is blamed."""
    for table in tree.find_all(exp.Table):
        if table.db and (table.db.lower() != "ops" or table.name.lower() not in tables):
            _refuse_hive_it_cant_run(f"it has no table {table.db}.{table.name}", tables)


def run_query(text: str, tables: dict[str, tuple[Table, list[tuple[object, ...]]]]
              ) -> tuple[list[str], list[tuple[object, ...]]]:
    """Run a query's Hive on sqlglot's executor: its column names, and its rows.

    `tables` maps each table's short name to its Table reference and its rows.
    """
    if text.split(None, 1)[:1] and text.split(None, 1)[0].upper() == "EXPLAIN":
        # The executor runs a query step by step, with no plan of Hive's to show.
        _refuse_missing_part("EXPLAIN")
    try:
        tree = sqlglot.parse_one(text, read="hive")
    except sqlglot.errors.SqlglotError as error:
        _refuse_hive_it_cant_run(reason_without_place(error), tables, error)
    _check_example_tables(tree, tables)
    _check_executor()
    schema = {"ops": {name: dict(table._columns) for name, (table, _) in tables.items()}}
    rows = {"ops": {}}
    for name, (table, table_rows) in tables.items():
        rows["ops"][name] = [dict(zip(table._columns, row)) for row in table_rows]
    try:
        return run_on_executor(tree, schema, rows, HIVE_DAYS)
    except MissingPart as missing:
        _refuse_missing_part(missing.missing, missing)
    except NtileWithNoParts as ntile:
        _refuse_ntile_of_no_parts(ntile.parts)
    except sqlglot.errors.SqlglotError as error:  # such as a column it can't find
        _refuse_hive_it_cant_run(reason_without_place(error), tables, error)
