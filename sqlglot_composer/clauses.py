"""Clause functions: SELECT, FROM, JOIN, WHERE and the rest, assembled by statement(...).

A Statement is a list of clause functions written in SQL order, one per SQL clause:

    statement(SELECT(...), FROM(job_runs), WHERE(...), GROUP_BY(...))

statement(...) runs the Guards and Load limits that need the whole Statement, and
to_hive(...) turns it into the Hive string. derived(name, statement) names a Statement so
another Statement can read it like a table.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, NoReturn

from . import kinds
from .calculations import Ordering, ordered
from .conditions import Condition, bounded_columns
from .joins import (
    BOUNDED_IN_ON,
    ONLY_TESTS,
    check_joins,
    full_joined,
    need_broadcast_true_or_false,
    refuse_anti_join_with_nothing_matched,
    refuse_only_tests_with_no_on,
    refuse_right_join,
    tested_column,
)
from .keys import keys_of, statement_keys, unproven
from .refusals import (
    guard_cross_join,
    guard_left_join_then_where,
    guard_missing_group_by,
    guard_order_by_in_derived_table,
    guard_unnamed_calculation,
    guard_unproven_key,
    guard_write_lines_up,
    load_limit_partition_bound,
    load_limit_order_by,
    refuse,
    refuse_what_another_folder_made,
    warning_repeated_rows,
)
from .tables import Column, Table, aliased, literal, need_saved_table, python_text
from .trees import SIMPLE_NAME, Node, has_aggregate, has_window, is_aggregate
from .writing import hive_text
from .windows import refuse_a_window_in, ungrouped_in_window

if TYPE_CHECKING:
    from .stacking import Subtotals  # only for a hint: stacking.py imports this file

TOOLBOX_VERSION = "7.1"

# The order clauses come in, as in SQL. A write comes first, and the joins share one place.
ORDER = ["INSERT", "SELECT", "FROM", "JOIN", "WHERE", "GROUP_BY", "HAVING", "ORDER_BY", "LIMIT"]
WRITES = ("INSERT_OVERWRITE", "INSERT_INTO")
JOINS = ("JOIN", "LEFT_JOIN", "CROSS_JOIN", "SEMI_JOIN", "ANTI_JOIN", "FULL_JOIN")


class Clause:
    """One clause of a Statement, made by a clause function such as SELECT(...).

    >>> SELECT(jobs.job_name)
    <SELECT clause - put it in statement(...)>

    Each clause function fills in only the parts its clause has; the rest keep their
    defaults. statement(...) reads them back to build the Statement. Make one with its clause
    function, never Clause(). Write the name in a type hint, to say that a function of yours
    gives back a clause, as a Building block that joins a table does:

    >>> def with_their_jobs() -> Clause:
    ...     return JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id))
    >>> with_their_jobs()
    <JOIN clause - put it in statement(...)>
    """

    def __init__(self, name: str, *, outputs: list[tuple[Column, str]] | None = None,
                 distinct: bool = False, table: Table | None = None,
                 on: Condition | None = None, reads_all_partitions: bool = False,
                 many_matches: bool = False, keeps_only_matches: bool = False,
                 conditions: list[Condition] | None = None,
                 group_columns: list[Column | str | Subtotals] | None = None,
                 sort_keys: list[Node] | None = None, sorts_everything: bool = False,
                 n: int | None = None, unproven_key: bool = False,
                 partition: dict[str, Node] | None = None, broadcast: bool = False) -> None:
        self._name = name  # the clause function's name: "SELECT", "LEFT_JOIN", ...
        # SELECT and SELECT_DISTINCT: the (column, output name) pairs, and whether DISTINCT.
        self.outputs = outputs
        self.distinct = distinct
        # FROM, the joins and the writes: the table, a join's ON= condition, and opt-outs.
        self.table = table
        self.on = on
        self.reads_all_partitions = reads_all_partitions
        self.many_matches = many_matches
        self.keeps_only_matches = keeps_only_matches
        self.broadcast = broadcast  # a join's ask that Hive copy its table to every worker
        self.unproven_key = unproven_key  # the writes' opt-out of the Key check
        # The writes' partition={...}: each partition column it names, in the table's order,
        # with its value as a Hive literal.
        self.partition = partition or {}
        # WHERE and HAVING: the conditions. GROUP_BY: its columns and output names.
        self.conditions = conditions
        self.group_columns = group_columns
        # ORDER_BY: the sort keys, and its opt-out. LIMIT: the row count.
        self.sort_keys = sort_keys
        self.sorts_everything = sorts_everything
        self.n = n

    def _place(self) -> str:
        """This clause's place in ORDER: INSERT_INTO sits at INSERT, LEFT_JOIN at JOIN."""
        if self._name in WRITES:
            return "INSERT"
        if self._name in JOINS:
            return "JOIN"
        return self._name.replace("_DISTINCT", "")

    def _call(self) -> str:
        """How this clause was written, for messages: FROM(job_runs), JOIN(jobs, ON=...)."""
        on = ", ON=..." if self.on is not None else ""
        return f"{self._name}({self.table._alias}{on})"

    def __repr__(self) -> str:
        return f"<{self._name} clause - put it in statement(...)>"


class Named:
    """A column or calculation with the name it gets in the result, made by AS(...).

    >>> AS(count_rows(), "runs")
    COUNT(*) AS runs

    Make one with AS(...), never Named(). Write the name in a type hint, to say that a function
    of yours gives back a named column:

    >>> def runs_named() -> Named:
    ...     return AS(count_rows(), "runs")
    >>> runs_named()
    COUNT(*) AS runs
    """

    def __init__(self, column: Column, name: str) -> None:
        self._column = column
        self._name = name

    def __repr__(self) -> str:
        return hive_text(Node("Alias", this=self._column._tree.copy(), alias=self._name))


class Statement:
    """A query, made by statement(...): to_hive(s) gives its Hive string.

    >>> statement(SELECT(jobs.job_name), FROM(jobs))
    <Statement reading ops.jobs - print(to_hive(s)) shows its Hive>

    Make one with statement(...), never Statement(); a Stack, such as UNION_ALL(...), and
    explain(...) give back a Statement too. Write the name in a type hint, to say that a
    function of yours gives back a Statement:

    >>> def failed_runs(first_day: str, last_day: str) -> Statement:
    ...     return statement(
    ...         SELECT(job_runs.run_id, job_runs.status),
    ...         FROM(job_runs),
    ...         WHERE(between(job_runs.dt, first_day, last_day),
    ...               equals(job_runs.status, "FAILED")),
    ...     )
    >>> print(to_hive(failed_runs("2026-09-23", "2026-09-24")))
    SELECT
      job_runs.run_id,
      job_runs.status
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24' AND job_runs.status = 'FAILED'
    """

    def __init__(self) -> None:
        # What it is, as kinds.py names it: its maker marks it, a read until then.
        self._kind = kinds.READ
        # Filled in by statement(...), from the clauses it was given:
        self._clauses = ()  # the clauses, in the order written
        self._returns_all_rows = False  # the opt-out of the automatic LIMIT
        self._write = None  # the Saved table an INSERT_OVERWRITE or INSERT_INTO writes
        self._write_call = None  # how that write was called, for messages
        self._replaces_rows = False  # True for INSERT_OVERWRITE, False for INSERT_INTO
        # The write's partition={...}: each partition column it names, with its value as Hive
        # text, such as {"region": "'EU'"}; empty when it names none.
        self._static_partitions = {}
        self._unproven_key = False  # the write's opt-out of the Key check
        self._outputs = []  # SELECT's (column, output name) pairs
        self._distinct = False  # whether it is SELECT_DISTINCT
        self._reads = []  # the FROM clause, then each join clause
        self._where = []  # WHERE's conditions
        self._having = []  # HAVING's conditions
        self._group_by = []  # GROUP_BY's columns, with output names looked up
        # With subtotals in GROUP_BY: each set of columns it groups by, and how the subtotals
        # were written, such as rollup(jobs.team); else None (stacking.py).
        self._grouping_sets = None
        self._subtotals_call = None
        self._order_by = []  # ORDER_BY's sort keys
        self._limit = None  # LIMIT's row count
        # Set instead by create_table and the admin module, whose Statement is a CREATE, DROP
        # or other tree ready to write, with none of the parts above. An ALTER TABLE keeps the
        # table it changes here, and its Hive in _admin_hive.
        self._ddl = None
        # Set by the admin module on each Admin statement: the call that made it, which the
        # Admin log names when run_execute sends it; and what it changes, which show_hive
        # prints first, a sentence to each item.
        self._admin_call = None
        self._admin_about = []
        # The Hive of an ALTER TABLE, which the admin module writes itself from pieces
        # writing.py wrote: the table's name, values and column types.
        self._admin_hive = None
        # Set instead by UNION_ALL, UNION, INTERSECT and EXCEPT (stacking.py) on a Stack:
        # (the function's name, the Statements it stacks). Its _outputs are then its columns,
        # and it has none of the clauses above.
        self._stack = None

    def __repr__(self) -> str:
        if not kinds.is_a_query(self):
            return "<Statement - print(to_hive(s)) shows it>"
        if self._stack is not None:
            call, branches = self._stack
            return (f"<Statement stacking {len(branches)} Statements with {call} - "
                    "print(to_hive(s)) shows its Hive>")
        reads = ", ".join(read.table._name for read in self._reads)
        return f"<Statement reading {reads} - print(to_hive(s)) shows its Hive>"


# --- Naming things -------------------------------------------------------------------------


def AS(expression: Column | Table, name: str) -> Named | Table:
    """Name a calculation, as AS(count_rows(), "runs"), or give a table a second name.

    >>> AS(count_rows(), "runs")
    COUNT(*) AS runs
    >>> AS(job_runs.duration_mins / 60, "hours")
    job_runs.duration_mins / 60 AS hours

    Every calculation in SELECT needs a name, which becomes its column in pandas. Arithmetic
    uses Python's + - * / and comes out bracketed. / divides as Python's / does, so 7 / 2 is
    3.5, and dividing by zero gives NULL rather than an error.

    A table named twice in one Statement, such as a table joined to itself, needs a second
    name for one of them: AS(job_runs, "earlier") is read as FROM ops.job_runs AS earlier.
    """
    if isinstance(expression, Table):
        return aliased(expression, name)
    if isinstance(expression, Named):
        expression = expression._column
    if not isinstance(expression, Column):
        refuse(
            what=f"AS was given {expression!r}, which can't be named.",
            why="AS names a column or a calculation for SELECT, or a table for FROM or JOIN.",
            fix='Pass a column or calculation first, such as AS(count_rows(), "runs").',
            given=expression, call="AS",
        )
    if not isinstance(name, str) or not name:
        refuse(
            what=f"AS(..., {name!r}) needs a name as a string.",
            why="The name becomes the column's name in the result.",
            fix='Write it like AS(count_rows(), "runs").',
        )
    return Named(expression, name)


# --- Clause functions ----------------------------------------------------------------------


def _flatten(items: list[object] | tuple[object, ...]) -> list[object]:
    found = []
    for item in items:
        if isinstance(item, (list, tuple)):
            found.extend(_flatten(item))
        else:
            found.append(item)
    return found


def _outputs(items: tuple[object, ...], call: str) -> list[tuple[Column, str]]:
    outputs = []
    for item in _flatten(items):
        if isinstance(item, Named):
            outputs.append((item._column, item._name))
        elif isinstance(item, Column) and item._name is not None:
            outputs.append((item, item._name))
        elif isinstance(item, Column):
            guard_unnamed_calculation(repr(item))
        else:
            _refuse_output(item, call)
    if not outputs:
        refuse(what=f"{call} was given nothing to select.", why="A Statement returns columns.",
               fix="Name the columns, such as SELECT(job_runs.run_id, job_runs.status).")
    names = [name for _, name in outputs]
    twice = sorted({name for name in names if names.count(name) > 1})
    if twice:
        refuse(
            what=f"{call} has more than one column called {', '.join(twice)}.",
            why="Each column in the result needs its own name, or pandas can't tell them apart.",
            fix='Rename one with AS, such as AS(jobs.job_id, "jobs_job_id").',
            error=ValueError,
        )
    return outputs


def _refuse_output(item: object, call: str) -> NoReturn:
    refuse_what_another_folder_made(item, call)
    if isinstance(item, Table):
        fix = f"Name its columns, or use all_columns({item._alias})."
    elif isinstance(item, Condition) and any(item._tree.find_all("Grouping")):
        fix = (f"To show it as a column, use AS(if_else({python_text(item)}, 1, 0), "
               '"is_subtotal").')
    elif isinstance(item, Condition):
        fix = 'A condition goes in WHERE. To show it as a column, use if_else(condition, 1, 0).'
    else:
        fix = "Pass columns such as job_runs.status, or calculations named with AS(...)."
    refuse(what=f"{call} was given {item!r}.", why="SELECT takes columns and calculations.",
           fix=fix)


def SELECT(*columns: Column | Named | list[Column | Named]) -> Clause:
    """The columns and named calculations a Statement returns; takes a list too.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.status, AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY(job_runs.status),
    ... )))
    SELECT
      job_runs.status,
      COUNT(*) AS runs
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    GROUP BY
      job_runs.status
    """
    return Clause("SELECT", outputs=_outputs(columns, "SELECT(...)"), distinct=False)


def SELECT_DISTINCT(*columns: Column | Named | list[Column | Named]) -> Clause:
    """Like SELECT, but each different row comes back once.

    >>> print(to_hive(statement(
    ...     SELECT_DISTINCT(jobs.team),
    ...     FROM(jobs),
    ... )))
    SELECT DISTINCT
      jobs.team
    FROM ops.jobs AS jobs
    """
    return Clause("SELECT_DISTINCT", outputs=_outputs(columns, "SELECT_DISTINCT(...)"),
                  distinct=True)


def _need_table(table: object, call: str) -> Table:
    if isinstance(table, Table):
        return table
    refuse(
        what=f"{call} was given {table!r}, which isn't a table.",
        why="It reads a Table reference, or a Statement named with derived(...).",
        fix="Pass the table itself, such as FROM(job_runs).",
        given=table, call=call,
    )


def FROM(table: Table, reads_all_partitions: bool = False) -> Clause:
    """The table a Statement reads; WHERE must filter a partitioned one's Partitions.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    ... )))
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'

    A partitioned table, such as job_runs with partitioned_by=["dt"], is stored a Partition at
    a time, and reading every Partition of a big table can stall the cluster, so a read that
    filters none of its partition columns is refused; reads_all_partitions=True reads them all
    anyway. A table that isn't partitioned is never refused.
    """
    return Clause("FROM", table=_need_table(table, "FROM(...)"), on=None,
                  reads_all_partitions=reads_all_partitions)


def _need_on(on: object, call: str, table: Table) -> Condition:
    if on is None and call in ONLY_TESTS:
        refuse_only_tests_with_no_on(call, table._alias)
    if on is None:
        guard_cross_join(call, table._alias)
    if not isinstance(on, Condition):
        refuse(
            what=f"{call}({table._alias}, ON={on!r}): ON= isn't a condition.",
            why="ON= says which rows of the two tables belong together.",
            fix=f"Pass a condition, such as ON=equals({table._alias}.job_id, job_runs.job_id).",
            given=on, call=call,
        )
    return on


def _and_parts(tree: Node) -> list[Node]:
    """The conditions an AND joins, an AND in brackets inside it, as from all_of(...) inside
    all_of(...), joined the same way."""
    if tree.kind != "And":
        return [tree]
    return [part for side in tree.flatten() for part in _and_parts(side)]


def _matched_columns(table: Table, on: Condition) -> list[str]:
    """The columns of `table` that ON= pins with an equals joined by AND at its top."""
    parts = _and_parts(on._tree)
    matched = set()
    for part in parts:
        if part.kind != "EQ":
            continue
        sides = (part.parts["this"], part.parts["expression"])
        for mine, other in (sides, sides[::-1]):
            if mine.kind == "Column" and mine.table == table._alias and not (
                    other.kind == "Column" and other.table == table._alias):
                matched.add(mine.name)
    return sorted(matched)


def _refuse_a_column_compared_with_itself(call: str, table: Table, on: Condition) -> None:
    """Refuse an ON= that sets a column of the joined table equal to the same column of a table
    with the same name, as when one Statement reads one Building block twice.

    The SQL reads both sides as the same column of the same table, so ON= pairs every row with
    every row. Refused here, at the join, before the repeated-rows Warning, which would say
    the join matches on nothing.
    """
    alias = table._alias
    for part in on._tree.find_all("EQ"):
        sides = (part.parts["this"], part.parts["expression"])
        if all(side.kind == "Column" and side.table == alias for side in sides) and (
                sides[0].name == sides[1].name):
            column = f"{alias}.{sides[0].name}"
            if table._statement is None:
                called = f"both sides are tables called {alias}"
                fix = (f'To read {alias} twice, give the second a name of its own with AS: '
                       f'earlier = AS({alias}, "earlier"), then JOIN(earlier, ON=...) with '
                       "earlier's columns.")
            else:
                called = (f"both sides are Derived tables called {alias}, the name given to "
                          "derived(...)")
                fix = (f"To read a Derived table twice, give the second a name of its own. "
                       f"Built for other days, give it another name in derived(...), such as "
                       f'"{alias}_earlier": a Building block can take the name as an '
                       f'argument. The same one twice: AS(it, "earlier").')
            refuse(
                what=f"{call}({alias}, ON=...) compares {column} with {column}: {called}.",
                why="The SQL reads both sides as one column of one table, so every row of the "
                f"tables before the join would match every {alias} row.",
                fix=fix,
                error=ValueError,
            )


def _join(call: str, table: object, on: object, many_matches: bool,
          reads_all_partitions: bool, broadcast: object = False, **more: bool) -> Clause:
    table = _need_table(table, f"{call}(...)")
    on = _need_on(on, call, table)
    need_broadcast_true_or_false(call, table, broadcast)
    _refuse_a_column_compared_with_itself(call, table, on)
    matched = _matched_columns(table, on)
    if call not in ONLY_TESTS and not any(set(key) <= set(matched) for key in keys_of(table)):
        warning_repeated_rows(call, table._alias, matched, table._key, many_matches,
                              derived=table._statement is not None,
                              lost=table._keys.lost if table._statement is not None else None)
    return Clause(call, table=table, on=on, reads_all_partitions=reads_all_partitions,
                  many_matches=many_matches, broadcast=broadcast, **more)


def JOIN(table: Table, ON: Condition | None = None, many_matches: bool = False,
         reads_all_partitions: bool = False, broadcast: bool = False) -> Clause:
    """Add a second table's columns to the rows its ON= condition matches.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id, jobs.team),
    ...     FROM(job_runs),
    ...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ... )))
    SELECT
      job_runs.run_id,
      jobs.team
    FROM ops.job_runs AS job_runs
    JOIN ops.jobs AS jobs
      ON jobs.job_id = job_runs.job_id
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'

    When ON= doesn't pin down the joined table's whole Key, one row can match several, and
    sums over them come out too big. The Statement is still built, with a warning at your
    JOIN line; many_matches=True says you mean it and silences it. To keep only the rows that
    have a match, each once, without the joined table's columns, use SEMI_JOIN.

    broadcast=True asks for a map join: a small joined table, such as jobs, is copied whole to
    every worker (each of the machines that share the work), so each matches the big table's
    rows where they are, without first sorting them and sending them across the cluster.
    JOIN, LEFT_JOIN, SEMI_JOIN and ANTI_JOIN take it; FULL_JOIN doesn't, since it keeps the
    small table's unmatched rows too. It is written as a hint after SELECT, as below: a
    comment, /*+ ... */, that Hive reads as a request. Send the Session setting "map_joins"
    first, with run_execute(hive_settings("map_joins"), execute): Hive ignores the hint without it.
    You rarely need the hint, though: with "map_joins" sent, Hive makes map joins by itself,
    from the tables' sizes and statistics. Ask for it only for a table you know is small:
    copied to every worker, a big one can run them out of memory.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id, jobs.team),
    ...     FROM(job_runs),
    ...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), broadcast=True),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ... )))
    SELECT /*+ MAPJOIN(jobs) */
      job_runs.run_id,
      jobs.team
    FROM ops.job_runs AS job_runs
    JOIN ops.jobs AS jobs
      ON jobs.job_id = job_runs.job_id
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    """
    return _join("JOIN", table, ON, many_matches, reads_all_partitions, broadcast)


def LEFT_JOIN(table: Table, ON: Condition | None = None, keeps_only_matches: bool = False,
              many_matches: bool = False, reads_all_partitions: bool = False,
              broadcast: bool = False) -> Clause:
    """Like JOIN, but rows with no match are kept, with NULL in the joined columns.

    >>> print(to_hive(statement(
    ...     SELECT(jobs.job_name, AS(count_rows(where=is_not_null(job_runs.run_id)), "runs")),
    ...     FROM(jobs),
    ...     LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
    ...                                   last_n_days(job_runs.dt, 2)), many_matches=True),
    ...     GROUP_BY(jobs.job_name),
    ... )))
    SELECT
      jobs.job_name,
      COUNT(CASE WHEN NOT job_runs.run_id IS NULL THEN 1 END) AS runs
    FROM ops.jobs AS jobs
    LEFT JOIN ops.job_runs AS job_runs
      ON job_runs.job_id = jobs.job_id
      AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    GROUP BY
      jobs.job_name

    A condition on the joined table in WHERE would throw those rows away again, so it is
    refused: put it in ON= instead, filter the joined table's partition columns there too,
    or pass keeps_only_matches=True if you mean it. A WHERE that keeps the rows with no match is
    allowed: is_null(...) of a joined column, or any_of(...) that has such an is_null among
    its conditions, as for the jobs that never ran or whose run failed; ANTI_JOIN keeps just
    the rows with no match. broadcast=True asks for a map join, as JOIN's does.
    """
    return _join("LEFT_JOIN", table, ON, many_matches, reads_all_partitions, broadcast,
                 keeps_only_matches=keeps_only_matches)


def CROSS_JOIN(table: Table, reads_all_partitions: bool = False) -> Clause:
    """Pair every row with every row of another table, with no ON=.

    >>> other = AS(jobs, "other")
    >>> print(to_hive(statement(
    ...     SELECT(jobs.job_name, AS(other.job_name, "other_job")),
    ...     FROM(jobs),
    ...     CROSS_JOIN(other),
    ... )))
    SELECT
      jobs.job_name,
      other.job_name AS other_job
    FROM ops.jobs AS jobs
    CROSS JOIN ops.jobs AS other

    JOIN and LEFT_JOIN refuse a join with no ON=, because pairing every row with every row
    multiplies the rows and every sum and count over them. CROSS_JOIN is the opt-out of that
    refusal: its name says you mean every row with every row, so it takes no ON=.

    Joining a table to itself needs a second name for it, given with AS, as `other` is above.
    """
    return Clause("CROSS_JOIN", table=_need_table(table, "CROSS_JOIN(...)"), on=None,
                  reads_all_partitions=reads_all_partitions)


def SEMI_JOIN(table: Table, ON: Condition | None = None, reads_all_partitions: bool = False,
              broadcast: bool = False) -> Clause:
    """Keep each row another table matches, once, adding none of that table's columns.

    >>> run_alerts = example_database.run_alerts
    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id, job_runs.status),
    ...     FROM(job_runs),
    ...     SEMI_JOIN(run_alerts, ON=all_of(equals(run_alerts.run_id, job_runs.run_id),
    ...                                     equals(run_alerts.severity, "high"),
    ...                                     last_n_days(run_alerts.dt, 2))),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ... )))
    SELECT
      job_runs.run_id,
      job_runs.status
    FROM ops.job_runs AS job_runs
    LEFT SEMI JOIN ops.run_alerts AS run_alerts
      ON run_alerts.run_id = job_runs.run_id
      AND run_alerts.severity = 'high'
      AND run_alerts.dt BETWEEN '2026-09-23' AND '2026-09-24'
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'

    Where JOIN gives a row for each match, so a run with three alerts comes out three times,
    SEMI_JOIN keeps the run once however many match: it never repeats rows, so it needs no
    many_matches=. Hive adds none of the joined table's columns to the rows, so only ON= may
    read them: a SELECT, WHERE or any other clause that reads one is refused. Filter the
    joined table's partition columns inside ON=. It is written LEFT SEMI JOIN: LEFT, as the
    rows kept are those of the tables on its left, before it. broadcast=True asks for a map
    join, as JOIN's does. The example above keeps the runs that raised a high alert.
    """
    return _join("SEMI_JOIN", table, ON, False, reads_all_partitions, broadcast)


def ANTI_JOIN(table: Table, ON: Condition | None = None, reads_all_partitions: bool = False,
              broadcast: bool = False) -> Clause:
    """Keep each row with no match in another table, such as the jobs that never ran.

    >>> print(to_hive(statement(
    ...     SELECT(jobs.job_id, jobs.job_name),
    ...     FROM(jobs),
    ...     ANTI_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
    ...                                   last_n_days(job_runs.dt, 2))),
    ... )))
    SELECT
      jobs.job_id,
      jobs.job_name
    FROM ops.jobs AS jobs
    LEFT JOIN ops.job_runs AS job_runs
      ON job_runs.job_id = jobs.job_id
      AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    WHERE
      job_runs.job_id IS NULL

    Hive 3 has no anti join of its own, so it is written as a LEFT JOIN, which gives a row with
    no match NULL in every joined column, then a WHERE that keeps the rows where the joined
    table's column ON= matches with equals(...) is NULL: a row with a match has a value
    there. So ON= needs an equals(...) on a column of the joined table, joined with all_of(...)
    to any other condition. Every joined column is NULL in the rows it keeps, so only ON= may
    read them, and a clause that reads one is refused. Filter the joined table's partition
    columns inside ON=: only its rows in those Partitions count as a match. It never repeats
    rows, since the rows with a match, however many, are all left out. broadcast=True asks for
    a map join, as JOIN's does.
    """
    clause = _join("ANTI_JOIN", table, ON, False, reads_all_partitions, broadcast)
    if tested_column(clause.table, clause.on) is None:
        refuse_anti_join_with_nothing_matched(clause.table)
    return clause


def FULL_JOIN(table: Table, ON: Condition | None = None, keeps_only_matches: bool = False,
              many_matches: bool = False, reads_all_partitions: bool = False) -> Clause:
    """Pair two tables' matching rows, and keep each table's rows with no match.

    >>> recorded = derived("recorded", statement(
    ...     SELECT(job_runs.run_id), FROM(job_runs), WHERE(last_n_days(job_runs.dt, 2))))
    >>> scheduler_runs = example_database.scheduler_runs
    >>> started = derived("started", statement(
    ...     SELECT(scheduler_runs.run_id), FROM(scheduler_runs),
    ...     WHERE(last_n_days(scheduler_runs.dt, 2))))
    >>> print(to_hive(statement(
    ...     SELECT(AS(recorded.run_id, "in_job_runs"),
    ...            AS(started.run_id, "in_scheduler_runs")),
    ...     FROM(recorded),
    ...     FULL_JOIN(started, ON=equals(started.run_id, recorded.run_id)),
    ...     WHERE(any_of(is_null(recorded.run_id), is_null(started.run_id))),
    ... )))
    WITH recorded AS (
      SELECT
        job_runs.run_id
      FROM ops.job_runs AS job_runs
      WHERE
        job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    ), started AS (
      SELECT
        scheduler_runs.run_id
      FROM ops.scheduler_runs AS scheduler_runs
      WHERE
        scheduler_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    )
    SELECT
      recorded.run_id AS in_job_runs,
      started.run_id AS in_scheduler_runs
    FROM recorded
    FULL JOIN started
      ON started.run_id = recorded.run_id
    WHERE
      recorded.run_id IS NULL OR started.run_id IS NULL

    Use it to compare two records of the same things, such as the runs job_runs holds and the
    runs the scheduler started: each run comes out once, matched or not, with NULL in the
    columns of the side that lacks it, and fill_null(...) takes a value from whichever side
    has one. A WHERE on either side's columns would throw away the rows the other side lacks,
    so it is refused, unless it keeps them: is_null(...) of a column, or any_of(...) with such
    an is_null among its conditions. keeps_only_matches=True lets such a WHERE through, for
    when losing those rows is what you mean. For the same reason, read a partitioned table,
    on either side, through a derived(...) table that filters its partition columns in its own
    WHERE, and FULL_JOIN that: ON= can't filter it, since FULL_JOIN keeps the rows ON= doesn't
    match anyway. Either side's columns may be NULL, so its rows have no Key the Toolbox can
    see: a write needs a GROUP_BY to give them one, such as
    GROUP_BY(fill_null(recorded.run_id, started.run_id)) for the example above. A
    repeated-rows Warning, and its many_matches=True, work as JOIN's do. The example above
    gives the runs only one side holds.
    """
    return _join("FULL_JOIN", table, ON, many_matches, reads_all_partitions,
                 keeps_only_matches=keeps_only_matches)


def RIGHT_JOIN(table: Table, ON: Condition | None = None, **anything: object) -> NoReturn:
    """Refused: write LEFT_JOIN with the two tables swapped, which keeps the same rows.

    >>> RIGHT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id))
    Traceback (most recent call last):
    ...
    ValueError:
      What happened:  RIGHT_JOIN(jobs, ...): the Toolbox doesn't write a RIGHT JOIN.
    ...

    A RIGHT JOIN keeps every row of the table it joins, and only the matching rows of the
    tables before it. The Toolbox writes it as LEFT_JOIN, which reads in the order the rows
    are kept: the table whose every row you want goes in FROM, and the other in
    LEFT_JOIN(..., ON=...), with the same ON=.
    """
    refuse_right_join(table)


def WHERE(*conditions: Condition | list[Condition]) -> Clause:
    """Keep only the rows where every condition holds (they are joined with AND).

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.status, "FAILED"), last_n_days(job_runs.dt, 2)),
    ... )))
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.status = 'FAILED' AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    """
    return Clause("WHERE", conditions=_conditions(conditions, "WHERE(...)"))


def _conditions(items: tuple[object, ...], call: str) -> list[Condition]:
    found = _flatten(items)
    for item in found:
        if not isinstance(item, Condition):
            refuse(
                what=f"{call} was given {item!r}, which isn't a condition.",
                why="It keeps rows by conditions made with functions such as equals(...).",
                fix='Pass conditions, such as equals(job_runs.status, "FAILED").',
                given=item, call=call,
            )
    if not found:
        refuse(what=f"{call} was given no conditions.", why="It needs at least one.",
               fix="Pass a condition, or leave the clause out.")
    return found


def GROUP_BY(*columns: Column | str | Subtotals | list[Column | str | Subtotals]) -> Clause:
    """Group rows that share these values, one output row per group.

    >>> print(to_hive(statement(
    ...     SELECT(AS(week_start(job_runs.dt), "week"), AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY("week"),
    ... )))
    SELECT
      CAST(NEXT_DAY(DATE_ADD(job_runs.dt, 7 * -1), 'MO') AS STRING) AS week,
      COUNT(*) AS runs
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    GROUP BY
      CAST(NEXT_DAY(DATE_ADD(job_runs.dt, 7 * -1), 'MO') AS STRING)

    A calculation may be named by its output name, such as GROUP_BY("week"), and the
    Toolbox repeats it, since Hive can't group by a name given in SELECT. For subtotal rows
    added to the groups' rows, pass rollup(...), cube(...) or grouping_sets(...), with any
    plain columns: GROUP_BY(rollup(jobs.team, jobs.job_name)).
    """
    from .stacking import Subtotals  # here: stacking.py imports this file

    items = _flatten(columns)
    if not items:
        refuse(what="GROUP_BY was given nothing to group by.", why="It needs a column.",
               fix='Pass columns or output names, such as GROUP_BY(job_runs.status, "week").')
    for item in items:
        if not isinstance(item, (Column, str, Subtotals)):
            refuse(
                what=f"GROUP_BY was given {item!r}.",
                why="It groups by columns, or by the name of a calculation in SELECT.",
                fix='Pass columns or output names, such as GROUP_BY(job_runs.status, "week").',
                given=item, call="GROUP_BY",
            )
    return Clause("GROUP_BY", group_columns=items)


def HAVING(*conditions: Condition | list[Condition]) -> Clause:
    """Keep only the groups where every condition holds, tested after GROUP_BY.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.job_id, AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY(job_runs.job_id),
    ...     HAVING(at_least(count_rows(), 3)),
    ... )))
    SELECT
      job_runs.job_id,
      COUNT(*) AS runs
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    GROUP BY
      job_runs.job_id
    HAVING
      COUNT(*) >= 3
    """
    return Clause("HAVING", conditions=_conditions(conditions, "HAVING(...)"))


def ORDER_BY(*columns: Column | str | Ordering | list[Column | str | Ordering],
             sorts_everything: bool = False) -> Clause:
    """Sort the result; it needs a LIMIT, as sorting every row is slow, or use pandas.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY(job_runs.job_id),
    ...     ORDER_BY(descending("minutes")),
    ...     LIMIT(3),
    ... )))
    SELECT
      job_runs.job_id,
      SUM(job_runs.duration_mins) AS minutes
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    GROUP BY
      job_runs.job_id
    ORDER BY
      minutes DESC
    LIMIT 3

    Sort by columns, output names or descending(...). Without LIMIT(n) it is refused, since
    it makes the warehouse put every row in order before any comes back: sort in pandas after
    run_query(...), or pass sorts_everything=True. In a Statement you pass to derived(...), an
    ORDER_BY without LIMIT is refused even with sorts_everything=True: the order of rows there
    may not be kept, so a Statement that reads it can't rely on that order.
    """
    items = _flatten(columns)
    if not items:
        refuse(what="ORDER_BY was given nothing to sort by.", why="It needs a column.",
               fix='Pass columns, output names or descending(...), such as '
               'ORDER_BY(descending("runs")).')
    for item in items:
        if not isinstance(item, (Column, str, Ordering)):
            refuse(what=f"ORDER_BY was given {item!r}.",
                   why="It sorts by columns or output names.",
                   fix="Pass a column, an output name, or descending(...).",
                   given=item, call="ORDER_BY")
    trees = [ordered(item, "ORDER_BY(...)") for item in items]
    return Clause("ORDER_BY", sort_keys=trees, sorts_everything=sorts_everything)


def LIMIT(n: int) -> Clause:
    """Return at most n rows.

    >>> print(to_hive(statement(SELECT(jobs.job_name), FROM(jobs), LIMIT(2))))
    SELECT
      jobs.job_name
    FROM ops.jobs AS jobs
    LIMIT 2
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        refuse(what=f"LIMIT({n!r}) needs a whole number of rows, 1 or more.",
               why="It is how many rows come back at most.", fix="Write it like LIMIT(20).",
               error=ValueError)
    return Clause("LIMIT", n=n)


def _write_clause(call: str, table: object, unproven_key: object,
                  partition: object) -> Clause:
    """The clause for INSERT_OVERWRITE(table) or INSERT_INTO(table), once the table is checked."""
    table = _need_table(table, f"{call}(...)")
    if not isinstance(unproven_key, bool):
        refuse(
            what=f"{call}({table._alias}, unproven_key={unproven_key!r}): unproven_key= is "
            "True or False.",
            why="unproven_key=True lets through a write whose rows the Toolbox can't see have "
            "a Key of their own.",
            fix=f"Write {call}({table._alias}, unproven_key=True), or leave it out.",
            error=ValueError,
        )
    if table._statement is not None:
        refuse(
            what=f"{call}({table._alias}) was given a Derived table, not a Saved table.",
            why="A write fills a real table, and a Derived table is only a part of the "
            "Statement that reads it.",
            fix="Pass the Saved table's own Table reference.",
            error=ValueError,
        )
    # Only your own Saved tables are written: ADR 0007. A table someone else owns would lose
    # the rows, or the Partitions, the write replaces.
    need_saved_table(table, f"{call}({table._alias})")
    return Clause(call, table=table, unproven_key=unproven_key,
                  partition=_static_partition(call, table, partition))


def _static_partition(call: str, table: Table, partition: object) -> dict[str, Node]:
    """A write's partition={...}, checked: each column it names a partition column of the
    table, together the first ones of its partitioned_by, each with one value. They come back
    in the table's order, each value a Hive literal."""
    if partition is None:
        return {}
    columns = table._partitioned_by
    written = f"{call}({table._alias}, partition={partition!r})"
    example = f'{call}({table._alias}, partition={{"{columns[0] if columns else "dt"}": ...}})'
    if not isinstance(partition, dict) or not partition:
        refuse(
            what=f"{written}: partition= is a dict of partition columns and their values.",
            why="It names the Partition the write fills: each partition column it names, with "
            "the one value the write gives it.",
            fix=f"Write it like {example}, or leave it out to fill every partition column from "
            "the rows.",
            given=partition, call=call,
        )
    if not columns:
        refuse(
            what=f"{call}({table._alias}, partition=...): {table._name} isn't partitioned.",
            why="partition= names values of a table's partition columns, and its Table "
            "reference has no partitioned_by=.",
            fix="Leave partition= out: the write fills the whole table.",
            error=ValueError,
        )
    unknown = [name for name in partition if name not in columns]
    if unknown:
        refuse(
            what=f"{call}({table._alias}, partition=...) names {', '.join(map(repr, unknown))}, "
            f"which isn't a partition column of {table._name}.",
            why="partition= gives values only to the columns the table is partitioned by.",
            fix=f"Name its partition columns, in its partitioned_by: {', '.join(columns)}.",
            error=ValueError,
        )
    first = columns[:len(partition)]
    skipped = [name for name in first if name not in partition]
    if skipped:
        refuse(
            what=f"{call}({table._alias}, partition=...) names {', '.join(partition)}, but not "
            f"{', '.join(skipped)}, which comes before it in {table._name}'s partitioned_by "
            f"({', '.join(columns)}).",
            why="Hive takes the partition columns in order: the ones the write names first, "
            "then the ones it fills from the rows. A column named after one left out can't be.",
            fix=f"Name {', '.join(skipped)} too, or leave out the ones after it, to fill them "
            "from the rows.",
            error=ValueError,
        )
    values = {}
    for name in first:
        value = partition[name]
        if value is None or isinstance(value, Column):
            refuse(
                what=f"{call}({table._alias}, partition=...) gives {name} {python_text(value)}.",
                why="partition= names the one value each of its columns has in every row the "
                "write fills, written into the Hive as it is.",
                fix=f"Give {name} a value, such as a string or a number, or leave {name} out to "
                "fill it from each row's own value.",
                error=ValueError,
            )
        values[name] = literal(value, call=f"{call}({table._alias}, partition=...)",
                               column=table._column(name), position=f"the value of {name}")
    return values


def INSERT_OVERWRITE(table: Table, unproven_key: bool = False,
                     partition: dict[str, str | int | float | bool | datetime.date] | None = None
                     ) -> Clause:
    """Write rows into a Saved table, replacing the Partitions they fill, or all of it.

    >>> daily_runs = Table("mart.daily_runs", partitioned_by=["dt"], key=["job_id", "dt"],
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/mart.db/daily_runs")
    >>> text = show_hive(statement(
    ...     INSERT_OVERWRITE(daily_runs),
    ...     SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY(job_runs.job_id, job_runs.dt),
    ... ))
    -- The Session setting "dynamic_partitions": this write fills dt from its rows.
    SET hive.exec.dynamic.partition=true;
    SET hive.exec.dynamic.partition.mode=nonstrict;
    INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt)
    SELECT
      job_runs.job_id,
      COUNT(*) AS runs,
      job_runs.dt
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    GROUP BY
      job_runs.job_id,
      job_runs.dt;

    It goes first, before SELECT. Columns are matched to the Saved table by name, and the
    Toolbox puts them in the table's order, its partition columns last, as Hive fills them.
    Into a table with partitioned_by=, each row goes to the Partition its own values of the
    partition columns name, and INSERT_OVERWRITE replaces only the Partitions the rows fill: one
    they don't fill keeps what it held. Sent again, it replaces them again rather than adding
    to them, so a write can safely be sent twice; to add rows instead, use INSERT_INTO. If your
    warehouse runs Hive 2.3 or 3.1 under Tez (ask whoever looks after it), a write that now
    comes back empty may leave the old rows in place (HIVE-18702). After editing a Saved
    table's Table reference, check it with check_table_reference(t, query=...).

    Filling Partitions from the rows needs Hive's dynamic partitioning switched on, the
    Session setting the Toolbox calls "dynamic_partitions", whose two SET lines show_hive
    prints ahead of such a write. Send them with run_execute(hive_settings("dynamic_partitions"),
    execute) before the first such write: the warehouse keeps them for as long as your
    execute's connection lasts, and sending them again does no harm. The example above writes
    each job's runs on each of two days, one Partition for each day.

    partition={"dt": "2026-09-24"} names the Partition instead: each column it names is one
    value, written into the Hive, so SELECT leaves it out. The columns it names are the first
    of the table's partitioned_by, since Hive takes the named ones first and fills the rest
    from the rows: a table with partitioned_by=["region", "dt"] may name region alone, and
    fill dt from the rows. A write that names every partition column needs no Session setting.
    partition= says where the rows go, and WHERE which rows are read: keep them the same.

    When the Saved table's Table reference declares a Key, the write is refused unless the
    Toolbox can see that each row it writes has a Key of its own, since Hive never checks one.
    It sees that from any of these:

    - a GROUP_BY over the Key's columns;
    - a SELECT_DISTINCT;
    - a row_number(...) kept at 1 for each Key, in a Derived table;
    - reading a table by its own Key, each join matching its joined table's whole Key.

    A column partition= names is one value, so a Key that holds it needs only its other
    columns. unproven_key=True writes it anyway, for rows that are one per Key for a reason the
    Toolbox can't see. A table with no Key is written unchecked. Below, GROUP_BY makes one row
    for each job_id:

    >>> print(to_hive(statement(
    ...     INSERT_OVERWRITE(daily_runs, partition={"dt": "2026-09-24"}),
    ...     SELECT(job_runs.job_id, AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24")),
    ...     GROUP_BY(job_runs.job_id),
    ... )))
    INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt = '2026-09-24')
    SELECT
      job_runs.job_id,
      COUNT(*) AS runs
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24'
    GROUP BY
      job_runs.job_id

    A Saved table with no partitioned_by= is written whole: INSERT_OVERWRITE replaces every row
    it holds with the Statement's rows, and its Hive names no PARTITION. Such a table must be
    one of your Saved tables, with location=, since a write would replace all of it. Below,
    each team's runs over two days, whose Key is the team, which GROUP_BY makes one row for:

    >>> team_runs = Table("mart.team_runs", key=["team"],
    ...     columns={"team": "string", "runs": "bigint"},
    ...     location="/data/your_team/mart.db/team_runs")
    >>> print(to_hive(statement(
    ...     INSERT_OVERWRITE(team_runs),
    ...     SELECT(jobs.team, AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    ...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    ...     GROUP_BY(jobs.team),
    ... )))
    INSERT OVERWRITE TABLE mart.team_runs
    SELECT
      jobs.team,
      COUNT(*) AS runs
    FROM ops.job_runs AS job_runs
    JOIN ops.jobs AS jobs
      ON jobs.job_id = job_runs.job_id
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    GROUP BY
      jobs.team
    """
    return _write_clause("INSERT_OVERWRITE", table, unproven_key, partition)


def INSERT_INTO(table: Table, unproven_key: bool = False,
                partition: dict[str, str | int | float | bool | datetime.date] | None = None
                ) -> Clause:
    """Add rows to a Saved table or its Partitions; sent twice, it adds twice.

    >>> run_alerts = example_database.run_alerts
    >>> runs_to_review = Table("mart.runs_to_review", partitioned_by=["dt"], key=["run_id"],
    ...     columns={"run_id": "bigint", "dt": "string"},
    ...     location="/data/your_team/mart.db/runs_to_review")
    >>> print(to_hive(statement(
    ...     INSERT_INTO(runs_to_review, partition={"dt": "2026-09-24"}),
    ...     SELECT_DISTINCT(run_alerts.run_id),
    ...     FROM(run_alerts),
    ...     WHERE(equals(run_alerts.dt, "2026-09-24"), equals(run_alerts.severity, "high")),
    ... )))
    INSERT INTO mart.runs_to_review PARTITION(dt = '2026-09-24')
    SELECT DISTINCT
      run_alerts.run_id
    FROM ops.run_alerts AS run_alerts
    WHERE
      run_alerts.dt = '2026-09-24' AND run_alerts.severity = 'high'

    It follows every rule of INSERT_OVERWRITE: it goes first, its columns are matched by name,
    it fills Partitions from the rows or names one with partition={...}, and it writes into
    the whole table for one with no partitioned_by=. The difference is what happens to the
    rows already there: INSERT_OVERWRITE replaces the Partitions it fills, INSERT_INTO keeps
    their rows and adds more. Use it when a Partition's rows come from more than one table:
    send INSERT_OVERWRITE first, from the first table, then INSERT_INTO from each other table.
    Sending the same INSERT_INTO twice adds its rows twice, so to redo it, start again from
    its INSERT_OVERWRITE. A Saved table's Key is checked as INSERT_OVERWRITE checks it, on the
    rows this write adds: rows the table holds already may share a Key with them, which
    check_key(t, query=..., where=...) finds once they are written. In the example above, a
    day of failed runs gets the runs with a high alert added, each run once, by its Key, run_id.
    """
    return _write_clause("INSERT_INTO", table, unproven_key, partition)


# --- statement(...) ------------------------------------------------------------------------


def _check_order(clauses: tuple[object, ...]) -> None:
    for clause in clauses:
        if not isinstance(clause, Clause):
            refuse(
                what=f"statement(...) was given {clause!r}, which isn't a clause.",
                why="A Statement is a list of clause functions such as SELECT(...) and "
                "FROM(...).",
                fix="Wrap it in its clause, such as WHERE(equals(...)).",
                given=clause, call="statement",
            )
    places = [clause._place() for clause in clauses]
    ranks = [ORDER.index(place) for place in places]
    # Only a join may come more than once: not two writes, nor SELECT with SELECT_DISTINCT.
    for place in ORDER:
        found = [clause._name for clause in clauses if clause._place() == place]
        if place != "JOIN" and len(found) > 1:
            refuse(
                what=f"statement(...) has {' and '.join(found)}, but a Statement has only one "
                f"{place} clause.",
                why="A Statement is one query, so it has one of each clause (only JOINs may "
                "repeat), and it writes at most once.",
                fix="Keep one of them. Put all conditions in one WHERE, and send a second "
                "write as a Statement of its own.",
                error=ValueError,
            )
    if ranks != sorted(ranks):
        refuse(
            what="statement(...) has its clauses out of SQL order: "
            + ", ".join(clause._name for clause in clauses) + ".",
            why="A Statement reads in SQL order, one clause each.",
            fix="Order them as INSERT_OVERWRITE or INSERT_INTO, SELECT, FROM, JOIN..., WHERE, "
            "GROUP_BY, HAVING, ORDER_BY, LIMIT, and put all conditions in one WHERE.",
            error=ValueError,
        )
    for needed in ("SELECT", "FROM"):
        if needed not in places:
            refuse(what=f"statement(...) has no {needed}(...).",
                   why="Every Statement says what it returns and which table it reads.",
                   fix="Add SELECT(...) and FROM(...).",
                   error=ValueError)


def statement(*clauses: Clause, returns_all_rows: bool = False) -> Statement:
    """Assemble clause functions, in SQL order, into a Statement.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id, job_runs.status),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ... )))
    SELECT
      job_runs.run_id,
      job_runs.status
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'

    It runs the Guards and Load limits that need the whole Statement. to_hive(s) gives the
    Hive string, and run_query(s, query) sends it. returns_all_rows=True drops the automatic
    LIMIT, if set_load_limits(rows=...) has set one.
    """
    _check_order(clauses)
    s = Statement()
    s._clauses = clauses
    s._returns_all_rows = returns_all_rows
    # _check_order has made sure each place but JOIN comes at most once.
    by_place = {clause._place(): clause for clause in clauses if clause._place() != "JOIN"}
    write = by_place.get("INSERT")
    s._write = write.table if write else None
    s._kind = kinds.WRITE if write else kinds.READ
    # How the write was called, for messages: INSERT_INTO(daily_runs).
    s._write_call = f"{write._name}({write.table._alias})" if write else None
    s._replaces_rows = write is not None and write._name == "INSERT_OVERWRITE"
    s._static_partitions = {name: hive_text(value)
                            for name, value in write.partition.items()} if write else {}
    s._unproven_key = write is not None and write.unproven_key
    select = by_place["SELECT"]
    s._outputs, s._distinct = select.outputs, select.distinct
    s._reads = [c for c in clauses if c._name == "FROM" or c._name in JOINS]
    s._where = by_place["WHERE"].conditions if "WHERE" in by_place else []
    s._having = by_place["HAVING"].conditions if "HAVING" in by_place else []
    groups = by_place["GROUP_BY"].group_columns if "GROUP_BY" in by_place else []
    from .stacking import check_subtotals, grouped  # here: stacking.py imports this file

    s._group_by, s._grouping_sets, s._subtotals_call = grouped(s, groups)
    order = by_place.get("ORDER_BY")
    s._order_by = order.sort_keys if order else []
    s._limit = by_place["LIMIT"].n if "LIMIT" in by_place else None
    check_subtotals(s)
    _check_tables(s)
    check_joins(s)
    _run_guards(s)
    _run_load_limits(s, order)
    return s


def _resolve_group_by(s: Statement, items: list[Column | str]) -> list[Column]:
    by_name = {name: column for column, name in s._outputs}
    resolved = []
    for item in items:
        if isinstance(item, str) and item not in by_name:
            refuse(
                what=f"GROUP_BY({item!r}): SELECT has no column called {item!r}.",
                why="A name in GROUP_BY stands for a calculation named in SELECT.",
                fix=f"Use one of: {', '.join(by_name)}.",
                error=ValueError,
            )
        resolved.append(by_name[item] if isinstance(item, str) else item)
    return resolved


def derived_tables(s: Statement) -> list[Table]:
    """Every Derived table a Statement reads, directly or not, each after those it reads; a
    Stack's are those of each Statement it stacks."""
    found = []
    for read in [read for step in (s._stack[1] if s._stack else [s]) for read in step._reads]:
        table = read.table
        if table._statement is None:
            continue
        for inner in [*derived_tables(table._statement), table]:
            if not any(inner._statement is seen._statement for seen in found):
                found.append(inner)
    return found


def _check_tables(s: Statement) -> None:
    aliases = [read.table._alias for read in s._reads]
    twice = sorted({alias for alias in aliases if aliases.count(alias) > 1})
    if twice:
        refuse(
            what=f"statement(...) reads two tables called {', '.join(twice)}.",
            why="In the SQL a table is called by its short name, so the two would be mixed up.",
            fix=f'Give one a second name with AS, such as AS({twice[0]}, "earlier").',
            error=ValueError,
        )
    names = {}
    for table in derived_tables(s):
        if table._name in names and names[table._name] is not table._statement:
            refuse(
                what=f"statement(...) reads two different Derived tables called {table._name!r}.",
                why="Each becomes a named part of the same Hive string, so the names must differ.",
                fix="Give one of them another name in derived(...).",
                error=ValueError,
            )
        names[table._name] = table._statement
    used = set()
    for tree in _trees(s):
        used |= {column.table for column in tree.find_all("Column") if column.table}
    unread = sorted(used - set(aliases))
    if unread:
        refuse(
            what=f"statement(...) uses columns of {', '.join(unread)}, which it doesn't read.",
            why="A Statement can only use columns of the tables in its FROM and JOINs.",
            fix=f"Add {unread[0]} with FROM(...) or JOIN(...), or use another table's column.",
            error=ValueError,
        )
    _check_placement(s)
    _check_order_names(s)


def _check_order_names(s: Statement) -> None:
    """Refuse an ORDER_BY name that SELECT hasn't got, as GROUP_BY does."""
    names = [name for _, name in s._outputs]
    for key in s._order_by:
        sorted_by = key.parts["this"]
        if sorted_by.kind == "Column" and not sorted_by.table and sorted_by.name not in names:
            written = repr(sorted_by.name)
            if key.parts["desc"]:
                written = f"descending({written})"
            refuse(
                what=f"ORDER_BY({written}): SELECT has no column called {sorted_by.name!r}.",
                why="A name in ORDER_BY stands for a column or a calculation named in SELECT.",
                fix=f"Use one of: {', '.join(names)}.",
                error=ValueError,
            )


def _check_placement(s: Statement) -> None:
    """Refuse a count, a sum or a window where Hive can't work it out yet."""
    places = [("WHERE", c) for c in s._where] + [("HAVING", c) for c in s._having]
    places += [("ON=", read.on) for read in s._reads if read.on is not None]
    places += [("GROUP_BY", column) for column in s._group_by]
    for place, part in places:
        if place != "HAVING" and has_aggregate(part._tree):
            fix = "Test a count or a sum in HAVING(...), which tests groups after GROUP_BY."
            if place == "GROUP_BY":
                fix = ("Group by the columns themselves. To group by a count, make it in a "
                       "derived(...) table, and group by its column in the Statement that "
                       "reads it.")
            refuse(
                what=f"{place} has {part!r}, which counts or adds up rows.",
                why=f"Rows are counted after {place} has done its work, so Hive would refuse "
                "it there.",
                fix=fix,
                error=ValueError,
            )
        if has_window(part._tree):
            refuse_a_window_in(place, part)


def _trees(s: Statement) -> list[Node]:
    trees = [column._tree for column, _ in s._outputs]
    trees += [c._tree for c in s._where + s._having]
    trees += [read.on._tree for read in s._reads if read.on is not None]
    trees += [column._tree for column in s._group_by] + list(s._order_by)
    return trees


def _run_guards(s: Statement) -> None:
    _guard_group_by(s)
    for read in s._reads:
        if read._name != "LEFT_JOIN":
            continue
        for condition in s._where:
            alias = read.table._alias
            if alias in condition._tables() and alias not in condition._keeps_unmatched:
                guard_left_join_then_where(alias, repr(condition), read.keeps_only_matches)
    if kinds.kind(s) == kinds.WRITE:
        table = s._write
        expected = [c for c in table._columns if c not in s._static_partitions]
        names = [name for _, name in s._outputs]
        missing = [c for c in expected if c not in names]
        extra = [n for n in names if n not in expected]
        if missing or extra:
            guard_write_lines_up(s._write_call, table._alias, missing, extra)
        why = None if s._unproven_key else unproven(s)
        if why is not None:
            guard_unproven_key(s._write_call, table._key, why)


def _guard_group_by(s: Statement) -> None:
    """When a Statement groups or counts, every column it shows, tests or sorts by must be in
    GROUP_BY, or inside a count or a sum."""
    counted = [column._tree for column, _ in s._outputs]
    counted += [key.parts["this"] for key in s._order_by]
    if not (any(has_aggregate(tree) for tree in counted) or s._group_by or s._having):
        return
    groups = [column._tree for column in s._group_by]
    names = [name for _, name in s._outputs]
    places = [
        ("SELECT", [column._tree for column, _ in s._outputs]),
        ("HAVING", [condition._tree for condition in s._having]),
        ("ORDER_BY", [key.parts["this"] for key in s._order_by]),
    ]
    for place, trees in places:
        missing, calculations = [], []
        for number, tree in enumerate(trees):
            ungrouped = _ungrouped(tree, groups)
            # A calculation in SELECT, such as week_start(dt) named "week", is grouped by its
            # name: grouped by the column inside it, it would give one row per day, not week.
            if (place == "SELECT" and ungrouped and tree.kind != "Column"
                    and not has_aggregate(tree) and not has_window(tree)):
                inside = list(dict.fromkeys(hive_text(column) for column in ungrouped))
                calculations.append((names[number], inside))
                continue
            for column in ungrouped:
                text = hive_text(column)
                is_a_name = place == "ORDER_BY" and not column.table and column.name in names
                if not is_a_name and text not in missing:
                    missing.append(text)
        if missing or calculations:
            guard_missing_group_by(place, missing, bool(s._group_by), calculations)


def _ungrouped(tree: Node, groups: list[Node]) -> list[Node]:
    """The columns in `tree` that are neither inside a GROUP_BY part nor counted or summed."""
    if tree in groups or is_aggregate(tree):
        return []
    if tree.kind == "Column":
        return [tree]
    children = ungrouped_in_window(tree) if tree.kind == "Window" else tree.children()
    return [column for child in children for column in _ungrouped(child, groups)]


def read_bounds(s: Statement) -> list[tuple[Clause, bool]]:
    """Each read of a partitioned table in `s`, with whether the conditions that bound it
    filter at least one of its partition columns: WHERE and each JOIN's ON=, or, for a
    LEFT_JOIN, SEMI_JOIN or ANTI_JOIN, its own ON=; a FULL_JOIN's sides only by WHERE, with
    keeps_only_matches=True."""
    inner = [read.on for read in s._reads if read._name == "JOIN"]
    everywhere = bounded_columns(s._where + inner)
    found = []
    for read in s._reads:
        table = read.table
        if table._statement is not None or not table._partitioned_by:
            continue
        bounds = everywhere
        if read._name in BOUNDED_IN_ON:
            bounds = bounded_columns([read.on] + (s._where + inner if read.keeps_only_matches
                                                  else []))
        elif read._name == "FULL_JOIN" and not read.keeps_only_matches:
            # FULL_JOIN keeps every row of its table, matched or not.
            bounds = frozenset()
        found.append((read, any((table._alias, column) in bounds
                                for column in table._partitioned_by)))
    return found


def _run_load_limits(s: Statement, order: Clause | None) -> None:
    for read, bounded in read_bounds(s):
        if not bounded:
            table = read.table
            load_limit_partition_bound(read._call(), table._alias, table._name,
                                       table._partitioned_by, read.reads_all_partitions,
                                       full_join=full_joined(s, read))
    if order is not None and s._limit is None:
        load_limit_order_by(order.sorts_everything)


# --- derived(...) --------------------------------------------------------------------------


def derived(name: str, statement: Statement) -> Table:
    """Name a Statement so another Statement can read it like a table.

    >>> runs_per_job = derived("runs_per_job", statement(
    ...     SELECT(job_runs.job_id, AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY(job_runs.job_id),
    ... ))
    >>> print(to_hive(statement(
    ...     SELECT(jobs.job_name, runs_per_job.runs),
    ...     FROM(runs_per_job),
    ...     JOIN(jobs, ON=equals(jobs.job_id, runs_per_job.job_id)),
    ... )))
    WITH runs_per_job AS (
      SELECT
        job_runs.job_id,
        COUNT(*) AS runs
      FROM ops.job_runs AS job_runs
      WHERE
        job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
      GROUP BY
        job_runs.job_id
    )
    SELECT
      jobs.job_name,
      runs_per_job.runs
    FROM runs_per_job
    JOIN ops.jobs AS jobs
      ON jobs.job_id = runs_per_job.job_id

    You then use its output columns like a Table reference's, as runs_per_job.runs, and a typo
    in one is caught the same way. The Toolbox writes it at the top of the Hive, as WITH
    runs_per_job AS (...). The warehouse usually works it out again each time the Statement
    reads it, so if it gets slow, write it to a Saved table instead. Its Key, which a JOIN on it
    checks ON= against, is worked out from how it makes its rows: its GROUP_BY columns (it has
    none when GROUP_BY holds rollup, cube or grouping_sets, whose subtotal rows repeat them),
    every column of a SELECT_DISTINCT, none for a SELECT of only totals (one row), every column
    of a UNION, INTERSECT or EXCEPT, which give distinct rows (none for a UNION_ALL), or the Key
    of the table in its FROM, carried through each join that matches its table's whole Key, and
    through a row_number(...) kept at 1.
    """
    if not isinstance(name, str) or not SIMPLE_NAME.fullmatch(name):
        refuse(what=f"derived({name!r}, ...) needs a plain name.",
               why="The name is how the SQL calls it.",
               fix='Use letters, digits and _, such as derived("latest", ...).',
               error=ValueError)
    if not kinds.is_a_query(statement):
        refuse(what=f"derived({name!r}, ...) was given {statement!r}.",
               why="derived names a Statement made by statement(...).",
               fix="Pass statement(SELECT(...), FROM(...), ...).",
               given=statement, call="derived")
    if kinds.kind(statement) == kinds.WRITE:
        refuse(what=f"derived({name!r}, ...) was given a write.",
               why="A Statement that writes a Saved table returns no rows to read.",
               fix="Read the Saved table through its own Table reference instead.",
               error=ValueError)
    if statement._order_by and statement._limit is None:
        guard_order_by_in_derived_table(name)
    columns = {n: column._type for column, n in statement._outputs}
    table = Table(name, columns=columns)
    table._statement = statement
    table._keys = statement_keys(statement)
    found = table._keys.found
    table._key = found[0].names if found else None
    table._not_adding_up_because = {
        n: column._not_adding_up_because
        for column, n in statement._outputs if not column._adds_up
    }
    return table


__all__ = [
    "SELECT",
    "SELECT_DISTINCT",
    "AS",
    "FROM",
    "JOIN",
    "LEFT_JOIN",
    "CROSS_JOIN",
    "SEMI_JOIN",
    "ANTI_JOIN",
    "FULL_JOIN",
    "RIGHT_JOIN",
    "WHERE",
    "GROUP_BY",
    "HAVING",
    "ORDER_BY",
    "LIMIT",
    "INSERT_OVERWRITE",
    "INSERT_INTO",
    "statement",
    "derived",
]
