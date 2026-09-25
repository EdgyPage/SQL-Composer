"""Running: turn a Statement into Hive, send it, split it by day, and set the load limits.

run(s, send=...) is the only way the Toolbox reaches the query API, and `send` is your own
function: it takes a Hive string and returns a DataFrame. Connection, retries and saving
CSVs stay in it. The Toolbox never imports it.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp

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
)
from .tables import aliased, hive_text, identifier, source

TOOLBOX_VERSION = "2.0"

# The two seams that ship switched off. set_load_limits(...) switches them on.
_limits = {"rows": None, "dates": None}


def set_load_limits(rows=None, dates=None):
    """Switch on an automatic row LIMIT and a cap on days per query; both start off.

    Call it from your own notebook, since the Toolbox folder is replaced on each update.
    `rows` adds LIMIT rows to every Statement that has no LIMIT of its own, and run(...)
    refuses a result that fills it, since it was probably cut short. `dates` refuses a
    query that reads more days than that from one table. An argument left out means no
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


def _set(tree: exp.Expression, part: str, value) -> None:
    """Set a part of a sqlglot tree. sqlglot 30 renamed `from` and `with` to `from_`, `with_`."""
    for key in (part, part + "_"):
        if key in type(tree).arg_types:
            tree.set(key, value)
            return
    raise RuntimeError(f"sql_composer: this sqlglot has no {part!r} on {type(tree).__name__}.")


def _output(column, name: str) -> exp.Expression:
    if column._name == name and column._table is not None:
        return column._tree.copy()
    return exp.alias_(column._tree.copy(), identifier(name))


def _join(read) -> exp.Join:
    parts = {"this": source(read.table)}
    if read.on is not None:
        parts["on"] = read.on._tree.copy()
    if read._name == "LEFT_JOIN":
        parts["side"] = "LEFT"
    if read._name == "CROSS_JOIN":
        parts["kind"] = "CROSS"
    return exp.Join(**parts)


def _select_tree(s: Statement) -> exp.Select:
    outputs = s._outputs
    if s._write is not None:
        order = list(s._write._columns)
        outputs = sorted(outputs, key=lambda output: order.index(output[1]))
    tree = exp.Select(expressions=[_output(column, name) for column, name in outputs])
    if s._distinct:
        tree.set("distinct", exp.Distinct())
    _set(tree, "from", exp.From(this=source(s._reads[0].table)))
    if len(s._reads) > 1:
        tree.set("joins", [_join(read) for read in s._reads[1:]])
    if s._where:
        tree.set("where", exp.Where(this=exp.and_(*[c._tree.copy() for c in s._where])))
    if s._group_by:
        tree.set("group", exp.Group(expressions=[c._tree.copy() for c in s._group_by]))
    if s._having:
        tree.set("having", exp.Having(this=exp.and_(*[c._tree.copy() for c in s._having])))
    if s._order_by:
        tree.set("order", exp.Order(expressions=[o.copy() for o in s._order_by]))
    if s._limit is not None:
        tree.set("limit", exp.Limit(expression=exp.Literal.number(s._limit)))
    return tree


def _with(tree: exp.Expression, s: Statement) -> exp.Expression:
    parts = [
        exp.CTE(this=_select_tree(table._statement),
                alias=exp.TableAlias(this=identifier(table._name)))
        for table in derived_tables(s)
    ]
    if parts:
        _set(tree, "with", exp.With(expressions=parts))
    return tree


def automatic_limit(s: Statement) -> int | None:
    """The automatic LIMIT this Statement gets when sent, if any."""
    if s._write is not None or s._limit is not None or s._returns_all_rows:
        return None
    return _limits["rows"]


def _days_read(s: Statement) -> list:
    """Each read of a partitioned table, at every level, with the days it reads."""
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
    days = span.dates() if span is not None and span.is_bounded() else None
    if days is None:
        raise ValueError(
            four_part_message(
                what=f"INSERT_OVERWRITE({s._write._alias}) reads {table._name} without a "
                "bound on its Date partition, so the day to write isn't known.",
                why="A write replaces the one day its Statement reads.",
                fix=f"Bound {table._alias}.{table._date_partition} in WHERE, and send one day "
                "at a time with by_day(...).",
                opt_out=None,
            )
        )
    if len(days) != 1:
        guard_one_day_per_write(s._write._alias, len(days))
    return days[0]


def _bottom_read(s: Statement):
    """The real table under FROM, following Derived tables down, and its date bound."""
    level = s
    while level._reads[0].table._statement is not None:
        level = level._reads[0].table._statement
    read = level._reads[0]
    span = next((found for r, found in read_spans(level) if r is read), None)
    return read.table, span


def _write_tree(s: Statement) -> exp.Expression:
    table = s._write
    day = _written_day(s).strftime(table._date_format)
    parts = table._name.split(".")
    partition = exp.Partition(expressions=[
        exp.EQ(this=exp.column(identifier(table._date_partition)),
               expression=exp.Literal.string(day)),
    ])
    target = exp.Table(this=identifier(parts[-1]),
                       db=identifier(parts[0]) if len(parts) == 2 else None,
                       partition=partition)
    return exp.Insert(this=target, expression=_select_tree(s), overwrite=True)


def _tree(s: Statement) -> exp.Expression:
    if s._ddl is not None:
        return s._ddl.copy()
    if s._write is not None:
        return _with(_write_tree(s), s)
    tree = _select_tree(s)
    limit = automatic_limit(s)
    if limit is not None:
        tree.set("limit", exp.Limit(expression=exp.Literal.number(limit)))
    return _with(tree, s)


def _self_check(text: str) -> None:
    """Parse the Hive back and write it again: it must come out the same."""
    again = hive_text(sqlglot.parse_one(text, read="hive"), pretty=True)
    if again != text:
        raise RuntimeError(
            "sql_composer wrote Hive that doesn't read back the same. This is a bug in the "
            "Toolbox, not in your Statement: nothing was sent. Please report it with the "
            f"Statement that caused it.\n\nWritten:\n{text}\n\nRead back:\n{again}"
        )


def to_hive(s):
    """The Hive string for a Statement, ready to send.

    It checks itself by reading the string back, and refuses what would read too many days
    (see set_load_limits) or write more than one day. sqlglot writes a few functions its own
    way, for example DATE_SUB(dt, 7) as DATE_ADD(dt, 7 * -1), which means the same.

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
    text = hive_text(_tree(s), pretty=True)
    _self_check(text)
    return text


def run(s, send):
    """Send a Statement's Hive through your `send` function and return what comes back.

    `send` is your own function from a Hive string to a DataFrame. At work it calls the
    query API; example_database.send runs the Example database instead.

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
    limit = automatic_limit(s) if s._ddl is None else None
    if limit is not None and hasattr(result, "__len__"):
        load_limit_rows(len(result), limit)
    return result


# --- by_day ----------------------------------------------------------------------------------


def _check_splittable(s: Statement, date_column: str, where: str) -> None:
    """A level may aggregate or pick rows only if it keeps the date in its grouping."""
    outputs = [column for column, _ in s._outputs]
    grouping = None
    if s._distinct:
        grouping = [name for _, name in s._outputs]
    elif s._group_by:
        grouping = [c._name for c in s._group_by if c._name is not None]
    elif any(column._aggregate for column in outputs):
        grouping = []
    if grouping is not None and date_column not in grouping:
        guard_by_day_grouping(where, date_column)
    for column in outputs:
        for window in column._tree.find_all(exp.Window):
            names = [c.name for c in window.args.get("partition_by") or []
                     if isinstance(c, exp.Column)]
            if date_column not in names:
                guard_by_day_grouping(where, date_column)


def _levels(s: Statement) -> list[tuple[Statement, str]]:
    """The Statement and each Derived table below it through FROM, top first."""
    levels = [(s, "the outer Statement")]
    while levels[-1][0]._reads[0].table._statement is not None:
        table = levels[-1][0]._reads[0].table
        levels.append((table._statement, f"derived({table._name!r}, ...)"))
    return levels


def _one_day(level: Statement, day, new_from=None) -> Statement:
    """A copy of `level` reading one day, or reading `new_from` in place of its FROM table."""
    clauses = list(level._clauses)
    first = level._reads[0]
    index = clauses.index(first)
    if new_from is not None:
        clauses[index] = FROM(new_from, reads_all_partitions=first.reads_all_partitions)
        return statement(*clauses, returns_all_rows=level._returns_all_rows)
    table = first.table
    key = (table._alias, table._date_partition)
    kept = [c for c in level._where if c._only_bounds != key]
    where = WHERE(*kept, equals(getattr(table, table._date_partition), day))
    old = next((c for c in clauses if c._name == "WHERE"), None)
    if old is not None:
        clauses[clauses.index(old)] = where
    else:
        clauses.insert(index + len(level._reads), where)
    return statement(*clauses, returns_all_rows=level._returns_all_rows)


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
        raise TypeError(
            four_part_message(
                what=f"by_day was given {s!r}, which isn't a Statement that reads a table.",
                why="It splits a Statement's days.",
                fix="Pass statement(SELECT(...), FROM(...), WHERE(...)).",
                opt_out=None,
            )
        )
    levels = _levels(s)
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
    for level, where in levels:
        _check_splittable(level, table._date_partition, where)
    return [_split(levels, day) for day in span.dates()]


def _split(levels, day) -> Statement:
    bottom = _one_day(levels[-1][0], day)
    for level, _ in reversed(levels[:-1]):
        old = level._reads[0].table
        new = derived(old._name, bottom)
        if old._alias != old._name:
            new = aliased(new, old._alias)
        bottom = _one_day(level, day, new_from=new)
    return bottom


__all__ = ["to_hive", "run", "by_day", "set_load_limits"]
