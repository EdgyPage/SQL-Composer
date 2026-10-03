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
    guard_by_day_limit,
    guard_one_day_per_write,
    load_limit_dates,
    load_limit_rows,
    refuse_a_spark_dataframe,
    refuse_what_the_other_edition_made,
)
from .tables import aliased, day_text, source, table_node
from .trees import Node, combined

TOOLBOX_VERSION = "3.2"

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
    from_read, _ = bottom_read(s)
    for read, span in _days_read(s):
        if span is not None and span.is_bounded():
            load_limit_dates(read._call(), read.table._name, len(span.dates()), cap,
                             read.reads_all_partitions, read is from_read)


def steps(s: Statement) -> list[tuple[Statement, str]]:
    """The Statement and each Derived table below it through FROM, top first, each with the
    words a refusal names it by. The last reads a real table in FROM: the one with the days."""
    found = [(s, "the outer Statement")]
    while found[-1][0]._reads[0].table._statement is not None:
        table = found[-1][0]._reads[0].table
        found.append((table._statement, f"derived({table._name!r}, ...)"))
    if len(found) == 1:
        found[0] = (s, "it")
    return found


def bottom_read(s: Statement):
    """The FROM read at the bottom of `s`, following Derived tables down, and the days its
    bound reads: a Span, or None."""
    step = steps(s)[-1][0]
    read = step._reads[0]
    return read, next((found for r, found in read_spans(step) if r is read), None)


def _bottom_days(s: Statement, who: str, why: str, no_days_fix: str):
    """The real table at the bottom of FROM and the days its bound reads, or a refusal."""
    read, span = bottom_read(s)
    table = read.table
    if table._date_partition is None:
        what, fix = f"its FROM table {table._name} has no Date partition", no_days_fix
    elif span is None or not span.is_bounded():
        column = f"{table._alias}.{table._date_partition}"
        what = f"nothing bounds the days of its FROM table {table._name}"
        if read.reads_all_partitions:
            what = (f"FROM({table._alias}, reads_all_partitions=True) reads every day of "
                    f"{table._name}, with no bound on its days")
        fix = f"Bound {column} in WHERE, such as between({column}, ...)."
    else:
        return table, span
    raise ValueError(four_part_message(what=f"{who}: {what}.", why=why, fix=fix, opt_out=None))


def _written_day(s: Statement):
    """The one day a write covers, from the date bound of the table it reads from."""
    _, span = _bottom_days(
        s, f"{s._write_call} can't tell which day to write",
        "A write fills the one day its FROM table reads.",
        "A Saved table is filled from a table with days: put one in FROM, bounded to one day "
        "in WHERE.")
    days = span.dates()
    if len(days) != 1:
        guard_one_day_per_write(s._write_call, len(days))
    return days[0]


def _write_tree(s: Statement) -> Node:
    """INSERT OVERWRITE or INSERT INTO the one day the Statement reads, then its SELECT."""
    table = s._write
    day = day_text(_written_day(s), table._date_format)
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
            "sql_composer wrote Hive that doesn't read back the same. This is a bug in the "
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


def _check_splittable(s: Statement, step: str, dates: list, partition: str,
                      below: str) -> None:
    """A step may group or pick rows only if it keeps the Date partition, and may have no
    LIMIT.

    `dates` holds the Date partition as this step sees it, under each name the step below,
    `below`, gave it; `partition` is the Date partition at the bottom step.
    """
    if s._limit is not None:
        guard_by_day_limit(step, s._limit)
    if s._distinct:
        grouping, clause = [column._tree for column, _ in s._outputs], "SELECT_DISTINCT(...)"
    elif s._group_by or any(column._aggregate for column, _ in s._outputs):
        grouping, clause = [column._tree for column in s._group_by], "GROUP_BY(...)"
    else:
        grouping, clause = None, ""
    if grouping is not None and not any(date in grouping for date in dates):
        _refuse_grouping(step, dates, partition, below, clause)
    for column, _ in s._outputs:
        for window in column._tree.find_all("Window"):
            if not any(date in window.parts["partition_by"] for date in dates):
                _refuse_grouping(step, dates, partition, below,
                                 "the PARTITION_BY of row_number(...)")


def _refuse_grouping(step: str, dates: list, partition: str, below: str, clause: str):
    """Refuse a step for leaving the Date partition out of `clause`, naming it as the step
    sees it, or saying where to keep it when the step below dropped it."""
    if not dates:
        guard_by_day_grouping(step, f"the Date partition {partition}",
                              f"Keep {partition} in the SELECT of {below}, then add it to "
                              f"{clause} here")
    name = f"{dates[0].table}.{dates[0].name}"
    keeping = (f"the Date partition {partition}" if name == partition
               else f"{name} ({partition}, the Date partition)")
    guard_by_day_grouping(step, keeping, f"Add {name} to {clause}")


def _dates_above(below: Statement, table, dates: list) -> list:
    """The Date partition as the step that reads `below` as `table` sees it: each output of
    `below` whose calculation is the Date partition, under that output's name."""
    return [Node("Column", name=name, table=table._alias)
            for column, name in below._outputs if column._tree in dates]


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
    """Split a Statement into one Statement per day its FROM table reads, oldest first.

    Use it to read a long range a day at a time, or to write a Saved table day by day:

        for day in by_day(s):
            df = run(day, send=run_query)

    It splits on the Date partition of the table in FROM, following Derived tables down to
    it; a joined table keeps its own bound. It refuses a Statement that groups rows without
    keeping that date, since each day's partial groups couldn't be added back up, and one with
    a LIMIT, which would keep that many rows of each day.

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
    found = steps(s)
    table, span = _bottom_days(
        s, "by_day can't split this Statement",
        "by_day makes one Statement for each day its FROM table reads.",
        "Run it whole with run(...): by_day splits only a table with days.")
    # Follow the Date partition up from the bottom step, under each name a step gives it.
    partition = f"{table._alias}.{table._date_partition}"
    dates = [Node("Column", name=table._date_partition, table=table._alias)]
    below, below_described = None, ""
    for step, described in reversed(found):
        if below is not None:
            dates = _dates_above(below, step._reads[0].table, dates)
        _check_splittable(step, described, dates, partition, below_described)
        below, below_described = step, described
    days = span.dates()
    if not days:
        raise ValueError(
            four_part_message(
                what=f"by_day can't split this Statement: its WHERE leaves no day of "
                f"{table._alias}.{table._date_partition} to read.",
                why="No day is inside every bound, so there would be no Statement to send, "
                "and nothing would be read or written.",
                fix="Check the days in its WHERE: a low end may be later than a high end, "
                "as at_least's day after at_most's, or not_equals or is_not_in may leave "
                "out the only day.",
                opt_out=None,
            )
        )
    return [_split(found, day) for day in days]


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
