"""Hive run on sqlglot's own executor, on this computer, over rows it is given (Toolbox 8.9,
ticket 09; ADR 0016).

sqlglot's executor runs a query in Python, over rows held in memory: it reaches nothing, no
warehouse and no file. It knows only part of Hive, so `run_on_executor` first works out, in
Hive's own way, what it has no Python for: GROUPING SETS and ROLLUP, window functions, a
grouped column beside an aggregate, an escaped LIKE, a CASE on one column, a CAST to text, and
two reads of one table stacked with UNION ALL; and it compares text with a number as Hive
does, reading the text as a number. A part it still can't run, such as a function
it has no Python for, stops it with a MissingPart naming that part, never a guess.

Two places run Hive on it: the Workbook check (`workbook_check.py`), over a Formula
workbook's own Tables, and dev's Example database, over its own rows. Each gives the Hive day
functions and any others it needs as `functions`, taught to the executor only while it runs.
"""

from __future__ import annotations

import contextlib
import datetime
import decimal
import functools
import re
from collections.abc import Callable, Iterator
from typing import NamedTuple

import sqlglot
from sqlglot import exp
from sqlglot.executor import env
from sqlglot.executor import table as executed
from sqlglot.optimizer.scope import traverse_scope

from .shared import number_read_from
from .writing import executed_hive, optimized_hive, qualified_hive, sql_text

# The database the tables made while windows are worked out are held in, apart from any the
# query reads.
MADE_TABLES = "made_by_the_executor"
# Hive's names for each day of the week, Monday first, as NEXT_DAY reads them in any case.
_HIVE_WEEKDAY_NAMES = [
    ("MO", "MON", "MONDAY"), ("TU", "TUE", "TUESDAY"), ("WE", "WED", "WEDNESDAY"),
    ("TH", "THU", "THURSDAY"), ("FR", "FRI", "FRIDAY"), ("SA", "SAT", "SATURDAY"),
    ("SU", "SUN", "SUNDAY"),
]


class MissingPart(Exception):
    """A part of Hive the executor hasn't got, or would run wrong without a word, such as
    TRUNC or a LEFT SEMI JOIN: `missing` names it."""

    def __init__(self, missing: str) -> None:
        super().__init__(missing)
        self.missing = missing


class NtileWithNoParts(Exception):
    """NTILE given a number of parts below 1, which Hive refuses too: `parts` is the number."""

    def __init__(self, parts: int) -> None:
        super().__init__(f"NTILE({parts})")
        self.parts = parts


def executor_counts_right() -> bool:
    """Whether this sqlglot's executor counts COUNT(DISTINCT ...) right, as some of the
    versions the Toolbox takes don't, without a word."""
    check = executed_hive("SELECT COUNT(DISTINCT x) AS n FROM t", None,
                          {"t": [{"x": "a"}, {"x": "a"}, {"x": "b"}, {"x": None}]})
    return check.rows == [(2,)]


def _date_add(day: object, days: object, unit: object = None) -> str | None:
    """Hive's date_add and date_sub, which sqlglot's executor reads as one function, TsOrDsAdd:
    the day, as text such as '2026-09-24', moved on by a number of days. `unit`, DAY, is what
    the executor passes beside the two."""
    if day is None or days is None:
        return None
    start = datetime.date.fromisoformat(str(day)[:10])
    return (start + datetime.timedelta(days=int(days))).isoformat()


def _next_day(day: object, weekday: object) -> str | None:
    """Hive's next_day, which week_start writes: the first day after the given one, as text,
    that falls on the named day of the week, such as 'MO', 'MON' or 'MONDAY' in any case, or
    NULL for a name Hive doesn't know."""
    if day is None or weekday is None:
        return None
    named = [number for number, names in enumerate(_HIVE_WEEKDAY_NAMES)
             if str(weekday).upper() in names]
    if not named:
        return None
    start = datetime.date.fromisoformat(str(day)[:10])
    # From 1 to 7 days on: a day already on the named weekday moves on a whole week.
    ahead = (named[0] - start.weekday() - 1) % 7 + 1
    return (start + datetime.timedelta(days=ahead)).isoformat()


# The Hive day functions sqlglot's executor has no Python for, by its name for each, each
# taking and giving back a day as text, such as '2026-09-24', as the rows given hold a day.
HIVE_DAYS: dict[str, Callable[..., object]] = {"TSORDSADD": _date_add, "NEXTDAY": _next_day}


def _compared_as_hive_compares(compare: Callable[..., object]) -> Callable[..., object]:
    """One of the executor's comparisons, made to compare as Hive does (Toolbox 8.10, ticket
    09): given text and a number, it reads the text as a number, or as NULL where it reads as
    none, as job_id = '3' matches 3 in Hive. Python's own == would match nothing."""
    def compared(*values: object) -> object:
        has_text = any(isinstance(value, str) for value in values)
        has_number = any(isinstance(value, (int, float, decimal.Decimal))
                         and not isinstance(value, bool) for value in values)
        if has_text and has_number:
            values = tuple(_number_or_value(value) for value in values)
        return compare(*values)
    return compared


def _number_or_value(value: object) -> object:
    """Text as the number Hive reads it as, None where it reads as none; any other value as it
    is."""
    if isinstance(value, str):
        return number_read_from(value)
    return value


# The executor's comparisons, by its name for each, each comparing text and a number as Hive
# does: taught to it each time it runs.
_HIVE_COMPARISONS: dict[str, Callable[..., object]] = {
    name: _compared_as_hive_compares(env.ENV[name])
    for name in ("EQ", "NEQ", "GT", "GTE", "LT", "LTE", "BETWEEN", "IN")}


def run_on_executor(tree: exp.Expression, schema: dict[str, dict[str, dict[str, str]]],
                    rows: dict[str, dict[str, list[dict[str, object]]]],
                    functions: dict[str, Callable[..., object]]
                    ) -> tuple[list[str], list[tuple[object, ...]]]:
    """A query's column names and its rows, run on sqlglot's executor over `rows`, each table's
    rows by its database and its name, its columns' types in `schema`, the same way; each of
    `functions`, by the executor's name for it, such as TSORDSADD, taught to it while it runs.

    It raises MissingPart for a part of Hive it can't run, NtileWithNoParts for NTILE of no
    parts, and what sqlglot raises on Hive it can't read or run, such as a column it can't
    find. A table it makes while it works out a window is added to `schema` and `rows`, in
    MADE_TABLES."""
    _check_parts_it_runs_right(tree)
    try:
        # Grouping sets stack a SELECT per set, so they are worked out before the stacked reads
        # are told apart.
        tree = _stacked_reads_told_apart(_work_out_grouping_sets(tree), schema)
        with _joined_tables_kept_apart(), _functions_taught({**_HIVE_COMPARISONS,
                                                             **functions}):
            def run(query: exp.Expression) -> executed.Table:
                spelled_out = _make_casts_plain(_spell_out_cases(_spell_out_likes(query)))
                return executed_hive(_work_out_mixed_groups(spelled_out), schema, rows)
            result = run(_work_out_windows(tree, schema, rows, run))
    except sqlglot.errors.ExecuteError as error:
        # The executor wraps what stops a step in an ExecuteError, raised from it.
        missing = _missing_function(tree, str(error))
        if missing is None:
            raise
        raise MissingPart(missing) from error
    return list(result.columns), list(result.rows)


@contextlib.contextmanager
def _functions_taught(functions: dict[str, Callable[..., object]]) -> Iterator[None]:
    """While it lasts, sqlglot's executor has each of `functions`, by its name for it, in
    place of any of that name it had; afterwards it has what it had."""
    had = {name: env.ENV[name] for name in functions if name in env.ENV}
    env.ENV.update(functions)
    try:
        yield
    finally:
        for name in functions:
            env.ENV.pop(name)
        env.ENV.update(had)


def _spell_out_likes(tree: exp.Expression) -> exp.Expression:
    """Rewrite each escaped LIKE, since sqlglot's executor ignores LIKE's backslash.

    starts_with and contains put a backslash before % and _ so they match themselves. Hive
    reads them that way, but the executor would still take _ for any one character.
    """
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
    for case in list(tree.find_all(exp.Case)):
        tested = case.this
        if tested is None:
            continue
        for when in case.args.get("ifs") or []:
            when.set("this", exp.EQ(this=tested.copy(), expression=when.this))
        case.set("this", None)
    return tree


def _work_out_grouping_sets(tree: exp.Expression) -> exp.Expression:
    """Work out each SELECT grouped by GROUPING SETS, a ROLLUP or a CUBE as Hive does: a SELECT
    grouped by each set's columns in turn, each column the set leaves out NULL and grouping() of
    it 1, their rows stacked with UNION ALL. sqlglot's executor has none of them."""
    # The innermost first, so a SELECT is worked out before one around it is copied.
    for number, select in enumerate(reversed(list(tree.find_all(exp.Select)))):
        group = select.args.get("group")
        sets = _grouping_sets_of(group) if group is not None else None
        if sets is None:
            continue
        if select.args.get("order") is not None or select.args.get("limit") is not None:
            raise MissingPart("ORDER BY or LIMIT on the same SELECT as GROUPING SETS")
        grouped_by = set()
        for each_set in sets:
            grouped_by |= set(each_set)
        stacked = None
        for each_set in sets:
            one_set = _grouped_by_one_set(select, grouped_by, each_set)
            stacked = one_set if stacked is None else exp.union(stacked, one_set,
                                                                distinct=False)
        every_set = exp.select("*").from_(_named_subquery(stacked, f"_sets_{number}"))
        tree = _in_place_of(tree, select, every_set)
    return tree


def _grouping_sets_of(group: exp.Group) -> list[list[exp.Expression]] | None:
    """The sets a GROUP BY groups by, each its columns, as GROUPING SETS lists them, a ROLLUP
    each leading run of its columns, with any column beside it in every set; None for a plain
    one."""
    keys = list(group.expressions)
    if group.args.get("grouping_sets"):
        sets = []
        for listed in group.args["grouping_sets"][0].expressions:
            inside = listed.expressions if isinstance(listed, exp.Tuple) else [listed.unnest()]
            sets.append(list(inside))
        return sets
    if group.args.get("rollup"):  # GROUP BY a, b WITH ROLLUP rolls up every column
        return _rolled_up([], keys)
    rolled = [key for key in keys if isinstance(key, exp.Rollup)]
    if rolled:  # GROUP BY a, ROLLUP(b, c) keeps a in every set
        beside = [key for key in keys if not isinstance(key, exp.Rollup)]
        return _rolled_up(beside, rolled[0].expressions)
    if group.args.get("cube") or any(isinstance(key, exp.Cube) for key in keys):
        raise MissingPart("CUBE, which cube writes")
    return None


def _rolled_up(beside: list[exp.Expression],
               columns: list[exp.Expression]) -> list[list[exp.Expression]]:
    """A ROLLUP's sets: `beside` and each leading run of `columns`, longest first."""
    return [beside + list(columns[:size]) for size in range(len(columns), -1, -1)]


def _grouped_by_one_set(select: exp.Select, grouped_by: set[exp.Expression],
                        each_set: list[exp.Expression]) -> exp.Select:
    """The SELECT grouped by the columns of `each_set` alone: each column of `grouped_by` the
    set leaves out NULL, and grouping() of a column 1 when the set leaves it out, else 0.
    sqlglot's nodes are compared as they are written, so a column is found by its node."""
    in_the_set = set(each_set)
    left_out = grouped_by - in_the_set

    def as_the_set_gives_it(node: exp.Expression) -> exp.Expression:
        if isinstance(node, exp.Grouping):
            return exp.Literal.number(int(node.expressions[0] not in in_the_set))
        if (isinstance(node, exp.Column) and node in left_out
                and node.find_ancestor(exp.AggFunc) is None):
            return exp.Null()
        return node

    one_set = select.copy()
    one_set.set("expressions", _outputs_rewritten(select, as_the_set_gives_it))
    one_set.set("group", exp.Group(expressions=[column.copy() for column in each_set])
                if each_set else None)
    if select.args.get("having"):
        one_set.set("having", select.args["having"].copy().transform(as_the_set_gives_it))
    return one_set


def _outputs_rewritten(select: exp.Select,
                       rewrite: Callable[[exp.Expression], exp.Expression]
                       ) -> list[exp.Expression]:
    """Each of a SELECT's outputs rewritten by `rewrite`, under the name it had."""
    outputs = []
    for output in select.expressions:
        rewritten = output.copy().transform(rewrite)
        if not isinstance(output, exp.Alias):
            rewritten = exp.alias_(rewritten, output.alias_or_name)
        outputs.append(rewritten)
    return outputs


def _named_subquery(query: exp.Expression, name: str) -> exp.Subquery:
    """`query` as a subquery read under `name`."""
    return exp.Subquery(this=query, alias=exp.TableAlias(this=exp.to_identifier(name)))


def _in_place_of(tree: exp.Expression, select: exp.Select,
                 worked_out: exp.Select) -> exp.Expression:
    """The tree with `worked_out` in place of `select`, which may be the whole tree."""
    if select is tree:
        return worked_out
    select.replace(worked_out)
    return tree


def _work_out_mixed_groups(tree: exp.Expression) -> exp.Expression:
    """Work out each grouped SELECT whose output mixes an aggregate with its group's own
    column, such as CASE WHEN job_id = 3 THEN 1000 ELSE COUNT(*) END, in two steps: the group's
    columns and each aggregate under a name of its own, then the output from them.

    sqlglot's executor reads the group's column wrong beside an aggregate in one output, giving
    every row the aggregate's branch, without a word: a value typed over a formula, converted,
    is written so.
    """
    for number, select in enumerate(reversed(list(tree.find_all(exp.Select)))):
        if select.args.get("group") is None:
            continue
        if not any(_mixes_a_group(output) for output in select.expressions):
            continue
        # A name of its own for each, since the executor keeps one step of each name.
        tree = _in_place_of(tree, select, _grouped_in_two_steps(select, f"_grouped_{number}"))
    return tree


def _mixes_a_group(output: exp.Expression) -> bool:
    """Whether an output holds an aggregate and, outside any aggregate, a column."""
    return output.find(exp.AggFunc) is not None and any(
        column.find_ancestor(exp.AggFunc) is None for column in output.find_all(exp.Column))


class _GroupPart(NamedTuple):
    """A column a grouped SELECT groups by, or an aggregate it gives, under its own name."""

    name: str
    part: exp.Expression


def _parts_of_the_group(select: exp.Select) -> dict[exp.Expression, _GroupPart]:
    """Each column a grouped SELECT groups by and each aggregate its outputs hold, by its node,
    which is equal to any node written the same."""
    parts = {}
    for number, key in enumerate(select.args["group"].expressions):
        parts[key] = _GroupPart(f"_group_{number}", key)
    for output in select.expressions:
        for aggregate in output.find_all(exp.AggFunc):
            if aggregate not in parts and aggregate.find_ancestor(exp.AggFunc) is None:
                parts[aggregate] = _GroupPart(f"_aggregate_{len(parts)}", aggregate)
    return parts


def _grouped_in_two_steps(select: exp.Select, name: str) -> exp.Select:
    """A grouped SELECT as two: an inner one, named `name`, giving the group's columns and each
    aggregate under a name of its own, and an outer one giving the outputs from those names."""
    parts = _parts_of_the_group(select)
    inner = select.copy()
    inner.set("expressions", [exp.alias_(each.part.copy(), each.name)
                              for each in parts.values()])
    for clause in ("order", "limit"):
        inner.set(clause, None)

    def by_its_name(node: exp.Expression) -> exp.Expression:
        if isinstance(node, (exp.AggFunc, exp.Column)) and node in parts:
            return exp.column(parts[node].name)
        return node

    outer = exp.select(*_outputs_rewritten(select, by_its_name)).from_(
        _named_subquery(inner, name))
    for clause in ("order", "limit"):
        if select.args.get(clause) is not None:
            outer.set(clause, select.args[clause].copy().transform(by_its_name))
    return outer


def _make_casts_plain(tree: exp.Expression) -> exp.Expression:
    """Make each CAST to text a plain one, which is all sqlglot's executor knows.

    sqlglot reads Hive's CAST as a TRY_CAST, since Hive gives NULL for a value it can't cast.
    Any value can be made text, so a CAST to text is the same plain, and the executor gets as
    far as what it really lacks, such as month_start's TRUNC. A CAST to any other type stays
    as it is, so the executor says it has no CAST rather than failing on a value Hive makes
    NULL.
    """
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
        raise MissingPart(f"LIKE with a % or _ in the middle ({pattern!r})")
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
    found = re.search(r"name '(\w+)' is not defined", error)
    if found is not None:
        for function in tree.find_all(exp.Func):
            if function.key.upper() == found.group(1):
                return sql_text(function).split("(")[0]
    return None



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
    real = executed.Table.add_columns

    def add_columns(table: executed.Table, *columns: str) -> None:
        table.columns += columns
        table.reader = executed.RowReader(table.columns, table.column_range)

    executed.Table.add_columns = add_columns
    try:
        yield
    finally:
        executed.Table.add_columns = real


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
    """A window, as it is worked out here: its function, by sqlglot's name; where
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
    if not tree.find(exp.Window):
        return tree
    tree = qualified_hive(tree, schema)  # each * as its columns, each named
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
    answer = exp.select(*outputs).from_(exp.table_(name, db=MADE_TABLES, alias=name))
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
            raise MissingPart("window outside SELECT's columns, such as one in ORDER BY: "
                              "work it out in SELECT, named with AS, and order by that name")


def _add_made_table(name: str, columns: list[str], given: list[list[object]],
                    schema: dict[str, dict[str, dict[str, str]]],
                    rows: dict[str, dict[str, list[dict[str, object]]]]) -> None:
    """Add the table `name`, of the rows `given`, to `schema` and `rows`, in MADE_TABLES, each
    column's type from its values."""
    made_columns = {}
    for place, column in enumerate(columns):
        made_columns[column] = _kind_of([row[place] for row in given])
    schema.setdefault(MADE_TABLES, {})[name] = made_columns
    rows.setdefault(MADE_TABLES, {})[name] = [dict(zip(columns, row)) for row in given]


def _order_after(query: exp.Select, value: Callable[[exp.Expression], exp.Column]
                 ) -> exp.Order | None:
    """A SELECT's ORDER BY, to sort the rows once its windows are worked out: a column it gives
    by name, as itself, and anything else read by `value`."""
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
    where it can't be worked out here."""
    function = window.this
    kind = type(function).__name__
    if isinstance(function, exp.Count) and isinstance(function.this, exp.Distinct):
        raise MissingPart("COUNT(DISTINCT ...) over a window")
    if isinstance(function, (exp.IgnoreNulls, exp.RespectNulls)):
        raise MissingPart("IGNORE NULLS or RESPECT NULLS in a window")
    if kind not in _PLACES | set(_A_PLACE_AWAY) | _OVER_ROWS:
        if isinstance(function, exp.Anonymous):
            named = function.name.upper()
        elif isinstance(function, exp.Func):
            named = function.sql_name()
        else:
            named = function.key.upper()
        raise MissingPart(f"window function {named}")
    spec = window.args.get("spec")
    if spec is not None and (spec.args.get("kind") or "").upper() == "RANGE" and any(
            isinstance(spec.args.get(end), exp.Expression) for end in ("start", "end")):
        raise MissingPart("window over RANGE with a number of rows, such as RANGE "
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
        raise NtileWithNoParts(parts)
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
    if not tree.find(exp.Union, exp.Intersect, exp.Except):
        return tree
    tree = optimized_hive(tree, schema)
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


def reason_without_place(error: Exception) -> str:
    """The first line of what sqlglot said, without where it stopped ("Line 1, Col: 45.")."""
    reason = (str(error).strip().splitlines() or [type(error).__name__])[0]
    return re.sub(r"\s*Line:? \d+, Col: \d+\.?$", "", reason).rstrip(".")


def _check_parts_it_runs_right(tree: exp.Expression) -> None:
    """Stop with a MissingPart at a part of Hive the executor hasn't got, or would run wrong
    without a word."""
    # The executor would run a LEFT SEMI JOIN as a LEFT JOIN, repeating and keeping rows.
    if any(join.kind == "SEMI" for join in tree.find_all(exp.Join)):
        raise MissingPart("LEFT SEMI JOIN")
    # Its executor runs a LATERAL VIEW as a join it can't finish, as an Unchecked derived table
    # may hold.
    if tree.find(exp.Lateral):
        raise MissingPart("LATERAL VIEW")
