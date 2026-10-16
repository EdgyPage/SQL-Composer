"""Windows: a calculation over the rows around each row, such as a running total or a rank.

window(...) names the rows each row's value is worked out over: the rows that share its
PARTITION_BY values, in ORDER_BY's order, and, with rows=, only those near it. Pass it as over=
to sum_of, average_of, count_rows, min_of or max_of, or to the functions here, which always take
one. Each row keeps its own row, so a Window changes no row count, and a Statement's Key stays
what it was. Hive can't test a Window's result in the Statement that works it out: work it out
in a derived(...) table, and test it in the Statement that reads it.
"""

from __future__ import annotations

from .calculations import Ordering, _need_column, ordered
from .refusals import refuse
from .tables import Column, made_by, python_text
from .trees import Node, has_window, is_aggregate, number

TOOLBOX_VERSION = "4.1"

# What a function needs of its window: ORDER_BY, and whether it takes rows=.
TOTAL = "a total"  # sum_of, average_of, count_rows, min_of, max_of: rows= with ORDER_BY
_PLACE = "a place"  # row_number, rank, dense_rank, ntile, lag, lead: ORDER_BY, no rows=
_VALUE = "a value"  # first_value, last_value: ORDER_BY; rows= left out is the whole group


class Window:
    """The rows a calculation looks across for each row. Made by window(...), passed as over=."""

    def __init__(self, partition_by: list[Node], order: Node | None, rows, call: str):
        self._partition_by = partition_by  # each PARTITION_BY column's tree
        self._order = order  # an Order of ORDER_BY's Ordered trees, or None
        self._rows = rows  # (start, end), or None
        self._call = call  # how it was written, as window(PARTITION_BY=..., ...)

    def __repr__(self) -> str:
        return self._call


def _listed(items) -> list:
    if items is None:
        return []
    return list(items) if isinstance(items, (list, tuple)) else [items]


def _no_name(call: str, keyword: str, given) -> None:
    """Refuse a name given in SELECT where a window needs the column itself."""
    refuse(
        what=f"{call} was given {keyword}={given!r}.",
        why="Inside a Window, Hive can't see the names given in SELECT.",
        fix=f"Pass the columns themselves, such as {keyword}="
        + ("job_runs.job_id." if keyword == "PARTITION_BY" else "descending(job_runs.run_id)."),
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


def _checked_rows(rows):
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
                "itself, positive after it. None is every row that way.",
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


def window(PARTITION_BY=None, ORDER_BY=None, rows=None):
    """The rows a calculation looks across for each row, passed to it as over=.

    - PARTITION_BY= makes the groups: each row looks only at the rows sharing its values. The
      word is SQL's, and has nothing to do with a table's Date partition. Left out, every row
      is in one group.
    - ORDER_BY= puts each group's rows in order, with descending(...) for largest first.
    - rows=(start, end) keeps only the rows near each one, counted from the row itself:
      negative before it, 0 the row itself, positive after it, and None every row that way.
      rows=(-6, 0) is the row and the 6 before it; rows=(None, 0) every row up to it. It needs
      ORDER_BY. Left out, each row looks across its whole group.

    PARTITION_BY and ORDER_BY take columns or a list of them, never a name given in SELECT.
    Each row keeps its own row, so a Window changes no row count. Hive can't test a Window's
    result in WHERE or HAVING of the Statement that works it out: work it out in a
    derived(...) table, and test it in the Statement that reads it.

    by_day refuses a Statement whose Window looks across days, such as a lag(...) ordered by
    the day: split by day, it would see one day at a time. To write one day of a Saved table
    from it, read the earlier days it needs in a derived(...) table, and keep the day written
    in the Statement that writes, with equals(...) of the day the Derived table passes on;
    run one such Statement for each day.

    Here, each run's minutes beside its job's total for the day, and the job's runs so far:

    >>> by_job = window(PARTITION_BY=job_runs.job_id)
    >>> so_far = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id,
    ...                 rows=(None, 0))
    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id, job_runs.duration_mins,
    ...            AS(sum_of(job_runs.duration_mins, over=by_job), "job_minutes"),
    ...            AS(count_rows(over=so_far), "runs_so_far")),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24")),
    ... )))
    SELECT
      job_runs.run_id,
      job_runs.duration_mins,
      SUM(job_runs.duration_mins) OVER (PARTITION BY job_runs.job_id) AS job_minutes,
      COUNT(*) OVER (
        PARTITION BY job_runs.job_id
        ORDER BY job_runs.run_id ASC
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) AS runs_so_far
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24'
    """
    return _made_window(PARTITION_BY, ORDER_BY, rows, "window(...)")


def _columns_of(items, keyword: str, call: str) -> list:
    """PARTITION_BY's or ORDER_BY's items, once each is a column, or descending(column)."""
    found = _listed(items)
    for item in found:
        sorted_down = isinstance(item, Ordering) and keyword == "ORDER_BY"
        target = item._target if sorted_down else item
        if isinstance(target, str):
            _no_name(call, keyword, items)
        no_window_inside(call, _need_column(target, call))
    return found


def _made_window(PARTITION_BY, ORDER_BY, rows, call: str) -> Window:
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


def windowed(tree: Node, over, call: str, needs: str) -> Node:
    """`tree` worked out over the window `over`, once the window suits it: `needs` says what
    the function needs of its window (TOTAL, _PLACE or _VALUE)."""
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
            why="It would be unclear which rows it works over: Hive would take the rows up to "
            "each row and every row tied with it in ORDER_BY's order, which is seldom what is "
            "meant.",
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
    if needs == _PLACE and rows is not None:
        refuse(
            what=f"{call} takes no rows= in its Window.",
            why="It works by each row's place in ORDER_BY's order among all its group's rows, "
            "so Hive refuses rows= on it.",
            fix="Leave rows= out of its Window.",
            error=ValueError,
        )
    if needs == _VALUE and rows is None:
        rows = (None, None)  # the whole group, which Hive would otherwise end at the row
    return Node("Window", this=tree, partition_by=[p.copy() for p in over._partition_by],
                order=None if over._order is None else over._order.copy(), rows=rows)


def _window_call(name: str, args: list[Node], over, call: str, needs: str) -> Node:
    return windowed(Node("WindowCall", name=name, args=args), over, call, needs)


def _whole_number(value, given: str, call: str, what_it_is: str, example: str) -> None:
    """Refuse `value` unless it is a whole number, 1 or more."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        refuse(
            what=f"{call} was given {given}, which isn't a whole number, 1 or more.",
            why=f"It is {what_it_is}.",
            fix=f"Write it like {example}.",
            error=ValueError,
        )


def row_number(*, PARTITION_BY=None, ORDER_BY=None, over=None):
    """Number the rows of each group from 1, in ORDER_BY's order.

    Pass over=window(PARTITION_BY=..., ORDER_BY=...), or, as up to 4.x, PARTITION_BY= and
    ORDER_BY= themselves. Keeping the rows numbered 1 gives the latest row per key; keeping
    those up to N gives the top N per group. Hive can't filter on a row number in the SELECT
    that makes it, so number the rows in a derived(...) table and keep the ones you want in the
    Statement that reads it. Kept at 1, each row is one for each PARTITION_BY value, which a
    write's Key check sees. Here is the latest run of each job:

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
    if over is not None:
        if PARTITION_BY is not None or ORDER_BY is not None:
            refuse(
                what="row_number(...) was given over= and PARTITION_BY= or ORDER_BY= too.",
                why="It takes either over=window(...) or PARTITION_BY= and ORDER_BY=, not both: "
                "the two would say different things.",
                fix="Put PARTITION_BY= and ORDER_BY= inside window(...), and pass only over=.",
                error=ValueError,
            )
        tree = _window_call_row_number(over, call)
        made_by(tree, "row_number", over=over)
        return Column(tree, type="int")
    sorts = _listed(ORDER_BY)
    by_name = [s for s in sorts
               if isinstance(s, str) or (isinstance(s, Ordering) and isinstance(s._target, str))]
    if not sorts or by_name:
        why = "It numbers each group's rows in the order of one or more columns."
        if by_name:
            why = "Inside row_number, Hive can't see the names given in SELECT."
        refuse(
            what=f"row_number(...) was given ORDER_BY={ORDER_BY!r}.",
            why=why,
            fix="Pass the columns themselves, such as "
            "ORDER_BY=descending(job_runs.run_id), or pass over=window(...).",
            error=ValueError,
        )
    tree = _window_call_row_number(_made_window(PARTITION_BY, ORDER_BY, None, call), call)
    made_by(tree, "row_number", PARTITION_BY=PARTITION_BY, ORDER_BY=ORDER_BY)
    return Column(tree, type="int")


def _window_call_row_number(over, call: str) -> Node:
    return windowed(Node("RowNumber"), over, call, _PLACE)


def rank(*, over):
    """Rank each row in its group from 1; rows that tie share a rank.

    Two rows tied in ORDER_BY's order get the same rank, and the next row the rank after both:
    1, 2, 2, 4. dense_rank(...) gives 1, 2, 2, 3 instead, and row_number(...) a number of its
    own to each. Ties mean a rank kept at 1 can keep several rows of a group, so it doesn't
    show a Key; keep row_number(...) at 1 for one row per group.

    >>> longest_first = window(PARTITION_BY=job_runs.job_id,
    ...                        ORDER_BY=descending(job_runs.duration_mins))
    >>> rank(over=longest_first)
    RANK() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.duration_mins DESC)
    """
    tree = _window_call("rank", [], over, "rank(...)", _PLACE)
    return Column(made_by(tree, "rank", over=over), type="int")


def dense_rank(*, over):
    """Rank each row in its group from 1, ties sharing a rank, with no rank left out.

    Two rows tied in ORDER_BY's order get the same rank, and the next row the rank straight
    after: 1, 2, 2, 3, where rank(...) gives 1, 2, 2, 4.

    >>> dense_rank(over=window(PARTITION_BY=job_runs.job_id,
    ...                        ORDER_BY=descending(job_runs.duration_mins)))
    DENSE_RANK() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.duration_mins DESC)
    """
    tree = _window_call("dense_rank", [], over, "dense_rank(...)", _PLACE)
    return Column(made_by(tree, "dense_rank", over=over), type="int")


def ntile(groups, *, over):
    """Split each group's rows, in order, into a number of nearly equal parts.

    ntile(4, over=...) gives each row 1, 2, 3 or 4: its quarter of its group, from the first
    rows in ORDER_BY's order. When the rows don't split evenly, the first parts get one more.

    >>> ntile(4, over=window(ORDER_BY=job_runs.duration_mins))
    NTILE(4) OVER (ORDER BY job_runs.duration_mins ASC)
    """
    call = f"ntile({groups!r}, ...)"
    _whole_number(groups, repr(groups), call, "how many parts each group's rows are split into",
                  "ntile(4, over=window(...))")
    tree = _window_call("ntile", [number(str(groups))], over, call, _PLACE)
    return Column(made_by(tree, "ntile", groups, over=over), type="int")


def _shifted(name: str, column, over, by: int, keyword: str, words: str) -> Column:
    """lag's or lead's Column: the value `by` rows before or after each row in its group."""
    call = f"{name}({python_text(column)}, ...)"
    column = _need_column(column, call)
    no_window_inside(call, column)
    _whole_number(by, f"{keyword}={by!r}", call, f"how many rows {words} to look",
                  f"{keyword}=2")
    tree = _window_call(name, [column._tree.copy(), number(str(by))], over, call, _PLACE)
    made_by(tree, name, column, over=over, **{keyword: by if by != 1 else None})
    return Column(tree, type=column._type, adds_up=column._adds_up,
                  not_adding_up_because=column._not_adding_up_because)


def lag(column, *, over, back=1):
    """The column's value on the row before each row in its group, in ORDER_BY's order.

    back=2 looks 2 rows back. The first row of each group has no row before it, so it gets
    NULL; fill_null(lag(...), 0) puts a value in its place. Here, each run's minutes beside
    those of the job's run before it:

    >>> lag(job_runs.duration_mins, over=window(PARTITION_BY=job_runs.job_id,
    ...                                         ORDER_BY=job_runs.run_id))
    LAG(job_runs.duration_mins, 1) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC)
    """
    return _shifted("lag", column, over, back, "back", "back")


def lead(column, *, over, ahead=1):
    """The column's value on the row after each row in its group, in ORDER_BY's order.

    ahead=2 looks 2 rows ahead. The last row of each group has no row after it, so it gets
    NULL.

    >>> lead(job_runs.status, over=window(PARTITION_BY=job_runs.job_id,
    ...                                   ORDER_BY=job_runs.run_id))
    LEAD(job_runs.status, 1) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC)
    """
    return _shifted("lead", column, over, ahead, "ahead", "ahead")


def _end_value(name: str, column, over) -> Column:
    call = f"{name}({python_text(column)}, ...)"
    column = _need_column(column, call)
    no_window_inside(call, column)
    tree = _window_call(name, [column._tree.copy()], over, call, _VALUE)
    made_by(tree, name, column, over=over)
    return Column(tree, type=column._type, adds_up=column._adds_up,
                  not_adding_up_because=column._not_adding_up_because)


def first_value(column, *, over):
    """The column's value on the first row of each row's group, in ORDER_BY's order.

    With no rows= in the Window, it is the whole group's first row, which the Hive spells out
    as ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING.

    >>> first_value(job_runs.status, over=window(PARTITION_BY=job_runs.job_id,
    ...                                          ORDER_BY=job_runs.run_id))
    FIRST_VALUE(job_runs.status) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
    """
    return _end_value("first_value", column, over)


def last_value(column, *, over):
    """The column's value on the last row of each row's group, in ORDER_BY's order.

    With no rows= in the Window, it is the whole group's last row, which the Hive spells out
    as ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING: left to itself, Hive would
    stop at each row, and give each row its own value.

    >>> last_value(job_runs.status, over=window(PARTITION_BY=job_runs.job_id,
    ...                                         ORDER_BY=job_runs.run_id))
    LAST_VALUE(job_runs.status) OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id ASC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
    """
    return _end_value("last_value", column, over)


def _numbers_rows(tree: Node) -> bool:
    return any(window.parts["this"].kind == "RowNumber" for window in tree.find_all("Window"))


def refuse_a_window_in(place: str, part) -> None:
    """Refuse a window in WHERE, HAVING, ON= or GROUP_BY of the Statement that works it out."""
    if _numbers_rows(part._tree):
        made, worked_out, fix_it = "numbers rows", "Rows are numbered", "Number the rows"
        use, shows = "the number", "help(row_number)"
    else:
        made, worked_out = "looks across rows through a Window", "Windows are worked out"
        fix_it, use, shows = "Work it out", "it", "help(window)"
    refuse(
        what=f"{place} has {part!r}, which {made}.",
        why=f"{worked_out} last, after the rows are picked and grouped, so Hive can't use "
        f"{use} in {place} of the SELECT that makes it.",
        fix=f"{fix_it} in a derived(...) table, then use {use} in the Statement that reads "
        f"it; {shows} shows how.",
        error=ValueError,
    )


def ungrouped_in_window(tree: Node) -> list[Node]:
    """What of a window's tree a Statement with GROUP_BY must group: its PARTITION_BY and
    ORDER_BY columns and, for a count or a sum over the window, the column inside it, which
    the window reads from the rows GROUP_BY made."""
    this = tree.parts["this"]
    inside = list(this.children()) if is_aggregate(this) else [this]
    return [*inside, *(child for child in tree.children() if child is not this)]


def call_of(window_tree: Node) -> str:
    """The call that made a window's calculation, cut short, such as lag(...)."""
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
