"""Running: turn a Statement into Hive, send it, split it by day, and set the load limits.

run(s, send=...) is the only way the Toolbox reaches the query API, and `send` is your own
function: it takes a Hive string and returns a DataFrame. Connection, retries and saving
CSVs stay in it. The Toolbox never imports it.
"""

from __future__ import annotations

import inspect
import textwrap
from typing import NamedTuple

from . import edition
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
from .joins import HOW, anti_join_tests, broadcast
from .keys import writes_one_day
from .refusals import (
    guard_by_day_grouping,
    guard_by_day_limit,
    guard_by_day_stack,
    guard_by_day_window,
    guard_kept_day_in_a_whole_table_write,
    guard_kept_day_without_window,
    guard_one_day_per_write,
    load_limit_dates,
    load_limit_rows,
    refuse,
    refuse_what_isnt_a_dataframe,
)
from .stacking import STACK_HOW, nth, stack_steps, stacked
from .tables import Table, aliased, as_date, day_text, source, table_node
from .trees import Node, combined, has_window
from .unchecked import (
    SHIPPED,
    SessionSettings,
    UncheckedStatement,
    logged_run,
    settings_text,
    unchecked_call,
    unchecked_text,
)
from .windows import call_of

TOOLBOX_VERSION = "5.1"

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
            refuse(
                what=f"set_load_limits({name}={value!r}): a limit must be a whole number, "
                "1 or more, or None for no limit.",
                why="It is a count of rows or days.",
                fix=f"Write it like set_load_limits({name}=100000), or leave it out.",
                error=ValueError,
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
    """One join clause, as Hive writes it: an ANTI_JOIN as a LEFT JOIN."""
    return Node("Join", how=HOW[read._name], this=source(read.table),
                on=None if read.on is None else read.on._tree.copy())


def _all_of(conditions: list, more: list | None = None) -> Node | None:
    """The conditions of WHERE or HAVING, then any `more` trees, joined with AND, or None when
    there are none."""
    trees = [c._tree.copy() for c in conditions] + (more or [])
    return combined("And", trees) if trees else None


def _select_tree(s: Statement, order: list[str] | None = None) -> Node:
    """A Statement's SELECT, from FROM to LIMIT, without WITH. `order` puts its outputs in the
    order of those names, as a Stack puts each Statement's in its first one's order."""
    outputs = s._outputs
    if s._write is not None:
        # The table's columns in its order, then the Partitions its rows fill, which Hive
        # fills from the last columns.
        later = s._write._partitioned_by
        # A write's own order wins over `order`: a write is never stacked.
        order = [column for column in s._write._columns if column not in later] + later
    if order is not None:
        outputs = sorted(outputs, key=lambda output: order.index(output[1]))
    return Node(
        "Select",
        outputs=[_output(column, name) for column, name in outputs],
        distinct=s._distinct,
        broadcast=broadcast(s),
        source=source(s._reads[0].table),
        joins=[_join_tree(read) for read in s._reads[1:]],
        # Each ANTI_JOIN keeps the rows whose matched column is NULL.
        where=_all_of(s._where, anti_join_tests(s)),
        group_by=[c._tree.copy() for c in s._group_by],
        grouping_sets=None if s._grouping_sets is None else [
            Node("Tuple", expressions=[c._tree.copy() for c in each])
            for each in s._grouping_sets],
        having=_all_of(s._having),
        order_by=[o.copy() for o in s._order_by],
        limit=s._limit,
    )


def _query_tree(s: Statement) -> Node:
    """A Statement that reads, without WITH: its SELECT, or a Stack of its Statements' SELECTs,
    each with its columns in the first one's order."""
    if s._stack is None:
        return _select_tree(s)
    call, branches = s._stack
    names = [name for _, name in s._outputs]
    return Node("Stack", how=STACK_HOW[call],
                branches=[_select_tree(b, names) for b in branches])


def _with(tree: Node, s: Statement) -> Node:
    """Put each Derived table the Statement reads at the top, as WITH name AS (...)."""
    tree.set("derived_tables", [Node("CTE", this=_query_tree(table._statement),
                                     alias=table._name) for table in derived_tables(s)])
    return tree


def automatic_limit(s: Statement) -> int | None:
    """The automatic LIMIT this Statement gets when sent, if any."""
    if s._write is not None or s._limit is not None or s._returns_all_rows:
        return None
    return _limits["rows"]


def statements_within(s: Statement) -> list[Statement]:
    """Every step of `s` that reads tables: itself and each Derived table it reads, or, for a
    Stack, each Statement it stacks."""
    return [part for step in [s] + [table._statement for table in derived_tables(s)]
            for part in stack_steps(step)]


def _days_read(s: Statement) -> list:
    """Each read of a partitioned table, at every step, with the days it reads."""
    return [found for step in statements_within(s) for found in read_spans(step)]


def _check_dates_cap(s: Statement) -> None:
    cap = _limits["dates"]
    if cap is None:
        return
    from_reads = [read for read, _ in bottom_reads(s)]
    for read, span in _days_read(s):
        if span is not None and span.is_bounded():
            load_limit_dates(read._call(), read.table._name, len(span.dates()), cap,
                             read.reads_all_partitions, any(read is r for r in from_reads))


def steps(s: Statement) -> list[tuple[Statement, str]]:
    """The Statement and each Derived table below it through FROM, top first, each with the
    words a refusal names it by. The last reads a real table in FROM: the one with the days;
    or it is a Stack, whose Statements each read one."""
    found = [(s, "the outer Statement")]
    while found[-1][0]._stack is None and found[-1][0]._reads[0].table._statement is not None:
        table = found[-1][0]._reads[0].table
        found.append((table._statement, f"derived({table._name!r}, ...)"))
    if len(found) == 1:
        found[0] = (s, "it")
    return found


def bottom_steps(s: Statement) -> list[Statement]:
    """The step at the bottom of `s` through FROM, which reads a real table there; below a
    Stack, the bottom step of each Statement it stacks."""
    step = steps(s)[-1][0]
    if step._stack is not None:
        return [found for branch in step._stack[1] for found in bottom_steps(branch)]
    return [step]


def bottom_reads(s: Statement) -> list:
    """Each FROM read at the bottom of `s`, following Derived tables down, with the days its
    bound reads: a Span, or None. There is one, or one for each Statement a Stack stacks."""
    found = []
    for step in bottom_steps(s):
        read = step._reads[0]
        found.append((read, next((span for r, span in read_spans(step) if r is read), None)))
    return found


def bottom_read(s: Statement):
    """The first of bottom_reads(s): the FROM read the days come from."""
    return bottom_reads(s)[0]


def _bottom_days(s: Statement, who: str, why: str, no_days_fix: str):
    """The real table at the bottom of FROM and the days its bound reads, or a refusal. Below
    a Stack, each of its Statements must read the same days."""
    found = []
    for read, span in bottom_reads(s):
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
            found.append((table, span))
            continue
        refuse(what=f"{who}: {what}.", why=why, fix=fix, error=ValueError)
    if len({tuple(span.dates()) for _, span in found}) > 1:
        listed = "; ".join(f"{table._name} reads {_days_text(table, span)}"
                           for table, span in found)
        refuse(
            what=f"{who}: the Statements of its Stack read different days: {listed}.",
            why=f"{why} Each day's rows come from every Statement of the Stack at once, so "
            "each must read the same days.",
            fix="Bound each Statement's FROM table to the same days in its WHERE.",
            error=ValueError,
        )
    return found[0]


def _days_text(table: Table, span) -> str:
    """The days a span lets through, for a message: each, or the first to the last."""
    days = [day_text(day, table._date_format) for day in span.dates()]
    if len(days) <= 3:
        return ", ".join(days) or "no day"
    return f"{days[0]} to {days[-1]}"


def _written_day(s: Statement):
    """The one day a write covers, from the date bound of the table it reads from, or, when
    it reads several days, as a Window that looks back does, the one a step above keeps."""
    table, span = _bottom_days(
        s, f"{s._write_call} can't tell which day to write",
        "A write fills the one day its FROM table reads.",
        "A Saved table is filled from a table with days: put one in FROM, bounded to one day "
        "in WHERE.")
    days = span.dates()
    if len(days) == 1:
        return days[0]
    windowed = _has_a_window(s)
    kept = _day_kept_above(s) if len(days) > 1 else None
    if kept is not None and not windowed:
        guard_kept_day_without_window(s._write_call, len(days), _column_text(kept.column),
                                      f"{table._alias}.{table._date_partition}")
    if kept is None:
        guard_one_day_per_write(s._write_call, len(days), windowed)
    if kept.day not in days:
        written = [day_text(day, table._date_format) for day in (kept.day, days[0], days[-1])]
        refuse(
            what=f"{s._write_call} keeps {written[0]}, a day its FROM table {table._name} "
            f"doesn't read: its WHERE reads {written[1]} to {written[2]}.",
            why="The write would fill that day with no rows.",
            fix=f"Widen the bound on {table._alias}.{table._date_partition} to take in the day "
            "written and the earlier days it looks back on.",
            error=ValueError,
        )
    return kept.day


class KeptDay(NamedTuple):
    """The one day a step above a write's FROM table keeps: the step, its condition, the day,
    and the column of that step that equals(...) holds to it."""

    step: Statement
    condition: object
    day: object  # a datetime.date
    column: Node


def _has_a_window(s: Statement) -> bool:
    """Whether any step of the Statement works out a Window."""
    return any(has_window(column._tree) for step, _ in steps(s) for column, _ in step._outputs)


def kept_day(s: Statement) -> KeptDay | None:
    """The one day a step above a write's FROM table keeps, with equals(...) of the Date
    partition passed up to it; or None when no step keeps one, or the Statement has no Window.

    A write whose Window looks back on earlier days reads them in a Derived table, and keeps
    the day it writes in a step above that table, as help(window) shows. Only a write with a
    Window may read several days this way: any other write reads the one day it writes.
    """
    return _day_kept_above(s) if _has_a_window(s) else None


def _day_kept_above(s: Statement) -> KeptDay | None:
    """The one day a step above a write's FROM table keeps, Window or not; None when none."""
    found = steps(s)
    if found[-1][0]._stack is not None:
        return None  # a Stack's Statements each read their own days: none is kept above
    table = found[-1][0]._reads[0].table
    if table._date_partition is None:
        return None  # it reads no days, so none is kept
    dates = [Node("Column", name=table._date_partition, table=table._alias)]
    for (step, _), (below, _) in zip(reversed(found[:-1]), reversed(found[1:])):
        dates = _dates_above(below, step._reads[0].table, dates)
        for condition in step._where:
            column_and_day = _day_of(condition._tree, dates,
                                     getattr(table, table._date_partition))
            if column_and_day is not None:
                column, day = column_and_day
                return KeptDay(step, condition, day, column)
    return None


def _day_of(tree: Node, dates: list, partition):
    """The column of `dates` an equals(...) holds to a day, and that day as a Python date, or
    None. `partition` is the Date partition they carry up, whose Table reference says how its
    days are written."""
    if tree.kind != "EQ":
        return None
    sides = (tree.parts["this"], tree.parts["expression"])
    for column, value in (sides, sides[::-1]):
        if column in dates and value.kind == "Literal" and value.parts.get("is_string"):
            return column, as_date(value.parts["this"], partition, "equals(...)")
    return None


def _column_text(column: Node) -> str:
    """A column as the user writes it, such as finishes.dt."""
    return f"{column.table}.{column.name}" if column.table else column.name


def day_partition(table: Table, day: str) -> Node:
    """PARTITION(dt = '<day>', region): the day named, written as the table writes its days,
    then each Partition after it by its column alone, for every value it holds."""
    return Node("Partition", expressions=[
        Node("EQ", this=Node("Column", name=table._date_partition),
             expression=Node("Literal", this=day, is_string=True)),
        *[Node("Column", name=column) for column in table._partitioned_by],
    ])


def _write_tree(s: Statement) -> Node:
    """INSERT OVERWRITE or INSERT INTO the one day the Statement reads, then its SELECT; or
    the whole table, for a Saved table with no Date partition.

    The day is named; each Partition after it is filled from the rows, by its column."""
    table = s._write
    partition = None
    if writes_one_day(s):
        partition = day_partition(table, day_text(_written_day(s), table._date_format))
    else:
        kept = _day_kept_above(s)
        if kept is not None:
            guard_kept_day_in_a_whole_table_write(s._write_call, table._name,
                                                  _column_text(kept.column))
    return Node("Insert", target=table_node(table._name, partition=partition),
                select=_select_tree(s), overwrite=s._replaces_day)


def _statement_tree(s: Statement) -> Node:
    """The whole tree to_hive writes: CREATE or DROP, a write, or a SELECT."""
    if s._ddl is not None:
        return s._ddl.copy()
    if s._write is not None:
        return _with(_write_tree(s), s)
    tree = _query_tree(s)
    limit = automatic_limit(s)
    if limit is not None:
        tree.set("limit", limit)
    return _with(tree, s)


def _self_check(text: str) -> None:
    """The Hive must read back as the same text (edition.read_back), or nothing is sent."""
    again = edition.read_back(text)
    if again != text:
        raise RuntimeError(
            f"{edition.FOLDER} wrote Hive that doesn't read back the same. This is a bug in the "
            "Toolbox, not in your Statement: nothing was sent. Please report it with the "
            f"Statement that caused it.\n\nWritten:\n{text}\n\nRead back:\n{again}"
        )


def to_hive(s):
    """The Hive string for a Statement, ready to send.

    It checks itself by reading the string back, and refuses what would read too many days
    (see set_load_limits) or write more than one day. An Admin statement, from the admin
    module, is checked by the function that made it instead: no Load limit applies to it, so
    the move's comparison reads every day, and an ALTER TABLE it writes isn't read back. The
    Hive may write a function
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
    if isinstance(s, SessionSettings):
        return "\n".join(s._lines)
    if isinstance(s, UncheckedStatement):
        return s._text
    _need_statement(s, "to_hive", inspect.currentframe().f_back,
                    why="to_hive writes the Hive of one Statement made by statement(...).")
    if s._admin_hive is not None:
        # An ALTER TABLE, which the admin module writes from pieces the Edition wrote and
        # checked: not a tree the Edition reads back.
        return s._admin_hive
    if s._ddl is None:
        _check_dates_cap(s)
    text = edition.hive_statement(_statement_tree(s))
    _self_check(text)
    return text


def _need_statement(s, call: str, frame, why: str, more: str = "") -> None:
    """Refuse what isn't a Statement, in the name of `call`, the function it was given to.

    `frame` is the caller's, so the usual fix can name their own variable: a Derived table is
    wrapped in a Statement that reads it, and a list is sent one Statement at a time. `more`
    is what the fix's call takes after the Statement, such as ", send=...".
    """
    if isinstance(s, Statement):
        return
    name = name_in(frame, s) if frame is not None else None
    if isinstance(s, Table) and s._statement is not None:
        d = name or "d"
        fix = (f"A Derived table is a step for another Statement to read, so wrap it in the "
               f"smallest Statement that reads it: {call}(statement(SELECT(all_columns({d})), "
               f"FROM({d})){more})" + ("." if name else ", where d is the Derived table."))
    elif isinstance(s, (list, tuple)):
        fix = (f"Pass its Statements one at a time, with a loop: for step in "
               f"{name or 'steps'}: {call}(step{more}).")
    elif isinstance(s, str):
        fix = (f"Pass the Statement itself, made by statement(...): {call} writes its Hive "
               "for you.")
    else:
        fix = "Pass statement(SELECT(...), FROM(...), ...)."
    refuse(what=f"{call} was given {s!r}, which isn't a Statement.", why=why, fix=fix,
           given=s, call=call)


def name_in(frame, value) -> str | None:
    """The caller's variable name for `value`, found by identity, or None if it has none."""
    return next((name for scope in (frame.f_locals, frame.f_globals)
                 for name, held in scope.items()
                 if held is value and not name.startswith("_")), None)


def settings_needed(s: Statement) -> list[str]:
    """The lines show_hive prints ahead of a Statement: a note and the SET lines of the
    Session setting it needs, or none. A write that fills Partitions after the day from its
    rows needs Hive's dynamic partitioning, the shipped set "dynamic_partitions", which the
    user sends with run(hive_settings("dynamic_partitions"), send=...). run sends the
    Statement alone."""
    if s._ddl is not None or s._write is None or not s._write._partitioned_by:
        return []
    filled = ", ".join(s._write._partitioned_by)
    return [f'-- The Session setting "dynamic_partitions": this write fills {filled} from its '
            "rows."] + [f"SET {name}={value};" for name, value in SHIPPED["dynamic_partitions"].items()]


def admin_notes(s: Statement) -> list[str]:
    """The comment lines show_hive prints ahead of an Admin statement: what it changes, what
    can't be undone, and what to check first, each item wrapped on lines starting --."""
    lines = []
    for item in s._admin_about:
        lines += ["-- " + line for line in textwrap.wrap(item, width=_NOTE_WIDTH)]
    return lines


# How wide an Admin statement's notes are, after the -- that starts each line.
_NOTE_WIDTH = 90


class HiveText(str):
    """The Hive show_hive printed, kept as text. In a notebook it isn't shown a second time."""

    def _ipython_display_(self) -> None:
        pass  # show_hive has printed it already


class HivePlan(str):
    """The plan run(explain(s), send=...) gives back, as text. In a notebook it is printed,
    line by line, rather than shown as one string."""

    def _ipython_display_(self) -> None:
        print(self)


def _plan(result) -> HivePlan:
    """The plan an EXPLAIN's send gave back, as one text: Hive gives each line of it as a row,
    and Spark the whole plan in one row, in the DataFrame's only column."""
    refuse_what_isnt_a_dataframe(result)
    lines = [str(line) for line in result.iloc[:, 0]] if len(result.columns) else []
    return HivePlan("\n".join(lines).rstrip())


def show_hive(*statements):
    """Print the Hive that runs, ready to paste into another program, and return it.

    Each Statement's Hive is exactly what to_hive gives and run sends, with a ; added at the
    end, which a program such as Hue, DBeaver or spark-sql needs between Statements; run sends
    it without one. Pass several Statements, or a list such as by_day(...) gives, and each is
    headed by a comment: its number, and the name of the variable it is in, such as
    -- 1 of 2: failed_runs, or, for one in a list, days[0]. It refuses whatever to_hive would.
    A write that fills Partitions from its rows, into a table with partitioned_by=, is printed
    after the Session setting it needs: a line saying so, then its SET lines, which run
    doesn't send with it: send them first with run(hive_settings("dynamic_partitions"),
    send=...). An Admin statement, from the admin module, is printed after comment lines
    saying what it changes, what can't be undone, and what to check first.

    It returns the same text, so `text = show_hive(...)` keeps it to use or save. In a
    notebook, show_hive(...) on its own shows the Hive once.

    >>> failed_runs = statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
    ... )
    >>> text = show_hive(failed_runs)
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24' AND job_runs.status = 'FAILED';
    >>> every_run = statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24")),
    ... )
    >>> text = show_hive(failed_runs, every_run)
    -- 1 of 2: failed_runs
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24' AND job_runs.status = 'FAILED';
    <BLANKLINE>
    -- 2 of 2: every_run
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24';
    """
    frame = inspect.currentframe().f_back
    named = []
    for given in statements:
        if not isinstance(given, list):
            named.append((name_in(frame, given), given))
            continue
        list_name = name_in(frame, given)
        for index, s in enumerate(given):
            if isinstance(s, list):
                refuse(
                    what="show_hive was given a list inside a list.",
                    why="It takes Statements, or one list of them, such as by_day(...) gives.",
                    fix="Pass the inner lists one by one, as show_hive(first, second), or put "
                    "their Statements in one list.",
                )
            own = name_in(frame, s) or (f"{list_name}[{index}]" if list_name else None)
            named.append((own, s))
    if not named:
        refuse(
            what="show_hive() was given no Statement.",
            why="It prints the Hive of the Statements it is given.",
            fix="Pass one or more Statements, such as show_hive(weekly), or a list of them.",
        )
    texts = []
    for position, (name, s) in enumerate(named, start=1):
        if isinstance(s, SessionSettings):
            hive = settings_text(s)
        elif isinstance(s, UncheckedStatement):
            hive = unchecked_text(s)
        else:
            _need_statement(s, "show_hive", frame,
                            why="show_hive prints the Hive of Statements made by "
                            "statement(...).")
            hive = "\n".join([*settings_needed(s), *admin_notes(s), to_hive(s) + ";"])
        if len(named) > 1:
            heading = f"-- {position} of {len(named)}" + (f": {name}" if name else "")
            hive = f"{heading}\n{hive}"
        texts.append(hive)
    text = "\n\n".join(texts)
    print(text)
    return HiveText(text)


def run(s, send):
    """Send a Statement's Hive through your `send` function and return what comes back.

    `send` is your own function from a Hive string to a pandas DataFrame. At work it calls
    the query API, or, where your notebook runs Spark, is
    lambda hive: spark.sql(hive).toPandas(); example_database.send runs the Example database
    instead. A write into a table with partitioned_by= needs the Session setting
    "dynamic_partitions" sent first, with run(hive_settings("dynamic_partitions"), send=...),
    as show_hive prints and help(INSERT_OVERWRITE) explains: run sends the write alone. For
    explain(s), run gives back Hive's plan as text, rather than a DataFrame.

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
        refuse(
            what=f"run(..., send={send!r}): send isn't a function.",
            why="run hands the Hive string to your own function, which sends it and "
            "returns a DataFrame.",
            fix="Pass your function itself, without calling it: run(s, send=run_query).",
        )
    if isinstance(s, SessionSettings):
        for line in s._lines:  # Hive takes one SET per call
            send(line)
        return None
    if isinstance(s, UncheckedStatement):
        return logged_run("Unchecked statement", unchecked_call(s), s._text, send)
    _need_statement(s, "run", inspect.currentframe().f_back,
                    why="run writes the Hive of one Statement made by statement(...) and "
                    "sends it.", more=", send=...")
    text = to_hive(s)
    if s._admin_call is not None:
        check = s._admin_check
        sent = send if check is None else (lambda hive: check(send(hive)))
        return logged_run("Admin statement", s._admin_call, text, sent)
    result = send(text)
    if s._ddl is not None and s._ddl.kind == "Explain":
        return _plan(result)
    # A write has already been carried out when its send returns, so only a read's rows matter.
    if s._ddl is None and s._write is None:
        refuse_what_isnt_a_dataframe(result)
    limit = automatic_limit(s) if s._ddl is None else None
    if limit is not None and hasattr(result, "__len__"):
        load_limit_rows(len(result), limit)
    return result


# --- by_day ----------------------------------------------------------------------------------


def _check_splittable(s: Statement, step: str, dates: list, partition: str,
                      lost_in: list) -> None:
    """A step may group or pick rows only if it keeps the Date partition, and may have no
    LIMIT.

    `dates` holds the Date partition as this step sees it, under each name the step below
    gave it; `partition` is the Date partition at the bottom step, and `lost_in` lists the
    step that dropped it, if one did, then each step above that one.
    """
    if s._limit is not None:
        guard_by_day_limit(step, s._limit)
    if s._distinct:
        grouping, clause = [column._tree for column, _ in s._outputs], "SELECT_DISTINCT(...)"
    elif s._group_by or any(column._aggregate for column, _ in s._outputs):
        # With subtotals, only a column in every set of them is in every row's group.
        grouping = [column._tree for column in s._group_by if s._grouping_sets is None or all(
            any(column._tree == other._tree for other in each) for each in s._grouping_sets)]
        clause = "GROUP_BY(...)"
        if s._grouping_sets is not None:
            clause = (f"GROUP_BY(...) as a plain column before {s._subtotals_call}, taking it "
                      "out of the subtotals if it is in them, so that each subtotal stays "
                      "within one day")
    else:
        grouping, clause = None, ""
    if grouping is not None and not any(date in grouping for date in dates):
        _refuse_grouping(step, dates, partition, lost_in, clause)
    for column, _ in s._outputs:
        for window in column._tree.find_all("Window"):
            if not any(date in window.parts["partition_by"] for date in dates):
                call = call_of(window)
                _refuse_grouping(step, dates, partition, lost_in,
                                 f"PARTITION_BY= of {call}", window=call)


def _refuse_grouping(step: str, dates: list, partition: str, lost_in: list, clause: str,
                     window: str | None = None):
    """Refuse a step for leaving the Date partition out of `clause`, naming it as the step
    sees it, or saying where to keep it when a step below dropped it. `window` is the call of
    a Window that looks across days, such as lag(...), when that is what leaves it out."""
    if not dates:
        by, between = lost_in[0], lost_in[1:]
        also = ""
        if between:
            reads = "reads" if len(between) == 1 else "read"
            also = f", and in {' and '.join(between)}, which {reads} it"
        keeping = f"the Date partition {partition}"
        add = f"Keep {partition} in the SELECT of {by}{also}, then add it to {clause} here"
    else:
        name = f"{dates[0].table}.{dates[0].name}"
        keeping = (f"the Date partition {partition}" if name == partition
                   else f"{name} ({partition}, the Date partition)")
        add = f"Add {name} to {clause}"
    if window is not None:
        guard_by_day_window(window, step, keeping, add)
    guard_by_day_grouping(step, keeping, add)


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
        refuse(
            what=f"by_day was given {s!r}, which isn't a Statement that reads a table.",
            why="It splits a Statement's days.",
            fix="Pass statement(SELECT(...), FROM(...), WHERE(...)).",
            given=s, call="by_day",
        )
    if s._write is not None and not writes_one_day(s):
        refuse(
            what=f"by_day can't split this Statement: {s._write_call} writes "
            f"{s._write._name}, which has no Date partition.",
            why="A write into a table with no days fills the whole table at once, from all the "
            "rows its Statement reads, so it is sent whole, not a day at a time.",
            fix="Send it whole, with run(s, send=...).",
            error=ValueError,
        )
    table, span = _bottom_days(
        s, "by_day can't split this Statement",
        "by_day makes one Statement for each day its FROM table reads.",
        "Run it whole with run(...): by_day splits only a table with days.")
    _day_names(s)
    days = span.dates()
    if not days:
        refuse(
            what=f"by_day can't split this Statement: its WHERE leaves no day of "
            f"{table._alias}.{table._date_partition} to read.",
            why="No day is inside every bound, so there would be no Statement to send, "
            "and nothing would be read or written.",
            fix="Check the days in its WHERE: a low end may be later than a high end, "
            "as at_least's day after at_most's, or not_equals or is_not_in may leave "
            "out the only day.",
            error=ValueError,
        )
    return [_split(s, day) for day in days]


def _day_names(s: Statement, top: str | None = None) -> list[str]:
    """Check that each step of `s` can be split by day, bottom first, following the Date
    partition up under each name a step gives it, and give the names of the outputs of `s`
    that hold it. `top` names `s` in a refusal, for a Statement a Stack stacks."""
    found = steps(s)
    if top is not None:
        found[0] = (s, top)
    read, _ = bottom_read(s)
    partition = f"{read.table._alias}.{read.table._date_partition}"
    lost_in = []  # the step that dropped the Date partition, then each step above that one
    last, last_described = found[-1]
    if last._stack is not None:
        # A Stack has no FROM: the day is each column every Statement it stacks has it in.
        dates = [Node("Column", name=name) for name in _stack_day_names(last, last_described)]
        lost_in = [] if dates else [last_described]
        above, below, below_described = found[:-1], last, last_described
    else:
        dates = [Node("Column", name=read.table._date_partition, table=read.table._alias)]
        above, below, below_described = found, None, ""
    for step, described in reversed(above):
        if below is not None:
            had_it = bool(dates)
            dates = _dates_above(below, step._reads[0].table, dates)
            if not dates:
                lost_in = [below_described] if had_it else [*lost_in, below_described]
        _check_splittable(step, described, dates, partition, lost_in)
        below, below_described = step, described
    return [name for column, name in s._outputs if column._tree in dates]


def _stack_day_names(stack: Statement, described: str) -> list[str]:
    """The names a Stack's Statements each give the day, once each is checked. UNION, INTERSECT
    and EXCEPT need one: they compare rows over every day they read."""
    call, branches = stack._stack
    each = [set(_day_names(branch, f"the {nth(number)} Statement of {call}(...)"))
            for number, branch in enumerate(branches, start=1)]
    names = [name for _, name in stack._outputs if all(name in found for found in each)]
    if not names and call != "UNION_ALL":
        guard_by_day_stack(described, call)
    return names


def _split(s: Statement, day) -> Statement:
    """The Statement for one day: the bottom step bounded to it, or each Statement of a Stack
    at the bottom, and each step above reading it."""
    found = steps(s)
    last = found[-1][0]
    if last._stack is not None:
        call, branches = last._stack
        bottom = stacked(call, [_split(branch, day) for branch in branches],
                         last._returns_all_rows)
    else:
        bottom = _one_day(last, day)
    for step, _ in reversed(found[:-1]):
        old = step._reads[0].table
        new = derived(old._name, bottom)
        if old._alias != old._name:
            new = aliased(new, old._alias)
        bottom = _reading(step, new)
    return bottom


__all__ = ["to_hive", "run", "by_day", "set_load_limits"]
