# SQL Composer 3.1, exported 2026-09-30 20:19 - generated from dev, do not edit
"""Conditions: the tests that go in WHERE, HAVING and JOIN's ON=.

Each condition is a named function, never a Python operator: `equals(job_runs.status,
"FAILED")`, not `job_runs.status == "FAILED"`. Every one comes with its own opposite, so there
is no `not_(...)`. Values are escaped by the Toolbox, so any string is safe to pass.
"""

from __future__ import annotations

import datetime

from .refusals import (
    four_part_message,
    guard_none_in_condition,
    refuse_what_the_other_edition_made,
)
from .tables import (
    Column,
    as_date,
    is_date_partition,
    literal,
    made_by,
    python_text,
    type_family,
)
from .trees import Node, combined, has_aggregate
from .writing import hive_text

TOOLBOX_VERSION = "3.1"


def today() -> datetime.date:
    """Today's date, as last_n_days sees it. The tests replace it with a fixed day."""
    return datetime.date.today()


class Span:
    """The days a condition lets through for one Date partition: low, high, or a list."""

    def __init__(self, low=None, high=None, days=None):
        self.low = low
        self.high = high
        self.days = days

    def is_bounded(self) -> bool:
        return self.days is not None or (self.low is not None and self.high is not None)

    def dates(self) -> list[datetime.date]:
        """Every day in the span, oldest first."""
        if self.days is not None:
            return sorted(day for day in self.days if self._inside(day))
        count = (self.high - self.low).days + 1
        return [self.low + datetime.timedelta(days=n) for n in range(max(count, 0))]

    def _inside(self, day) -> bool:
        return (self.low is None or day >= self.low) and (self.high is None or day <= self.high)


def days_in_both(first: Span, second: Span) -> Span:
    """The days two conditions joined with AND both let through."""
    low = max((s.low for s in (first, second) if s.low is not None), default=None)
    high = min((s.high for s in (first, second) if s.high is not None), default=None)
    sets = [s.days for s in (first, second) if s.days is not None]
    days = frozenset.intersection(*sets) if sets else None
    return Span(low, high, days)


def days_in_either(first: Span, second: Span) -> Span:
    """The days two conditions joined with OR let through between them."""
    low = None if None in (first.low, second.low) else min(first.low, second.low)
    high = None if None in (first.high, second.high) else max(first.high, second.high)
    if first.days is not None and second.days is not None:
        days = first.days | second.days
    else:
        days = None
    if days is not None and (low is None or high is None):
        low, high = min(days), max(days)
    return Span(low, high, days)


class Condition:
    """A test on rows, for WHERE, HAVING or ON=. Combine several with all_of or any_of."""

    def __init__(self, tree, *, spans=None, only_bounds=None, tests_for_null=False):
        self._tree = tree
        # {(table alias, column): Span} for each Date partition this condition bounds.
        self._spans = spans or {}
        # The (alias, column) this condition does nothing but bound, so by_day can replace it.
        self._only_bounds = only_bounds
        # True for is_null(...), which LEFT_JOIN allows in WHERE: it keeps the rows with no match.
        self._tests_for_null = tests_for_null
        self._aggregate = has_aggregate(tree)

    def __repr__(self) -> str:
        return hive_text(self._tree)

    def _tables(self) -> set[str]:
        return {column.table for column in self._tree.find_all("Column") if column.table}

    def __and__(self, other):
        _no_combining("&", "all_of(...), or separate conditions in WHERE(...)")

    __rand__ = __and__

    def __or__(self, other):
        _no_combining("|", "any_of(...)")

    __ror__ = __or__

    def __invert__(self):
        _no_combining("~", "the opposite condition, such as not_equals(...)")

    def __bool__(self):
        _no_combining("if, and, or or not", "all_of(...) or any_of(...)")


def _no_combining(symbol: str, instead: str) -> None:
    raise TypeError(
        four_part_message(
            what=f"A condition was used with Python's {symbol}.",
            why="Python would combine the Python objects, not the conditions, and the result "
            "would not mean what you wrote.",
            fix=f"Use {instead}.",
            opt_out=None,
        )
    )


def _need_column(column, call: str) -> Column:
    if isinstance(column, Column):
        return column
    refuse_what_the_other_edition_made(column, call)
    raise TypeError(
        four_part_message(
            what=f"{call} was given {column!r} where a column goes.",
            why="A condition tests a column of a table, such as job_runs.status.",
            fix="Pass the column as an attribute of its Table reference, such as "
            "equals(job_runs.status, \"FAILED\").",
            opt_out=None,
        )
    )


def _spans_key(column: Column) -> tuple[str, str]:
    """(table alias, column name): how a condition's spans name the Date partition they bound."""
    return (column._table._alias, column._name)


def _compare(name: str, kind: str, column, value, span_of) -> Condition:
    """A comparison of a column with one value, noting any Date partition bound."""
    call = f"{name}({python_text(column)}, ...)"
    column = _need_column(column, call)
    if value is None:
        guard_none_in_condition(f"{name}({python_text(column)}, None)")
    tree = Node(kind, this=column._tree.copy(),
                expression=literal(value, call=call, column=column))
    made_by(tree, name, column, value)
    if not is_date_partition(column) or isinstance(value, Column):
        return Condition(tree)
    span = span_of(as_date(value, column, call))
    key = _spans_key(column)
    return Condition(tree, spans={key: span}, only_bounds=key)


def equals(column, value):
    """Rows where the column equals the value.

    To find missing values use is_null(column): equals(column, None) is refused, because in
    SQL nothing equals NULL.

    >>> equals(job_runs.status, "FAILED")
    job_runs.status = 'FAILED'
    >>> equals(job_runs.status, "O'Brien")
    job_runs.status = 'O\\'Brien'
    """
    return _compare("equals", "EQ", column, value, lambda day: Span(day, day, frozenset([day])))


def not_equals(column, value):
    """Rows where the column differs from the value; rows where it is NULL drop out.

    Unlike pandas' !=, SQL's <> leaves out rows where the column is NULL. To keep them, use
    any_of(not_equals(column, value), is_null(column)).

    >>> not_equals(job_runs.status, "TEST")
    job_runs.status <> 'TEST'
    """
    return _compare("not_equals", "NEQ", column, value, lambda day: Span())


def at_least(column, value):
    """Rows where the column is greater than or equal to the value (>=).

    >>> at_least(job_runs.duration_mins, 30)
    job_runs.duration_mins >= 30
    """
    return _compare("at_least", "GTE", column, value, lambda day: Span(low=day))


def at_most(column, value):
    """Rows where the column is less than or equal to the value (<=).

    >>> at_most(job_runs.duration_mins, 30)
    job_runs.duration_mins <= 30
    """
    return _compare("at_most", "LTE", column, value, lambda day: Span(high=day))


def more_than(column, value):
    """Rows where the column is strictly greater than the value (>).

    >>> more_than(job_runs.duration_mins, 30)
    job_runs.duration_mins > 30
    """
    return _compare("more_than", "GT", column, value,
                    lambda day: Span(low=day + datetime.timedelta(days=1)))


def less_than(column, value):
    """Rows where the column is strictly less than the value (<).

    >>> less_than(job_runs.duration_mins, 30)
    job_runs.duration_mins < 30
    """
    return _compare("less_than", "LT", column, value,
                    lambda day: Span(high=day - datetime.timedelta(days=1)))


def between(column, low, high):
    """Rows where the column is from low to high, both ends included.

    On a Date partition this is the usual way to bound the days a Statement reads.

    >>> between(job_runs.dt, "2026-09-01", "2026-09-24")
    job_runs.dt BETWEEN '2026-09-01' AND '2026-09-24'
    """
    call = f"between({python_text(column)}, ...)"
    column = _need_column(column, call)
    if low is None or high is None:
        guard_none_in_condition(f"between({python_text(column)}, {low!r}, {high!r})")
    tree = Node(
        "Between",
        this=column._tree.copy(),
        low=literal(low, call=call, column=column, position="the low end"),
        high=literal(high, call=call, column=column, position="the high end"),
    )
    made_by(tree, "between", column, low, high)
    if not is_date_partition(column) or isinstance(low, Column) or isinstance(high, Column):
        return Condition(tree)
    first, last = as_date(low, column, call), as_date(high, column, call)
    if first > last:
        raise ValueError(
            four_part_message(
                what=f"between({python_text(column)}, {low!r}, {high!r}) starts after it ends.",
                why="No day is both on or after the first and on or before the second, so "
                "this would match nothing.",
                fix="Put the earlier day first.",
                opt_out=None,
            )
        )
    key = _spans_key(column)
    return Condition(tree, spans={key: Span(first, last)}, only_bounds=key)


def last_n_days(column, n):
    """Rows from the n days before today; today itself isn't included.

    The dates are worked out when the condition is made, and written into the Hive, so the
    days a Statement reads are there to see. last_n_days(job_runs.dt, 1) is yesterday.

    >>> last_n_days(job_runs.dt, 7)
    job_runs.dt BETWEEN '2026-09-18' AND '2026-09-24'
    """
    call = f"last_n_days({python_text(column)}, {n!r})"
    column = _need_column(column, call)
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError(
            four_part_message(
                what=f"{call}: n must be a whole number of days, 1 or more.",
                why="It counts back that many days from yesterday.",
                fix="Use a number such as last_n_days(job_runs.dt, 7).",
                opt_out=None,
            )
        )
    last = today() - datetime.timedelta(days=1)
    first = today() - datetime.timedelta(days=n)
    if type_family(column._type) == "timestamp":
        tree = combined("And", [
            Node("GTE", this=column._tree.copy(), expression=literal(first, call=call)),
            Node("LT", this=column._tree.copy(), expression=literal(today(), call=call)),
        ])
    elif first == last:
        tree = Node("EQ", this=column._tree.copy(), expression=literal(first, call=call,
                                                                         column=column))
    else:
        tree = Node(
            "Between",
            this=column._tree.copy(),
            low=literal(first, call=call, column=column),
            high=literal(last, call=call, column=column),
        )
    made_by(tree, "last_n_days", column, n)
    if not is_date_partition(column):
        return Condition(tree)
    key = _spans_key(column)
    return Condition(tree, spans={key: Span(first, last)}, only_bounds=key)


def _values(values, call: str) -> list:
    if isinstance(values, (str, bytes, dict)) or not hasattr(values, "__iter__"):
        raise TypeError(
            four_part_message(
                what=f"{call} was given {values!r} where a list of values goes.",
                why="It tests the column against each value in a list.",
                fix='Pass a list, such as is_in(job_runs.status, ["FAILED", "TEST"]).',
                opt_out=None,
            )
        )
    if isinstance(values, (set, frozenset)):
        values = sorted(values, key=repr)
    values = list(values)
    if not values:
        raise ValueError(
            four_part_message(
                what=f"{call} was given an empty list.",
                why="No value is in an empty list, so this would match nothing.",
                fix="Check the list before building the Statement.",
                opt_out=None,
            )
        )
    return values


def _in(name: str, column, values, negated: bool) -> Condition:
    call = f"{name}({python_text(column)}, ...)"
    column = _need_column(column, call)
    values = _values(values, call)
    if any(value is None for value in values):
        guard_none_in_condition(f"{name}({python_text(column)}, [..., None, ...])")
    items = [
        literal(value, call=call, column=column, position=f"item {number}")
        for number, value in enumerate(values, start=1)
    ]
    tree = Node("In", this=column._tree.copy(), expressions=items)
    if negated:
        return Condition(made_by(Node("Not", this=tree), name, column, values))
    made_by(tree, name, column, values)
    if not is_date_partition(column):
        return Condition(tree)
    days = frozenset(as_date(value, column, call) for value in values)
    span = Span(min(days), max(days), days)
    key = _spans_key(column)
    return Condition(tree, spans={key: span}, only_bounds=key)


def is_in(column, values):
    """Rows where the column is one of the values in a list.

    >>> is_in(job_runs.status, ["FAILED", "TEST"])
    job_runs.status IN ('FAILED', 'TEST')
    """
    return _in("is_in", column, values, negated=False)


def is_not_in(column, values):
    """Rows where the column is none of the values; rows where it is NULL drop out.

    A None in the list is refused: in SQL it would make the whole test match nothing.

    >>> is_not_in(job_runs.status, ["TEST"])
    NOT job_runs.status IN ('TEST')
    """
    return _in("is_not_in", column, values, negated=True)


def is_null(column):
    """Rows where the column has no value (NULL).

    >>> is_null(job_runs.status)
    job_runs.status IS NULL
    """
    column = _need_column(column, "is_null(...)")
    tree = Node("Is", this=column._tree.copy(), expression=Node("Null"))
    return Condition(made_by(tree, "is_null", column), tests_for_null=True)


def is_not_null(column):
    """Rows where the column has a value (is not NULL).

    >>> is_not_null(job_runs.status)
    NOT job_runs.status IS NULL
    """
    column = _need_column(column, "is_not_null(...)")
    tree = Node("Not", this=Node("Is", this=column._tree.copy(), expression=Node("Null")))
    return Condition(made_by(tree, "is_not_null", column))


def _like(name: str, column, text: str, pattern) -> Condition:
    call = f"{name}({python_text(column)}, {text!r})"
    column = _need_column(column, call)
    if not isinstance(text, str):
        raise TypeError(
            four_part_message(
                what=f"{call} needs a string to look for.",
                why="It looks for text inside a text column.",
                fix=f'Pass a string, such as {name}(jobs.job_name, "sync").',
                opt_out=None,
            )
        )
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    tree = Node("Like", this=column._tree.copy(),
                expression=literal(pattern(escaped), call=call))
    return Condition(made_by(tree, name, column, text))


def contains(column, text):
    """Rows where the column contains your text, a % or _ in it matched as % or _.

    It writes SQL's LIKE, which reads % as any run of characters and _ as any one character.
    So the Hive puts a backslash before each % or _ of your own text, for it to match just
    itself, and writes that backslash as \\\\ inside the quotes.

    >>> contains(jobs.job_name, "sync")
    jobs.job_name LIKE '%sync%'
    >>> contains(jobs.job_name, "a_b")
    jobs.job_name LIKE '%a\\\\_b%'
    """
    return _like("contains", column, text, lambda escaped: f"%{escaped}%")


def starts_with(column, text):
    """Rows where the column starts with your text, a % or _ in it matched as % or _.

    As in contains(...), a backslash before your own % or _ makes LIKE match it as itself.

    >>> starts_with(jobs.job_name, "invoice_")
    jobs.job_name LIKE 'invoice\\\\_%'
    """
    return _like("starts_with", column, text, lambda escaped: f"{escaped}%")


def _conditions(items, call: str) -> list[Condition]:
    found = []
    for item in items:
        if isinstance(item, (list, tuple)):
            found.extend(_conditions(item, call))
        elif isinstance(item, Condition):
            found.append(item)
        else:
            refuse_what_the_other_edition_made(item, call)
            raise TypeError(
                four_part_message(
                    what=f"{call} was given {item!r}, which isn't a condition.",
                    why="It combines conditions made by functions such as equals(...).",
                    fix="Pass conditions, such as equals(job_runs.status, \"FAILED\").",
                    opt_out=None,
                )
            )
    if not found:
        raise TypeError(
            four_part_message(
                what=f"{call} was given no conditions.",
                why="It combines one or more conditions.",
                fix="Pass at least one condition.",
                opt_out=None,
            )
        )
    return found


def any_of(*conditions):
    """Rows where at least one of the conditions holds (OR); takes a list too.

    >>> any_of(equals(job_runs.status, "FAILED"), is_null(job_runs.status))
    job_runs.status = 'FAILED' OR job_runs.status IS NULL
    """
    found = _conditions(conditions, "any_of(...)")
    spans = dict(found[0]._spans)
    for condition in found[1:]:
        spans = {key: days_in_either(span, condition._spans[key])
                 for key, span in spans.items() if key in condition._spans}
    tree = combined("Or", [c._tree.copy() for c in found])
    return Condition(made_by(tree, "any_of", *found), spans=spans)


def all_of(*conditions):
    """Rows where every one of the conditions holds (AND), for use inside any_of.

    WHERE(...) already joins its conditions with AND, so all_of is needed only inside
    any_of(...) or in JOIN's ON=.

    >>> any_of(all_of(equals(jobs.team, "finance"), equals(jobs.region, "PAR")),
    ...        equals(jobs.team, "data"))
    (jobs.team = 'finance' AND jobs.region = 'PAR') OR jobs.team = 'data'
    """
    found = _conditions(conditions, "all_of(...)")
    tree = made_by(combined("And", [c._tree.copy() for c in found]), "all_of", *found)
    return Condition(tree, spans=combined_spans(found))


def combined_spans(conditions: list[Condition]) -> dict:
    """The Date partition bounds of several conditions joined with AND."""
    spans = {}
    for condition in conditions:
        for key, span in condition._spans.items():
            spans[key] = days_in_both(spans[key], span) if key in spans else span
    return spans


__all__ = [
    "equals",
    "not_equals",
    "is_null",
    "is_not_null",
    "at_least",
    "at_most",
    "more_than",
    "less_than",
    "between",
    "last_n_days",
    "is_in",
    "is_not_in",
    "contains",
    "starts_with",
    "any_of",
    "all_of",
]
