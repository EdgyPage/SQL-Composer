"""Running: turn a Statement into Hive, send it, and set the load limit on rows.

run(s, query=..., execute=...) is the only way the Toolbox reaches the warehouse, through your
own two functions: `query` takes a Hive string and gives back a DataFrame, `execute` takes one
and gives back nothing. Connection, retries and saving CSVs stay in them. The Toolbox never
imports them.
"""

from __future__ import annotations

import inspect
import textwrap
from collections.abc import Callable
from types import FrameType
from typing import NoReturn

import pandas as pd

from . import _FOLDER, writing
from .clauses import Clause, Statement, derived_tables
from .conditions import Condition
from .joins import HOW, anti_join_tests, broadcast
from .python_steps import PythonStep, python_step_text
from .refusals import (
    arguments_of,
    load_limit_rows,
    need_warehouse_call,
    refuse,
    refuse_removed_arguments,
    refuse_what_isnt_a_dataframe,
)
from .stacking import STACK_HOW, stack_steps
from .tables import Column, Table, source, table_node
from .trees import Node, combined
from .unchecked import (
    SHIPPED,
    SessionSettings,
    UncheckedStatement,
    logged_run,
    settings_text,
    unchecked_call,
    unchecked_text,
)

TOOLBOX_VERSION = "7.0"

# The seam that ships switched off. set_load_limits(...) switches it on.
_limits = {"rows": None}


def set_load_limits(rows: int | None = None, **removed: object) -> dict[str, int | None]:
    """Switch on an automatic LIMIT for every Statement that reads; it starts off.

    >>> set_load_limits(rows=100000)
    {'rows': 100000}
    >>> set_load_limits()
    {'rows': None}

    Call it from your own notebook, since the Toolbox folder is replaced on each update.
    `rows` adds LIMIT rows to every Statement that has no LIMIT of its own, and run(...)
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
    if rows is not None and (isinstance(rows, bool) or not isinstance(rows, int) or rows < 1):
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
    if s._write is not None:
        # The table's columns in its order, then the partition columns its rows fill, which
        # Hive fills from the last columns; partition={...} gives the others their values.
        partitioned_by = s._write._partitioned_by
        later = [column for column in partitioned_by if column not in s._static_partitions]
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


def partition_node(table: Table, static: dict[str, Node]) -> Node | None:
    """PARTITION(region = 'EU', dt): each partition column `static` names, with its value as a
    Hive literal, then the others by name alone, for every value they hold; None for a table
    that isn't partitioned."""
    if not table._partitioned_by:
        return None
    return Node("Partition", expressions=[
        Node("EQ", this=Node("Column", name=column), expression=static[column].copy())
        if column in static else Node("Column", name=column)
        for column in table._partitioned_by])


def _the_write(s: Statement) -> Clause:
    """The INSERT_OVERWRITE or INSERT_INTO clause of a write."""
    return next(clause for clause in s._clauses if clause._place() == "INSERT")


def _write_tree(s: Statement) -> Node:
    """INSERT OVERWRITE or INSERT INTO the Saved table, then its SELECT: into the Partitions
    its rows fill, and those partition={...} names, or the whole of a table that isn't
    partitioned."""
    table = s._write
    partition = partition_node(table, _the_write(s).partition)
    return Node("Insert", target=table_node(table._name, partition=partition),
                select=_select_tree(s), overwrite=s._replaces_rows)


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
    if isinstance(s, SessionSettings):
        return "\n".join(s._lines)
    if isinstance(s, UncheckedStatement):
        return s._text
    if isinstance(s, PythonStep):
        _refuse_a_python_step("to_hive", "It writes the Hive a Statement sends, and a "
                              "Python step has none")
    _need_statement(s, "to_hive", inspect.currentframe().f_back,
                    why="to_hive writes the Hive of one Statement made by statement(...).")
    if s._admin_hive is not None:
        # An ALTER TABLE, which the admin module writes from pieces writing.py wrote and
        # checked: not a tree writing.py reads back.
        return s._admin_hive
    text = writing.hive_statement(_statement_tree(s))
    _self_check(text)
    return text


def _need_statement(s: object, call: str, frame: FrameType | None, why: str,
                    more: str = "") -> None:
    """Refuse what isn't a Statement, in the name of `call`, the function it was given to.

    `frame` is the caller's, so the usual fix can name their own variable: a Derived table is
    wrapped in a Statement that reads it, and a list is sent one Statement at a time. `more`
    is what the fix's call takes after the Statement, such as ", query=...".
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
    "dynamic_partitions", which the user sends with run(hive_settings("dynamic_partitions"),
    execute=...). run sends the Statement alone."""
    if s._ddl is not None or s._write is None:
        return []
    filled = ", ".join(column for column in s._write._partitioned_by
                       if column not in s._static_partitions)
    if not filled:
        return []
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
    """The plan run(explain(s), query=...) gives back, as text. In a notebook it is printed,
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

    Each Statement's Hive is exactly what to_hive gives and run sends, with a ; added at the
    end, which a program such as Hue, Beeline or DBeaver needs between Statements; run sends
    it without one. Pass several Statements, or a list of them, and each is headed by a
    comment: its number, and the name of the variable it is in, such as -- 1 of 2: failed_runs,
    or, for one in a list, steps[0]. It refuses whatever to_hive would. A write that fills
    Partitions from its rows, into a table with partitioned_by=, is printed after the Session
    setting it needs: a line saying so, then its SET lines, which run
    doesn't send with it: send them first with run(hive_settings("dynamic_partitions"),
    execute=...). An Admin statement, from the admin module, is printed after comment lines
    saying what it changes, what can't be undone, and what to check first. A Python step has
    no Hive: it is printed as comment lines saying where its function lives, what it read and
    wrote, and that nothing is sent for it.

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
    if isinstance(s, SessionSettings):
        return settings_text(s)
    if isinstance(s, UncheckedStatement):
        return unchecked_text(s)
    if isinstance(s, PythonStep):
        return python_step_text(s)
    _need_statement(s, "show_hive", frame,
                    why="show_hive prints the Hive of Statements made by statement(...).")
    return "\n".join([*settings_needed(s), *admin_notes(s), to_hive(s) + ";"])


def run(s: Statement | SessionSettings | UncheckedStatement | PythonStep, *,
        query: Callable[[str], pd.DataFrame] | None = None,
        execute: Callable[[str], None] | None = None,
        **removed: object) -> pd.DataFrame | str | None:
    """Send a Statement's Hive through your query or execute; a read gives back rows.

    >>> run(statement(
    ...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.status, "FAILED"), last_n_days(job_runs.dt, 2)),
    ... ), query=example_database.query)
       run_id  job_id          dt
    0      97       3  2026-09-23
    1     102       2  2026-09-24

    `query` and `execute` are your own functions, in your Project's warehouse.py: `query`
    sends Hive whose rows you want back and gives them back as a pandas DataFrame; `execute`
    sends Hive that changes something, and gives back nothing. run picks which one each
    Statement goes to, so pass the ones it needs: a read and explain(s) go to `query`; a write,
    create_table, hive_settings(...) and the Admin statements go to `execute`, but for the step
    of admin.move_to_own_folder that compares the counts, which reads rows through `query`; an
    Unchecked statement goes to the one its returns_rows= names. At work they call your query API; example_database.query and
    example_database.execute stand in for them.

    A read, and an Unchecked statement with returns_rows=True, give back their rows; explain(s)
    gives back Hive's plan as text; the rest give back None. A write that fills Partitions from
    its rows needs the Session setting "dynamic_partitions" sent first, with
    run(hive_settings("dynamic_partitions"), execute=...), as show_hive prints and
    help(INSERT_OVERWRITE) explains: run sends the write alone. hive_settings(...) sends each SET line as a call of its own.
    A Python step is refused, since it sends nothing: you save its rows yourself.
    """
    refuse_removed_arguments("run", removed, run)
    if isinstance(s, PythonStep):
        _refuse_a_python_step("run", "It sends Hive through your query or execute, and a "
                              "Python step has none")
    if isinstance(s, SessionSettings):
        need_warehouse_call("run", "execute", execute,
                            "Session settings change the session, and give back no rows.")
        for line in s._lines:  # Hive takes one SET per call
            execute(line)
        return None
    if isinstance(s, UncheckedStatement):
        return _run_unchecked(s, query, execute)
    _need_statement(s, "run", inspect.currentframe().f_back,
                    why="run writes the Hive of one Statement made by statement(...) and "
                    "sends it.", more=", execute=..." if query is None and execute is not None
                    else ", query=...")
    text = to_hive(s)
    if s._admin_call is not None:
        check = s._admin_check
        if check is None:
            need_warehouse_call("run", "execute", execute,
                                "This Admin statement changes a table, and gives back no rows.")
            logged_run("Admin statement", s._admin_call, text, execute)
            return None
        need_warehouse_call("run", "query", query, "This Admin statement checks what the "
                            "steps before it did, by reading rows through your query.")
        return logged_run("Admin statement", s._admin_call, text,
                          lambda hive: check(query(hive)))
    if s._ddl is not None and s._ddl.kind == "Explain":
        need_warehouse_call("run", "query", query,
                            "explain(...) reads Hive's plan, which comes back as rows.")
        return _plan(query(text))
    if s._ddl is not None or s._write is not None:
        need_warehouse_call("run", "execute", execute,
                            "This Statement changes a table, and gives back no rows.")
        execute(text)
        return None
    need_warehouse_call("run", "query", query,
                        "This Statement reads rows, which come back through your query.")
    result = query(text)
    refuse_what_isnt_a_dataframe(result)
    limit = automatic_limit(s)
    if limit is not None:
        load_limit_rows(len(result), limit)
    return result


def _run_unchecked(s: UncheckedStatement, query: Callable[[str], pd.DataFrame] | None,
                   execute: Callable[[str], None] | None) -> pd.DataFrame | None:
    """Send an Unchecked statement through the call its returns_rows= names, and log it."""
    if s._returns_rows:
        need_warehouse_call("run", "query", query, "This Unchecked statement says "
                            "returns_rows=True: its rows come back through your query.")
        rows = logged_run("Unchecked statement", unchecked_call(s), s._text, query)
        refuse_what_isnt_a_dataframe(rows)
        return rows
    need_warehouse_call("run", "execute", execute, "This Unchecked statement says "
                        "returns_rows=False: it goes through your execute.")
    logged_run("Unchecked statement", unchecked_call(s), s._text, execute)
    return None


__all__ = ["to_hive", "run", "set_load_limits"]
