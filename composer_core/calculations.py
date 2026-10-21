"""Calculations: counts and sums, row-level functions, and dates grouped into weeks and months.

A calculation in SELECT needs a name, given with AS(...). Arithmetic uses Python's own
+ - * / on columns (`job_runs.duration_mins / 60`), and the Toolbox writes the brackets.
The aggregates are lower case and end in `_of`, so they never hide Python's own sum, min or
max. Each takes `where=` to count or add up only some rows.
"""

from __future__ import annotations

from .conditions import Condition
from .refusals import (
    guard_unsafe_regrouping,
    refuse,
)
from .tables import (
    Column,
    hive_date_pattern,
    is_date_partition,
    literal,
    made_by,
    python_text,
)
from .trees import (
    HIVE_AGGREGATES,
    HIVE_FUNCTION_ARGUMENTS,
    SIMPLE_NAME,
    WINDOW_FUNCTIONS,
    Node,
    arguments_text,
    has_aggregate,
    has_window,
    number,
    numbers_rows,
    string,
)
from .edition import check_writable_call

TOOLBOX_VERSION = "5.1"

DEFAULT_HIVE_PATTERN = "yyyy-MM-dd"


def _need_column(column, call: str) -> Column:
    if isinstance(column, Column):
        return column
    refuse(
        what=f"{call} was given {column!r} where a column goes.",
        why="It works on a column of a table, or on a calculation made from columns.",
        fix="Pass a column, such as job_runs.duration_mins.",
        given=column, call=call,
    )


def _only_where(tree: Node, where, call: str, then=None) -> Node:
    """`tree`, or CASE WHEN where THEN tree END when only some rows count."""
    if where is None:
        return tree
    if not isinstance(where, Condition):
        refuse(
            what=f"{call}: where={where!r} isn't a condition.",
            why="where= picks the rows to count or add up.",
            fix='Pass a condition, such as where=equals(job_runs.status, "FAILED").',
            given=where, call=call,
        )
    _not_inside(call, where)
    return Node("Case", ifs=[Node("If", this=where._tree.copy(), true=then or tree)])


def _not_inside(call: str, inner) -> None:
    """Refuse a count, a sum or a calculation over a Window inside a function that works over
    many rows."""
    window = has_window(inner._tree)
    if window or has_aggregate(inner._tree):
        made = "already works over many rows itself"
        if window:
            made = ("is a row number" if numbers_rows(inner._tree)
                    else "looks across rows through a Window")
        refuse(
            what=f"{call} has {inner!r} inside it, which {made}.",
            why="In one SELECT, Hive can't put a count, a sum or a calculation over a Window "
            "inside a function that works over many rows, such as a count, a sum, a max or "
            "collect_set.",
            fix="Work it out as a named column in a derived(...) table, then use it in the "
            "Statement that reads that table; help(derived) shows how.",
            error=ValueError,
        )


def _aggregate(name, kind, column, where, *, adds_up=True, because=None,
               distinct=False, over=None) -> Column:
    call = f"{name}({python_text(column)})"
    column = _need_column(column, call)
    _not_inside(call, column)
    inner = _only_where(column._tree.copy(), where, call)
    if distinct:
        inner = Node("Distinct", expressions=[inner])
    tree, adds_up, because = _over(Node(kind, this=inner), over, call, adds_up, because)
    made_by(tree, name, column, where=where, over=over)
    return Column(tree, adds_up=adds_up, not_adding_up_because=because)


# Why a value worked out over a Window doesn't add up again: guard_unsafe_regrouping's reason.
OVER_A_WINDOW = "worked out over a Window"


def _over(tree: Node, over, call: str, adds_up: bool, because):
    """A count's or a sum's tree worked out over the Window `over`, if one is given, with
    whether it adds up: rows share the rows their Windows cover, so it doesn't."""
    if over is None:
        return tree, adds_up, because
    from .windows import TOTAL, windowed  # here: windows.py imports this file

    if adds_up:
        adds_up, because = False, OVER_A_WINDOW
    return windowed(tree, over, call, TOTAL), adds_up, because


def count_rows(where=None, over=None):
    """The number of rows, or of the rows where a condition holds.

    over=window(...) counts the rows of each row's Window, beside each row: see help(window).

    >>> count_rows()
    COUNT(*)
    >>> count_rows(where=equals(job_runs.status, "FAILED"))
    COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END)
    """
    call = "count_rows(...)"
    tree = _only_where(Node("Star"), where, call, then=number("1"))
    tree, adds_up, because = _over(Node("Count", this=tree), over, call, True, None)
    return Column(made_by(tree, "count_rows", where=where, over=over), type="bigint",
                  adds_up=adds_up, not_adding_up_because=because)


def count_distinct(column, where=None):
    """The number of different values in a column, leaving out NULL.

    A distinct count doesn't add up: counts for two days can't be added to give the count
    for both, since a value seen on both days would be counted twice.

    >>> count_distinct(job_runs.job_id)
    COUNT(DISTINCT job_runs.job_id)
    """
    return _aggregate("count_distinct", "Count", column, where, adds_up=False,
                      because="a distinct count", distinct=True)


def sum_of(column, where=None, adds_up=False, over=None):
    """The total of a column, or of its rows where a condition holds.

    It refuses a column made by an average, a division or a distinct count, or one its Table
    reference lists in does_not_add_up, since adding those up gives a wrong total. Pass
    adds_up=True if it really does add up.

    over=window(...) gives each row a total of its own, over the rows of its Window, such as a
    running total, or its group's total beside each row; see help(window). It keeps every row,
    and needs no GROUP_BY. That total doesn't add up again: a group's total repeated on each of
    its rows, or running totals that overlap, added up, count rows more than once.

    >>> sum_of(job_runs.duration_mins)
    SUM(job_runs.duration_mins)
    >>> sum_of(job_runs.duration_mins, where=equals(job_runs.status, "FAILED"))
    SUM(CASE WHEN job_runs.status = 'FAILED' THEN job_runs.duration_mins END)
    >>> sum_of(job_runs.duration_mins, over=window(PARTITION_BY=job_runs.job_id,
    ...                                            ORDER_BY=job_runs.run_id, rows=(None, 0)))
    SUM(job_runs.duration_mins) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
    """
    call = f"sum_of({python_text(column)})"
    column = _need_column(column, call)
    guard_unsafe_regrouping(call, python_text(column), column._not_adding_up_because, adds_up)
    return _aggregate("sum_of", "Sum", column, where, over=over)


def average_of(column, where=None, adds_up=False, over=None):
    """The average of a column that isn't a division, an average or a distinct count.

    An average itself doesn't add up: the average of two daily averages isn't the average
    over both days. Keep sum_of(...) and count_rows(where=is_not_null(...)) of the column,
    since AVG leaves NULL out, and divide after your own GROUP_BY. Like sum_of, it refuses a
    column that doesn't add up; pass adds_up=True if it really does.

    over=window(...) gives each row the average of its Window's rows, such as a moving
    average, and keeps every row; see help(window).

    >>> average_of(job_runs.duration_mins)
    AVG(job_runs.duration_mins)
    >>> average_of(job_runs.duration_mins, over=window(PARTITION_BY=job_runs.job_id,
    ...                                                ORDER_BY=job_runs.run_id, rows=(-2, 0)))
    AVG(job_runs.duration_mins) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
    """
    call = f"average_of({python_text(column)})"
    column = _need_column(column, call)
    guard_unsafe_regrouping(call, python_text(column), column._not_adding_up_because, adds_up)
    return _aggregate("average_of", "Avg", column, where, adds_up=False,
                      because="an average", over=over)


def min_of(column, where=None, over=None):
    """The smallest value in a column.

    over=window(...) gives each row the smallest of its Window's rows; see help(window).

    >>> min_of(job_runs.duration_mins)
    MIN(job_runs.duration_mins)
    """
    return _aggregate("min_of", "Min", column, where, over=over)


def max_of(column, where=None, over=None):
    """The largest value in a column.

    over=window(...) gives each row the largest of its Window's rows; see help(window).

    >>> max_of(job_runs.duration_mins)
    MAX(job_runs.duration_mins)
    """
    return _aggregate("max_of", "Max", column, where, over=over)


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
        refuse(
            what=f"if_else was given {condition!r} where a condition goes.",
            why="if_else picks `then` for rows where the condition holds.",
            fix='Pass a condition first, such as if_else(equals(job_runs.status, "FAILED"), '
            "1, 0).",
            given=condition, call=call,
        )
    first, second = _as_column(then, call), _as_column(otherwise, call)
    tree = Node(
        "Case",
        ifs=[Node("If", this=condition._tree.copy(), true=first._tree.copy())],
        default=second._tree.copy(),
    )
    made_by(tree, "if_else", condition, then, otherwise)
    adds_up = first._adds_up and second._adds_up
    because = first._not_adding_up_because or second._not_adding_up_because
    return Column(tree, adds_up=adds_up, not_adding_up_because=None if adds_up else because)


def fill_null(column, value):
    """The column, with a value put in where it is NULL (COALESCE).

    >>> fill_null(job_runs.status, "RUNNING")
    COALESCE(job_runs.status, 'RUNNING')
    """
    call = f"fill_null({python_text(column)}, ...)"
    column = _need_column(column, call)
    other = _as_column(value, call)
    return Column(
        made_by(Node("Coalesce", this=column._tree.copy(), expressions=[other._tree.copy()]),
                "fill_null", column, value),
        type=column._type,
        adds_up=column._adds_up,
        not_adding_up_because=column._not_adding_up_because,
    )


def _as_day(column: Column) -> Node:
    """A date column as a day Hive's date functions read ("2026-09-25")."""
    if not is_date_partition(column):
        return column._tree.copy()
    pattern = hive_date_pattern(column._table._date_format)
    if pattern == DEFAULT_HIVE_PATTERN:
        return column._tree.copy()
    unix = _call("unix_timestamp", column._tree.copy(), string(pattern))
    return _call("from_unixtime", unix, string(DEFAULT_HIVE_PATTERN))


def _call(name: str, *args: Node) -> Node:
    """A call to one of Hive's date functions, such as next_day."""
    return Node("Call", name=name, args=list(args))


def week_start(column):
    """The Monday that starts each date's week, to group days into weeks.

    Hive and Spark have no week function that works the same on both, so this takes the first
    Monday after the day a week earlier: in the example below, DATE_ADD(job_runs.dt, 7 * -1) is
    the day seven days before. The result is text, a day like "2026-09-21", whether your
    warehouse runs the query on Hive or on Spark: Hive's NEXT_DAY gives text already, and
    Spark's gives a date, so CAST(... AS STRING) makes it text there too. A Saved table's column
    for it is typed "string".

    >>> week_start(job_runs.dt)
    CAST(NEXT_DAY(DATE_ADD(job_runs.dt, 7 * -1), 'MO') AS STRING)
    """
    column = _need_column(column, "week_start(...)")
    week_ago = _call("date_sub", _as_day(column), number("7"))
    tree = Node("Cast", this=_call("next_day", week_ago, string("MO")), to="STRING")
    return Column(made_by(tree, "week_start", column), type="string")


def month_start(column):
    """The first day of each date's month, to group days into months.

    The result is text, a day like "2026-09-01", whether your warehouse runs the query on Hive
    or on Spark: Hive's TRUNC gives text already, and Spark's gives a date, so CAST(... AS
    STRING) makes it text there too. A Saved table's column for it is typed "string".

    >>> month_start(job_runs.dt)
    CAST(TRUNC(job_runs.dt, 'MM') AS STRING)
    """
    column = _need_column(column, "month_start(...)")
    tree = Node("Cast", this=_call("trunc", _as_day(column), string("MM")), to="STRING")
    return Column(made_by(tree, "month_start", column), type="string")


class Ordering:
    """A column to sort by, and which way. Made by descending(...)."""

    def __init__(self, target):
        self._target = target

    def __repr__(self) -> str:
        return f"descending({self._target!r})"


def descending(column):
    """Sort by a column from largest to smallest, in ORDER_BY or a Window's ORDER_BY.

    Pass a column; in ORDER_BY(...), the name of an output column as a string works too, but
    not in window(...) or row_number(...), which can't see the names given in SELECT.

    >>> row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id))
    ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id DESC)
    """
    if not isinstance(column, (Column, str)):
        _need_column(column, "descending(...)")
    return Ordering(column)


def ordered(item, call: str) -> Node:
    """The ORDER BY entry for a column, an output name or descending(...)."""
    descending_order = isinstance(item, Ordering)
    target = item._target if descending_order else item
    if isinstance(target, str):
        tree = Node("Column", name=target)
    else:
        tree = _need_column(target, call)._tree.copy()
    return Node("Ordered", this=tree, desc=descending_order)


def hive_function(name, *args):
    """Call a Hive function the Toolbox doesn't wrap, with your text quoted for you.

    The Hive writes its name in capitals. It may write another name that does the same, as
    COALESCE for nvl, or leave out an argument that is filled in anyway, as
    regexp_extract(col, pattern, 1) without its 1: group 1 is what the warehouse takes when none
    is given. Either way it does the same. In a date_format pattern, write yyyy for the year, not YYYY: YYYY is the
    year a week belongs to, which Spark refuses in a pattern.

    It checks the call before writing it:

    - it refuses a call with the wrong number of arguments, for the functions it knows, such as
      upper, substr or date_add;
    - a function that turns many rows into one, such as collect_set or percentile, is treated
      as count_rows() is: it needs a name with AS, and GROUP_BY for the other columns;
    - it refuses a function that works only over a window of rows, written OVER (...) after
      it, such as lag or rank, since it can't write OVER. For lag, lead, rank, dense_rank,
      ntile and row_number, the refusal names the Toolbox's own function, such as lag(...),
      which takes a window(...); for the others, such as percent_rank, it says to work it out
      in pandas.

    >>> hive_function("regexp_replace", jobs.job_name, "_", " ")
    REGEXP_REPLACE(jobs.job_name, '_', ' ')
    """
    if not isinstance(name, str) or not SIMPLE_NAME.fullmatch(name):
        refuse(
            what=f"hive_function({name!r}, ...) isn't a function name.",
            why="Only the function's name is written as it is, so it must be a plain "
            "name: letters, digits and _.",
            fix='Use the Hive function\'s name, such as hive_function("upper", jobs.team).',
            error=ValueError,
        )
    call = f"hive_function({name!r}, ...)"
    trees = [
        literal(arg, call=call, position=f"argument {number}", in_condition=False)
        for number, arg in enumerate(args, start=1)
    ]
    _check_function(name, len(trees), call)
    check_writable_call(name, trees, call)
    # Hive reads a function's name whatever its case, so "NVL" and "nvl" are one function.
    tree = Node("HiveFunction", name=name.lower(), args=trees,
                aggregate=name.lower() in HIVE_AGGREGATES)
    made_by(tree, "hive_function", name, *args)
    parts = [arg for arg in args if isinstance(arg, Column)]
    if tree.parts["aggregate"]:
        for part in parts:
            _not_inside(call, part)
    because = next((p._not_adding_up_because for p in parts if not p._adds_up), None)
    return Column(tree, adds_up=because is None, not_adding_up_because=because)


def _check_function(name: str, count: int, call: str) -> None:
    """Refuse a call Hive and Spark would stop on: a window function, or a count of arguments
    HIVE_FUNCTION_ARGUMENTS in trees.py says the function doesn't take."""
    if name.lower() in WINDOW_FUNCTIONS:
        refuse(
            what=f"{call} calls {name}, which works only over a window of rows, written "
            f"{name.upper()}(...) OVER (...).",
            why="hive_function can't write OVER, and without it Hive and Spark stop the whole "
            "Statement with an error.",
            fix=_WINDOW_FIXES.get(name.lower(), "SELECT the columns it needs, and work it out "
                                  "in pandas on the DataFrame run(...) gives back."),
            error=ValueError,
        )
    fewest, most = HIVE_FUNCTION_ARGUMENTS.get(name.lower(), (0, None))
    if count < fewest or (most is not None and count > most):
        takes = arguments_text(fewest, most)
        refuse(
            what=f"{call} gives {name} {arguments_text(count, count)}, and {name} takes "
            f"{takes}.",
            why="The warehouse would stop the whole Statement with an error when it runs.",
            fix=f'Give hive_function {takes} after "{name}".',
        )


# What to do instead of a window function: the Toolbox's own name for it, which writes OVER.
_WINDOW_FIXES = {
    name: f"Use {name}({written}), which writes OVER (...) itself; help(window) shows how."
    for name, written in {
        "row_number": "over=window(...)", "rank": "over=window(...)",
        "dense_rank": "over=window(...)", "ntile": "parts, over=window(...)",
        "lag": "column, over=window(...)", "lead": "column, over=window(...)",
    }.items()
}


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
    "descending",
    "hive_function",
]
