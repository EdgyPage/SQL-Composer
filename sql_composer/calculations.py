"""Calculations: counts and sums, row-level functions, and dates grouped into weeks and months.

A calculation in SELECT needs a name, given with AS(...). Arithmetic uses Python's own
+ - * / on columns (`job_runs.duration_mins / 60`), and the Toolbox writes the brackets.
The aggregates are lower case and end in `_of`, so they never hide Python's own sum, min or
max. Each takes `where=` to count or add up only some rows.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp

from .conditions import Condition
from .refusals import four_part_message, guard_unsafe_regrouping
from .tables import (
    Column,
    SIMPLE_NAME,
    has_aggregate,
    hive_date_pattern,
    hive_text,
    identifier,
    is_date_partition,
    literal,
    made_by,
)

TOOLBOX_VERSION = "2.0"

DEFAULT_HIVE_PATTERN = "yyyy-MM-dd"


def _need_column(column, call: str) -> Column:
    if isinstance(column, Column):
        return column
    raise TypeError(
        four_part_message(
            what=f"{call} was given {column!r} where a column goes.",
            why="It works on a column of a table, or on a calculation made from columns.",
            fix="Pass a column, such as job_runs.duration_mins.",
            opt_out=None,
        )
    )


def _only_where(tree: exp.Expression, where, call: str, then=None) -> exp.Expression:
    """`tree`, or CASE WHEN where THEN tree END when only some rows count."""
    if where is None:
        return tree
    if not isinstance(where, Condition):
        raise TypeError(
            four_part_message(
                what=f"{call}: where={where!r} isn't a condition.",
                why="where= picks the rows to count or add up.",
                fix='Pass a condition, such as where=equals(job_runs.status, "FAILED").',
                opt_out=None,
            )
        )
    return exp.Case(ifs=[exp.If(this=where._tree.copy(), true=then or tree)])


def _aggregate(node, column, where, call, *, adds_up=True, because=None,
               distinct=False) -> Column:
    column = _need_column(column, call)
    inner = _only_where(column._tree.copy(), where, call)
    tree = node(this=exp.Distinct(expressions=[inner])) if distinct else node(this=inner)
    made_by(tree, call.split("(")[0], column, where=where)
    return Column(tree, adds_up=adds_up, not_adding_up_because=because, aggregate=True)


def count_rows(where=None):
    """The number of rows, or of the rows where a condition holds.

    >>> count_rows()
    COUNT(*)
    >>> count_rows(where=equals(job_runs.status, "FAILED"))
    COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END)
    """
    tree = _only_where(exp.Star(), where, "count_rows(...)", then=exp.Literal.number(1))
    return Column(made_by(exp.Count(this=tree), "count_rows", where=where), type="bigint",
                  aggregate=True)


def count_distinct(column, where=None):
    """The number of different values in a column, leaving out NULL.

    A distinct count doesn't add up: counts for two days can't be added to give the count
    for both, since a value seen on both days would be counted twice.

    >>> count_distinct(job_runs.job_id)
    COUNT(DISTINCT job_runs.job_id)
    """
    return _aggregate(exp.Count, column, where, f"count_distinct({column!r})", adds_up=False,
                      because="a distinct count", distinct=True)


def sum_of(column, where=None, adds_up=False):
    """The total of a column, or of its rows where a condition holds.

    It refuses a column made by an average, a division or a distinct count, or one its Table
    reference lists in does_not_add_up, since adding those up gives a wrong total. Pass
    adds_up=True if it really does add up.

    >>> sum_of(job_runs.duration_mins)
    SUM(job_runs.duration_mins)
    >>> sum_of(job_runs.duration_mins, where=equals(job_runs.status, "FAILED"))
    SUM(CASE WHEN job_runs.status = 'FAILED' THEN job_runs.duration_mins END)
    """
    call = f"sum_of({column!r})"
    column = _need_column(column, call)
    guard_unsafe_regrouping(call, repr(column), column._not_adding_up_because, adds_up)
    return _aggregate(exp.Sum, column, where, call)


def average_of(column, where=None, adds_up=False):
    """The average of a column; it refuses to average something that doesn't add up.

    An average itself doesn't add up: the average of two daily averages isn't the average
    over both days. Keep the sum and the count, and divide after your own GROUP_BY. Like
    sum_of, it refuses a column that doesn't add up; pass adds_up=True if it really does.

    >>> average_of(job_runs.duration_mins)
    AVG(job_runs.duration_mins)
    """
    call = f"average_of({column!r})"
    column = _need_column(column, call)
    guard_unsafe_regrouping(call, repr(column), column._not_adding_up_because, adds_up)
    return _aggregate(exp.Avg, column, where, call, adds_up=False, because="an average")


def min_of(column, where=None):
    """The smallest value in a column.

    >>> min_of(job_runs.duration_mins)
    MIN(job_runs.duration_mins)
    """
    return _aggregate(exp.Min, column, where, f"min_of({column!r})")


def max_of(column, where=None):
    """The largest value in a column.

    >>> max_of(job_runs.duration_mins)
    MAX(job_runs.duration_mins)
    """
    return _aggregate(exp.Max, column, where, f"max_of({column!r})")


def _as_column(value, call: str) -> Column:
    if isinstance(value, Column):
        return value
    return Column(literal(value, call=call, in_condition=False))


def if_else(condition, then, otherwise):
    """One value where a condition holds and another where it doesn't (CASE WHEN).

    >>> if_else(equals(job_runs.status, "FAILED"), 1, 0)
    CASE WHEN job_runs.status = 'FAILED' THEN 1 ELSE 0 END
    """
    call = "if_else(...)"
    if not isinstance(condition, Condition):
        raise TypeError(
            four_part_message(
                what=f"if_else was given {condition!r} where a condition goes.",
                why="if_else picks `then` for rows where the condition holds.",
                fix='Pass a condition first, such as if_else(equals(job_runs.status, "FAILED"), '
                "1, 0).",
                opt_out=None,
            )
        )
    first, second = _as_column(then, call), _as_column(otherwise, call)
    tree = exp.Case(
        ifs=[exp.If(this=condition._tree.copy(), true=first._tree.copy())],
        default=second._tree.copy(),
    )
    made_by(tree, "if_else", condition, then, otherwise)
    adds_up = first._adds_up and second._adds_up
    because = first._not_adding_up_because or second._not_adding_up_because
    return Column(tree, adds_up=adds_up, not_adding_up_because=None if adds_up else because,
                  aggregate=has_aggregate(tree))


def fill_null(column, value):
    """The column, with a value put in where it is NULL (COALESCE).

    >>> fill_null(job_runs.status, "RUNNING")
    COALESCE(job_runs.status, 'RUNNING')
    """
    call = f"fill_null({column!r}, ...)"
    column = _need_column(column, call)
    other = _as_column(value, call)
    return Column(
        made_by(exp.Coalesce(this=column._tree.copy(), expressions=[other._tree.copy()]),
                "fill_null", column, value),
        type=column._type,
        adds_up=column._adds_up,
        not_adding_up_because=column._not_adding_up_because,
        aggregate=column._aggregate,
    )


def _as_day(column: Column) -> exp.Expression:
    """A date column as a day Hive's date functions read ("2026-09-25")."""
    if not is_date_partition(column):
        return column._tree.copy()
    pattern = hive_date_pattern(column._table._date_format)
    if pattern == DEFAULT_HIVE_PATTERN:
        return column._tree.copy()
    unix = exp.func("unix_timestamp", column._tree.copy(), exp.Literal.string(pattern),
                    dialect="hive")
    return exp.func("from_unixtime", unix, exp.Literal.string(DEFAULT_HIVE_PATTERN),
                    dialect="hive")


def week_start(column):
    """The Monday that starts each date's week, to group days into weeks.

    Hive has no week function that works the same everywhere, so this takes the first
    Monday after the day a week earlier. The result is a day like "2026-09-21".

    >>> week_start(job_runs.dt)
    NEXT_DAY(DATE_ADD(job_runs.dt, 7 * -1), 'MO')
    """
    column = _need_column(column, "week_start(...)")
    week_ago = exp.func("date_sub", _as_day(column), exp.Literal.number(7), dialect="hive")
    tree = exp.func("next_day", week_ago, exp.Literal.string("MO"), dialect="hive")
    return Column(made_by(tree, "week_start", column), type="string")


def month_start(column):
    """The first day of each date's month, to group days into months.

    >>> month_start(job_runs.dt)
    TRUNC(job_runs.dt, 'MM')
    """
    column = _need_column(column, "month_start(...)")
    tree = exp.func("trunc", _as_day(column), exp.Literal.string("MM"), dialect="hive")
    return Column(made_by(tree, "month_start", column), type="string")


class Ordering:
    """A column to sort by, and which way. Made by descending(...)."""

    def __init__(self, target):
        self._target = target

    def __repr__(self) -> str:
        return f"descending({self._target!r})"


def descending(column):
    """Sort by a column from largest to smallest, in ORDER_BY or row_number.

    Pass a column, or the name of an output column as a string.

    >>> row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id))
    ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id DESC)
    """
    if not isinstance(column, (Column, str)):
        _need_column(column, "descending(...)")
    return Ordering(column)


def ordered(item, call: str) -> exp.Ordered:
    """The ORDER BY entry for a column, an output name or descending(...)."""
    descending_order = isinstance(item, Ordering)
    target = item._target if descending_order else item
    if isinstance(target, str):
        tree = exp.column(identifier(target))
    else:
        tree = _need_column(target, call)._tree.copy()
    # Hive puts NULL first when sorting up and last when sorting down; saying so keeps sqlglot
    # from writing NULLS LAST or NULLS FIRST into the Hive.
    return exp.Ordered(this=tree, desc=descending_order, nulls_first=not descending_order)


def _listed(items) -> list:
    return list(items) if isinstance(items, (list, tuple)) else [items]


def row_number(*, PARTITION_BY, ORDER_BY):
    """Number the rows within each group from 1, in the order you give.

    Keeping the rows numbered 1 gives the latest row per key; keeping those up to N gives
    the top N per group. Hive can't filter on a row number in the SELECT that makes it, so
    number the rows in a derived(...) table and keep the ones you want in the Statement that
    reads it. Here is the latest run of each job:

    >>> numbered = derived("numbered", statement(
    ...     SELECT(job_runs.job_id, job_runs.run_id, job_runs.status,
    ...            AS(row_number(PARTITION_BY=job_runs.job_id,
    ...                          ORDER_BY=descending(job_runs.run_id)), "newest_first")),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ... ))
    >>> print(to_hive(statement(
    ...     SELECT(numbered.job_id, numbered.run_id, numbered.status),
    ...     FROM(numbered),
    ...     WHERE(equals(numbered.newest_first, 1)),
    ... )))
    WITH numbered AS (
      SELECT
        job_runs.job_id,
        job_runs.run_id,
        job_runs.status,
        ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id DESC) AS newest_first
      FROM ops.job_runs AS job_runs
      WHERE
        job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    )
    SELECT
      numbered.job_id,
      numbered.run_id,
      numbered.status
    FROM numbered
    WHERE
      numbered.newest_first = 1
    """
    call = "row_number(...)"
    groups = [_need_column(column, call)._tree.copy() for column in _listed(PARTITION_BY)]
    order = exp.Order(expressions=[ordered(item, call) for item in _listed(ORDER_BY)])
    tree = exp.Window(this=exp.RowNumber(), partition_by=groups, order=order)
    made_by(tree, "row_number", PARTITION_BY=PARTITION_BY, ORDER_BY=ORDER_BY)
    return Column(tree, type="int", window=True)


def hive_function(name, *args):
    """Call a Hive function the Toolbox doesn't wrap, with its arguments escaped.

    sqlglot may write a function under Hive's other name for it, or leave out an argument
    that Hive fills in anyway: nvl comes out as COALESCE, and regexp_extract(col, pattern, 1)
    without the 1, since group 1 is what Hive takes when none is given.

    >>> hive_function("regexp_replace", jobs.job_name, "_", " ")
    REGEXP_REPLACE(jobs.job_name, '_', ' ')
    """
    if not isinstance(name, str) or not SIMPLE_NAME.fullmatch(name):
        raise ValueError(
            four_part_message(
                what=f"hive_function({name!r}, ...) isn't a function name.",
                why="Only the function's name is written as it is, so it must be a plain "
                "name: letters, digits and _.",
                fix='Use the Hive function\'s name, such as hive_function("upper", jobs.team).',
                opt_out=None,
            )
        )
    call = f"hive_function({name!r}, ...)"
    trees = [
        literal(arg, call=call, position=f"argument {number}", in_condition=False)
        for number, arg in enumerate(args, start=1)
    ]
    try:
        tree = exp.func(name, *trees, dialect="hive")
        # Read the call back once, as to_hive's self-check will: a few functions come back in
        # sqlglot's own form (DATEDIFF gains TO_DATE on older sqlglot), which is then stable.
        tree = sqlglot.parse_one(hive_text(tree), read="hive")
    except (ValueError, TypeError, sqlglot.errors.ParseError) as error:
        raise TypeError(
            four_part_message(
                what=f"{call} was given {len(args)} arguments, which don't fit {name}.",
                why="sqlglot knows this Hive function and couldn't build it from these "
                "arguments.",
                fix=f"Check {name}'s arguments in Hive's documentation.",
                opt_out=None,
            )
        ) from error
    made_by(tree, "hive_function", name, *args)
    parts = [arg for arg in args if isinstance(arg, Column)]
    because = next((p._not_adding_up_because for p in parts if not p._adds_up), None)
    return Column(tree, aggregate=has_aggregate(tree), window=any(p._window for p in parts),
                  adds_up=because is None, not_adding_up_because=because)


__all__ = [
    "count_rows",
    "count_distinct",
    "sum_of",
    "average_of",
    "min_of",
    "max_of",
    "if_else",
    "fill_null",
    "week_start",
    "month_start",
    "row_number",
    "descending",
    "hive_function",
]
