"""Running: turn a Statement into Hive, send it, split it by day, and set the load limits.

run(s, send=...) is the only way the Toolbox reaches the query API, and `send` is your own
function: it takes a Hive string and returns a DataFrame. Connection, retries and saving
CSVs stay in it. The Toolbox never imports it.
"""

from __future__ import annotations

from . import writing
from .clauses import (
    FROM,
    WHERE,
    Statement,
    derived,
    derived_tables,
    read_spans,
    statement,
)
from .conditions import equals
from .refusals import (
    four_part_message,
    guard_by_day_grouping,
    guard_one_day_per_write,
    load_limit_dates,
    load_limit_rows,
    refuse_a_spark_dataframe,
    refuse_what_the_other_edition_made,
)
from .tables import aliased, source, table_node
from .trees import Node, combined

TOOLBOX_VERSION = "3.0"

# The two seams that ship switched off. set_load_limits(...) switches them on.
_limits = {"rows": None, "dates": None}


def set_load_limits(rows=None, dates=None):
    """Switch on an automatic LIMIT and a cap on days per Statement; both start off.

    Call it from your own notebook, since the Toolbox folder is replaced on each update.
    `rows` adds LIMIT rows to every Statement that has no LIMIT of its own, and run(...)
    refuses a result that fills it, since it was probably cut short. `dates` refuses a
    Statement that reads more days than that from one table. An argument left out means no
    limit, so set_load_limits() switches both off. It returns the limits now in force.

    >>> set_load_limits(rows=100000, dates=31)
    {'rows': 100000, 'dates': 31}
    >>> set_load_limits()
    {'rows': None, 'dates': None}
    """
    for name, value in (("rows", rows), ("dates", dates)):
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)
                                  or value < 1):
            raise ValueError(
                four_part_message(
                    what=f"set_load_limits({name}={value!r}): a limit must be a whole number, "
                    "1 or more, or None for no limit.",
                    why="It is a count of rows or days.",
                    fix=f"Write it like set_load_limits({name}=100000), or leave it out.",
                    opt_out=None,
                )
            )
    _limits["rows"], _limits["dates"] = rows, dates
    return dict(_limits)


# --- Building the Hive -----------------------------------------------------------------------


def _output(column, name: str) -> Node:
    """One SELECT entry: the column as it is, or with AS name when the name differs."""
    if column._name == name and column._table is not None:
        return column._tree.copy()
    return Node("Alias", this=column._tree.copy(), alias=name)


def _join_tree(read) -> Node:
    """One JOIN, LEFT_JOIN or CROSS_JOIN clause."""
    return Node("Join", how=read._name.replace("_", " "), this=source(read.table),
                on=None if read.on is None else read.on._tree.copy())


def _all_of(conditions: list) -> Node | None:
    """The conditions of WHERE or HAVING, joined with AND, or None when there are none."""
    return combined("And", [c._tree.copy() for c in conditions]) if conditions else None


def _select_tree(s: Statement) -> Node:
    """A Statement's SELECT, from FROM to LIMIT, without WITH."""
    outputs = s._outputs
    if s._write is not None:
        order = list(s._write._columns)
        outputs = sorted(outputs, key=lambda output: order.index(output[1]))
    return Node(
        "Select",
        outputs=[_output(column, name) for column, name in outputs],
        distinct=s._distinct,
        source=source(s._reads[0].table),
        joins=[_join_tree(read) for read in s._reads[1:]],
        where=_all_of(s._where),
        group_by=[c._tree.copy() for c in s._group_by],
        having=_all_of(s._having),
        order_by=[o.copy() for o in s._order_by],
        limit=s._limit,
    )


def _with(tree: Node, s: Statement) -> Node:
    """Put each Derived table the Statement reads at the top, as WITH name AS (...)."""
    tree.set("derived_tables", [Node("CTE", this=_select_tree(table._statement),
                                     alias=table._name) for table in derived_tables(s)])
    return tree


def automatic_limit(s: Statement) -> int | None:
    """The automatic LIMIT this Statement gets when sent, if any."""
    if s._write is not None or s._limit is not None or s._returns_all_rows:
        return None
    return _limits["rows"]


def _days_read(s: Statement) -> list:
    """Each read of a partitioned table, at every step, with the days it reads."""
    found = read_spans(s)
    for table in derived_tables(s):
        found += read_spans(table._statement)
    return found


def _check_dates_cap(s: Statement) -> None:
    cap = _limits["dates"]
    if cap is None:
        return
    for read, span in _days_read(s):
        if span is not None and span.is_bounded():
            load_limit_dates(read._call(), read.table._name, len(span.dates()), cap,
                             read.reads_all_partitions)


def _written_day(s: Statement):
    """The one day a write covers, from the date bound of the table it reads from."""
    table, span = _bottom_read(s)
    if table._date_partition is None:
        raise _day_unknown(s, f"reads {table._name}, which has no Date partition",
                     "A Saved table is filled one day at a time from a table with days: "
                     "read one with a Date partition in FROM, bounded to one day in WHERE.")
    if span is None or not span.is_bounded():
        raise _day_unknown(s, f"reads {table._name} without a bound on its Date partition",
                     f"Bound {table._alias}.{table._date_partition} in WHERE, and send one day "
                     "at a time with by_day(...).")
    days = span.dates()
    if len(days) != 1:
        guard_one_day_per_write(s._write_call, len(days))
    return days[0]


def _day_unknown(s: Statement, what: str, fix: str) -> ValueError:
    """The error for a write whose day isn't known; the caller raises it."""
    return ValueError(
        four_part_message(
            what=f"{s._write_call} {what}, so the day to write isn't known.",
            why="A write fills the one day its Statement reads.",
            fix=fix,
            opt_out=None,
        )
    )


def _bottom_read(s: Statement):
    """The real table under FROM, following Derived tables down, and its date bound."""
    step = s
    while step._reads[0].table._statement is not None:
        step = step._reads[0].table._statement
    read = step._reads[0]
    span = next((found for r, found in read_spans(step) if r is read), None)
    return read.table, span


def _write_tree(s: Statement) -> Node:
    """INSERT OVERWRITE or INSERT INTO the one day the Statement reads, then its SELECT."""
    table = s._write
    day = _written_day(s).strftime(table._date_format)
    partition = Node("Partition", expressions=[
        Node("EQ", this=Node("Column", name=table._date_partition),
             expression=Node("Literal", this=day, is_string=True)),
    ])
    return Node("Insert", target=table_node(table._name, partition=partition),
                select=_select_tree(s), overwrite=s._replaces_day)


def _statement_tree(s: Statement) -> Node:
    """The whole tree to_hive writes: CREATE or DROP, a write, or a SELECT."""
    if s._ddl is not None:
        return s._ddl.copy()
    if s._write is not None:
        return _with(_write_tree(s), s)
    tree = _select_tree(s)
    limit = automatic_limit(s)
    if limit is not None:
        tree.set("limit", limit)
    return _with(tree, s)


def _self_check(text: str) -> None:
    """The Hive must read back as the same text (writing.read_back), or nothing is sent."""
    again = writing.read_back(text)
    if again != text:
        raise RuntimeError(
            "spark_composer wrote Hive that doesn't read back the same. This is a bug in the "
            "Toolbox, not in your Statement: nothing was sent. Please report it with the "
            f"Statement that caused it.\n\nWritten:\n{text}\n\nRead back:\n{again}"
        )


def to_hive(s):
    """The Hive string for a Statement, ready to send.

    It checks itself by reading the string back, and refuses what would read too many days
    (see set_load_limits) or write more than one day. The Hive may write a function
    differently from how you would by hand, for example DATE_SUB(dt, 7) as
    DATE_ADD(dt, 7 * -1), which means the same.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24")),
    ... )))
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24'
    """
    if not isinstance(s, Statement):
        refuse_what_the_other_edition_made(s, "to_hive")
        raise TypeError(
            four_part_message(
                what=f"to_hive was given {s!r}, which isn't a Statement.",
                why="It writes the Hive for a Statement made by statement(...).",
                fix="Pass statement(SELECT(...), FROM(...), ...).",
                opt_out=None,
            )
        )
    if s._ddl is None:
        _check_dates_cap(s)
    text = writing.hive_statement(_statement_tree(s))
    _self_check(text)
    return text


def run(s, send):
    """Send a Statement's Hive through your `send` function and return what comes back.

    `send` is your own function from a Hive string to a pandas DataFrame. At work it calls
    the query API, or, where your notebook runs Spark, is
    lambda hive: spark.sql(hive).toPandas(); example_database.send runs the Example database
    instead.

    >>> run(statement(
    ...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.status, "FAILED"), last_n_days(job_runs.dt, 2)),
    ... ), send=example_database.send)
       run_id  job_id          dt
    0      97       3  2026-09-23
    1     102       2  2026-09-24
    """
    if not callable(send):
        raise TypeError(
            four_part_message(
                what=f"run(..., send={send!r}): send isn't a function.",
                why="run hands the Hive string to your own function, which sends it and "
                "returns a DataFrame.",
                fix="Pass your function itself, without calling it: run(s, send=run_query).",
                opt_out=None,
            )
        )
    text = to_hive(s)
    result = send(text)
    # A write has already been carried out when its send returns, so only a read's rows matter.
    if s._ddl is None and s._write is None:
        refuse_a_spark_dataframe(result)
    limit = automatic_limit(s) if s._ddl is None else None
    if limit is not None and hasattr(result, "__len__"):
        load_limit_rows(len(result), limit)
    return result


# --- by_day ----------------------------------------------------------------------------------


def _check_splittable(s: Statement, date_partition: str, step: str) -> None:
    """A step may aggregate or pick rows only if it keeps the date in its grouping."""
    outputs = [column for column, _ in s._outputs]
    grouping = None
    if s._distinct:
        grouping = [name for _, name in s._outputs]
    elif s._group_by:
        grouping = [c._name for c in s._group_by if c._name is not None]
    elif any(column._aggregate for column in outputs):
        grouping = []
    if grouping is not None and date_partition not in grouping:
        guard_by_day_grouping(step, date_partition)
    for column in outputs:
        for window in column._tree.find_all("Window"):
            names = [c.name for c in window.parts["partition_by"] if c.kind == "Column"]
            if date_partition not in names:
                guard_by_day_grouping(step, date_partition)


def _steps(s: Statement) -> list[tuple[Statement, str]]:
    """The Statement and each Derived table below it through FROM, top first."""
    steps = [(s, "the outer Statement")]
    while steps[-1][0]._reads[0].table._statement is not None:
        table = steps[-1][0]._reads[0].table
        steps.append((table._statement, f"derived({table._name!r}, ...)"))
    return steps


def _reading(step: Statement, new_from) -> Statement:
    """A copy of `step` that reads `new_from` in place of its FROM table."""
    clauses = list(step._clauses)
    first = step._reads[0]
    clauses[clauses.index(first)] = FROM(new_from,
                                         reads_all_partitions=first.reads_all_partitions)
    return statement(*clauses, returns_all_rows=step._returns_all_rows)


def _one_day(step: Statement, day) -> Statement:
    """A copy of `step` whose WHERE bounds its FROM table's Date partition to one day."""
    clauses = list(step._clauses)
    first = step._reads[0]
    index = clauses.index(first)
    table = first.table
    key = (table._alias, table._date_partition)
    # Keep every condition but the old bound on the date, then bound it to the one day.
    kept = [c for c in step._where if c._only_bounds != key]
    where = WHERE(*kept, equals(getattr(table, table._date_partition), day))
    old = next((c for c in clauses if c._name == "WHERE"), None)
    if old is not None:
        clauses[clauses.index(old)] = where
    else:
        clauses.insert(index + len(step._reads), where)
    return statement(*clauses, returns_all_rows=step._returns_all_rows)


def by_day(s):
    """Split a Statement into one Statement per day of its date bound, oldest first.

    Use it to read a long range a day at a time, or to write a Saved table day by day:

        for day in by_day(s):
            df = run(day, send=run_query)

    It splits on the Date partition of the table in FROM, following Derived tables down to
    it; a joined table keeps its own bound. It refuses a Statement that groups rows without
    keeping that date, since each day's partial groups couldn't be added back up.

    >>> days = by_day(statement(
    ...     SELECT(job_runs.dt, job_runs.status, AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY(job_runs.dt, job_runs.status),
    ... ))
    >>> for day in days:
    ...     print(to_hive(day))
    SELECT
      job_runs.dt,
      job_runs.status,
      COUNT(*) AS runs
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-23'
    GROUP BY
      job_runs.dt,
      job_runs.status
    SELECT
      job_runs.dt,
      job_runs.status,
      COUNT(*) AS runs
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24'
    GROUP BY
      job_runs.dt,
      job_runs.status
    """
    if not isinstance(s, Statement) or s._ddl is not None:
        refuse_what_the_other_edition_made(s, "by_day")
        raise TypeError(
            four_part_message(
                what=f"by_day was given {s!r}, which isn't a Statement that reads a table.",
                why="It splits a Statement's days.",
                fix="Pass statement(SELECT(...), FROM(...), WHERE(...)).",
                opt_out=None,
            )
        )
    steps = _steps(s)
    table, span = _bottom_read(s)
    if table._date_partition is None or span is None or not span.is_bounded():
        raise ValueError(
            four_part_message(
                what=f"by_day can't split this Statement: {table._name} has no bounded Date "
                "partition.",
                why="It makes one Statement per day of the bound on the FROM table's Date "
                "partition.",
                fix=f"Bound its Date partition in WHERE, such as between({table._alias}."
                f"{table._date_partition or 'dt'}, ...).",
                opt_out=None,
            )
        )
    for step, described in steps:
        _check_splittable(step, table._date_partition, described)
    return [_split(steps, day) for day in span.dates()]


def _split(steps, day) -> Statement:
    """The Statement for one day: the bottom step bounded to it, each step above reading it."""
    bottom = _one_day(steps[-1][0], day)
    for step, _ in reversed(steps[:-1]):
        old = step._reads[0].table
        new = derived(old._name, bottom)
        if old._alias != old._name:
            new = aliased(new, old._alias)
        bottom = _reading(step, new)
    return bottom


__all__ = ["to_hive", "run", "by_day", "set_load_limits"]
