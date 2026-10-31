"""Stacks and subtotals: UNION_ALL and the rest, rollup, cube, grouping_sets and is_total.

A Stack puts the rows of whole Statements together, one Statement after another:

    UNION_ALL(failed, alerted)

Each Statement must return the same columns, matched by name, and the Stack is a Statement
itself: to_hive, run_query and show_hive take it, and derived(name, stack) names it for another
Statement to read, filter, group or write. Subtotals go in GROUP_BY:

    GROUP_BY(rollup(jobs.team, jobs.job_name))

gives the usual row for each team and job, and as well, a subtotal row for each team and one
for all the rows; is_total(column) tells a subtotal row from a row whose column is really
NULL.
"""

from __future__ import annotations

from itertools import combinations

from . import kinds
from .clauses import (
    Statement,
    check_derived_names,
    derived_tables,
    flattened,
    resolve_group_by,
    stack_steps,
)
from .conditions import Condition
from .refusals import refuse
from .shared import counted
from .tables import (
    Column,
    Table,
    is_unchecked,
    made_by,
    python_text,
    readable,
    type_family,
)
from .trees import Node, number

# How each Stack is written in Hive.
STACK_HOW = {"UNION_ALL": "UNION ALL", "UNION": "UNION", "INTERSECT": "INTERSECT",
             "EXCEPT": "EXCEPT"}


def nth(position: int) -> str:
    """1st, 2nd, 3rd, 4th, ... 11th, 12th, 21st."""
    ending = {1: "st", 2: "nd", 3: "rd"}.get(position % 10, "th")
    if position % 100 in (11, 12, 13):
        ending = "th"
    return f"{position}{ending}"


# --- Stacks ----------------------------------------------------------------------------------


def UNION_ALL(*statements: Statement | list[Statement],
              returns_all_rows: bool = False) -> Statement:
    """Stack the rows of Statements one after another, keeping every row.

    >>> run_alerts = example_database.run_alerts
    >>> failed = statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
    ... )
    >>> alerted = statement(
    ...     SELECT(run_alerts.run_id),
    ...     FROM(run_alerts),
    ...     WHERE(equals(run_alerts.dt, "2026-09-24"), equals(run_alerts.severity, "high")),
    ... )
    >>> print(to_hive(UNION_ALL(failed, alerted)))
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24' AND job_runs.status = 'FAILED'
    UNION ALL
    SELECT
      run_alerts.run_id
    FROM ops.run_alerts AS run_alerts
    WHERE
      run_alerts.dt = '2026-09-24' AND run_alerts.severity = 'high'
    >>> run_query(UNION_ALL(failed, alerted), example_database.query)
       run_id
    0     101
    1     102
    2     102

    Each Statement must return the same columns. Hive lines columns up by their place in
    SELECT, so it would quietly put one column under another of a different name; the Toolbox
    lines them up by name, and writes each Statement's columns in the first one's order. A
    column that is a number in one Statement and text in another is refused, and so is a
    Statement with ORDER_BY or LIMIT: to sort or cut the stacked rows, name them with
    derived(...) and read them like any table. A row two Statements both return comes back
    twice: UNION gives each different row once. So the stacked rows have no Key: the same row
    can come back twice. returns_all_rows=True drops the LIMIT that set_load_limits(rows=...)
    adds, as in statement(...).
    """
    return stacked("UNION_ALL", statements, returns_all_rows)


def UNION(*statements: Statement | list[Statement],
          returns_all_rows: bool = False) -> Statement:
    """Stack the rows of Statements, each different row once.

    >>> run_alerts = example_database.run_alerts
    >>> failed = statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
    ... )
    >>> alerted = statement(
    ...     SELECT(run_alerts.run_id),
    ...     FROM(run_alerts),
    ...     WHERE(equals(run_alerts.dt, "2026-09-24"), equals(run_alerts.severity, "high")),
    ... )
    >>> run_query(UNION(failed, alerted), example_database.query)
       run_id
    0     101
    1     102

    It stacks as UNION_ALL does, with the same checks, then drops repeated rows, so each
    different row comes back once, whether its copies came from different Statements or the
    same one. So all its columns together are a Key, which a write into a Saved table checks.
    """
    return stacked("UNION", statements, returns_all_rows)


def INTERSECT(*statements: Statement | list[Statement],
              returns_all_rows: bool = False) -> Statement:
    """Keep the rows every Statement returns, each different row once.

    >>> run_alerts = example_database.run_alerts
    >>> failed = statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
    ... )
    >>> alerted = statement(
    ...     SELECT(run_alerts.run_id),
    ...     FROM(run_alerts),
    ...     WHERE(equals(run_alerts.dt, "2026-09-24"), equals(run_alerts.severity, "high")),
    ... )
    >>> run_query(INTERSECT(failed, alerted), example_database.query)
       run_id
    0     102

    A row counts as in every Statement when each returns a row alike in every column, the
    columns matched by name as UNION_ALL matches them; two NULLs count as alike here, unlike
    in equals(...). Hive has INTERSECT from version 2.2, so Hive 3 does.

    Each row comes back once, so all its columns together are a Key, which a write into a
    Saved table checks; each Statement's own Key is one too, since its rows are some of that
    Statement's rows.
    """
    return stacked("INTERSECT", statements, returns_all_rows)


def EXCEPT(*statements: Statement | list[Statement],
           returns_all_rows: bool = False) -> Statement:
    """Keep the first Statement's rows that no other Statement returns, each once.

    >>> run_alerts = example_database.run_alerts
    >>> failed = statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
    ... )
    >>> alerted = statement(
    ...     SELECT(run_alerts.run_id),
    ...     FROM(run_alerts),
    ...     WHERE(equals(run_alerts.dt, "2026-09-24"), equals(run_alerts.severity, "high")),
    ... )
    >>> print(to_hive(EXCEPT(alerted, failed)))
    SELECT
      run_alerts.run_id
    FROM ops.run_alerts AS run_alerts
    WHERE
      run_alerts.dt = '2026-09-24' AND run_alerts.severity = 'high'
    EXCEPT
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24' AND job_runs.status = 'FAILED'
    >>> run_query(EXCEPT(alerted, failed), example_database.query)
       run_id
    0     101

    A row is left out when another Statement returns a row alike in every column, the
    columns matched by name as UNION_ALL matches them; two NULLs count as alike here. Pass
    the same two Statements both ways round to find every difference between two tables.
    Hive has EXCEPT from version 2.2, so Hive 3 does.

    Each row comes back once, so all its columns together are a Key, which a write into a
    Saved table checks; the first Statement's own Key is one too, since its rows are some of
    that Statement's rows. The example above keeps the runs with a high alert that didn't
    fail.
    """
    return stacked("EXCEPT", statements, returns_all_rows)


def stacked(call: str, statements: list[object] | tuple[object, ...],
            returns_all_rows: bool) -> Statement:
    """A Stack of `statements`, by `call`, checked: the Statement the four functions return."""
    branches = _branches(call, statements)
    _check_names(call, branches)
    _check_types(call, branches)
    check_derived_names(call, [table for s in branches for table in derived_tables(s)],
                        why="The Stack's Hive names each Derived table once, at its top, so "
                        "two different ones can't share a name.")
    s = Statement()
    s._stack = (call, branches)
    s._returns_all_rows = returns_all_rows
    s._outputs = [(_stacked_column(name, branches), name) for _, name in branches[0]._outputs]
    return s


def _branches(call: str, statements: list[object] | tuple[object, ...]) -> list[Statement]:
    found = flattened(statements)
    for position, s in enumerate(found, start=1):
        _check_branch(call, position, s)
    if len(found) < 2:
        refuse(
            what=f"{call}(...) was given {counted(len(found), 'Statement')}.",
            why="It stacks the rows of two or more Statements.",
            fix=f"Pass each Statement, such as {call}(failed, alerted).",
            error=ValueError,
        )
    return found


def _check_branch(call: str, position: int, s: object) -> None:
    which = f"{call}(...)'s {nth(position)} Statement"
    if isinstance(s, Table) and s._statement is not None:
        refuse(
            what=f"{which} is the Derived table {s._name}.",
            why=f"{call} stacks the rows of Statements, and a Derived table is read by one.",
            fix=f"Pass a Statement that reads it: statement(SELECT(all_columns({s._alias})), "
            f"FROM({s._alias})).",
            given=s, call=call,
        )
    if not kinds.is_a_query(s):
        refuse(
            what=f"{which} is {s!r}, which isn't a Statement that reads a table.",
            why=f"{call} stacks the rows of Statements made by statement(...).",
            fix=f"Pass Statements, such as {call}(failed, alerted).",
            given=s, call=call,
        )
    if kinds.kind(s) == kinds.WRITE:
        refuse(
            what=f"{which} writes {s._write._name}.",
            why="A write returns no rows to stack.",
            fix="Stack the Statements that read, then name the Stack with derived(...) and "
            "write it in a Statement of its own, as from any Derived table.",
            error=ValueError,
        )
    if s._stack is not None:
        refuse(
            what=f"{which} is itself a Stack, made by {s._stack[0]}(...).",
            why="Hive stacks one Statement after another, left to right, and takes no "
            "brackets around a Stack inside another.",
            fix=f'Name the inner Stack with derived(...), such as inner = derived("inner", '
            f"{s._stack[0]}(...)), and pass a Statement that reads it: "
            "statement(SELECT(all_columns(inner)), FROM(inner)). Or pass all the Statements "
            "to one call, if both stack the same way.",
            error=ValueError,
        )
    if s._order_by or s._limit is not None:
        refuse(
            what=f"{which} has {'ORDER_BY' if s._order_by else 'LIMIT'}.",
            why="In Hive, an ORDER BY or LIMIT at the end of a Stack is for all the stacked "
            "rows, and one inside a Statement of the Stack isn't allowed.",
            fix="To keep a Statement's top rows, make them in a derived(...) table and stack a "
            "Statement that reads it. To sort or cut the stacked rows, name the Stack with "
            "derived(...) and read it with ORDER_BY and LIMIT, or sort in pandas.",
            error=ValueError,
        )


def _check_names(call: str, branches: list[Statement]) -> None:
    """Refuse a Statement whose column names aren't the first Statement's."""
    first = [name for _, name in branches[0]._outputs]
    for position, s in enumerate(branches[1:], start=2):
        names = [name for _, name in s._outputs]
        missing = [name for name in first if name not in names]
        extra = [name for name in names if name not in first]
        if not missing and not extra:
            continue
        said = []
        if missing:
            said.append(f"doesn't return {', '.join(missing)}, which the 1st returns")
        if extra:
            said.append(f"returns {', '.join(extra)}, which the 1st doesn't")
        fix = "Return the same columns from each Statement"
        if missing and extra:
            fix = (f"If {extra[0]} is the same column as {missing[0]}, name it alike with AS, "
                   f'such as AS(..., "{missing[0]}"); else return the same columns from each '
                   "Statement")
        refuse(
            what=f"{call}(...)'s {nth(position)} Statement {', and '.join(said)}.",
            why="The Toolbox stacks the rows column by column, matching each column by its "
            "name, so every Statement must return the same names.",
            fix=f"{fix}, leaving out a column only some of them have.",
            error=ValueError,
        )


def _check_types(call: str, branches: list[Statement]) -> None:
    """Refuse a column whose type is a number in one Statement and text in another, and the
    like: the types of each name must be of one kind wherever they are known."""
    known = {}  # each name's first known type, and the place of the Statement it is from
    for position, s in enumerate(branches, start=1):
        for column, name in s._outputs:
            theirs = column._type
            if not type_family(theirs):
                continue
            mine, where = known.setdefault(name, (theirs, position))
            if type_family(mine) != type_family(theirs):
                refuse(
                    what=f"{call}(...): {name} is {mine} in its {nth(where)} Statement and "
                    f"{theirs} in its {nth(position)}.",
                    why="Stacked, they are one column, so Hive would turn one into the other "
                    "type, or refuse the Statement.",
                    fix=f"Return {name} as the same kind of value from each Statement: a "
                    "number with a number, text with text, a day with a day.",
                    error=ValueError,
                )


def _stacked_column(name: str, branches: list[Statement]) -> Column:
    """A Stack's output column: its type the first one known, and it adds up only if it adds
    up in every Statement."""
    columns = [column for s in branches for column, own in s._outputs if own == name]
    known = next((column._type for column in columns if column._type), None)
    because = next((column._not_adding_up_because for column in columns
                    if not column._adds_up), None)
    return Column(Node("Column", name=name), name=name, type=known,
                  adds_up=all(column._adds_up for column in columns),
                  not_adding_up_because=because)


# --- Subtotals -------------------------------------------------------------------------------


class Subtotals:
    """Subtotals for GROUP_BY, made by rollup(...), cube(...) or grouping_sets(...).

    >>> rollup(jobs.team, jobs.job_name)
    <rollup(jobs.team, jobs.job_name) - put it in GROUP_BY(...)>

    Make them with one of those three, never Subtotals(). Write the name in a type hint, to say
    that a function of yours gives them back:

    >>> def per_status_with_a_total() -> Subtotals:
    ...     return rollup(job_runs.status)
    >>> per_status_with_a_total()
    <rollup(job_runs.status) - put it in GROUP_BY(...)>
    """

    def __init__(self, call: str, columns: list[Column | str], sets: list[list[int]]) -> None:
        self._call = call  # how it was written, such as rollup(jobs.team, jobs.job_name)
        self._columns = columns  # each column, or output name, once, in order
        self._sets = sets  # each set of columns to group by, by its place in _columns

    def __repr__(self) -> str:
        return f"<{self._call} - put it in GROUP_BY(...)>"


def _subtotal_columns(call: str, items: list[object]) -> list[Column | str]:
    for item in items:
        if not isinstance(item, (Column, str)):
            refuse(
                what=f"{call} was given {item!r}.",
                why="It groups by columns, or by the name of a calculation in SELECT.",
                fix='Pass columns or output names, such as rollup(jobs.team, jobs.job_name).',
                given=item, call=call,
            )
    return items


def _distinct_columns(items: list[Column | str]) -> list[Column | str]:
    """The columns, each once: two are the same when their Hive is."""
    kept = []
    for item in items:
        if not any(_same(item, other) for other in kept):
            kept.append(item)
    return kept


def _same(one: Column | str, other: Column | str) -> bool:
    if isinstance(one, str) or isinstance(other, str):
        return isinstance(one, str) and isinstance(other, str) and one == other
    return one._tree == other._tree


def rollup(*columns: Column | str | list[Column | str]) -> Subtotals:
    """Subtotals for GROUP_BY: dropping its columns from the right, to a grand total.

    >>> print(to_hive(statement(
    ...     SELECT(jobs.team, jobs.job_name, AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    ...     WHERE(equals(job_runs.dt, "2026-09-24")),
    ...     GROUP_BY(rollup(jobs.team, jobs.job_name)),
    ... )))
    SELECT
      jobs.team,
      jobs.job_name,
      COUNT(*) AS runs
    FROM ops.job_runs AS job_runs
    JOIN ops.jobs AS jobs
      ON jobs.job_id = job_runs.job_id
    WHERE
      job_runs.dt = '2026-09-24'
    GROUP BY
      jobs.team,
      jobs.job_name
      GROUPING SETS (
        (jobs.team, jobs.job_name),
        jobs.team,
        ()
      )

    GROUP_BY(rollup(jobs.team, jobs.job_name)) gives the usual row for each team and job, as
    GROUP_BY(jobs.team, jobs.job_name) does, and as well, a subtotal row for each team, which
    totals over every job_name, so job_name is NULL in it, and the grand total, one row over
    all the rows, with team NULL too. A plain column next to it, as in
    GROUP_BY(job_runs.dt, rollup(jobs.team)), is in every subtotal: a total for each day,
    never one across days. is_total(column) tells a subtotal row from a row whose column is
    really NULL. The Toolbox refuses to write subtotals into a Saved table, as they repeat the
    rows they total. Not every Example database makes subtotals; the how-to "Rollups and
    subtotals" shows their rows.

    Each line of GROUPING SETS is one set of rows: (jobs.team, jobs.job_name) the row of each
    job, jobs.team each team's subtotal, and (), no column, the grand total. The Toolbox writes
    this form rather than ROLLUP, so the Hive names each set of rows it makes.
    """
    call = f"rollup({', '.join(python_text(column) for column in columns)})"
    items = _distinct_columns(_subtotal_columns(call, flattened(columns)))
    _need_some(call, items, "rollup(jobs.team, jobs.job_name)")
    sets = [list(range(size)) for size in range(len(items), -1, -1)]
    return Subtotals(call, items, sets)


def cube(*columns: Column | str | list[Column | str]) -> Subtotals:
    """Subtotals for GROUP_BY over every mix of the columns, and a grand total.

    >>> print(to_hive(statement(
    ...     SELECT(jobs.team, jobs.region, AS(count_rows(), "job_count")),
    ...     FROM(jobs),
    ...     GROUP_BY(cube(jobs.team, jobs.region)),
    ... )))
    SELECT
      jobs.team,
      jobs.region,
      COUNT(*) AS job_count
    FROM ops.jobs AS jobs
    GROUP BY
      jobs.team,
      jobs.region
      GROUPING SETS (
        (jobs.team, jobs.region),
        jobs.team,
        jobs.region,
        ()
      )

    GROUP_BY(cube(jobs.team, jobs.region)) gives a row for each team and region, a subtotal
    row for each team over every region, one for each region over every team, and one for all
    the rows. Two columns give 4 sets of rows, three give 8: each column doubles them. It
    works as rollup(...) does in every other way.
    """
    call = f"cube({', '.join(python_text(column) for column in columns)})"
    items = _distinct_columns(_subtotal_columns(call, flattened(columns)))
    _need_some(call, items, "cube(jobs.team, jobs.region)")
    sets = [list(chosen) for size in range(len(items), -1, -1)
            for chosen in combinations(range(len(items)), size)]
    return Subtotals(call, items, sets)


def grouping_sets(*sets: list[Column | str] | Column | str) -> Subtotals:
    """Subtotals for GROUP_BY: the groups of each listed set of columns, in one result.

    >>> print(to_hive(statement(
    ...     SELECT(jobs.team, jobs.region, AS(count_rows(), "job_count")),
    ...     FROM(jobs),
    ...     GROUP_BY(grouping_sets([jobs.team], [jobs.region], [])),
    ... )))
    SELECT
      jobs.team,
      jobs.region,
      COUNT(*) AS job_count
    FROM ops.jobs AS jobs
    GROUP BY
      jobs.team,
      jobs.region
      GROUPING SETS (
        jobs.team,
        jobs.region,
        ()
      )

    Each set is a list of columns, or one column, and [] is the grand total, one row over all
    the rows. Its rows are those of a GROUP_BY over each set in turn, one set after another,
    with the columns a set leaves out NULL, as rollup(...) and cube(...) give; it works as
    they do in every other way.
    """
    call = f"grouping_sets({', '.join(python_text(each) for each in sets)})"
    _need_some(call, sets, "grouping_sets([jobs.team], [jobs.region], [])")
    listed = [_distinct_columns(_subtotal_columns(call, flattened([each]))) for each in sets]
    items = _distinct_columns([item for each in listed for item in each])
    found = []
    for each in listed:
        places = sorted(next(place for place, item in enumerate(items) if _same(item, column))
                        for column in each)
        if places in found:
            refuse(
                what=f"{call} lists the set [{', '.join(python_text(c) for c in each)}] twice.",
                why="Each set gives its own rows, so the rows of that one would come back "
                "twice.",
                fix="List each set once.",
                error=ValueError,
            )
        found.append(places)
    return Subtotals(call, items, found)


def _need_some(call: str, items: list[Column | str] | tuple[object, ...],
               example: str) -> None:
    if not items:
        refuse(what=f"{call} was given nothing to group by.", why="It needs a column.",
               fix=f"Pass columns or output names, such as {example}.", error=ValueError)


def is_total(column: Column) -> Condition:
    """A condition true on a subtotal row that totals over every value of the column.

    >>> is_total(jobs.team)
    GROUPING(jobs.team) = 1
    >>> if_else(is_total(jobs.team), "every team", jobs.team)
    CASE WHEN GROUPING(jobs.team) = 1 THEN 'every team' ELSE jobs.team END

    A subtotal row of GROUP_BY(rollup(...)), cube(...) or grouping_sets(...) has NULL in each
    column it totals over, as a real row may have NULL too; is_total tells them apart. Use it
    in SELECT, through if_else, to label the row, or in HAVING, to keep or leave out subtotal
    rows. In HAVING or ORDER_BY, the column you pass must also be in SELECT. It is refused in
    WHERE and ON=, which pick rows before any subtotal is made, and in a Statement with no
    subtotals.
    """
    call = f"is_total({python_text(column)})"
    if not isinstance(column, Column):
        fix = "Pass a column of rollup(...), cube(...) or grouping_sets(...), such as " \
              "is_total(jobs.team)."
        if isinstance(column, str):
            fix += (f" For a calculation named {python_text(column)} with AS, pass the "
                    "calculation itself, as GROUP_BY holds it.")
        refuse(what=f"{call} was given {column!r} where a column goes.",
               why="It tests whether a row adds that column up.", fix=fix,
               given=column, call="is_total")
    tree = Node("EQ", this=Node("Grouping", this=column._tree.copy()), expression=number("1"))
    return Condition(made_by(tree, "is_total", column))


def grouped(s: Statement, items: list[Column | str | Subtotals]
            ) -> tuple[list[Column], list[list[Column]] | None, str | None]:
    """GROUP_BY's columns, names looked up; the sets of columns its subtotals group by, each
    with GROUP_BY's other columns; and how the subtotals were written. The last two are None
    when it has no subtotals."""
    found = [item for item in items if isinstance(item, Subtotals)]
    if not found:
        return resolve_group_by(s, items), None, None
    if len(found) > 1:
        refuse(
            what=f"GROUP_BY has {found[0]._call} and {found[1]._call}.",
            why="One GROUP_BY makes one set of subtotals.",
            fix="Keep one, or list every set of columns you want in one "
            "grouping_sets(...).",
            error=ValueError,
        )
    subtotals = found[0]
    plain = resolve_group_by(s, [item for item in items if item is not subtotals])
    columns = resolve_group_by(s, subtotals._columns)
    every = _distinct_columns(plain + columns)
    sets = [_distinct_columns(plain + [columns[place] for place in places])
            for places in subtotals._sets]
    return every, sets, subtotals._call


# --- What a Statement with subtotals may do --------------------------------------------------


def check_subtotals(s: Statement) -> None:
    """Refuse is_total where it can't go, and a write of subtotal rows into a Saved table."""
    places = [("WHERE", c._tree) for c in s._where]
    places += [("ON=", read.on._tree) for read in s._reads if read.on is not None]
    places += [("GROUP_BY", column._tree) for column in s._group_by]
    places += [("SELECT", column._tree) for column, _ in s._outputs]
    places += [("HAVING", c._tree) for c in s._having]
    places += [("ORDER_BY", key) for key in s._order_by]
    for place, tree in places:
        for grouping in tree.find_all("Grouping"):
            _check_is_total(s, place, grouping)
    if kinds.kind(s) == kinds.WRITE:
        _refuse_writing_subtotals(s)


def _check_is_total(s: Statement, place: str, grouping: Node) -> None:
    column = grouping.parts["this"]
    call = f"is_total({readable(column)})"
    if place in ("WHERE", "ON=", "GROUP_BY"):
        why = (f"GROUP_BY makes the subtotal rows after {place} has picked the rows, so there "
               f"is none to test in {place}.")
        if place == "GROUP_BY":
            why = "is_total tests the rows GROUP_BY makes, so GROUP_BY can't group by it."
        refuse(
            what=f"{place} has {call}.",
            why=why,
            fix=f"Test it in HAVING, or show it in SELECT, such as "
            f'AS(if_else({call}, 1, 0), "is_subtotal").',
            error=ValueError,
        )
    if s._grouping_sets is None:
        refuse(
            what=f"{place} has {call}, but GROUP_BY makes no subtotal rows.",
            why="is_total tells a subtotal row from the others, and only GROUP_BY(rollup(...)), "
            "cube(...) or grouping_sets(...) make subtotal rows.",
            fix="Add the subtotals to GROUP_BY, such as GROUP_BY(rollup(jobs.team, "
            "jobs.job_name)), or leave is_total out.",
            error=ValueError,
        )
    if not any(group._tree == column for group in s._group_by):
        refuse(
            what=f"{place} has {call}, but GROUP_BY doesn't group by {readable(column)}.",
            why="is_total says whether a row totals over one of the columns GROUP_BY groups by.",
            fix="Pass one of: " + ", ".join(readable(group._tree) for group in s._group_by)
            + ".",
            error=ValueError,
        )
    if place in ("HAVING", "ORDER_BY") and not any(output._tree == column
                                                   for output, _ in s._outputs):
        refuse(
            what=f"{place} has {call}, but SELECT doesn't return {readable(column)}.",
            why=f"Without {readable(column)} in the rows, a subtotal row looks like the "
            "rows it totals, so nothing in the result says which rows are totals.",
            fix=f"Add {readable(column)} to SELECT.",
            error=ValueError,
        )


def _refuse_writing_subtotals(s: Statement) -> None:
    """Refuse a write whose rows come from subtotals, at any step."""
    for step, where in [(s, "")] + [(table._statement, f" in derived({table._name!r}, ...)")
                                     for table in derived_tables(s) if not is_unchecked(table)]:
        for part in stack_steps(step):
            if part._grouping_sets is None:
                continue
            refuse(
                what=f"{s._write_call} writes rows made by GROUP_BY({part._subtotals_call})"
                f"{where}.",
                why="Each subtotal row totals over rows written with it, with NULL in the columns "
                "it totals over: it can repeat the Key of a real row, and a sum over the Saved "
                "table would count each row more than once.",
                fix="Write the plain GROUP_BY into the Saved table, and add the subtotals in "
                "the Statement that reads it.",
                error=ValueError,
            )


__all__ = ["UNION_ALL", "UNION", "INTERSECT", "EXCEPT", "rollup", "cube", "grouping_sets",
           "is_total"]
