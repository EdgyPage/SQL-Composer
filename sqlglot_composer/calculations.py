"""Calculations: counts and sums, row-level functions, and dates grouped into weeks and months.

A calculation in SELECT needs a name, given with AS(...). Arithmetic uses Python's own
+ - * / on columns (`job_runs.duration_mins / 60`), and the Toolbox writes the brackets.
The aggregates are lower case and end in `_of`, so they never hide Python's own sum, min or
max. Each takes `where=` to count or add up only some rows.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from .conditions import Condition
from .refusals import (
    guard_unsafe_regrouping,
    refuse,
)
from .tables import (
    COMPARABLE_VALUES,
    Column,
    literal,
    made_by,
    python_text,
    value_family,
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
from .writing import check_writable_call

if TYPE_CHECKING:
    from .windows import Window  # here only: windows.py imports this file

def need_column(column: object, call: str) -> Column:
    if isinstance(column, Column):
        return column
    refuse(
        what=f"{call} was given {column!r} where a column goes.",
        why="It works on a column of a table, or on a calculation made from columns.",
        fix="Pass a column, such as job_runs.duration_mins.",
        given=column, call=call,
    )


def _only_where(tree: Node, where: object, call: str, then: Node | None = None) -> Node:
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


def _not_inside(call: str, inner: Column | Condition) -> None:
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


def _aggregate(name: str, kind: str, column: object, where: object, *, adds_up: bool = True,
               because: str | None = None, distinct: bool = False,
               over: object = None, column_adds_up: bool | None = None) -> Column:
    """`kind` over `column`, made by the function `name`. `column_adds_up` is sum_of's and
    average_of's adds_up=: given, the column must add up, unless it is True."""
    call = f"{name}({python_text(column)})"
    column = need_column(column, call)
    if column_adds_up is not None:
        guard_unsafe_regrouping(call, python_text(column), column._not_adding_up_because,
                                column_adds_up)
    _not_inside(call, column)
    inner = _only_where(column._tree.copy(), where, call)
    if distinct:
        inner = Node("Distinct", expressions=[inner])
    tree, adds_up, because = _over(Node(kind, this=inner), over, call, adds_up, because)
    made_by(tree, name, column, where=where, over=over)
    return Column(tree, adds_up=adds_up, not_adding_up_because=because)


# Why a value worked out over a Window doesn't add up again: guard_unsafe_regrouping's reason.
OVER_A_WINDOW = "worked out over a Window"


def _over(tree: Node, over: object, call: str, adds_up: bool,
          because: str | None) -> tuple[Node, bool, str | None]:
    """A count's or a sum's tree worked out over the Window `over`, if one is given, with
    whether it adds up: rows share the rows their Windows cover, so it doesn't."""
    if over is None:
        return tree, adds_up, because
    from .windows import TOTAL, windowed  # here: windows.py imports this file

    if adds_up:
        adds_up, because = False, OVER_A_WINDOW
    return windowed(tree, over, call, TOTAL), adds_up, because


def count_rows(where: Condition | None = None, over: Window | None = None) -> Column:
    """The number of rows, or of the rows where a condition holds.

    >>> count_rows()
    COUNT(*)
    >>> count_rows(where=equals(job_runs.status, "FAILED"))
    COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END)

    over=window(...) counts the rows of each row's Window, beside each row: see help(window).
    """
    call = "count_rows(...)"
    tree = _only_where(Node("Star"), where, call, then=number("1"))
    tree, adds_up, because = _over(Node("Count", this=tree), over, call, True, None)
    return Column(made_by(tree, "count_rows", where=where, over=over), type="bigint",
                  adds_up=adds_up, not_adding_up_because=because)


def count_distinct(column: Column, where: Condition | None = None) -> Column:
    """The number of different values in a column, leaving out NULL.

    >>> count_distinct(job_runs.job_id)
    COUNT(DISTINCT job_runs.job_id)

    A distinct count doesn't add up: counts for two days can't be added to give the count
    for both, since a value seen on both days would be counted twice.
    """
    return _aggregate("count_distinct", "Count", column, where, adds_up=False,
                      because="a distinct count", distinct=True)


def sum_of(column: Column, where: Condition | None = None, adds_up: bool = False,
           over: Window | None = None) -> Column:
    """The total of a column, or of its rows where a condition holds.

    >>> sum_of(job_runs.duration_mins)
    SUM(job_runs.duration_mins)
    >>> sum_of(job_runs.duration_mins, where=equals(job_runs.status, "FAILED"))
    SUM(CASE WHEN job_runs.status = 'FAILED' THEN job_runs.duration_mins END)

    It refuses a column made by an average, a division or a distinct count, or one its Table
    reference lists in does_not_add_up, since adding those up gives a wrong total. Pass
    adds_up=True if it really does add up.

    over=window(...) gives each row a total of its own, over the rows of its Window, such as a
    running total, or its group's total beside each row; see help(window). It keeps every row,
    and needs no GROUP_BY. That total doesn't add up again: a group's total repeated on each of
    its rows, or running totals that overlap, added up, count rows more than once.

    >>> sum_of(job_runs.duration_mins, over=window(PARTITION_BY=job_runs.job_id,
    ...                                            ORDER_BY=job_runs.run_id, rows=(None, 0)))
    SUM(job_runs.duration_mins) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
    """
    return _aggregate("sum_of", "Sum", column, where, over=over, column_adds_up=adds_up)


def average_of(column: Column, where: Condition | None = None, adds_up: bool = False,
               over: Window | None = None) -> Column:
    """The average of a column that isn't a division, an average or a distinct count.

    >>> average_of(job_runs.duration_mins)
    AVG(job_runs.duration_mins)

    An average itself doesn't add up: the average of two daily averages isn't the average
    over both days. Keep sum_of(...) and count_rows(where=is_not_null(...)) of the column,
    since AVG leaves NULL out, and divide after your own GROUP_BY. Like sum_of, it refuses a
    column that doesn't add up; pass adds_up=True if it really does.

    over=window(...) gives each row the average of its Window's rows, such as a moving
    average, and keeps every row; see help(window).

    >>> average_of(job_runs.duration_mins, over=window(PARTITION_BY=job_runs.job_id,
    ...                                                ORDER_BY=job_runs.run_id, rows=(-2, 0)))
    AVG(job_runs.duration_mins) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
    """
    return _aggregate("average_of", "Avg", column, where, adds_up=False,
                      because="an average", over=over, column_adds_up=adds_up)


def min_of(column: Column, where: Condition | None = None,
           over: Window | None = None) -> Column:
    """The smallest value in a column.

    >>> min_of(job_runs.duration_mins)
    MIN(job_runs.duration_mins)

    over=window(...) gives each row the smallest of its Window's rows; see help(window).
    """
    return _aggregate("min_of", "Min", column, where, over=over)


def max_of(column: Column, where: Condition | None = None,
           over: Window | None = None) -> Column:
    """The largest value in a column.

    >>> max_of(job_runs.duration_mins)
    MAX(job_runs.duration_mins)

    over=window(...) gives each row the largest of its Window's rows; see help(window).
    """
    return _aggregate("max_of", "Max", column, where, over=over)


def _as_column(value: object, call: str) -> Column:
    if isinstance(value, Column):
        return value
    return Column(literal(value, call=call, in_condition=False))


def if_else(condition: Condition,
            then: Column | str | int | float | datetime.date | None,
            otherwise: Column | str | int | float | datetime.date | None) -> Column:
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


def first_match(
        cases: list[tuple[Condition, Column | str | int | float | datetime.date | None]],
        otherwise: Column | str | int | float | datetime.date | None = None) -> Column:
    """Each row's value from the first condition that holds for it (CASE WHEN ...).

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id,
    ...            AS(first_match([(is_null(job_runs.status), "still running"),
    ...                            (more_than(job_runs.duration_mins, 20), "long")],
    ...                           otherwise="short"), "length")),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24")))))
    SELECT
      job_runs.run_id,
      CASE
        WHEN job_runs.status IS NULL
        THEN 'still running'
        WHEN job_runs.duration_mins > 20
        THEN 'long'
        ELSE 'short'
      END AS length
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24'

    Give it a list of (condition, value) pairs. Each row gets the value of the first pair whose
    condition holds for it, so a run still going is "still running" whatever its minutes. A
    row no condition holds for gets otherwise=; leave otherwise= out, and the Hive has no ELSE,
    so that row gets NULL:

    >>> first_match([(equals(job_runs.status, "FAILED"), 1)])
    CASE WHEN job_runs.status = 'FAILED' THEN 1 END

    It writes a whole if/else chain as one CASE, however many pairs it has. For one condition,
    if_else(...) is shorter; where every pair tests one column against a value, mapped(...)
    reads plainer. Each value is a number, a string, a date, None or a column, and all of
    them, otherwise= included, are one type, as a column's values are: a string beside a number
    is refused, as is a condition where a value goes.
    """
    call = "first_match(...)"
    if not isinstance(cases, list):
        refuse(
            what=f"first_match was given {_written(cases)} where a list of (condition, "
            "value) pairs goes.",
            why="Each pair is one test and the value it gives, and the list keeps them in the "
            "order they are tried.",
            fix='Put the pairs in a list, even one pair: first_match([(equals(job_runs.status, '
            '"FAILED"), 1)]).',
            given=cases, call=call,
        )
    if not cases:
        refuse(
            what="first_match(...) was given an empty list.",
            why="With no condition to test, it would give every row its otherwise=.",
            fix="Give it at least one (condition, value) pair, or use the otherwise= value "
            "itself.",
            error=ValueError,
        )
    pairs = [_pair(item, number, call) for number, item in enumerate(cases, start=1)]
    written = ", ".join(f"({python_text(condition)}, {python_text(value)})"
                        for condition, value in pairs)
    return _case(None, [(condition._tree.copy(), value) for condition, value in pairs],
                 otherwise, call, f"first_match([{written}]")


def _pair(item: object, number: int, call: str) -> tuple[Condition, object]:
    """One of first_match's pairs, checked: a condition, then the value it gives."""
    if not isinstance(item, (tuple, list)) or len(item) != 2:
        refuse(
            what=f"first_match: pair {number} is {_written(item)}, which isn't a "
            "(condition, value) pair.",
            why="Each item of the list is one condition and the value rows get where it holds, "
            "in round brackets.",
            fix='Write each as (condition, value), such as (equals(job_runs.status, "FAILED"), '
            '"failed").',
            given=item, call=call,
        )
    condition, value = item
    if not isinstance(condition, Condition):
        if isinstance(value, Condition):
            refuse(
                what=f"first_match: pair {number} has the condition second: "
                f"{_written(item)}.",
                why="Each pair is a condition, then the value rows get where it holds.",
                fix="Swap the two, as in (equals(job_runs.status, \"FAILED\"), \"failed\").",
            )
        refuse(
            what=f"first_match: pair {number} has {python_text(condition)} where a condition "
            "goes.",
            why="Each pair starts with the test a row must pass to get the pair's value.",
            fix="Start the pair with a condition, such as (equals(job_runs.status, \"FAILED\"), "
            "\"failed\").",
            given=condition, call=call,
        )
    return condition, value


def _written(value: object) -> str:
    """A value as the user wrote it, a tuple in round brackets: python_text writes one as a
    list."""
    if isinstance(value, tuple):
        return "(" + ", ".join(python_text(item) for item in value) + ")"
    return python_text(value)


def mapped(column: Column,
           values: dict[str | int | float | bool | datetime.date,
                        Column | str | int | float | datetime.date | None],
           otherwise: Column | str | int | float | datetime.date | None = None) -> Column:
    """A value for each value of a column, looked up in a dict (CASE column WHEN ...).

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id,
    ...            AS(mapped(job_runs.status, {"SUCCESS": "passed", "FAILED": "failed"},
    ...                      otherwise="other"), "outcome")),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24")))))
    SELECT
      job_runs.run_id,
      CASE job_runs.status WHEN 'SUCCESS' THEN 'passed' WHEN 'FAILED' THEN 'failed' ELSE 'other' END AS outcome
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24'

    Each key of the dict is a value the column may hold, and each row gets the value its
    column's value is the key of. A row whose value is no key gets otherwise=; leave otherwise=
    out, and the Hive has no ELSE, so that row gets NULL. A row whose column is NULL matches no
    key, since NULL equals nothing, so a None key is refused: first_match([(is_null(column),
    value), ...]) gives those rows a value of their own. Keep a long dict as a constant at the
    top of your script, such as STATUS_LABELS = {...}, and pass it by its name.

    It is first_match(...) for the chain that tests one column against a value in each pair,
    written shorter. Each key is a value of the column's own type: a key it can't hold, such as
    "one" for a bigint column, is refused, as equals(...) refuses it. The values follow
    first_match's rule: all one type, otherwise= included, and never a condition.
    """
    call = f"mapped({python_text(column)}, ...)"
    column = need_column(column, call)
    if not isinstance(values, dict):
        refuse(
            what=f"{call} was given {_written(values)} where a dict of values goes.",
            why="The dict pairs each value the column may hold with the value rows that hold "
            "it get.",
            fix=f'Write it as a dict, such as mapped({python_text(column)}, {{"FAILED": '
            '"failed", "SUCCESS": "passed"}).',
            given=values, call=call,
        )
    if not values:
        refuse(
            what=f"{call} was given an empty dict.",
            why="With no value to look up, it would give every row its otherwise=.",
            fix="Give it at least one key and its value, or use the otherwise= value itself.",
            error=ValueError,
        )
    for key in values:
        if isinstance(key, (Column, Condition)):
            refuse(
                what=f"{call} was given {python_text(key)} as a key, where a value to look up "
                "goes.",
                why="mapped compares its column with each key, so a key is a value, such as "
                '"FAILED"; a test of anything else needs a condition of its own.',
                fix="Use first_match([(condition, value), ...]), which takes any condition, "
                "or give a value as the key.",
                given=key, call=call,
            )
    keys = [literal(key, call=call, column=column) for key in values]
    _one_type(list(values), call, "keys")
    written = ", ".join(f"{python_text(key)}: {python_text(value)}"
                        for key, value in values.items())
    return _case(column, list(zip(keys, values.values())), otherwise, call,
                 f"mapped({python_text(column)}, {{{written}}}")


def _case(column: Column | None, pairs: list[tuple[Node, object]], otherwise: object,
          call: str, written: str) -> Column:
    """first_match's or mapped's CASE: each pair a WHEN's condition, or the value mapped looks
    `column` up for, and its THEN, the user's value as given; ELSE only when `otherwise` isn't
    None. `written` is the call as the user wrote it, up to its otherwise=, for the lineage."""
    given = [value for _, value in pairs] + ([otherwise] if otherwise is not None else [])
    for value in given:
        if isinstance(value, Condition):
            refuse(
                what=f"{call.split('(')[0]} was given {python_text(value)} where a value goes.",
                why="A value is what the rows get: a number, a string, a date, None or a "
                "column. A condition is a test on rows, and only decides which rows get "
                "which value.",
                fix="Give the value the rows get, such as \"failed\" or 1. A condition goes "
                "first in a first_match pair: (condition, value).",
                given=value, call=call,
            )
    values = [_as_column(value, call) for value in given]
    _one_type(given, call, "values")
    tree = Node("Case", ifs=[Node("If", this=when, true=value._tree.copy())
                             for (when, _), value in zip(pairs, values)])
    if column is not None:
        tree.set("this", column._tree.copy())
    if otherwise is not None:
        tree.set("default", values[-1]._tree.copy())
        written += f", otherwise={python_text(otherwise)}"
    tree.meta["call"] = f"{written})"
    because = next((value._not_adding_up_because for value in values if not value._adds_up),
                   None)
    return Column(tree, adds_up=because is None, not_adding_up_because=because)


# How a refusal names the type of a value, by its family (tables.value_family).
_FAMILY_WORDS = {"number": "a number", "string": "a string", "date": "a date",
                 "timestamp": "a timestamp", "boolean": "True or False"}


def _one_type(given: list[object], call: str, what: str) -> None:
    """Refuse `what`, first_match's or mapped's values or mapped's keys, when two of them are of
    types that can't stand in one column; one whose type isn't known, as NULL's, goes with any."""
    known = [(value, family) for value in given
             if (family := value_family(value)) is not None]
    for value, family in known[1:]:
        first, first_family = known[0]
        if family in COMPARABLE_VALUES[first_family]:
            continue
        refuse(
            what=f"{call.split('(')[0]} gives {what} whose types don't mix: "
            f"{_with_type(first, first_family)}, and {_with_type(value, family)}.",
            why=_MIXED_WHY[what],
            fix=_MIXED_FIX[what],
        )


# What to do instead, for values or for keys.
_MIXED_FIX = {
    "values": 'Give all the values one type, such as all strings: "1" in place of 1.',
    "keys": "Give every key the type of the values the column holds: for a string column, "
    '"1" in place of 1.',
}
# Why values, or keys, of types that don't mix give a wrong answer.
_MIXED_WHY = {
    "values": "A CASE gives back one column, of one type, so the warehouse would turn one into "
    "the other's type: a row could quietly get NULL or a changed value, or the whole Statement "
    "stop with an error.",
    "keys": "Each key is compared with the column's value, so the warehouse would turn one into "
    "the other's type: a row could quietly match the wrong key or none, or the whole Statement "
    "stop with an error.",
}


def _with_type(value: object, family: str) -> str:
    """A value and its type, as a refusal names them: "0, a number" or "job_runs.dt, a string
    column"."""
    if isinstance(value, Column):
        article = "an" if value._type[0] in "aeiou" else "a"
        return f"{python_text(value)}, {article} {value._type} column"
    return f"{python_text(value)}, {_FAMILY_WORDS[family]}"


def fill_null(column: Column, value: Column | str | int | float | datetime.date) -> Column:
    """The column, with a value put in where it is NULL (COALESCE).

    >>> fill_null(job_runs.status, "RUNNING")
    COALESCE(job_runs.status, 'RUNNING')
    """
    call = f"fill_null({python_text(column)}, ...)"
    column = need_column(column, call)
    other = _as_column(value, call)
    return Column(
        made_by(Node("Coalesce", this=column._tree.copy(), expressions=[other._tree.copy()]),
                "fill_null", column, value),
        type=column._type,
        adds_up=column._adds_up,
        not_adding_up_because=column._not_adding_up_because,
    )


def _call(name: str, *args: Node) -> Node:
    """A call to one of Hive's date functions, such as next_day."""
    return Node("Call", name=name, args=list(args))


def week_start(column: Column) -> Column:
    """The Monday that starts each date's week, to group days into weeks.

    >>> week_start(job_runs.dt)
    CAST(NEXT_DAY(DATE_ADD(job_runs.dt, 7 * -1), 'MO') AS STRING)

    Hive has no function for the Monday of a week, so this takes the first Monday after the
    day a week earlier: in the example above, DATE_ADD(job_runs.dt, 7 * -1) is the day seven
    days before. The result is text, a day like "2026-09-21": CAST(... AS STRING) makes it
    text wherever the query runs, even on a warehouse whose NEXT_DAY gives a date, so a Saved
    table's column for it is always typed "string". It works on any column of dates, a
    partition column or not, whose days are written as Hive's date functions read them, like
    "2026-09-25".
    """
    column = need_column(column, "week_start(...)")
    week_ago = _call("date_sub", column._tree.copy(), number("7"))
    tree = Node("Cast", this=_call("next_day", week_ago, string("MO")), to="STRING")
    return Column(made_by(tree, "week_start", column), type="string")


def month_start(column: Column) -> Column:
    """The first day of each date's month, to group days into months.

    >>> month_start(job_runs.dt)
    CAST(TRUNC(job_runs.dt, 'MM') AS STRING)

    The result is text, a day like "2026-09-01": CAST(... AS STRING) makes it text wherever
    the query runs, even on a warehouse whose TRUNC gives a date, so a Saved table's column for
    it is always typed "string". Like week_start, it works on any column of dates written like
    "2026-09-25".
    """
    column = need_column(column, "month_start(...)")
    tree = Node("Cast", this=_call("trunc", column._tree.copy(), string("MM")), to="STRING")
    return Column(made_by(tree, "month_start", column), type="string")


class Ordering:
    """A column to sort by from largest to smallest, made by descending(...).

    >>> descending(job_runs.dt)
    descending(job_runs.dt)

    A column given as it is sorts from smallest to largest, and needs no Ordering. Make one
    with descending(...), never Ordering(). Write the name in a type hint, to say that
    a function of yours gives one back:

    >>> def newest_first() -> Ordering:
    ...     return descending(job_runs.dt)
    >>> newest_first()
    descending(job_runs.dt)
    """

    def __init__(self, target: Column | str) -> None:
        self._target = target

    def __repr__(self) -> str:
        return f"descending({self._target!r})"


def descending(column: Column | str) -> Ordering:
    """Sort by a column from largest to smallest, in ORDER_BY or a Window's ORDER_BY.

    >>> print(to_hive(statement(SELECT(jobs.job_name), FROM(jobs),
    ...                         ORDER_BY(descending(jobs.job_name)), LIMIT(2))))
    SELECT
      jobs.job_name
    FROM ops.jobs AS jobs
    ORDER BY
      jobs.job_name DESC
    LIMIT 2

    Pass a column; in ORDER_BY(...), the name of an output column as a string works too, but
    not in window(...) or row_number(...), which can't see the names given in SELECT.

    >>> row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id))
    ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id DESC)
    """
    if not isinstance(column, (Column, str)):
        need_column(column, "descending(...)")
    return Ordering(column)


def ordered(item: object, call: str) -> Node:
    """The ORDER BY entry for a column, an output name or descending(...)."""
    descending_order = isinstance(item, Ordering)
    target = item._target if descending_order else item
    if isinstance(target, str):
        tree = Node("Column", name=target)
    else:
        tree = need_column(target, call)._tree.copy()
    return Node("Ordered", this=tree, desc=descending_order)


def hive_function(name: str, *args: Column | str | int | float | datetime.date) -> Column:
    """Call a Hive function the Toolbox doesn't wrap, with your text quoted for you.

    >>> hive_function("regexp_replace", jobs.job_name, "_", " ")
    REGEXP_REPLACE(jobs.job_name, '_', ' ')

    The Toolbox writes the function's name in capitals, and writes the call in its usual form:
    sometimes by another name that does the same, as COALESCE for nvl, or without an
    argument that is filled in anyway, as regexp_extract(col, pattern, 1) without its 1: group 1
    is what the warehouse takes when none is given. Either way it does the same. In a date_format
    pattern, write yyyy for the year, not YYYY: YYYY is the year a week belongs to, which differs
    from the year in the last days of December and the first of January.

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
    """Refuse a call Hive would stop on: a window function, or a count of arguments
    HIVE_FUNCTION_ARGUMENTS in trees.py says the function doesn't take."""
    if name.lower() in WINDOW_FUNCTIONS:
        refuse(
            what=f"{call} calls {name}, which works only over a window of rows, written "
            f"{name.upper()}(...) OVER (...).",
            why="hive_function can't write OVER, and without it Hive stops the whole "
            "Statement with an error.",
            fix=_WINDOW_FIXES.get(name.lower(), "SELECT the columns it needs, and work it out "
                                  "in pandas on the DataFrame run_query(...) gives back."),
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
    "first_match",
    "mapped",
    "fill_null",
    "week_start",
    "month_start",
    "descending",
    "hive_function",
]
