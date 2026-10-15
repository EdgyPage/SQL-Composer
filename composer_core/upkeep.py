"""Upkeep and speed: repair_partitions, compute_statistics and explain.

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
    Table,
    as_date,
    day_text,
    need_saved_table,
    partition_columns,
    table_node,
)
from .trees import Node
from .unchecked import SessionSettings, UncheckedStatement

TOOLBOX_VERSION = "4.1"


def _upkeep(tree: Node) -> Statement:
    s = Statement()
    s._ddl = tree
    return s


def repair_partitions(t):
    """The MSCK REPAIR TABLE Statement, which finds the days in a Saved table's folder.

    The warehouse keeps a list of each table's Partitions, the day folders it reads, and never
    reads a folder missing from it. A folder goes missing from it when files reach the table's
    folder without a write: when create_table makes a table again where an old one's files
    stayed, since it was dropped without purge=True, or when someone copies files in.
    run(repair_partitions(t), send=...) adds each day folder it finds to the list. It only adds:
    it deletes no file and no day, so it is safe to send again. It takes only one of your Saved
    tables, a Table reference with location= and a Date partition. The Example database can't
    run it, as its tables are made up and fixed.

    >>> daily_runs = Table("mart.daily_runs", date_partition="dt",
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/tables")
    >>> print(to_hive(repair_partitions(daily_runs)))
    MSCK REPAIR TABLE mart.daily_runs
    """
    t = need_saved_table(t, "repair_partitions")
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
    """The ANALYZE TABLE Statement, counting a Saved table's day for Hive's planner.

    Hive picks how to join a table from its statistics: how many rows and bytes each day
    holds. Without them it guesses, and may sort two big tables to join them where copying a
    small one to every worker would do; the Session setting "map_joins" lets Hive make that
    choice. run(compute_statistics(t, day), send=...) reads the day's files, counts them again
    and keeps what it counts in place of what was there, so it is safe to send again; it
    changes no row. The Session setting "statistics_on_write", sent before your writes, has
    each write count its day as it writes it: this is for the days written without it.

    `day` is the one day to count, written as the table writes its days or as a
    datetime.date; for a table partitioned by more than its day, such as by region too, it
    counts every region of the day. A Saved table with no Date partition takes no day.
    columns=True counts each column too, all but the Partitions: how many different values it
    has, its smallest and largest, and how many are NULL, which Hive's planner reads to order
    its joins. It reads more, so columns=["job_id"] counts only the columns you join or filter
    on. Where your send runs on Spark, not Hive, Spark counts columns over every day of the
    table, whatever the day. It takes only one of your Saved tables, a Table reference with
    location=, and the Example database can't run it.

    >>> daily_runs = Table("mart.daily_runs", date_partition="dt",
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/tables")
    >>> print(to_hive(compute_statistics(daily_runs, "2026-09-24")))
    ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24') COMPUTE STATISTICS
    >>> print(to_hive(compute_statistics(daily_runs, "2026-09-24", columns=True)))
    ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24') COMPUTE STATISTICS FOR COLUMNS job_id, runs
    """
    t = need_saved_table(t, "compute_statistics")
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
    found = as_date(day, t._column(t._date_partition), f"compute_statistics({t._alias}, ...)")
    return day_text(found, t._date_format)


def _columns_counted(t: Table, columns) -> list[str]:
    """The columns FOR COLUMNS names: none, every column but the Partitions, or those named."""
    counted = [column for column in t._columns if column not in partition_columns(t)]
    if columns is False or columns is None:
        return []
    if columns is True:
        return counted
    if isinstance(columns, str):
        columns = [columns]
    if not isinstance(columns, (list, tuple)):
        refuse(
            what=f"compute_statistics({t._alias}, ..., columns={columns!r}) isn't True or a "
            "list of columns.",
            why="columns= says which columns to count as well as the day's rows.",
            fix='Write columns=True for every column, or a list, such as columns=["job_id"].',
        )
    if not columns:
        refuse(
            what=f"compute_statistics({t._alias}, ..., columns=[]) names no column.",
            why="An empty list would count no column, which isn't what columns= is for.",
            fix="Leave columns= out to count only the day's rows, or name the columns.",
            error=ValueError,
        )
    for column in columns:
        if column not in t._columns:
            refuse(
                what=f"compute_statistics({t._alias}, ..., columns=...): {column} isn't one of "
                "its columns.",
                why="It counts the columns of the table it is given.",
                fix=f"Use some of: {', '.join(counted)}.",
                error=ValueError,
            )
        if column not in counted:
            refuse(
                what=f"compute_statistics({t._alias}, ..., columns=...): {column} is a "
                "Partition.",
                why="A Partition holds one value in each folder, which the warehouse knows "
                "already, so it isn't counted.",
                fix=f"Leave it out, and name some of: {', '.join(counted)}.",
                error=ValueError,
            )
    return list(columns)


def explain(s):
    """The EXPLAIN Statement: Hive's plan for running a Statement, without running it.

    run(explain(s), send=...) gives back Hive's plan as text, which prints line by line. It
    explains exactly the Hive run(s, send=...) would send, the automatic LIMIT too, and refuses
    what to_hive(s) would. The plan is a tree of steps, each reading from the ones below it:
    TableScan reads a table, with the filters it reads it with; a Map Join copies a small table
    to every worker, where a Merge Join sorts both sides first; and each step's Statistics line
    says how many rows Hive expects, or "Basic stats: NONE" where it has none to go by and
    compute_statistics would help. Read it to see why a Statement is slow, before and after
    you change it: whether the Session setting "map_joins" turned a join into a Map Join, or
    a condition kept the read to the days it names. It only reads, so it takes any Statement,
    a write too, whose plan shows the write without making it, and it is safe to send again.
    Spark Composer's Example database gives Spark's own plan, headed == Physical Plan ==;
    sqlglot Composer's can't give one.

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
        refuse(
            what=f"explain was given {s!r}, which isn't a query or a write.",
            why="Hive plans how a Statement reads and writes rows; a Statement that creates, "
            "drops, repairs or counts a table, or explains another, has no such plan.",
            fix="Pass a Statement made by statement(...).",
            error=ValueError,
        )
