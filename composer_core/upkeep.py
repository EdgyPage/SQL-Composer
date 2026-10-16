# Composer core 5.0, exported 2026-10-16 09:20 - generated from dev, do not edit
"""Keeping reads and joins fast: repair_partitions, compute_statistics and explain.

Each gives a Statement, run like any other, and each is safe to send again. repair_partitions
and compute_statistics change only what the warehouse keeps about one of your Saved tables,
never a row of it; explain only reads. create_table(t, may_exist=True), in tables.py, is the
fourth Statement of this kind.
"""

from __future__ import annotations

import inspect

from .clauses import Statement
from .refusals import refuse
from .running import _check_dates_cap, _need_statement, _statement_tree, day_partition
from .tables import (
    Column,
    Table,
    as_date,
    day_text,
    need_saved_table,
    partition_columns,
    table_node,
)
from .trees import Node
from .unchecked import SessionSettings, UncheckedStatement

TOOLBOX_VERSION = "5.0"


def _upkeep(tree: Node) -> Statement:
    s = Statement()
    s._ddl = tree
    return s


def repair_partitions(t):
    """The MSCK REPAIR TABLE Statement, which lists the days in a Saved table's folder.

    The warehouse keeps a list of each table's Partitions, the day folders it reads, and never
    reads a folder missing from it. A folder goes missing from the list when files reach the
    table's folder without a write: when create_table makes a table again where an old one's
    files stayed, because it was dropped without purge=True, or when someone copies files in.
    run(repair_partitions(t), send=...) adds each day folder it finds to the list. It only
    adds: it deletes no file and no day, so it is safe to send again.

    It takes only one of your Saved tables, a Table reference with location= and a Date
    partition. The Example database can't run it, as its tables are made up and fixed.

    >>> daily_runs = Table("mart.daily_runs", date_partition="dt",
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/tables")
    >>> print(to_hive(repair_partitions(daily_runs)))
    MSCK REPAIR TABLE mart.daily_runs
    """
    t = need_saved_table(t, "repair_partitions(...)")
    if t._date_partition is None:
        refuse(
            what=f"repair_partitions({t._alias}): {t._name} has no Date partition, so it has "
            "no day folders to find.",
            why="MSCK REPAIR TABLE lists the Partitions in a table's folder, and a table with "
            "none keeps all its files in one folder, which the warehouse always reads.",
            fix="Leave it out: the table needs no repair.",
            error=ValueError,
        )
    return _upkeep(Node("Repair", target=table_node(t._name)))


def compute_statistics(t, day=None, columns=False):
    """The ANALYZE TABLE Statement, which counts a Saved table's rows for one day.

    Hive picks how to join a table from its statistics: how many rows and bytes each day
    holds. Without them it guesses, and may sort two big tables to join them even when
    copying a small one to every worker would do; the Session setting "map_joins" lets Hive
    choose to copy it. run(compute_statistics(t, day), send=...) reads the day's files,
    counts them again and keeps the new count in place of the old, so it is safe to send
    again; it changes no row. The Session setting "statistics_on_write", sent before your
    writes, has each write count its day as it writes it; compute_statistics is for the days
    written without that setting.

    `day` is the one day to count, written as the table writes its days or as a
    datetime.date. For a table partitioned by more than its day, such as by region too, it
    counts every region of the day. A Saved table with no Date partition (date_partition=None)
    is counted whole, and takes no day.

    columns= counts columns too, other than the Partitions: how many different values each
    has, its smallest and largest, and how many are NULL, which Hive reads to order several
    joins. columns=True counts every column; as that reads more, columns=[daily_runs.job_id]
    counts only the columns you name, such as those you join or filter on. Where your send
    runs on Spark, not Hive, Spark counts columns over every day of the table, whatever the
    day, so name only those few.

    It takes only one of your Saved tables, a Table reference with location=. The Example
    database can't run it, as its tables are made up and fixed.

    >>> daily_runs = Table("mart.daily_runs", date_partition="dt",
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/tables")
    >>> print(to_hive(compute_statistics(daily_runs, "2026-09-24")))
    ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24') COMPUTE STATISTICS
    >>> print(to_hive(compute_statistics(daily_runs, "2026-09-24", columns=True)))
    ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24') COMPUTE STATISTICS FOR COLUMNS job_id, runs
    >>> print(to_hive(compute_statistics(daily_runs, "2026-09-24",
    ...     columns=[daily_runs.job_id])))
    ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24') COMPUTE STATISTICS FOR COLUMNS job_id
    """
    t = need_saved_table(t, "compute_statistics(...)")
    target = table_node(t._name)
    if t._date_partition is not None:
        target = table_node(t._name, partition=day_partition(t, _day_counted(t, day)))
    elif day is not None:
        refuse(
            what=f"compute_statistics({t._alias}): {t._name} has no Date partition, and was "
            f"given the day {day!r}.",
            why="A table with no Date partition is counted whole, with no day to pick.",
            fix=f"Leave the day out: compute_statistics({t._alias}).",
            error=ValueError,
        )
    return _upkeep(Node("Analyze", target=target, columns=_columns_counted(t, columns)))


def _day_counted(t: Table, day) -> str:
    """The day compute_statistics counts, as the table writes its days."""
    if day is None:
        refuse(
            what=f"compute_statistics({t._alias}) needs the day to count.",
            why="Statistics are counted a day at a time, as each write fills one day: "
            "counting every day would read the whole table.",
            fix=f'Pass the day, such as compute_statistics({t._alias}, "2026-09-24").',
        )
    if isinstance(day, (list, tuple, set, range)):
        refuse(
            what=f"compute_statistics({t._alias}, {day!r}) was given several days.",
            why="It counts one day at a time, each a Statement of its own.",
            fix=f"Count each day in a loop: for day in days: run(compute_statistics("
            f"{t._alias}, day), send=...).",
        )
    found = as_date(day, t._column(t._date_partition), f"compute_statistics({t._alias}, ...)",
                    compared=False)
    return day_text(found, t._date_format)


def _columns_counted(t: Table, columns) -> list[str]:
    """The columns FOR COLUMNS names: none, every column but the Partitions, or those named."""
    counted = [column for column in t._columns if column not in partition_columns(t)]
    if columns is False or columns is None:
        return []
    if columns is True:
        return counted
    if isinstance(columns, (str, Column)):
        columns = [columns]
    if not isinstance(columns, (list, tuple)) or not columns:
        refuse(
            what=f"compute_statistics({t._alias}, ..., columns={columns!r}) isn't True or a "
            "list of columns.",
            why="columns= says which columns to count as well as the day's rows.",
            fix=f"Write columns=True for every column, or a list, such as "
            f"columns=[{t._alias}.{counted[0]}].",
        )
    names = [_column_name(t, column) for column in columns]
    for name in names:
        if name not in counted:
            refuse(
                what=f"compute_statistics({t._alias}, ..., columns=...): {name} is a "
                "Partition.",
                why="A Partition holds one value in each folder, which the warehouse knows "
                "already, so it isn't counted.",
                fix=f"Leave it out, and name some of: {', '.join(counted)}.",
                error=ValueError,
            )
    return names


def _column_name(t: Table, column) -> str:
    """The name of a column given to columns=: one of t's, as t.job_id or as "job_id"."""
    if isinstance(column, Column) and column._table is t and column._name in t._columns:
        return column._name
    if isinstance(column, str) and column in t._columns:
        return column
    shown = repr(column) if isinstance(column, Column) else str(column)
    refuse(
        what=f"compute_statistics({t._alias}, ..., columns=...): {shown} isn't one of "
        f"{t._alias}'s columns.",
        why="It counts the columns of the table it is given.",
        fix=f"Name {t._alias}'s own columns, such as columns=[{t._alias}."
        f"{next(iter(t._columns))}].",
        error=ValueError,
    )


def explain(s):
    """The EXPLAIN Statement: Hive's plan for running a Statement, without running it.

    run(explain(s), send=...) gives back Hive's plan as text, which prints line by line. It is
    the plan of exactly the Hive run(s, send=...) would send, with the LIMIT run adds when
    set_load_limits(rows=...) is on, and explain refuses what to_hive(s) would refuse. It
    only reads, so it takes any Statement statement(...) makes, a write too, whose plan shows
    the write without making it; and it is safe to send again.

    Read the plan to see why a Statement is slow, before and after you change it. It is a
    tree of steps, each reading what the steps under it give:

    - TableScan reads a table, with the filters it reads it with, so you can see a condition
      keep the read to the days it names;
    - a Map Join copies a small table to every worker, as the Session setting "map_joins"
      lets Hive choose, where a Merge Join sorts both sides first;
    - each step's line headed "Statistics:" says how many rows Hive expects, or
      "Basic stats: NONE" where it has nothing to go by and compute_statistics would help.

    On the Example database, explain gives the plan of a query only, never of a write, which
    it refuses as it refuses the write itself. Where it runs on Spark, it gives Spark's own
    plan, headed == Physical Plan ==; where it runs on its own small executor, it says it has
    none to give.

    >>> print(to_hive(explain(statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24")),
    ... ))))
    EXPLAIN SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24'
    """
    _need_explainable(s, inspect.currentframe().f_back)
    _check_dates_cap(s)
    return _upkeep(Node("Explain", this=_statement_tree(s)))


# The function that makes each Statement explain has no plan for, by its kind.
_MADE_BY = {"Create": "create_table", "Repair": "repair_partitions",
            "Analyze": "compute_statistics", "Explain": "explain"}


def _need_explainable(s, frame) -> None:
    """Refuse what explain can't explain: Hive written by hand, Session settings, what isn't a
    Statement, and a Statement that creates, drops or keeps up a table."""
    if isinstance(s, UncheckedStatement):
        refuse(
            what="explain was given an Unchecked statement.",
            why="explain shows Hive's plan for a Statement it wrote itself, and Hive written by "
            "hand is sent as written.",
            fix='Write EXPLAIN at the start of its text: unchecked_hive("EXPLAIN ...").',
        )
    if isinstance(s, SessionSettings):
        refuse(
            what=f"explain was given {s!r}.",
            why="Session settings have no plan: they change how Hive plans the Statements sent "
            "after them.",
            fix="Send them with run(...), then pass explain the Statement they're sent before.",
        )
    _need_statement(s, "explain", frame,
                    why="explain shows Hive's plan for one Statement made by statement(...).")
    if s._ddl is not None:
        made_by = None if s._admin_call is not None else _MADE_BY.get(s._ddl.kind)
        given = f"the Statement {made_by}(...) makes" if made_by else "an Admin statement"
        refuse(
            what=f"explain was given {given}, which isn't a query or a write.",
            why="Hive plans how a Statement reads and writes rows; a Statement that creates, "
            "changes, drops, repairs or counts a table, or explains another, has no such plan.",
            fix="Pass a Statement made by statement(...).",
            error=ValueError,
        )
