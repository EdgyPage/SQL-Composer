"""What sqlglot Composer runs on: the sqlglot it needs, and its Example database's executor.

`__init__.py` calls `check_installed()` as soon as it knows the folder is whole, before it
imports any other file. The Example database hands `run_query` a query's Hive and its tables,
and gets back the query's column names and rows. This file imports sqlglot only inside its
functions, so it can be imported to check sqlglot before sqlglot is trusted.
"""

from __future__ import annotations

import contextlib
import re
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, NamedTuple, NoReturn

from . import _four_part_message as four_part_message
from . import _stop as _core_stop
from .shared import in_words

if TYPE_CHECKING:
    # Only for hints: sqlglot is imported inside the functions, once it is checked, and
    # tables.py imports writing.py, which imports sqlglot as it loads.
    from sqlglot import exp
    from sqlglot.executor import table as executed

    from .tables import Table


def _stop_import(what: str, why: str, fix: str) -> NoReturn:
    """Stop the Toolbox's import, named by its own folder, with the four-part message.

    Not refusals.refuse, whose message isn't headed by the folder's name, as every import stop
    is."""
    _core_stop(what, why, fix, folder=__name__.split(".")[0])


# The supported range: 30.19.0, where the Example database's executor first counts
# COUNT(DISTINCT ...) right, up to (not including) 31. CI runs the pin, _NEWEST_TESTED.
_LOWEST = (30, 19, 0)
_BELOW = (31, 0, 0)
_NEWEST_TESTED = (30, 23, 0)


# --- sqlglot --------------------------------------------------------------------------------


def _dotted(numbers: tuple[int, ...]) -> str:
    return ".".join(str(n) for n in numbers)


def _numbers(text: str) -> tuple[int, ...] | None:
    found = re.match(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(n) for n in found.groups()) if found else None


# Where sqlglot is missing or out of the range, the one the Toolbox is tested on.
_INSTALL_TESTED = ("Install the sqlglot sqlglot Composer is tested on from a notebook cell "
                   f'with %pip install "sqlglot=={_dotted(_NEWEST_TESTED)}", then restart '
                   "the kernel.")
_NO_INSTALLING = "If you can't install packages, ask whoever looks after your environment."
# What to install where a sqlglot in the range behaves wrongly: the one the Toolbox is tested
# on, or a newer one in its range.
INSTALL_NEWER = (f'Install a newer sqlglot from a notebook cell with %pip install '
                  f'"sqlglot>={_dotted(_NEWEST_TESTED)},<{_dotted(_BELOW)}", then restart the '
                  f"kernel. {_NO_INSTALLING}")


def check_installed() -> None:
    """Refuse a sqlglot outside the supported range, or one that behaves differently."""
    try:
        import sqlglot
    except ImportError:
        sqlglot = None
    if sqlglot is None:
        _stop_import(
            what="sqlglot Composer needs sqlglot, and this Python can't import it.",
            why="sqlglot Composer writes every Statement as Hive through sqlglot, and reads "
            "the Hive back to check it, so it can't build anything without it.",
            fix=f"{_INSTALL_TESTED} {_NO_INSTALLING}",
        )
    found = getattr(sqlglot, "__version__", "unknown")
    version = _numbers(found)
    if version is None or not _LOWEST <= version < _BELOW:
        _stop_import(
            what=f"sqlglot Composer needs sqlglot {_dotted(_LOWEST)} or newer, below "
            f"{_dotted(_BELOW)}, and this Python has sqlglot {found}.",
            why="sqlglot Composer works only with that range of sqlglot, and is tested on "
            f"{_dotted(_NEWEST_TESTED)}. Another sqlglot can write Hive differently, so a "
            "Statement could come out wrong without anything saying so.",
            fix=f"{_INSTALL_TESTED} {_NO_INSTALLING}",
        )
    problems = _sqlglot_behaviour()
    if problems:
        _stop_import(
            what=f"sqlglot {found} is in the supported range, but behaves differently: "
            + "; ".join(problems) + ". Nothing has been built or sent.",
            why="sqlglot Composer relies on this behaviour to write Hive safely, so a "
            "Statement could come out wrong.",
            fix="Install again the sqlglot version that sqlglot Composer is tested on, from "
            "a notebook cell with %pip install --force-reinstall "
            f'"sqlglot=={_dotted(_NEWEST_TESTED)}", then restart the kernel. '
            f"{_NO_INSTALLING}",
        )
    if version > _NEWEST_TESTED:
        print(f"Note: sqlglot {found} is newer than any version sqlglot Composer was tested on "
              f"({_dotted(_NEWEST_TESTED)}). Its behaviour checks passed.")


def _sqlglot_behaviour() -> list[str]:
    from sqlglot import exp
    from sqlglot.errors import OptimizeError, UnsupportedError
    from sqlglot.optimizer.qualify import qualify

    # Written the way the Toolbox writes, now that the sqlglot it needs is known to be here.
    from .trees import Node
    from .writing import sql_text, to_sqlglot

    def written(tree: exp.Expression) -> str:
        try:
            return sql_text(tree)
        except UnsupportedError:
            return ""  # a sqlglot that can no longer write it behaves differently too

    problems = []
    if written(exp.convert("O'Brien\\")) != "'O\\'Brien\\\\'":
        problems.append("Hive string escaping has changed")
    table = exp.table_("t", db="db")
    table.set("partition", exp.Partition(
        expressions=[exp.column("dt").eq(exp.Literal.string("2026-01-01"))]))
    insert = exp.Insert(this=table, expression=exp.select("a").from_("s"), overwrite=True)
    if "PARTITION(dt = '2026-01-01')" not in written(insert):
        problems.append("INSERT OVERWRITE drops its PARTITION")
    if written(to_sqlglot(Node("Drop", target=Node("Table", db="db", name="t")))) != (
            "DROP TABLE IF EXISTS db.t"):
        problems.append("DROP TABLE drops its table name")
    try:
        qualify(exp.select("nope").from_("t"), schema={"t": {"a": "INT"}}, dialect="hive")
        problems.append("qualify no longer refuses an unknown column")
    except OptimizeError:
        pass
    return problems


# --- The Example database's executor --------------------------------------------------------


def _check_executor() -> None:
    """Stop with a plain message when sqlglot's executor would give wrong answers."""
    import sqlglot

    # Imported only when a query runs: the rest of the Toolbox never needs the executor.
    from sqlglot.executor import execute

    # Imported here, as below: refusals.py imports pandas, which this file, imported first to
    # check sqlglot, leaves to the files after it.
    from .refusals import refuse

    check = execute("SELECT COUNT(DISTINCT x) AS n FROM t", dialect="hive",
                    tables={"t": [{"x": "a"}, {"x": "a"}, {"x": "b"}, {"x": None}]})
    if check.rows == [(2,)]:
        return
    refuse(
        what="The Example database runs queries on sqlglot's own executor, and sqlglot "
        f"{sqlglot.__version__}'s executor counts COUNT(DISTINCT ...) wrong.",
        why="An executor that counts COUNT(DISTINCT ...) wrong says nothing about it.",
        fix=f"{INSTALL_NEWER} Until then the rest of the Toolbox works as usual: to_hive(...) "
        "still shows a Statement's Hive.",
        error=RuntimeError,
    )


def _spell_out_likes(tree: exp.Expression) -> exp.Expression:
    """Rewrite each escaped LIKE, since sqlglot's executor ignores LIKE's backslash.

    starts_with and contains put a backslash before % and _ so they match themselves. Hive
    reads them that way, but the executor would still take _ for any one character.
    """
    from sqlglot import exp

    for like in list(tree.find_all(exp.Like)):
        pattern = like.expression
        if isinstance(pattern, exp.Literal) and pattern.is_string and "\\" in pattern.this:
            like.replace(_matching_text(like.this, pattern.this))
    return tree


def _spell_out_cases(tree: exp.Expression) -> exp.Expression:
    """Write each CASE on one column, CASE team WHEN 'data' THEN ..., as CASE WHEN team =
    'data' THEN ..., the same test, as Hive's = leaves NULL unmatched.

    sqlglot's executor writes the first as Python's = in place of == where it adds rows up,
    which stops it, as mapped(...) beside a count would.
    """
    from sqlglot import exp

    for case in list(tree.find_all(exp.Case)):
        tested = case.this
        if tested is None:
            continue
        for when in case.args.get("ifs") or []:
            when.set("this", exp.EQ(this=tested.copy(), expression=when.this))
        case.set("this", None)
    return tree


def _make_casts_plain(tree: exp.Expression) -> exp.Expression:
    """Make each CAST to text a plain one, which is all sqlglot's executor knows.

    sqlglot reads Hive's CAST as a TRY_CAST, since Hive gives NULL for a value it can't cast.
    Any value can be made text, so a CAST to text is the same plain, and the executor gets as
    far as what it really lacks, such as week_start's NEXT_DAY. A CAST to any other type stays
    as it is, so the executor says it has no CAST rather than failing on a value Hive makes
    NULL.
    """
    from sqlglot import exp

    for cast in list(tree.find_all(exp.TryCast)):
        if cast.to.is_type(*exp.DataType.TEXT_TYPES):
            cast.replace(exp.Cast(this=cast.this, to=cast.args["to"]))
    return tree


def _matching_text(column: exp.Expression, pattern: str) -> exp.Expression:
    """The same test as `column LIKE pattern`, for a pattern of text between optional %."""
    parts, i = [], 0
    while i < len(pattern):
        if pattern[i] == "\\" and i + 1 < len(pattern):
            parts.append(("text", pattern[i + 1]))
            i += 2
        else:
            parts.append(("wild" if pattern[i] in "%_" else "text", pattern[i]))
            i += 1
    # Take a % off each end; what is left in the middle must be plain text.
    leading = bool(parts) and parts[0] == ("wild", "%")
    middle = parts[1:] if leading else parts
    trailing = bool(middle) and middle[-1] == ("wild", "%")
    middle = middle[:-1] if trailing else middle
    if any(kind == "wild" for kind, _ in middle):
        _refuse_missing_part(f"LIKE with a % or _ in the middle ({pattern!r})")
    from sqlglot import exp

    text = "".join(char for _, char in middle)
    found = exp.Literal.string(text)
    size = exp.Literal.number(len(text))
    if leading and trailing:
        return exp.GT(this=exp.StrPosition(this=column, substr=found),
                      expression=exp.Literal.number(0))
    if leading:
        return exp.EQ(this=exp.Right(this=column, expression=size), expression=found)
    if trailing:
        return exp.EQ(this=exp.Left(this=column, expression=size), expression=found)
    return exp.EQ(this=column, expression=found)


def _missing_function(tree: exp.Expression, error: str) -> str | None:
    """The Hive name of the function the executor didn't know, from its error, or None."""
    from sqlglot import exp

    from .writing import sql_text

    found = re.search(r"name '(\w+)' is not defined", error)
    if found is not None:
        for function in tree.find_all(exp.Func):
            if function.key.upper() == found.group(1):
                return sql_text(function).split("(")[0]
    return None


def _refuse_missing_part(missing: str, error: Exception | None = None) -> NoReturn:
    """Refuse a query that needs a part of Hive the executor hasn't got, such as NEXT_DAY.

    Raised here, not through refusals.refuse, so that the executor's own `error` stays the
    refusal's cause."""
    raise RuntimeError(four_part_message(
        what=f"The Example database can't run this Hive: its executor has no {missing}.",
        why="The Example database runs Hive on sqlglot's own small executor, which knows only "
        "part of Hive. Hive at work knows all of it.",
        fix="See the Hive with to_hive(...), and run it at work with your own query. Or try "
        "the rest here without that part: in the Statement, or in the original Hive, where "
        "you compare a Statement with one.",
        opt_out=None,
    )) from error


def _refuse_hive_it_cant_run(reason: str,
                             tables: dict[str, tuple[Table, list[tuple[object, ...]]]],
                             error: Exception | None = None) -> NoReturn:
    """Refuse a query sqlglot couldn't read or run, as a warehouse refuses one.

    Raised here, not through refusals.refuse, so that sqlglot's own `error` stays the
    refusal's cause."""
    listed = in_words([f"ops.{name}" for name in tables])
    raise RuntimeError(four_part_message(
        what=f"The Example database couldn't run this Hive: {reason}.",
        why="Most often a table, column or hive_function(...) name is spelt wrong, which your "
        "warehouse would refuse too. Or the Hive uses a part of Hive your warehouse knows but "
        "the Example database's small executor doesn't.",
        fix=f"Check the names: the tables are {listed}, and all_columns(...) of one, such as "
        "all_columns(example_database.jobs), lists its columns, as the table alone on a "
        "cell's last line does. If they're right, see the Hive with "
        "to_hive(...), and run it at work with your own query.",
        opt_out=None,
    )) from error


@contextlib.contextmanager
def _joined_tables_kept_apart() -> Iterator[None]:
    """While it lasts, the executor adds rows up after a join without mixing up two columns of
    one name.

    To add rows up after a join, sqlglot's executor works out the inside of each count or sum
    as a new column at the end of each joined row, and widened each joined table by that many
    columns. A table's columns then ran on into the next table's, and a column name the two
    share read the next table's value: for a LEFT JOIN's row with no match, NULL. Here a
    joined table keeps its own columns; the new ones are read as the executor reads them, from
    the table of its own it makes for them.
    """
    from sqlglot.executor import table as rows

    real = rows.Table.add_columns

    def add_columns(table: rows.Table, *columns: str) -> None:
        table.columns += columns
        table.reader = rows.RowReader(table.columns, table.column_range)

    rows.Table.add_columns = add_columns
    try:
        yield
    finally:
        rows.Table.add_columns = real


# What each window function reads, by sqlglot's name for it: the places of the rows in their
# order, a value of the row a place away, or the values of the rows it looks across.
_PLACES = {"RowNumber", "Rank", "DenseRank", "Ntile"}
_A_PLACE_AWAY = {"Lag": -1, "Lead": 1}
_OVER_ROWS = {"FirstValue", "LastValue", "Sum", "Avg", "Min", "Max", "Count"}


class _Ordered(NamedTuple):
    """One column of a window's ORDER BY: its place in the rows the rest of the query gives,
    whether it is DESC, and whether NULL comes first."""

    place: int
    descending: bool
    null_first: bool


class _Worked(NamedTuple):
    """A window, as the Example database works it out: its function, by sqlglot's name; where
    each value it reads is in the rows the rest of the query gives, by place; and, where it
    says, which rows near each row it looks across, as window(..., rows=...) writes them."""

    function: str
    arguments: list[int | None]  # its column, then its other arguments, None where left out
    groups: list[int]  # PARTITION BY's columns
    order: list[_Ordered]
    rows_near: exp.WindowSpec | None


def _work_out_windows(tree: exp.Expression, schema: dict[str, dict[str, dict[str, str]]],
                      rows: dict[str, dict[str, list[dict[str, object]]]],
                      run: Callable[[exp.Expression], executed.Table]) -> exp.Expression:
    """The query, with each SELECT that has a window read from a table made of its answer.

    sqlglot's executor has no window functions. So each SELECT with one, the innermost first,
    runs without it, as `run` runs a query: the rows its FROM, JOIN, WHERE, GROUP BY and
    HAVING give, with each value the windows and the columns read. The windows are worked out
    from those rows, as Hive works them out, and the SELECT then reads them from a table made
    of them, added to `schema` and `rows`, which gives its columns, ORDER BY and LIMIT.
    """
    from sqlglot import exp
    from sqlglot.optimizer.qualify import qualify

    if not tree.find(exp.Window):
        return tree
    tree = qualify(tree, schema=schema, dialect="hive")  # each * as its columns, each named
    made = 0
    while True:
        windowed = [query for query in tree.find_all(exp.Select) if _own_windows(query)]
        if not windowed:
            return tree
        innermost = []
        for query in windowed:
            if not any(other is not query and _within(other, query) for other in windowed):
                innermost.append(query)
        made += 1
        query = min(innermost, key=lambda one: _where_in_with(one, tree))
        answer = _work_out_window(tree, query, f"_window_{made}", schema, rows, run)
        if query is tree:
            tree = answer
        else:
            query.replace(answer)


def _own_windows(query: exp.Expression) -> list[exp.Window]:
    """The windows of a SELECT, not of a query inside it."""
    from sqlglot import exp

    return [window for window in query.find_all(exp.Window)
            if window.find_ancestor(exp.Select) is query]


def _within(inner: exp.Expression, outer: exp.Expression) -> bool:
    """Whether a part of a query is inside another."""
    node = inner.parent
    while node is not None and node is not outer:
        node = node.parent
    return node is outer


def _with_of(query: exp.Expression) -> exp.With | None:
    """A query's WITH, or None."""
    return query.args.get("with_")


def _where_in_with(query: exp.Expression, tree: exp.Expression) -> int:
    """Where a SELECT is among the Derived tables of the query's WITH, which may read only
    those before it: the query itself, after them all."""
    around = _with_of(tree)
    derived_tables = around.expressions if around is not None else []
    for place, derived_table in enumerate(derived_tables):
        if query is derived_table or _within(query, derived_table):
            return place
    return len(derived_tables)


def _made_column(kind: str, place: int) -> str:
    """The name of a made table's column: _w_0, _w_1, ... for each value the SELECT without its
    windows gives, and _v_0, _v_1, ... for each window's."""
    return f"{kind}_{place}"


def _work_out_window(tree: exp.Expression, query: exp.Select, name: str,
                     schema: dict[str, dict[str, dict[str, str]]],
                     rows: dict[str, dict[str, list[dict[str, object]]]],
                     run: Callable[[exp.Expression], executed.Table]) -> exp.Select:
    """The SELECT that gives what `query`, a SELECT with windows, gives, from a table `name`
    made of its rows, as _work_out_windows says."""
    from sqlglot import exp

    windows = _own_windows(query)
    _check_windows_in_columns(query, windows)
    read = []  # each value the rows of the SELECT without its windows give

    def value(node: exp.Expression) -> exp.Column:
        read.append(node.copy())
        return exp.column(_made_column("_w", len(read) - 1), table=name)

    def read_at(node: exp.Expression | None) -> int | None:
        if node is None:
            return None
        value(node)
        return len(read) - 1

    worked = [_worked(window, read_at) for window in windows]
    outputs = [_column_from_made_table(column, windows, name, value)
               for column in query.expressions]
    order = _order_after(query, value)
    given = [list(row) for row in run(_without_windows(tree, query, read)).rows]
    for window in worked:
        for row, worked_value in zip(given, _window_values(window, given)):
            row.append(worked_value)
    columns = [_made_column("_w", place) for place in range(len(read))] + ["_w_row"] + [
        _made_column("_v", one) for one in range(len(worked))]
    _add_made_table(name, columns, given, schema, rows)
    answer = exp.select(*outputs).from_(exp.table_(name, db="ops", alias=name))
    for part in ("distinct", "limit", "offset"):
        if query.args.get(part) is not None:
            answer.set(part, query.args[part].copy())
    if order is not None:
        answer.set("order", order)
    return answer


def _check_windows_in_columns(query: exp.Select, windows: list[exp.Window]) -> None:
    """Refuse a window of a SELECT that isn't in its columns, such as one in ORDER BY."""
    for window in windows:
        if not any(window is found or _within(window, found) for found in query.expressions):
            _refuse_missing_part("window outside SELECT's columns, such as one in ORDER BY: "
                                 "work it out in SELECT, named with AS, and order by that name")


def _add_made_table(name: str, columns: list[str], given: list[list[object]],
                    schema: dict[str, dict[str, dict[str, str]]],
                    rows: dict[str, dict[str, list[dict[str, object]]]]) -> None:
    """Add the table `name`, of the rows `given`, to the Example database's `schema` and
    `rows`, as ops.name, each column's type from its values."""
    made_columns = {}
    for place, column in enumerate(columns):
        made_columns[column] = _kind_of([row[place] for row in given])
    schema["ops"][name] = made_columns
    rows["ops"][name] = [dict(zip(columns, row)) for row in given]


def _order_after(query: exp.Select, value: Callable[[exp.Expression], exp.Column]
                 ) -> exp.Order | None:
    """A SELECT's ORDER BY, to sort the rows once its windows are worked out: a column it gives
    by name, as itself, and anything else read by `value`."""
    from sqlglot import exp

    order = query.args.get("order")
    if order is None:
        return None
    names = {column.alias_or_name for column in query.expressions}
    order = order.copy()
    for ordered in order.expressions:
        if not (isinstance(ordered.this, exp.Column) and not ordered.this.table
                and ordered.this.name in names):
            ordered.set("this", value(ordered.this))
    return order


def _without_windows(tree: exp.Expression, query: exp.Select, read: list[exp.Expression]
                     ) -> exp.Select:
    """A SELECT with windows, giving in their place each value in `read`, and a 1 so it gives a
    column even where it reads none: its rows before its windows, ORDER BY, LIMIT and DISTINCT.
    It takes the Derived tables of the query's WITH that it may read."""
    from sqlglot import exp

    without = query.copy()
    without.set("expressions", [exp.alias_(one, _made_column("_w", place))
                                for place, one in enumerate(read)]
                + [exp.alias_(exp.Literal.number(1), "_w_row")])
    for part in ("order", "limit", "offset", "distinct"):
        if part in type(without).arg_types:
            without.set(part, None)
    around = _with_of(tree)
    before = around.expressions[:_where_in_with(query, tree)] if around is not None else []
    if query is not tree and before and _with_of(without) is None:
        without.set("with_", exp.With(expressions=[one.copy() for one in before]))
    return without


def _column_from_made_table(column: exp.Expression, windows: list[exp.Window], name: str,
                            value: Callable[[exp.Expression], exp.Column]) -> exp.Expression:
    """A column of a SELECT with windows, as the SELECT that reads the made table `name`
    gives it: each window its column there, and each value read by `value`."""
    from sqlglot import exp

    alias = column.alias_or_name
    if not column.find(exp.Window):
        return exp.alias_(value(column.unalias()), alias) if alias else value(column)
    given = column.unalias().copy()
    for original, copied in zip(column.unalias().find_all(exp.Window),
                                list(given.find_all(exp.Window))):
        held = exp.column(_made_column(
            "_v", next(i for i, w in enumerate(windows) if w is original)), table=name)
        if copied is given:
            given = held
        else:
            copied.replace(held)
    for node in list(given.find_all(exp.AggFunc, exp.Column)):
        if node.root() is given and not (isinstance(node, exp.Column) and node.table == name):
            node.replace(value(node))
    return exp.alias_(given, alias) if alias else given


def _worked(window: exp.Window, read_at: Callable[[exp.Expression | None], int | None]
            ) -> _Worked:
    """A window, its function and its pieces each read through `read_at`, or refused plainly
    where the Example database can't work it out."""
    from sqlglot import exp

    function = window.this
    kind = type(function).__name__
    if isinstance(function, exp.Count) and isinstance(function.this, exp.Distinct):
        _refuse_missing_part("COUNT(DISTINCT ...) over a window")
    if isinstance(function, (exp.IgnoreNulls, exp.RespectNulls)):
        _refuse_missing_part("IGNORE NULLS or RESPECT NULLS in a window")
    if kind not in _PLACES | set(_A_PLACE_AWAY) | _OVER_ROWS:
        if isinstance(function, exp.Anonymous):
            named = function.name.upper()
        elif isinstance(function, exp.Func):
            named = function.sql_name()
        else:
            named = function.key.upper()
        _refuse_missing_part(f"window function {named}")
    spec = window.args.get("spec")
    if spec is not None and (spec.args.get("kind") or "").upper() == "RANGE" and any(
            isinstance(spec.args.get(end), exp.Expression) for end in ("start", "end")):
        _refuse_missing_part("window over RANGE with a number of rows, such as RANGE "
                             "BETWEEN 1 PRECEDING AND CURRENT ROW; window(rows=...) writes "
                             "ROWS BETWEEN, which it has")
    if kind == "Count" and isinstance(function.this, exp.Star):
        arguments = [None]
    else:
        arguments = [read_at(function.args.get(part))
                     for part in ("this", "offset", "default")]
    groups = [read_at(column) for column in window.args.get("partition_by") or []]
    order = window.args.get("order")
    ordered_by = []
    for ordered in (order.expressions if order is not None else []):
        descending = bool(ordered.args.get("desc"))
        null_first = ordered.args.get("nulls_first")
        if null_first is None:
            null_first = not descending
        ordered_by.append(_Ordered(read_at(ordered.this), descending, null_first))
    return _Worked(kind, arguments, groups, ordered_by, spec)


def _window_values(window: _Worked, rows: list[list[object]]) -> list[object]:
    """Each row's value of a window, from the rows the rest of its SELECT gives."""
    import functools

    def compared(one: int, other: int) -> int:
        return _order_of_rows(window.order, rows[one], rows[other])

    groups = {}
    for row in range(len(rows)):
        groups.setdefault(tuple(rows[row][column] for column in window.groups), []).append(row)
    values = [None] * len(rows)
    for members in groups.values():
        ordered = sorted(members, key=functools.cmp_to_key(compared))
        peers = _peers(ordered, compared)
        for place, row in enumerate(ordered):
            values[row] = _window_value(window, rows, ordered, place, peers)
    return values


def _order_of_rows(order: list[_Ordered], one: list[object], other: list[object]) -> int:
    """Which of two rows comes first in a window's order: -1 the first, 1 the second, 0 tied.
    NULL comes first where `order` says so, as Hive puts it first in an ascending order."""
    for column, descending, null_first in order:
        a, b = one[column], other[column]
        if a is None and b is None:
            continue
        if a is None or b is None:
            return (-1 if a is None else 1) * (1 if null_first else -1)
        if a != b:
            return (-1 if a < b else 1) * (-1 if descending else 1)
    return 0


def _peers(ordered: list[int], compared: Callable[[int, int], int]) -> list[tuple[int, int]]:
    """For each place in a group's order, the first place and the after-last place of the rows
    tied with it."""
    firsts = [0] * len(ordered)
    for place in range(1, len(ordered)):
        tied = not compared(ordered[place - 1], ordered[place])
        firsts[place] = firsts[place - 1] if tied else place
    lasts = [len(ordered)] * len(ordered)
    for place in reversed(range(len(ordered) - 1)):
        tied = not compared(ordered[place], ordered[place + 1])
        lasts[place] = lasts[place + 1] if tied else place + 1
    return list(zip(firsts, lasts))


def _window_value(window: _Worked, rows: list[list[object]], ordered: list[int], place: int,
                  peers: list[tuple[int, int]]) -> object:
    """One row's value of a window: the row at `place` of `ordered`, its group in order."""
    if window.function in _PLACES:
        return _place_value(window, rows[ordered[place]], len(ordered), place, peers)
    if window.function in _A_PLACE_AWAY:
        this, offset, default = window.arguments
        row = rows[ordered[place]]
        away = place + _A_PLACE_AWAY[window.function] * (1 if offset is None
                                                         else int(row[offset]))
        if 0 <= away < len(ordered):
            return rows[ordered[away]][this]
        return None if default is None else row[default]
    start, end = _rows_looked_across(window.rows_near, place, peers[place], len(ordered),
                                     bool(window.order))
    return _value_over_rows(window, [rows[at] for at in ordered[start:end]])


def _place_value(window: _Worked, row: list[object], size: int, place: int,
                 peers: list[tuple[int, int]]) -> int:
    """A row's number, rank, dense rank or part, at `place` of a group of `size` rows."""
    if window.function == "RowNumber":
        return place + 1
    if window.function == "Rank":
        return peers[place][0] + 1
    if window.function == "DenseRank":
        return len({first for first, _ in peers[:place + 1]})
    parts = int(row[window.arguments[0]])  # NTILE(parts)
    if parts < 1:
        from .refusals import refuse  # here, as in _check_executor, for pandas' sake

        refuse(
            what=f"The Example database can't run this Hive: NTILE({parts}) splits each group "
            "into no parts.",
            why="NTILE numbers the rows of each group from 1 to its number of parts, so it "
            "needs 1 part or more. Hive refuses it too.",
            fix="Give NTILE a number of parts of 1 or more, such as ntile(4, over=...).",
            error=RuntimeError,
        )
    small, extra = divmod(size, parts)
    if small == 0:
        return place + 1
    big = extra * (small + 1)  # the first `extra` parts hold a row more
    return place // (small + 1) + 1 if place < big else extra + (place - big) // small + 1


def _value_over_rows(window: _Worked, across: list[list[object]]) -> object:
    """A window's value over the rows it looks across for one row."""
    this = window.arguments[0]
    if window.function == "Count":
        return len(across) if this is None else sum(one[this] is not None for one in across)
    if window.function in ("FirstValue", "LastValue"):
        at = 0 if window.function == "FirstValue" else -1
        return across[at][this] if across else None
    found = [one[this] for one in across if one[this] is not None]
    if not found:
        return None
    if window.function == "Sum":
        return sum(found)
    if window.function == "Avg":
        return sum(found) / len(found)
    return min(found) if window.function == "Min" else max(found)


def _rows_looked_across(spec: exp.WindowSpec | None, place: int, peers: tuple[int, int],
                        size: int, ordered: bool) -> tuple[int, int]:
    """The places of the rows a window looks across for the row at `place`, first to
    after-last: with no rows=, the whole group, or with ORDER BY every row up to the row and
    those tied with it, as Hive reads them."""
    if spec is None:
        return (0, peers[1]) if ordered else (0, size)
    by_rows = (spec.args.get("kind") or "ROWS").upper() == "ROWS"

    def end_of(given: str | exp.Expression | None, side: str | None, start: bool) -> int:
        given = given if isinstance(given, str) or given is None else given.name
        if given is None or given.upper() == "CURRENT ROW":
            if by_rows:
                return place if start else place + 1
            return peers[0] if start else peers[1]
        if given.upper() == "UNBOUNDED":
            return 0 if (side or "").upper() == "PRECEDING" else size
        away = int(given) * (-1 if (side or "").upper() == "PRECEDING" else 1)
        return place + away + (0 if start else 1)

    start = end_of(spec.args.get("start"), spec.args.get("start_side"), True)
    end = end_of(spec.args.get("end"), spec.args.get("end_side"), False)
    start, end = max(start, 0), min(end, size)
    return (start, end) if start < end else (0, 0)


def _kind_of(values: list[object]) -> str:
    """The Hive type a made table's column holds, from its values."""
    for one in values:
        if isinstance(one, bool):
            return "boolean"
        if isinstance(one, int):
            return "bigint"
        if isinstance(one, float):
            return "double"
        if one is not None:
            return "string"
    return "string"


def _stacked_reads_told_apart(tree: exp.Expression,
                              schema: dict[str, dict[str, dict[str, str | None]]]
                              ) -> exp.Expression:
    """The query, with each table it reads under a name of its own, where it stacks two reads.

    sqlglot's executor calls each step of a UNION, INTERSECT or EXCEPT by the name of the table
    it reads, and keeps one step of each name: two reads of job_runs, one a day, would give one
    day's rows twice, without saying so. So the query is first written out in full, as the
    executor writes it, each column with its table's name; then a name used before, in another
    part of the query, becomes job_runs_2, and so do the columns of that part that read it.
    """
    from sqlglot import exp
    from sqlglot.optimizer import optimize
    from sqlglot.optimizer.scope import traverse_scope

    if not tree.find(exp.Union, exp.Intersect, exp.Except):
        return tree
    tree = optimize(tree, schema, leave_tables_isolated=True, dialect="hive")
    used = set()
    for scope in traverse_scope(tree):
        for name, (read, _) in scope.selected_sources.items():
            if name not in used:
                used.add(name)
                continue
            new = next(f"{name}_{n}" for n in range(2, len(used) + 2)
                       if f"{name}_{n}" not in used)
            used.add(new)
            read.set("alias", exp.TableAlias(this=exp.to_identifier(new, quoted=True)))
            for column in scope.columns:
                if column.table == name:
                    column.set("table", exp.to_identifier(new, quoted=True))
    return tree


def _reason_without_place(error: Exception) -> str:
    """The first line of what sqlglot said, without where it stopped ("Line 1, Col: 45.")."""
    reason = (str(error).strip().splitlines() or [type(error).__name__])[0]
    return re.sub(r"\s*Line:? \d+, Col: \d+\.?$", "", reason).rstrip(".")


def _check_example_tables(tree: exp.Expression,
                          tables: dict[str, tuple[Table, list[tuple[object, ...]]]]) -> None:
    """Refuse a table the query names with a database that isn't one of the Example database's,
    such as mart.jobs, as a warehouse refuses it, before a column of it is blamed."""
    from sqlglot import exp

    for table in tree.find_all(exp.Table):
        if table.db and (table.db.lower() != "ops" or table.name.lower() not in tables):
            _refuse_hive_it_cant_run(f"it has no table {table.db}.{table.name}", tables)


def _refuse_what_it_runs_wrong(tree: exp.Expression) -> None:
    """Refuse a part of Hive the executor hasn't got, or would run wrong without a word."""
    from sqlglot import exp

    if tree.find(exp.GroupingSets):
        # Its executor would group by every column, leaving out the subtotal rows unsaid.
        _refuse_missing_part("GROUPING SETS, which rollup, cube and grouping_sets write")
    # The executor would run a LEFT SEMI JOIN as a LEFT JOIN, repeating and keeping rows.
    if any(join.kind == "SEMI" for join in tree.find_all(exp.Join)):
        _refuse_missing_part("LEFT SEMI JOIN")
    # Its executor runs a LATERAL VIEW as a join it can't finish, as an Unchecked derived table
    # may hold.
    if tree.find(exp.Lateral):
        _refuse_missing_part("LATERAL VIEW")


def run_query(text: str, tables: dict[str, tuple[Table, list[tuple[object, ...]]]]
              ) -> tuple[list[str], list[tuple[object, ...]]]:
    """Run a query's Hive on sqlglot's executor: its column names, and its rows.

    `tables` maps each table's short name to its Table reference and its rows.
    """
    import sqlglot

    if text.split(None, 1)[:1] and text.split(None, 1)[0].upper() == "EXPLAIN":
        # The executor runs a query step by step, with no plan of Hive's to show.
        _refuse_missing_part("EXPLAIN")
    try:
        tree = sqlglot.parse_one(text, read="hive")
    except sqlglot.errors.SqlglotError as error:
        _refuse_hive_it_cant_run(_reason_without_place(error), tables, error)
    _check_example_tables(tree, tables)
    _check_executor()
    from sqlglot.executor import execute  # only when a query runs, as in _check_executor

    schema = {"ops": {name: dict(table._columns) for name, (table, _) in tables.items()}}
    rows = {"ops": {}}
    for name, (table, table_rows) in tables.items():
        rows["ops"][name] = [dict(zip(table._columns, row)) for row in table_rows]
    _refuse_what_it_runs_wrong(tree)
    try:
        tree = _stacked_reads_told_apart(tree, schema)
        with _joined_tables_kept_apart():
            def run(query: exp.Expression) -> executed.Table:
                return execute(_make_casts_plain(_spell_out_cases(_spell_out_likes(query))),
                               schema=schema, tables=rows, dialect="hive")
            result = run(_work_out_windows(tree, schema, rows, run))
    except sqlglot.errors.ExecuteError as error:
        # The executor wraps what stops a step in an ExecuteError, raised from it.
        missing = _missing_function(tree, str(error))
        if missing is None:
            _refuse_hive_it_cant_run(_reason_without_place(error), tables, error)
        _refuse_missing_part(missing, error)
    except sqlglot.errors.SqlglotError as error:  # such as a column it can't find
        _refuse_hive_it_cant_run(_reason_without_place(error), tables, error)
    return list(result.columns), list(result.rows)
