"""Windows: a calculation over the rows around each row, such as a running total or a rank.

window(...) names the rows each row's value is worked out over: the rows that share its
PARTITION_BY values, in ORDER_BY's order, and, with rows=, only those near it. Pass it as over=
to sum_of, average_of, count_rows, min_of or max_of, or to the functions here, which always take
one. Each row keeps its own row, so a Window changes no row count, and a Statement's Key stays
what it was. Hive can't test a Window's result in the Statement that works it out: work it out
in a derived(...) table, and test it in the Statement that reads it.
"""

from __future__ import annotations

from typing import NoReturn

from .calculations import Ordering, need_column, ordered
from .conditions import Condition
from .refusals import refuse
from .tables import Column, made_by, python_text
from .trees import Node, has_window, is_aggregate, number, numbers_rows

TOOLBOX_VERSION = "7.1"

# What a function needs of its window: ORDER_BY, and whether it takes rows=.
TOTAL = "a total"  # sum_of, average_of, count_rows, min_of, max_of: rows= with ORDER_BY
PLACE = "a place"  # row_number, rank, dense_rank, ntile, lag, lead: ORDER_BY, no rows=
VALUE = "a value"  # first_value, last_value: ORDER_BY; rows= left out is the whole group


class Window:
    """The rows a calculation looks across for each row, made by window(...) for over=.

    >>> window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt)
    window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt)

    Make one with window(...), never Window(). Write the name in a type hint, to say that a
    function of yours gives back a Window:

    >>> def each_jobs_runs_in_order() -> Window:
    ...     return window(PARTITION_BY=[job_runs.job_id], ORDER_BY=[job_runs.dt])
    >>> each_jobs_runs_in_order()
    window(PARTITION_BY=[job_runs.job_id], ORDER_BY=[job_runs.dt])
    """

    def __init__(self, partition_by: list[Node], order: Node | None,
                 rows: tuple[int | None, int | None] | None, call: str) -> None:
        self._partition_by = partition_by  # each PARTITION_BY column's tree
        self._order = order  # an Order of ORDER_BY's Ordered trees, or None
        self._rows = rows  # (start, end), or None
        self._call = call  # how it was written, as window(PARTITION_BY=..., ...)

    def __repr__(self) -> str:
        return self._call


def _listed(items: object) -> list[object]:
    if items is None:
        return []
    return list(items) if isinstance(items, (list, tuple)) else [items]


def _no_name(call: str, keyword: str, given: object) -> NoReturn:
    """Refuse text where a Window needs a column, such as the name given in SELECT."""
    example = "job_runs.job_id" if keyword == "PARTITION_BY" else "descending(job_runs.run_id)"
    refuse(
        what=f"{call} was given {keyword}={given!r}.",
        why=f"{keyword}= takes columns, such as {example}, not text: inside {call}, Hive "
        "can't see the names given in SELECT.",
        fix=f"Pass the columns themselves, such as {keyword}={example}.",
        error=ValueError,
    )


def no_window_inside(call: str, column: Column) -> None:
    """Refuse a column that already looks across rows through a window, inside another."""
    if has_window(column._tree):
        refuse(
            what=f"{call} has {column!r} inside it, which already looks across rows.",
            why="Hive can't work out a Window inside a Window.",
            fix="Work it out as a named column in a derived(...) table, then use that column "
            "in the Statement that reads it; help(derived) shows how.",
            error=ValueError,
        )


def _checked_rows(rows: object) -> tuple[int | None, int | None]:
    """rows= as (start, end), once checked: whole numbers of rows, or None, start first."""
    if not isinstance(rows, (tuple, list)) or len(rows) != 2:
        refuse(
            what=f"window(..., rows={rows!r}): rows= is a pair of numbers.",
            why="It says where the rows each row looks across start and end, counted from "
            "the row itself: (-6, 0) is the 6 rows before it and the row itself.",
            fix="Write it like rows=(-6, 0), or rows=(None, 0) for every row up to it.",
            error=ValueError,
        )
    start, end = rows
    for end_of_it in rows:
        if end_of_it is not None and (isinstance(end_of_it, bool)
                                      or not isinstance(end_of_it, int)):
            refuse(
                what=f"window(..., rows={tuple(rows)!r}): rows= takes whole numbers of rows, "
                "or None.",
                why="Each end counts rows from the row itself: negative before it, 0 the row "
                "itself, positive after it. None means no limit: every row before it as the "
                "start, every row after it as the end.",
                fix="Write it like rows=(-6, 0) or rows=(None, 0).",
                error=ValueError,
            )
    if start is not None and end is not None and start > end:
        refuse(
            what=f"window(..., rows={tuple(rows)!r}) starts after it ends.",
            why="The first number is where the rows start and the second where they end, so "
            "the first comes before the second.",
            fix=f"Swap them: rows=({end}, {start}).",
            error=ValueError,
        )
    return (start, end)


def window(PARTITION_BY: Column | list[Column] | None = None,
           ORDER_BY: Column | Ordering | list[Column | Ordering] | None = None,
           rows: tuple[int | None, int | None] | None = None) -> Window:
    """The rows a calculation looks across for each row, passed to it as over=.

    >>> sum_of(job_runs.duration_mins, over=window(PARTITION_BY=job_runs.job_id))
    SUM(job_runs.duration_mins) OVER (PARTITION BY job_runs.job_id)

    - PARTITION_BY= makes the groups: each row looks only at the rows sharing its values. The
      word is SQL's, and has nothing to do with the Partitions a table is stored in. Left out,
      every row is in one group.
    - ORDER_BY= puts each group's rows in order, with descending(...) for largest first.
    - rows=(start, end) keeps only the rows near each one, counted from the row itself:
      negative before it, 0 the row itself, positive after it. None means no limit: every row
      before it as the start, every row after it as the end. rows=(-6, 0) is the row and the 6
      before it; rows=(None, 0) every row up to it. It needs ORDER_BY. Left out, each row
      looks across its whole group.

    PARTITION_BY and ORDER_BY take columns or a list of them, never a name given in SELECT.
    Each row keeps its own row, so a Window changes no row count, and needs no GROUP_BY. Hive
    can't test a Window's result in WHERE or HAVING of the Statement that works it out: work
    it out in a derived(...) table, and test it in the Statement that reads it. A Window over
    the totals of a GROUP_BY, such as each job's share of the day, goes the same way: total
    in a derived(...) table, and the Window in the Statement that reads it.

    Here, each run's minutes beside its job's total for the day, and the day's minutes so far,
    run by run:

    >>> by_job = window(PARTITION_BY=job_runs.job_id)
    >>> so_far = window(ORDER_BY=job_runs.run_id, rows=(None, 0))
    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id, job_runs.duration_mins,
    ...            AS(sum_of(job_runs.duration_mins, over=by_job), "job_minutes"),
    ...            AS(sum_of(job_runs.duration_mins, over=so_far), "minutes_so_far")),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24")),
    ... )))
    SELECT
      job_runs.run_id,
      job_runs.duration_mins,
      SUM(job_runs.duration_mins) OVER (PARTITION BY job_runs.job_id) AS job_minutes,
      SUM(job_runs.duration_mins) OVER (ORDER BY job_runs.run_id ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS minutes_so_far
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24'

    A Window sees only the rows its Statement reads. To write each run of one day beside its
    job's run before, which may be on the day before, read both days in a derived(...) table
    that works out the Window and keeps the day column, then keep only the day to write in the
    Statement that writes, with WHERE(equals(the_derived_table.dt, ...)). Here, each run of
    2026-09-24 beside the minutes of its job's run before, which may be on 2026-09-23, written
    into the Partition of its own day:

    >>> runs_before = Table("mart.runs_before", partitioned_by=["dt"], key=["run_id"],
    ...     columns={"run_id": "bigint", "minutes_before": "int", "dt": "string"},
    ...     location="/data/your_team/mart.db/runs_before")
    >>> two_days = derived("two_days", statement(
    ...     SELECT(job_runs.run_id, job_runs.dt,
    ...            AS(lag(job_runs.duration_mins, over=window(
    ...                PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id)),
    ...               "minutes_before")),
    ...     FROM(job_runs),
    ...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    ... ))
    >>> print(to_hive(statement(
    ...     INSERT_OVERWRITE(runs_before),
    ...     SELECT(two_days.run_id, two_days.minutes_before, two_days.dt),
    ...     FROM(two_days),
    ...     WHERE(equals(two_days.dt, "2026-09-24")),
    ... )))
    WITH two_days AS (
      SELECT
        job_runs.run_id,
        job_runs.dt,
        LAG(job_runs.duration_mins, 1) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC) AS minutes_before
      FROM ops.job_runs AS job_runs
      WHERE
        job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    )
    INSERT OVERWRITE TABLE mart.runs_before PARTITION(dt)
    SELECT
      two_days.run_id,
      two_days.minutes_before,
      two_days.dt
    FROM two_days
    WHERE
      two_days.dt = '2026-09-24'
    """
    return _made_window(PARTITION_BY, ORDER_BY, rows, "window(...)")


def _columns_of(items: object, keyword: str, call: str) -> list[Column | Ordering]:
    """PARTITION_BY's or ORDER_BY's items, once each is a column, or descending(column)."""
    found = _listed(items)
    for item in found:
        sorted_down = isinstance(item, Ordering) and keyword == "ORDER_BY"
        target = item._target if sorted_down else item
        if isinstance(target, str):
            _no_name(call, keyword, items)
        no_window_inside(call, need_column(target, call))
    return found


def _made_window(PARTITION_BY: object, ORDER_BY: object, rows: object, call: str) -> Window:
    groups = [column._tree.copy() for column in _columns_of(PARTITION_BY, "PARTITION_BY", call)]
    sorts = _columns_of(ORDER_BY, "ORDER_BY", call)
    order = Node("Order", expressions=[ordered(item, call) for item in sorts]) if sorts else None
    if rows is not None:
        rows = _checked_rows(rows)
        if order is None:
            refuse(
                what=f"window(..., rows={rows!r}): rows= needs ORDER_BY.",
                why="rows= counts the rows before and after each row, and a group's rows have "
                "no before or after until ORDER_BY puts them in order.",
                fix="Add ORDER_BY=..., such as ORDER_BY=job_runs.run_id.",
                error=ValueError,
            )
    written = [f"{name}={python_text(value)}" for name, value in
               (("PARTITION_BY", PARTITION_BY), ("ORDER_BY", ORDER_BY)) if value is not None]
    written += [f"rows={rows!r}"] if rows is not None else []
    return Window(groups, order, rows, f"window({', '.join(written)})")


def windowed(tree: Node, over: object, call: str, needs: str) -> Node:
    """`tree` worked out over the window `over`, once the window suits it: `needs` says what
    the function needs of its window (TOTAL, PLACE or VALUE)."""
    if not isinstance(over, Window):
        refuse(
            what=f"{call} was given over={over!r}, which isn't a Window.",
            why="over= takes window(...), which names the rows each row's value is worked out "
            "over.",
            fix="Pass over=window(PARTITION_BY=..., ORDER_BY=...).",
            given=over, call=call,
        )
    rows = over._rows
    if needs == TOTAL and over._order is not None and rows is None:
        refuse(
            what=f"{call} is given a Window with ORDER_BY and no rows=.",
            why="Hive would work it out over the rows up to each row and every row tied with "
            "it in ORDER_BY's order, which is seldom what is meant, so say which rows.",
            fix="Give rows=(None, 0) for a running total of every row up to each one, or "
            "rows=(-6, 0) for each row and the 6 before it; leave ORDER_BY out for the whole "
            "group's.",
            error=ValueError,
        )
    if needs != TOTAL and over._order is None:
        refuse(
            what=f"{call} needs ORDER_BY in its Window.",
            why="Which row comes first, or before another, depends on the order, and without "
            "ORDER_BY the warehouse picks one that can change from one run to the next.",
            fix="Add ORDER_BY=..., such as window(PARTITION_BY=job_runs.job_id, "
            "ORDER_BY=job_runs.run_id).",
            error=ValueError,
        )
    if needs == PLACE and rows is not None:
        refuse(
            what=f"{call} takes no rows= in its Window.",
            why="It works by each row's place in ORDER_BY's order among all its group's rows, "
            "so Hive refuses rows= on it.",
            fix="Leave rows= out of its Window.",
            error=ValueError,
        )
    if needs == VALUE and rows is None:
        rows = (None, None)  # the whole group, which Hive would otherwise end at the row
    return Node("Window", this=tree, partition_by=[p.copy() for p in over._partition_by],
                order=None if over._order is None else over._order.copy(), rows=rows)


def _whole_number(value: object, given: str, call: str, what_it_is: str, example: str) -> None:
    """Refuse `value` unless it is a whole number, 1 or more."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        refuse(
            what=f"{call} was given {given}, which isn't a whole number, 1 or more.",
            why=f"It is {what_it_is}.",
            fix=f"Write it like {example}.",
            error=ValueError,
        )


def _of_column(tree: Node, column: Column) -> Column:
    """A calculation over a Window of one column's values, typed and adding up as it does."""
    return Column(tree, type=column._type, adds_up=column._adds_up,
                  not_adding_up_because=column._not_adding_up_because)


def row_number(*, PARTITION_BY: Column | list[Column] | None = None,
               ORDER_BY: Column | Ordering | list[Column | Ordering] | None = None,
               over: Window | None = None) -> Column:
    """Number the rows of each group from 1, in ORDER_BY's order.

    >>> row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id))
    ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id DESC)

    Give it PARTITION_BY= and ORDER_BY=, or over=window(...) as lag(...) and rank(...) take
    theirs: both write the same Hive. Keeping the rows numbered 1 gives the latest row per key;
    keeping those up to N gives the top N per group. Hive can't filter on a row number in the
    SELECT that makes it, so number the rows in a derived(...) table and keep the ones you want
    in the Statement that reads it. Kept at 1, it leaves one row for each PARTITION_BY value,
    and a write's Key check knows that. Here is the latest run of each job:

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

    The same numbering, over a window(...):

    >>> row_number(over=window(PARTITION_BY=job_runs.job_id,
    ...                        ORDER_BY=descending(job_runs.run_id)))
    ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id DESC)
    """
    call = "row_number(...)"
    if over is not None:
        if PARTITION_BY is not None or ORDER_BY is not None:
            refuse(
                what="row_number(...) was given over= and PARTITION_BY= or ORDER_BY= too.",
                why="It takes either over=window(...) or PARTITION_BY= and ORDER_BY=, not both: "
                "the two would say different things.",
                fix="Put PARTITION_BY= and ORDER_BY= inside window(...), and pass only over=.",
                error=ValueError,
            )
        tree = windowed(Node("RowNumber"), over, call, PLACE)
        return Column(made_by(tree, "row_number", over=over), type="int")
    if not _listed(ORDER_BY):
        refuse(
            what=f"row_number(...) was given ORDER_BY={ORDER_BY!r}.",
            why="It numbers each group's rows in the order of one or more columns.",
            fix="Pass the columns themselves, such as ORDER_BY=descending(job_runs.run_id), or "
            "pass over=window(...).",
            error=ValueError,
        )
    tree = windowed(Node("RowNumber"), _made_window(PARTITION_BY, ORDER_BY, None, call), call,
                    PLACE)
    made_by(tree, "row_number", PARTITION_BY=PARTITION_BY, ORDER_BY=ORDER_BY)
    return Column(tree, type="int")


def rank(*, over: Window) -> Column:
    """Rank each row in its group from 1; rows that tie share a rank.

    >>> longest_first = window(PARTITION_BY=job_runs.job_id,
    ...                        ORDER_BY=descending(job_runs.duration_mins))
    >>> rank(over=longest_first)
    RANK() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.duration_mins DESC)

    Two rows tied in ORDER_BY's order get the same rank, and the next row the rank after both:
    1, 2, 2, 4. dense_rank(...) gives 1, 2, 2, 3 instead, and row_number(...) a number of its
    own to each. Since rows can tie, a rank kept at 1 can't promise one row per group, as a
    Key needs; keep row_number(...) at 1 for that.
    """
    tree = windowed(Node("WindowCall", name="rank", args=[]), over, "rank(...)", PLACE)
    return Column(made_by(tree, "rank", over=over), type="int")


def dense_rank(*, over: Window) -> Column:
    """Rank each row in its group from 1; ties share a rank, and the next follows on.

    >>> dense_rank(over=window(PARTITION_BY=job_runs.job_id,
    ...                        ORDER_BY=descending(job_runs.duration_mins)))
    DENSE_RANK() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.duration_mins DESC)

    Two rows tied in ORDER_BY's order get the same rank, and the next row the rank straight
    after: 1, 2, 2, 3, where rank(...) gives 1, 2, 2, 4.
    """
    tree = windowed(Node("WindowCall", name="dense_rank", args=[]), over, "dense_rank(...)",
                    PLACE)
    return Column(made_by(tree, "dense_rank", over=over), type="int")


def ntile(parts: int, *, over: Window) -> Column:
    """Which of N nearly equal parts of its group each row falls in, 1 to N, in order.

    >>> ntile(4, over=window(ORDER_BY=job_runs.duration_mins))
    NTILE(4) OVER (ORDER BY job_runs.duration_mins ASC)

    ntile(4, over=...) gives each row 1, 2, 3 or 4: its quarter of its group, from the first
    rows in ORDER_BY's order. When the rows don't split evenly, the first parts get one more.
    """
    call = f"ntile({parts!r}, ...)"
    _whole_number(parts, repr(parts), call, "how many parts each group's rows are split into",
                  "ntile(4, over=window(...))")
    tree = windowed(Node("WindowCall", name="ntile", args=[number(str(parts))]), over, call,
                    PLACE)
    return Column(made_by(tree, "ntile", parts, over=over), type="int")


def _shifted(name: str, column: object, over: object, keyword: str, by: object) -> Column:
    """lag's or lead's Column: the value `by` rows back or ahead of each row in its group;
    `keyword` is back or ahead."""
    call = f"{name}({python_text(column)}, ...)"
    column = need_column(column, call)
    no_window_inside(call, column)
    _whole_number(by, f"{keyword}={by!r}", call, f"how many rows {keyword} to look",
                  f"{keyword}=2")
    tree = windowed(Node("WindowCall", name=name, args=[column._tree.copy(), number(str(by))]),
                    over, call, PLACE)
    made_by(tree, name, column, over=over, **{keyword: by if by != 1 else None})
    return _of_column(tree, column)


def lag(column: Column, *, over: Window, back: int = 1) -> Column:
    """The column's value on the row before each row in its group, in ORDER_BY's order.

    >>> lag(job_runs.duration_mins, over=window(PARTITION_BY=job_runs.job_id,
    ...                                         ORDER_BY=job_runs.run_id))
    LAG(job_runs.duration_mins, 1) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC)

    back=2 looks 2 rows back; the Hive writes it after the column, 1 when you give none. The
    first row of each group has no row before it, so it gets NULL; fill_null(lag(...), 0)
    puts a value in its place. The example above gives each run the minutes of its job's run
    before it.
    """
    return _shifted("lag", column, over, "back", back)


def lead(column: Column, *, over: Window, ahead: int = 1) -> Column:
    """The column's value on the row after each row in its group, in ORDER_BY's order.

    >>> lead(job_runs.status, over=window(PARTITION_BY=job_runs.job_id,
    ...                                   ORDER_BY=job_runs.run_id))
    LEAD(job_runs.status, 1) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC)

    ahead=2 looks 2 rows ahead; the Hive writes it after the column, 1 when you give none.
    The last row of each group has no row after it, so it gets NULL.
    """
    return _shifted("lead", column, over, "ahead", ahead)


def _end_value(name: str, column: object, over: object) -> Column:
    call = f"{name}({python_text(column)}, ...)"
    column = need_column(column, call)
    no_window_inside(call, column)
    tree = windowed(Node("WindowCall", name=name, args=[column._tree.copy()]), over, call,
                    VALUE)
    return _of_column(made_by(tree, name, column, over=over), column)


def first_value(column: Column, *, over: Window) -> Column:
    """The column's value on the first row of each row's group, in ORDER_BY's order.

    >>> first_value(job_runs.status, over=window(PARTITION_BY=job_runs.job_id,
    ...                                          ORDER_BY=job_runs.run_id))
    FIRST_VALUE(job_runs.status) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)

    With no rows= in the Window, it is the whole group's first row, which the Hive spells out
    as ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING. With rows=, it is the first
    of those rows.
    """
    return _end_value("first_value", column, over)


def last_value(column: Column, *, over: Window) -> Column:
    """The column's value on the last row of each row's group, in ORDER_BY's order.

    >>> last_value(job_runs.status, over=window(PARTITION_BY=job_runs.job_id,
    ...                                         ORDER_BY=job_runs.run_id))
    LAST_VALUE(job_runs.status) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)

    With no rows= in the Window, it is the whole group's last row, which the Hive spells out
    as ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING: left to itself, Hive would
    stop at each row, and give each row its own value. With rows=, it is the last of those
    rows.
    """
    return _end_value("last_value", column, over)


def refuse_a_window_in(place: str, part: Column | Condition) -> NoReturn:
    """Refuse a Window in WHERE, HAVING, ON= or GROUP_BY of the Statement that works it out."""
    shows = "help(row_number)"
    if numbers_rows(part._tree):
        made, worked_out, fix_it = "numbers rows", "Rows are numbered", "Number the rows"
        use = "the number"
    else:
        made, worked_out = "looks across rows through a Window", "Windows are worked out"
        fix_it, use = "Work it out", "it"
    refuse(
        what=f"{place} has {part!r}, which {made}.",
        why=f"{worked_out} last, after the rows are picked and grouped, so Hive can't use "
        f"{use} in {place} of the SELECT that makes it.",
        fix=f"{fix_it} in a derived(...) table, then use {use} in the Statement that reads "
        f"it; {shows} shows how.",
        error=ValueError,
    )


def ungrouped_in_window(tree: Node) -> list[Node]:
    """What of a Window's tree a Statement with GROUP_BY must group: its PARTITION_BY and
    ORDER_BY columns and, for a count or a sum over the Window, the column inside it, which
    the Window reads from the rows GROUP_BY made."""
    this = tree.parts["this"]
    inside = list(this.children()) if is_aggregate(this) else [this]
    return [*inside, *(child for child in tree.children() if child is not this)]


def call_of(window_tree: Node) -> str:
    """The call that made a Window's calculation, cut short, such as lag(...)."""
    made = window_tree.meta.get("call", "")
    return f"{made.split('(')[0]}(...)" if made else "a Window"


__all__ = [
    "window",
    "row_number",
    "rank",
    "dense_rank",
    "ntile",
    "lag",
    "lead",
    "first_value",
    "last_value",
]
