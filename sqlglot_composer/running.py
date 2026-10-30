"""Running: turn a Statement into Hive, send it, and set the load limit on rows.

run_query(s, query) and run_execute(s, execute) are how a Statement reaches the warehouse,
through your own two functions: `query` takes a Hive string and gives back a DataFrame,
`execute` takes one and gives back nothing. You choose which by the one you call. Connection,
retries and saving CSVs stay in them. The Toolbox never imports them.
"""

from __future__ import annotations

import inspect
import textwrap
from collections.abc import Callable
from types import FrameType
from typing import NoReturn

import pandas as pd

from . import _FOLDER, kinds, writing
from .clauses import Clause, Statement, derived_tables, stack_steps
from .conditions import Condition
from .joins import HOW, anti_join_tests, broadcast
from .python_steps import PythonStep, python_step_text
from .refusals import (
    arguments_of,
    is_count,
    load_limit_rows,
    need_warehouse_call,
    refuse,
    refuse_removed_arguments,
    refuse_what_isnt_a_dataframe,
)
from .stacking import STACK_HOW
from .tables import Column, Table, is_unchecked, python_text, source, table_node
from .trees import Node, combined, unchecked_calls
from .unchecked import (
    SHIPPED,
    SessionSettings,
    UncheckedStatement,
    logged_run,
    settings_text,
    unchecked_call,
    unchecked_text,
)

# The seam that ships switched off. set_load_limits(...) switches it on.
_limits = {"rows": None}


def set_load_limits(rows: int | None = None, **removed: object) -> dict[str, int | None]:
    """Switch on an automatic LIMIT for every Statement that reads; it starts off.

    >>> set_load_limits(rows=100000)
    {'rows': 100000}
    >>> set_load_limits()
    {'rows': None}

    Call it from your own notebook, since the Toolbox folder is replaced on each update.
    `rows` adds LIMIT rows to every Statement that has no LIMIT of its own, and run_query(...)
    refuses a result that fills it, since it was probably cut short. Left out, there is no
    limit, so set_load_limits() switches it off. It returns the limits now in force.
    """
    if "dates" in removed:
        refuse(
            what="set_load_limits was given dates=, which Toolbox 7.0 took out.",
            why="A table's Partitions are its own, of any kind, so there is no count of days "
            "to cap. A read of a partitioned table must still filter one of its partition "
            "columns.",
            fix=f"Leave dates= out: it takes {arguments_of(set_load_limits)}, and nothing else.",
        )
    refuse_removed_arguments("set_load_limits", removed, set_load_limits)
    if rows is not None and not is_count(rows):
        refuse(
            what=f"set_load_limits(rows={rows!r}): a limit must be a whole number, 1 or more, "
            "or None for no limit.",
            why="It is a count of rows.",
            fix="Write it like set_load_limits(rows=100000), or leave it out.",
            error=ValueError,
        )
    _limits["rows"] = rows
    return dict(_limits)


# --- Building the Hive -----------------------------------------------------------------------


def _output(column: Column, name: str) -> Node:
    """One SELECT entry: the column as it is, or with AS name when the name differs."""
    if column._name == name and column._table is not None:
        return column._tree.copy()
    return Node("Alias", this=column._tree.copy(), alias=name)


def _join_tree(read: Clause) -> Node:
    """One join clause, as Hive writes it: an ANTI_JOIN as a LEFT JOIN."""
    return Node("Join", how=HOW[read._name], this=source(read.table),
                on=None if read.on is None else read.on._tree.copy())


def _all_of(conditions: list[Condition], more: list[Node] | None = None) -> Node | None:
    """The conditions of WHERE or HAVING, then any `more` trees, joined with AND, or None when
    there are none."""
    trees = [c._tree.copy() for c in conditions] + (more or [])
    return combined("And", trees) if trees else None


def _select_tree(s: Statement, order: list[str] | None = None) -> Node:
    """A Statement's SELECT, from FROM to LIMIT, without WITH. `order` puts its outputs in the
    order of those names, as a Stack puts each Statement's in its first one's order."""
    outputs = s._outputs
    if kinds.kind(s) == kinds.WRITE:
        # The table's columns in its order, then the partition columns its rows fill, which
        # Hive fills from the last columns; partition={...} gives the others their values.
        partitioned_by = s._write._partitioned_by
        later = [column for column in partitioned_by if column not in s._partitions.values]
        # A write's own order wins over `order`: a write is never stacked.
        order = [column for column in s._write._columns if column not in partitioned_by] + later
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
    tree.set("derived_tables", [Node("CTE", this=_derived_tree(table), alias=table._name)
                                for table in derived_tables(s)])
    return tree


def _derived_tree(table: Table) -> Node:
    """A Derived table's query: its Statement's, or an Unchecked derived table's text, noted
    with the call that made it."""
    if not is_unchecked(table):
        return _query_tree(table._statement)
    node = Node("UncheckedSelect", text=table._statement._text)
    node.meta["call"] = f"unchecked_derived({python_text(table._name)}, ...)"
    return node


def automatic_limit(s: Statement) -> int | None:
    """The automatic LIMIT this Statement gets when sent, if any."""
    if kinds.kind(s) == kinds.WRITE or s._limit is not None or s._returns_all_rows:
        return None
    return _limits["rows"]


def statements_within(s: Statement) -> list[Statement]:
    """Every step of `s` that reads tables: itself and each Derived table it reads, or, for a
    Stack, each Statement it stacks. An Unchecked derived table has no Statement: its text
    is Hive written by hand."""
    return [part for step in [s] + [table._statement for table in derived_tables(s)
                                    if not is_unchecked(table)]
            for part in stack_steps(step)]


def _write_tree(s: Statement) -> Node:
    """INSERT OVERWRITE or INSERT INTO the Saved table, then its SELECT: into the Partitions
    its rows fill, and those partition={...} names, or the whole of a table that isn't
    partitioned."""
    partition = s._partitions.tree
    target = table_node(s._write._name, partition=None if partition is None else partition.copy())
    return Node("Insert", target=target, select=_select_tree(s), overwrite=s._replaces_rows)


def statement_tree(s: Statement) -> Node:
    """The whole tree to_hive writes: CREATE or DROP, a write, or a SELECT."""
    if not kinds.is_a_query(s):
        return s._ddl.copy()
    if kinds.kind(s) == kinds.WRITE:
        return _with(_write_tree(s), s)
    tree = _query_tree(s)
    limit = automatic_limit(s)
    if limit is not None:
        tree.set("limit", limit)
    return _with(tree, s)


def _self_check(text: str) -> None:
    """The Hive must read back as the same text (writing.read_back), or nothing is sent."""
    again = writing.read_back(text)
    if again != text:
        raise RuntimeError(
            f"{_FOLDER} wrote Hive that doesn't read back the same. This is a bug in the "
            "Toolbox, not in your Statement: nothing was sent. Please report it with the "
            f"Statement that caused it.\n\nWritten:\n{text}\n\nRead back:\n{again}"
        )


def to_hive(s: Statement | SessionSettings | UncheckedStatement | PythonStep) -> str:
    """The Hive string for a Statement, ready to send.

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

    It checks itself by reading the string back. An Admin statement, from the admin module, is
    checked by the function that made it instead: an ALTER TABLE it writes isn't read back.
    The Hive may write a function
    differently from how you would by hand, for example DATE_SUB(dt, 7) as
    DATE_ADD(dt, 7 * -1), which means the same. Given Session settings, it gives their SET
    lines, one to a line; given an Unchecked statement, its text as you wrote it. A Python
    step has no Hive, so it is refused: show_hive prints comment lines saying what it is.
    """
    if kinds.kind(s) == kinds.SETTINGS:
        return "\n".join(s._lines)
    if kinds.kind(s) == kinds.UNCHECKED:
        return s._text
    if kinds.kind(s) == kinds.PYTHON:
        _refuse_a_python_step("to_hive", "It writes the Hive a Statement sends, and a "
                              "Python step has none")
    need_statement(s, "to_hive", inspect.currentframe().f_back,
                    why="to_hive writes the Hive of one Statement made by statement(...).")
    if s._admin_hive is not None:
        # An ALTER TABLE, which the admin module writes from pieces writing.py wrote and
        # checked: not a tree writing.py reads back.
        return s._admin_hive
    text = writing.hive_statement(statement_tree(s))
    _self_check(text)
    return text


def hive_without_automatic_limit(s: Statement) -> str:
    """to_hive's Hive for a read or a write, without the automatic LIMIT that
    set_load_limits(rows=...) adds when it is sent: the rows the Statement itself gives."""
    if automatic_limit(s) is None:
        return to_hive(s)
    text = writing.hive_statement(_with(_query_tree(s), s))
    _self_check(text)
    return text


def need_statement(s: object, call: str, frame: FrameType | None, why: str,
                    more: str = "") -> None:
    """Refuse what isn't a Statement, in the name of `call`, the function it was given to.

    `frame` is the caller's, so the usual fix can name their own variable: a Derived table is
    wrapped in a Statement that reads it, and a list is sent one Statement at a time. `more`
    is what the fix's call takes after the Statement, such as ", query=...". run_execute sends
    only what changes something, so its fixes write the rows into a Saved table instead.
    """
    if isinstance(s, Statement):
        return
    name = name_in(frame, s) if frame is not None else None
    writes = call == "run_execute"
    if isinstance(s, Table) and s._statement is not None:
        d = name or "d"
        reads = (f"statement(INSERT_OVERWRITE(t), SELECT(all_columns({d})), FROM({d}))" if writes
                 else f"statement(SELECT(all_columns({d})), FROM({d}))")
        fix = (f"A Derived table is a step for another Statement to read, so wrap it in the "
               f"smallest Statement that {'writes its rows' if writes else 'reads it'}: "
               f"{call}({reads}{more})" + _where(name is None, writes))
    elif isinstance(s, (list, tuple)):
        fix = (f"Pass its Statements one at a time, with a loop: for step in "
               f"{name or 'steps'}: {call}(step{more}).")
    elif isinstance(s, str):
        fix = (f"Pass the Statement itself, made by statement(...): {call} writes its Hive "
               "for you.")
    elif writes:
        fix = ("Pass a Statement that writes, such as statement(INSERT_OVERWRITE(t), "
               "SELECT(...), FROM(...)).")
    else:
        fix = "Pass statement(SELECT(...), FROM(...), ...)."
    refuse(what=f"{call} was given {s!r}, which isn't a Statement.", why=why, fix=fix,
           given=s, call=call)


def _where(unnamed: bool, writes: bool) -> str:
    """The end of a Derived table's fix: what its d and t stand for, if anything."""
    meant = (["d is the Derived table"] if unnamed else []) + (
        ["t is the Saved table to write"] if writes else [])
    return f", where {' and '.join(meant)}." if meant else "."


def _refuse_a_python_step(call: str, why: str) -> NoReturn:
    """Refuse a Python step given to `call`, which sends or writes Hive: it has none."""
    refuse(
        what=f"{call} was given a Python step, which sends nothing.",
        why=f"{why}: python_step(...) only declares a change you make in Python and save with "
        "your own call, so Lineage can show it. The Toolbox never moves its data.",
        fix="Save the rows with your own call, as you do now, and pass the step to "
        "export_lineage(...) with your Statements. show_hive(step) prints comment lines saying "
        "what it is, and in a Table notebook's write() project.run_tables passes over it.",
    )


def name_in(frame: FrameType, value: object) -> str | None:
    """The caller's variable name for `value`, found by identity, or None if it has none."""
    return next((name for scope in (frame.f_locals, frame.f_globals)
                 for name, held in scope.items()
                 if held is value and not name.startswith("_")), None)


def settings_needed(s: Statement) -> list[str]:
    """The lines show_hive prints ahead of a Statement: a note and the SET lines of the
    Session setting it needs, or none. A write that fills a partition column from its rows,
    one partition={...} doesn't name, needs Hive's dynamic partitioning, the shipped set
    "dynamic_partitions", which the user sends with
    run_execute(hive_settings("dynamic_partitions"), execute). run_execute sends the Statement
    alone."""
    if kinds.kind(s) != kinds.WRITE:
        return []
    filled = ", ".join(column for column in s._write._partitioned_by
                       if column not in s._partitions.values)
    if not filled:
        return []
    return [f'-- The Session setting "dynamic_partitions": this write fills {filled} from its '
            "rows."] + [f"SET {name}={value};"
                        for name, value in SHIPPED["dynamic_partitions"].items()]


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
    """The plan run_query(explain(s), query) gives back, as text. In a notebook it is printed,
    line by line, rather than shown as one string."""

    def _ipython_display_(self) -> None:
        print(self)


def _plan(result: object) -> HivePlan:
    """The plan an EXPLAIN's query gave back, as one text: Hive gives each line of it as a row,
    in the DataFrame's only column."""
    refuse_what_isnt_a_dataframe(result)
    lines = [str(line) for line in result.iloc[:, 0]] if len(result.columns) else []
    return HivePlan("\n".join(lines).rstrip())


def show_hive(*statements: Statement | SessionSettings | UncheckedStatement | PythonStep
              | list[Statement]) -> str:
    """Print the Hive that runs, ready to paste into another program, and return it.

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

    Each Statement's Hive is exactly what to_hive gives and run_query or run_execute sends, with
    a ; added at the end, which a program such as Hue, Beeline or DBeaver needs between
    Statements; they send it without one. Pass several Statements, or a list of them, and each
    is headed by a comment: its number, and the name of the variable it is in, such as
    -- 1 of 2: failed_runs, or, for one in a list, steps[0]. It refuses whatever to_hive would.
    A write that fills Partitions from its rows, into a table with partitioned_by=, is printed
    after the Session setting it needs: a line saying so, then its SET lines, which run_execute
    doesn't send with it: send them first with run_execute(hive_settings("dynamic_partitions"),
    execute). An Admin statement, from the admin module, is printed after comment lines saying
    what it changes, what can't be undone, and what to check first. A Python step has no Hive:
    it is printed as comment lines saying where its function lives, what it read and wrote, and
    that nothing is sent for it.

    It returns the same text, so `text = show_hive(...)` keeps it to use or save. In a
    notebook, show_hive(...) on its own shows the Hive once. Given two Statements, it heads
    each with its number and its variable's name:

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
                    why="It takes Statements, or lists of them.",
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
        hive = _shown(s, frame)
        if len(named) > 1:
            heading = f"-- {position} of {len(named)}" + (f": {name}" if name else "")
            hive = f"{heading}\n{hive}"
        texts.append(hive)
    text = "\n\n".join(texts)
    print(text)
    return HiveText(text)


def _shown(s: object, frame: FrameType) -> str:
    """What show_hive prints for one of the things it is given, or the refusal of what isn't
    one: `frame` is its caller's."""
    if kinds.kind(s) == kinds.SETTINGS:
        return settings_text(s)
    if kinds.kind(s) == kinds.UNCHECKED:
        return unchecked_text(s)
    if kinds.kind(s) == kinds.PYTHON:
        return python_step_text(s)
    need_statement(s, "show_hive", frame,
                    why="show_hive prints the Hive of Statements made by statement(...).")
    return "\n".join([*settings_needed(s), *admin_notes(s), to_hive(s) + ";"])


def run_query(s: Statement | UncheckedStatement,
              query: Callable[[str], pd.DataFrame] | None = None,
              **removed: object) -> pd.DataFrame | HivePlan:
    """Send a Statement's Hive through your query, and give back the rows it reads.

    >>> run_query(statement(
    ...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.status, "FAILED"), last_n_days(job_runs.dt, 2)),
    ... ), example_database.query)
       run_id  job_id          dt
    0      97       3  2026-09-23
    1     102       2  2026-09-24

    `query` is your own function, in your Project's warehouse.py: it sends Hive whose rows you
    want back and gives them back as a pandas DataFrame. At work it calls your query API;
    example_database.query stands in for it. You choose the call: run_query for a Statement
    that reads rows, run_execute(s, execute) for one that changes something.

    It takes a read, a statement(...) with no INSERT_OVERWRITE or INSERT_INTO, and gives back
    its rows, refusing a result that isn't a DataFrame, or that fills the row limit
    set_load_limits(rows=...) set, since it was probably cut short. Given explain(s), it gives
    back Hive's plan as text. Given an Unchecked statement, it sends your text as written,
    gives back its rows, and adds an entry to the Admin log (help(set_admin_log) says where).
    It refuses what changes something, a write, create_table(t), repair_partitions(t),
    compute_statistics(t), an Admin statement and hive_settings(...), saying to send it with
    run_execute; a Python step, which sends nothing; and your execute in query's place, which
    it knows by its name, before anything is sent.
    """
    _refuse_the_other_call("run_query", "execute", "run_execute", removed)
    refuse_removed_arguments("run_query", removed, run_query)
    _need_its_call(s, "run_query", kinds.QUERY, inspect.currentframe().f_back)
    need_warehouse_call("run_query", "query", query,
                        "run_query sends the Hive through your query, which gives back rows.")
    _refuse_a_swap("run_query", "query", query)
    if kinds.kind(s) == kinds.UNCHECKED:
        # No row Load limit: the Toolbox adds no LIMIT to text you wrote, so a full result
        # is a result, not one cut short.
        rows = logged_run("Unchecked statement", unchecked_call(s), s._text, query)
        refuse_what_isnt_a_dataframe(rows)
        return rows
    text = to_hive(s)
    if kinds.kind(s) == kinds.PLAN:
        return _plan(query(text))
    result = send_logged(s, text, query)
    refuse_what_isnt_a_dataframe(result)
    limit = automatic_limit(s)
    if limit is not None:
        load_limit_rows(len(result), limit)
    return result


def run_execute(s: Statement | SessionSettings | UncheckedStatement,
                execute: Callable[[str], None] | None = None, **removed: object) -> None:
    """Send a Statement's Hive through your execute, which gives back nothing.

    >>> run_execute(hive_settings("dynamic_partitions"), example_database.execute)
    execute: SET hive.exec.dynamic.partition=true
    execute: SET hive.exec.dynamic.partition.mode=nonstrict

    `execute` is your own function, in your Project's warehouse.py: it sends Hive that changes
    something, and gives back nothing. At work it calls your API; example_database.execute
    stands in for it, printing the first line it is given and changing nothing. You choose the
    call: run_execute for a Statement that changes something, run_query(s, query) for one that
    reads rows.

    It takes a write, create_table(t), repair_partitions(t), compute_statistics(t), an Admin
    statement, hive_settings(...), each of whose SET lines it sends in a call of its own, and
    an Unchecked statement, sent as you wrote it. An Admin or Unchecked statement adds an entry
    to the Admin log: inside a Project, its admin/admin_log.md; outside one, admin_log.md
    beside the script or notebook that sends it (help(set_admin_log)). It gives back None. A
    write that fills Partitions from its rows needs the Session setting "dynamic_partitions"
    sent first, as above, as show_hive prints and help(INSERT_OVERWRITE) explains: run_execute
    sends the write alone. It refuses a read and explain(s), whose rows come back only through
    run_query; a Python step, which sends nothing; and your query in execute's place, which it
    knows by its name, before anything is sent.
    """
    _refuse_the_other_call("run_execute", "query", "run_query", removed)
    refuse_removed_arguments("run_execute", removed, run_execute)
    _need_its_call(s, "run_execute", kinds.EXECUTE, inspect.currentframe().f_back)
    need_warehouse_call("run_execute", "execute", execute, "run_execute sends the Hive "
                        "through your execute, which changes something and gives back nothing.")
    _refuse_a_swap("run_execute", "execute", execute)
    marked = kinds.kind(s)
    if marked == kinds.SETTINGS:
        for line in s._lines:  # Hive takes one SET per call
            execute(line)
    elif marked == kinds.UNCHECKED:
        logged_run("Unchecked statement", unchecked_call(s), s._text, execute)
    elif marked == kinds.ADMIN:
        logged_run("Admin statement", s._admin_call, to_hive(s), execute)
    else:
        send_logged(s, to_hive(s), execute)


def send_logged(s: Statement, text: str, warehouse_call: Callable[[str], object],
                sent_for: str | None = None) -> object:
    """Send a Statement's Hive through your query or execute. One holding an Unchecked
    expression or an Unchecked derived table adds an entry to the Admin log, as an Unchecked
    statement does: its Hive is partly written by hand. `sent_for` says, in its heading, why
    other Hive than the Statement's own was sent, as "compared with the original by
    compare_with_original"."""
    tree = statement_tree(s) if kinds.is_a_query(s) else Node("Null")
    calls = unchecked_calls(tree)
    if not calls:
        return warehouse_call(text)
    found = {node.kind for node in tree.find_all("Unchecked", "UncheckedSelect")}
    held = [words for kind, words in (("Unchecked", "an Unchecked expression"),
                                      ("UncheckedSelect", "an Unchecked derived table"))
            if kind in found]
    kind = f"Statement with {' and '.join(held)}" + (f", {sent_for}" if sent_for else "")
    return logged_run(kind, "; ".join(calls), text, warehouse_call)


def _refuse_the_other_call(call: str, other: str, instead: str,
                           removed: dict[str, object]) -> None:
    """Refuse `call` given the other of your two functions, `other`=, which `instead` takes."""
    if other in removed:
        own = "query" if other == "execute" else "execute"
        refuse(
            what=f"{call} was given {other}=, your other call.",
            why=f"{call} sends through your {own} only: you choose which of your two "
            "functions sends a Statement by the function you call.",
            fix=f"To send through your {other}, call {instead}(s, {other}) instead.",
        )


def _refuse_a_swap(call: str, own: str, given: Callable[[str], object]) -> None:
    """Refuse your other function given in `own`'s place, known by its name, such as your
    execute given to run_query: it would get Hive it isn't for."""
    other = "execute" if own == "query" else "query"
    if getattr(given, "__name__", "") != other:
        return
    instead = "run_execute" if own == "query" else "run_query"
    wrong = ("a read whose rows it never gives back" if own == "query"
             else "a change sent as a query")
    refuse(
        what=f"{call} was given your {other} function where your {own} goes.",
        why=f"{call} sends through your {own}; your {other} would get Hive it isn't for, "
        f"{wrong}.",
        fix=f"Pass your {own}: {call}(s, {own}). To send through your {other}, call "
        f"{instead}(s, {other}).",
    )


def _need_its_call(s: object, call: str, through: str, frame: FrameType | None) -> None:
    """Refuse what `call` can't send: anything no maker made, a Python step, and the plain
    mix-up, a step that goes through your other call. `through` is the call it sends
    through."""
    marked = kinds.kind(s)
    if marked == kinds.PYTHON:
        _refuse_a_python_step(call, "It sends Hive through your query or execute, and a "
                              "Python step has none")
    if marked is None:
        need_statement(s, call, frame, why=f"{call} writes the Hive of one Statement made by "
                        "statement(...) and sends it.",
                        more=", query" if through == kinds.QUERY else ", execute")
    if kinds.sent_by(s) in (through, kinds.EITHER):
        return
    name = name_in(frame, s) if frame is not None else None
    if through == kinds.QUERY:
        why = ("run_query sends through your query, which gives back rows, and this changes "
               "something and gives back none, so it goes through your execute.")
        fix = f"Send it with run_execute({name or 's'}, execute)."
    else:
        why = ("run_execute sends through your execute, which gives back nothing, and this "
               "reads rows, which come back only through your query.")
        fix = f"Send it with run_query({name or 's'}, query), which gives back its rows."
    refuse(what=f"{call} was given {kinds.WORDS[marked]}.", why=why, fix=fix,
           error=ValueError)


__all__ = ["to_hive", "run_query", "run_execute", "set_load_limits"]
