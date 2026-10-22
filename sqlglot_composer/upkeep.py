"""Keeping reads and joins fast: repair_partitions, compute_statistics and explain.

Each gives a Statement, run like any other, and each is safe to send again. repair_partitions
and compute_statistics change only what the warehouse keeps about one of your Saved tables,
never a row of it; explain only reads. create_table(t, may_exist=True), in tables.py, is the
fourth Statement of this kind.
"""

from __future__ import annotations

import inspect
from types import FrameType

from .clauses import Statement
from .refusals import arguments_of, refuse, refuse_removed_arguments
from .running import _need_statement, _statement_tree
from .tables import (
    Column,
    Table,
    literal,
    need_saved_table,
    partition_columns,
    python_text,
    table_node,
)
from .trees import Node
from .unchecked import SessionSettings, UncheckedStatement

TOOLBOX_VERSION = "7.0"


def _upkeep(tree: Node) -> Statement:
    s = Statement()
    s._ddl = tree
    return s


def repair_partitions(t: Table) -> Statement:
    """The MSCK REPAIR TABLE Statement, which finds a Saved table's Partitions.

    >>> daily_runs = Table("mart.daily_runs", partitioned_by=["dt"],
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/mart.db/daily_runs")
    >>> print(to_hive(repair_partitions(daily_runs)))
    MSCK REPAIR TABLE mart.daily_runs

    The warehouse keeps a list of each table's Partitions, the folders inside its own that it
    reads, such as dt=2026-09-24 or region=EU/dt=2026-09-24, and never reads a folder missing
    from it. A folder goes missing from the list when files reach the table's folder without a
    write: when create_table makes a table again where an old one's files stayed, because it
    was dropped without purge=True, or when someone copies files in. run(repair_partitions(t),
    execute=...) adds each Partition's folder it finds to the list. It only adds: it deletes no
    file and no Partition, so it is safe to send again.

    It takes only one of your Saved tables, a Table reference with location= and
    partitioned_by=. The Example database can't run it, as its tables are made up and fixed.
    """
    t = need_saved_table(t, "repair_partitions(...)")
    if not t._partitioned_by:
        refuse(
            what=f"repair_partitions({t._alias}): {t._name} has no partitioned_by=, so it has "
            "no Partitions to find.",
            why="MSCK REPAIR TABLE lists the Partitions in a table's folder, and a table with "
            "none keeps all its files in one folder, which the warehouse always reads.",
            fix="Leave it out: the table needs no repair.",
            error=ValueError,
        )
    return _upkeep(Node("Repair", target=table_node(t._name)))


def compute_statistics(t: Table, partition: dict[str, object] | None = None,
                       columns: bool | list[Column | str] = False,
                       **removed: object) -> Statement:
    """The ANALYZE TABLE Statement, which counts a Saved table's rows again.

    >>> daily_runs = Table("mart.daily_runs", partitioned_by=["dt"],
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/mart.db/daily_runs")
    >>> print(to_hive(compute_statistics(daily_runs)))
    ANALYZE TABLE mart.daily_runs PARTITION(dt) COMPUTE STATISTICS

    Hive picks how to join a table from its statistics: how many rows and bytes it holds, in
    each of its Partitions. Without them it guesses, and may sort two big tables to join them
    even when copying a small one to every worker would do; the Session setting "map_joins"
    lets Hive choose to copy it. run(compute_statistics(t), execute=...) reads the table's
    files, counts them again and keeps the new count in place of the old, so it is safe to
    send again; it changes no row. The Session setting "statistics_on_write", sent before your
    writes, has each write count what it writes; compute_statistics is for what was written
    without that setting.

    A table with partitioned_by= is counted a Partition at a time, every Partition unless
    `partition` names some: partition={"dt": "2026-09-24"} counts the Partitions whose dt is
    that value. Each name in it is one of the table's partition columns, and its value one
    value of it; they are the first of its partitioned_by=, as Hive needs, so a table
    partitioned by region, then dt, names its region first. A Saved table with no
    partitioned_by= is counted whole, and takes no partition=.

    columns= counts columns too, other than the partition columns: how many different values
    each has, its smallest and largest, and how many are NULL, which Hive reads to order
    several joins. columns=True counts every column; as that reads more,
    columns=[daily_runs.job_id] counts only the columns you name, such as those you join or
    filter on.

    It takes only one of your Saved tables, a Table reference with location=. The Example
    database can't run it, as its tables are made up and fixed.

    >>> print(to_hive(compute_statistics(daily_runs, partition={"dt": "2026-09-24"})))
    ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24') COMPUTE STATISTICS
    >>> print(to_hive(compute_statistics(daily_runs, partition={"dt": "2026-09-24"},
    ...     columns=True)))
    ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24') COMPUTE STATISTICS FOR COLUMNS job_id, runs
    >>> print(to_hive(compute_statistics(daily_runs, columns=[daily_runs.job_id])))
    ANALYZE TABLE mart.daily_runs PARTITION(dt) COMPUTE STATISTICS FOR COLUMNS job_id
    """
    if "day" in removed:
        refuse(
            what="compute_statistics(...) was given day=, which Toolbox 7.0 replaced.",
            why="A table's Partitions are its own, of any kind, so the Partitions to count are "
            "named by their partition columns. It takes "
            f"{arguments_of(compute_statistics)}.",
            fix='Pass partition={...} instead, such as partition={"dt": "2026-09-24"}, or '
            "leave it out to count every Partition.",
        )
    refuse_removed_arguments("compute_statistics", removed, compute_statistics)
    t = need_saved_table(t, "compute_statistics(...)")
    target = table_node(t._name, partition=_partitions_counted(t, partition))
    return _upkeep(Node("Analyze", target=target, columns=_columns_counted(t, columns)))


def _partitions_counted(t: Table, partition: object) -> Node | None:
    """ANALYZE's PARTITION(...): each partition column, as `column = value` where `partition`
    names it and by its name where it doesn't; None for an unpartitioned table."""
    call = f"compute_statistics({t._alias}, partition=...)"
    if partition is not None and not isinstance(partition, dict):
        refuse(
            what=f"compute_statistics({t._alias}, {python_text(partition)}) wasn't given a "
            "dict for partition=.",
            why="partition= names the Partitions to count, from each partition column to its "
            "value.",
            fix='Write it as a dict, such as partition={"dt": "2026-09-24"}, or leave it out '
            "to count every Partition.",
        )
    if not t._partitioned_by:
        if partition:
            refuse(
                what=f"{call}: {t._name} has no partitioned_by=, and was given "
                f"partition={python_text(list(partition))}.",
                why="A table with no Partitions is counted whole, with none to pick.",
                fix=f"Leave partition= out: compute_statistics({t._alias}).",
                error=ValueError,
            )
        return None
    named = partition or {}
    for name, value in named.items():
        if name not in t._partitioned_by:
            refuse(
                what=f"{call}: {python_text(name)} isn't one of {t._name}'s partition columns.",
                why="partition= names Partitions by the columns the table is partitioned by.",
                fix=f"Name some of: {', '.join(t._partitioned_by)}.",
                error=ValueError,
            )
        if value is None:
            refuse(
                what=f"{call}: the value of {name} is None.",
                why="partition= names Partitions by one value of each column it gives.",
                fix=f"Give {name} a value, or leave it out to count every value of it.",
                error=ValueError,
            )
    leading = t._partitioned_by[:len(named)]
    if set(named) != set(leading):
        refuse(
            what=f"{call} names {', '.join(named)}, but not the partition columns before it: "
            f"{t._name} is partitioned by {', '.join(t._partitioned_by)}.",
            why="Hive takes the values of a table's first partition columns, then the rest by "
            "name, so a value can't follow a column given by its name alone.",
            fix=f"Name {', '.join(leading)} too, or only the first of them: "
            f"partition={{{python_text(t._partitioned_by[0])}: ...}}.",
            error=ValueError,
        )
    parts = []
    for name in t._partitioned_by:
        column = Node("Column", name=name)
        if name in named:
            value = literal(named[name], call=call, column=t._column(name),
                            position=f"the value of {name}", in_condition=False)
            column = Node("EQ", this=column, expression=value)
        parts.append(column)
    return Node("Partition", expressions=parts)


def _columns_counted(t: Table, columns: object) -> list[str]:
    """The columns FOR COLUMNS names: none, every column but the partition columns, or
    those named."""
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
            why="columns= says which columns to count as well as the rows.",
            fix=f"Write columns=True for every column, or a list, such as "
            f"columns=[{t._alias}.{counted[0]}].",
        )
    names = [_column_name(t, column) for column in columns]
    for name in names:
        if name not in counted:
            refuse(
                what=f"compute_statistics({t._alias}, ..., columns=...): {name} is a "
                "partition column.",
                why="A partition column holds one value in each Partition's folder, which the "
                "warehouse knows already, so it isn't counted.",
                fix=f"Leave it out, and name some of: {', '.join(counted)}.",
                error=ValueError,
            )
    return names


def _column_name(t: Table, column: object) -> str:
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


def explain(s: Statement) -> Statement:
    """The EXPLAIN Statement: Hive's plan for running a Statement, without running it.

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

    run(explain(s), query=...) gives back Hive's plan as text, which prints line by line. It is
    the plan of exactly the Hive run(s, query=...) would send, with the LIMIT run adds when
    set_load_limits(rows=...) is on, and explain refuses what to_hive(s) would refuse. It
    only reads, so it takes any Statement statement(...) makes, a write too, whose plan shows
    the write without making it; and it is safe to send again.

    Read the plan to see why a Statement is slow, before and after you change it. It is a
    tree of steps, each reading what the steps under it give:

    - TableScan reads a table, with the filters it reads it with, so you can see a condition
      keep the read to the Partitions it names;
    - a Map Join copies a small table to every worker, as the Session setting "map_joins"
      lets Hive choose, where a Merge Join sorts both sides first;
    - each step's line headed "Statistics:" says how many rows Hive expects, or
      "Basic stats: NONE" where it has nothing to go by and compute_statistics would help.

    On the Example database, explain gives no plan: it runs its queries on a small executor of
    its own, which makes none, and says so. It refuses explain of a write as it refuses the
    write itself.
    """
    _need_explainable(s, inspect.currentframe().f_back)
    return _upkeep(Node("Explain", this=_statement_tree(s)))


# The function that makes each Statement explain has no plan for, by its kind.
_MADE_BY = {"Create": "create_table", "Repair": "repair_partitions",
            "Analyze": "compute_statistics", "Explain": "explain"}


def _need_explainable(s: object, frame: FrameType | None) -> None:
    """Refuse what explain can't explain: Hive written by hand, Session settings, what isn't a
    Statement, and a Statement that creates, drops or keeps up a table."""
    if isinstance(s, UncheckedStatement):
        refuse(
            what="explain was given an Unchecked statement.",
            why="explain shows Hive's plan for a Statement it wrote itself, and Hive written by "
            "hand is sent as written.",
            fix="Write EXPLAIN at the start of its text: "
            'unchecked_hive("EXPLAIN ...", returns_rows=True).',
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
