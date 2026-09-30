"""Clause functions: SELECT, FROM, JOIN, WHERE and the rest, assembled by statement(...).

A Statement is a list of clause functions written in SQL order, one per SQL clause:

    statement(SELECT(...), FROM(job_runs), WHERE(...), GROUP_BY(...))

statement(...) runs the Guards and Load limits that need the whole Statement, and
to_hive(...) turns it into the Hive string. derived(name, statement) names a Statement so
another Statement can read it like a table.
"""

from __future__ import annotations

from .calculations import Ordering, ordered
from .conditions import Condition, combined_spans
from .refusals import (
    four_part_message,
    guard_cross_join,
    guard_left_join_then_where,
    guard_missing_group_by,
    guard_order_by_in_derived_table,
    guard_unnamed_calculation,
    refuse_what_the_other_edition_made,
    guard_write_lines_up,
    load_limit_date_bound,
    load_limit_order_by,
    warning_repeated_rows,
)
from .tables import Column, Table, aliased
from .trees import SIMPLE_NAME, Node
from .writing import hive_text

TOOLBOX_VERSION = "2.1"

# The order clauses come in, as in SQL. A write comes first, and the joins share one place.
ORDER = ["INSERT", "SELECT", "FROM", "JOIN", "WHERE", "GROUP_BY", "HAVING", "ORDER_BY", "LIMIT"]
WRITES = ("INSERT_OVERWRITE", "INSERT_INTO")
JOINS = ("JOIN", "LEFT_JOIN", "CROSS_JOIN")


def _misuse(what: str, why: str, fix: str, error=TypeError):
    raise error(four_part_message(what=what, why=why, fix=fix, opt_out=None))


class Clause:
    """One clause of a Statement, made by a clause function such as SELECT(...).

    Each clause function fills in only the parts its clause has; the rest keep their
    defaults. statement(...) reads them back to build the Statement.
    """

    def __init__(self, name: str, *, outputs=None, distinct=False, table=None, on=None,
                 reads_all_partitions=False, many_matches=False, keeps_only_matches=False,
                 conditions=None, group_columns=None, sort_keys=None, sorts_everything=False,
                 n=None):
        self._name = name  # the clause function's name: "SELECT", "LEFT_JOIN", ...
        # SELECT and SELECT_DISTINCT: the (column, output name) pairs, and whether DISTINCT.
        self.outputs = outputs
        self.distinct = distinct
        # FROM, the joins and the writes: the table, a join's ON= condition, and opt-outs.
        self.table = table
        self.on = on
        self.reads_all_partitions = reads_all_partitions
        self.many_matches = many_matches
        self.keeps_only_matches = keeps_only_matches
        # WHERE and HAVING: the conditions. GROUP_BY: its columns and output names.
        self.conditions = conditions
        self.group_columns = group_columns
        # ORDER_BY: the sort keys, and its opt-out. LIMIT: the row count.
        self.sort_keys = sort_keys
        self.sorts_everything = sorts_everything
        self.n = n

    def _place(self) -> str:
        """This clause's place in ORDER: INSERT_INTO sits at INSERT, LEFT_JOIN at JOIN."""
        if self._name in WRITES:
            return "INSERT"
        if self._name in JOINS:
            return "JOIN"
        return self._name.replace("_DISTINCT", "")

    def _call(self) -> str:
        """How this clause was written, for messages: FROM(job_runs), JOIN(jobs, ON=...)."""
        on = ", ON=..." if self.on is not None else ""
        return f"{self._name}({self.table._alias}{on})"

    def __repr__(self) -> str:
        return f"<{self._name} clause - put it in statement(...)>"


class Named:
    """A column or calculation with the name it gets in the result. Made by AS(...)."""

    def __init__(self, column: Column, name: str):
        self._column = column
        self._name = name

    def __repr__(self) -> str:
        return hive_text(Node("Alias", this=self._column._tree.copy(), alias=self._name))


class Statement:
    """A query, assembled by statement(...). to_hive(s) gives its Hive string."""

    def __init__(self):
        # Filled in by statement(...), from the clauses it was given:
        self._clauses = ()  # the clauses, in the order written
        self._returns_all_rows = False  # the opt-out of the automatic LIMIT
        self._write = None  # the Saved table an INSERT_OVERWRITE or INSERT_INTO writes
        self._write_call = None  # how that write was called, for messages
        self._replaces_day = False  # True for INSERT_OVERWRITE, False for INSERT_INTO
        self._outputs = []  # SELECT's (column, output name) pairs
        self._distinct = False  # whether it is SELECT_DISTINCT
        self._reads = []  # the FROM clause, then each join clause
        self._where = []  # WHERE's conditions
        self._having = []  # HAVING's conditions
        self._group_by = []  # GROUP_BY's columns, with output names looked up
        self._order_by = []  # ORDER_BY's sort keys
        self._limit = None  # LIMIT's row count
        # Set instead by create_table and drop_table, whose Statement is a CREATE or DROP
        # tree ready to write, with none of the parts above.
        self._ddl = None

    def __repr__(self) -> str:
        if self._ddl is not None:
            return "<Statement - print(to_hive(s)) shows it>"
        reads = ", ".join(read.table._name for read in self._reads)
        return f"<Statement reading {reads} - print(to_hive(s)) shows its Hive>"


# --- Naming things -------------------------------------------------------------------------


def AS(expression, name):
    """Give a calculation its name in the result, or a table a second name.

    Every calculation in SELECT needs a name, which becomes its column in pandas. Arithmetic
    uses Python's + - * / and comes out bracketed. / divides as Python's / does, so 7 / 2 is
    3.5, and dividing by zero gives NULL rather than an error.

    >>> AS(count_rows(), "runs")
    COUNT(*) AS runs
    >>> AS(job_runs.duration_mins / 60, "hours")
    job_runs.duration_mins / 60 AS hours

    A table named twice in one Statement, such as a table joined to itself, needs a second
    name for one of them: AS(job_runs, "earlier") is read as FROM ops.job_runs AS earlier.
    """
    if isinstance(expression, Table):
        return aliased(expression, name)
    if isinstance(expression, Named):
        expression = expression._column
    if not isinstance(expression, Column):
        refuse_what_the_other_edition_made(expression, "AS")
        _misuse(
            what=f"AS was given {expression!r}, which can't be named.",
            why="AS names a column or a calculation for SELECT, or a table for FROM or JOIN.",
            fix='Pass a column or calculation first, such as AS(count_rows(), "runs").',
        )
    if not isinstance(name, str) or not name:
        _misuse(
            what=f"AS(..., {name!r}) needs a name as a string.",
            why="The name becomes the column's name in the result.",
            fix='Write it like AS(count_rows(), "runs").',
        )
    return Named(expression, name)


# --- Clause functions ----------------------------------------------------------------------


def _flatten(items) -> list:
    found = []
    for item in items:
        if isinstance(item, (list, tuple)):
            found.extend(_flatten(item))
        else:
            found.append(item)
    return found


def _outputs(items, call: str) -> list[tuple[Column, str]]:
    outputs = []
    for item in _flatten(items):
        if isinstance(item, Named):
            outputs.append((item._column, item._name))
        elif isinstance(item, Column) and item._name is not None:
            outputs.append((item, item._name))
        elif isinstance(item, Column):
            guard_unnamed_calculation(repr(item))
        else:
            _refuse_output(item, call)
    if not outputs:
        _misuse(what=f"{call} was given nothing to select.", why="A Statement returns columns.",
                fix="Name the columns, such as SELECT(job_runs.run_id, job_runs.status).")
    names = [name for _, name in outputs]
    twice = sorted({name for name in names if names.count(name) > 1})
    if twice:
        _misuse(
            what=f"{call} has more than one column called {', '.join(twice)}.",
            why="Each column in the result needs its own name, or pandas can't tell them apart.",
            fix='Rename one with AS, such as AS(jobs.job_id, "jobs_job_id").',
            error=ValueError,
        )
    return outputs


def _refuse_output(item, call: str) -> None:
    refuse_what_the_other_edition_made(item, call)
    if isinstance(item, Table):
        fix = f"Name its columns, or use all_columns({item._alias})."
    elif isinstance(item, Condition):
        fix = 'A condition goes in WHERE. To show it as a column, use if_else(condition, 1, 0).'
    else:
        fix = "Pass columns such as job_runs.status, or calculations named with AS(...)."
    _misuse(what=f"{call} was given {item!r}.", why="SELECT takes columns and calculations.",
            fix=fix)


def SELECT(*columns):
    """The columns and named calculations a Statement returns; takes a list too.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.status, AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY(job_runs.status),
    ... )))
    SELECT
      job_runs.status,
      COUNT(*) AS runs
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    GROUP BY
      job_runs.status
    """
    return Clause("SELECT", outputs=_outputs(columns, "SELECT(...)"), distinct=False)


def SELECT_DISTINCT(*columns):
    """Like SELECT, but each different row comes back once.

    >>> print(to_hive(statement(
    ...     SELECT_DISTINCT(jobs.team),
    ...     FROM(jobs),
    ... )))
    SELECT DISTINCT
      jobs.team
    FROM ops.jobs AS jobs
    """
    return Clause("SELECT_DISTINCT", outputs=_outputs(columns, "SELECT_DISTINCT(...)"),
                  distinct=True)


def _need_table(table, call: str) -> Table:
    if isinstance(table, Table):
        return table
    refuse_what_the_other_edition_made(table, call)
    _misuse(
        what=f"{call} was given {table!r}, which isn't a table.",
        why="It reads a Table reference, or a Statement named with derived(...).",
        fix="Pass the table itself, such as FROM(job_runs).",
    )


def FROM(table, reads_all_partitions=False):
    """The table a Statement reads; its Date partition must be bounded in WHERE.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    ... )))
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'

    Reading every day of a big table can stall the cluster, so a missing bound is refused;
    reads_all_partitions=True reads them all anyway.
    """
    return Clause("FROM", table=_need_table(table, "FROM(...)"), on=None,
                  reads_all_partitions=reads_all_partitions)


def _need_on(on, call: str, table: Table):
    if on is None:
        guard_cross_join(call, table._alias)
    if not isinstance(on, Condition):
        refuse_what_the_other_edition_made(on, call)
        _misuse(
            what=f"{call}({table._alias}, ON={on!r}): ON= isn't a condition.",
            why="ON= says which rows of the two tables belong together.",
            fix=f"Pass a condition, such as ON=equals({table._alias}.job_id, job_runs.job_id).",
        )
    return on


def _matched_columns(table: Table, on: Condition) -> list[str]:
    """The columns of `table` that ON= pins with an equals at its top level."""
    parts = list(on._tree.flatten()) if on._tree.kind == "And" else [on._tree]
    matched = set()
    for part in parts:
        if part.kind != "EQ":
            continue
        sides = (part.parts["this"], part.parts["expression"])
        for mine, other in (sides, sides[::-1]):
            if mine.kind == "Column" and mine.table == table._alias and not (
                    other.kind == "Column" and other.table == table._alias):
                matched.add(mine.name)
    return sorted(matched)


def _join(call: str, table, on, many_matches, reads_all_partitions, **more) -> Clause:
    table = _need_table(table, f"{call}(...)")
    on = _need_on(on, call, table)
    matched = _matched_columns(table, on)
    key = table._key
    if key is None or not set(key) <= set(matched):
        warning_repeated_rows(call, table._alias, matched, key, many_matches,
                              derived=table._statement is not None)
    return Clause(call, table=table, on=on, reads_all_partitions=reads_all_partitions,
                  many_matches=many_matches, **more)


def JOIN(table, ON=None, many_matches=False, reads_all_partitions=False):
    """Add a second table's columns to each row, matching rows by ON=.

    When ON= doesn't pin down the joined table's whole key, one row can match several, and
    sums over them come out too big. The Statement is still built, with a warning at your
    JOIN line; many_matches=True says you mean it and silences it.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id, jobs.team),
    ...     FROM(job_runs),
    ...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ... )))
    SELECT
      job_runs.run_id,
      jobs.team
    FROM ops.job_runs AS job_runs
    JOIN ops.jobs AS jobs
      ON jobs.job_id = job_runs.job_id
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    """
    return _join("JOIN", table, ON, many_matches, reads_all_partitions)


def LEFT_JOIN(table, ON=None, keeps_only_matches=False, many_matches=False,
              reads_all_partitions=False):
    """Like JOIN, but rows with no match are kept, with NULL in the joined columns.

    A condition on the joined table in WHERE would throw those rows away again, so it is
    refused: put it in ON= instead, bound the joined table's Date partition there too, or
    pass keeps_only_matches=True if you mean it.

    >>> print(to_hive(statement(
    ...     SELECT(jobs.job_name, AS(count_rows(where=is_not_null(job_runs.run_id)), "runs")),
    ...     FROM(jobs),
    ...     LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
    ...                                   last_n_days(job_runs.dt, 2)), many_matches=True),
    ...     GROUP_BY(jobs.job_name),
    ... )))
    SELECT
      jobs.job_name,
      COUNT(CASE WHEN NOT job_runs.run_id IS NULL THEN 1 END) AS runs
    FROM ops.jobs AS jobs
    LEFT JOIN ops.job_runs AS job_runs
      ON job_runs.job_id = jobs.job_id
      AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    GROUP BY
      jobs.job_name
    """
    return _join("LEFT_JOIN", table, ON, many_matches, reads_all_partitions,
                 keeps_only_matches=keeps_only_matches)


def CROSS_JOIN(table, reads_all_partitions=False):
    """Pair every row with every row of another table, with no ON=.

    JOIN and LEFT_JOIN refuse a join with no ON=, because pairing every row with every row
    multiplies the rows and every sum and count over them. CROSS_JOIN is the opt-out of that
    refusal: its name says you mean every row with every row, so it takes no ON=.

    Joining a table to itself needs a second name for it, given with AS:

    >>> other = AS(jobs, "other")
    >>> print(to_hive(statement(
    ...     SELECT(jobs.job_name, AS(other.job_name, "other_job")),
    ...     FROM(jobs),
    ...     CROSS_JOIN(other),
    ... )))
    SELECT
      jobs.job_name,
      other.job_name AS other_job
    FROM ops.jobs AS jobs
    CROSS JOIN ops.jobs AS other
    """
    return Clause("CROSS_JOIN", table=_need_table(table, "CROSS_JOIN(...)"), on=None,
                  reads_all_partitions=reads_all_partitions)


def WHERE(*conditions):
    """Keep only the rows where every condition holds (they are joined with AND).

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.status, "FAILED"), last_n_days(job_runs.dt, 2)),
    ... )))
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.status = 'FAILED' AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    """
    return Clause("WHERE", conditions=_conditions(conditions, "WHERE(...)"))


def _conditions(items, call: str) -> list[Condition]:
    found = _flatten(items)
    for item in found:
        if not isinstance(item, Condition):
            refuse_what_the_other_edition_made(item, call)
            _misuse(
                what=f"{call} was given {item!r}, which isn't a condition.",
                why="It keeps rows by conditions made with functions such as equals(...).",
                fix='Pass conditions, such as equals(job_runs.status, "FAILED").',
            )
    if not found:
        _misuse(what=f"{call} was given no conditions.", why="It needs at least one.",
                fix="Pass a condition, or leave the clause out.")
    return found


def GROUP_BY(*columns):
    """Group rows that share these values, one output row per group.

    A calculation may be named by its output name, such as GROUP_BY("week"), and the
    Toolbox repeats it, since Hive can't group by a name given in SELECT.

    >>> print(to_hive(statement(
    ...     SELECT(AS(week_start(job_runs.dt), "week"), AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY("week"),
    ... )))
    SELECT
      NEXT_DAY(DATE_ADD(job_runs.dt, 7 * -1), 'MO') AS week,
      COUNT(*) AS runs
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    GROUP BY
      NEXT_DAY(DATE_ADD(job_runs.dt, 7 * -1), 'MO')
    """
    items = _flatten(columns)
    for item in items:
        if not isinstance(item, (Column, str)):
            refuse_what_the_other_edition_made(item, "GROUP_BY")
            _misuse(
                what=f"GROUP_BY was given {item!r}.",
                why="It groups by columns, or by the name of a calculation in SELECT.",
                fix='Pass columns or output names, such as GROUP_BY(job_runs.status, "week").',
            )
    return Clause("GROUP_BY", group_columns=items)


def HAVING(*conditions):
    """Keep only the groups where every condition holds, tested after GROUP_BY.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.job_id, AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY(job_runs.job_id),
    ...     HAVING(at_least(count_rows(), 3)),
    ... )))
    SELECT
      job_runs.job_id,
      COUNT(*) AS runs
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    GROUP BY
      job_runs.job_id
    HAVING
      COUNT(*) >= 3
    """
    return Clause("HAVING", conditions=_conditions(conditions, "HAVING(...)"))


def ORDER_BY(*columns, sorts_everything=False):
    """Sort the result; it needs a LIMIT, and sorting in pandas is usually better.

    Sort by columns, output names or descending(...). Without LIMIT(n) it is refused, since
    it makes the warehouse put every row in order before any comes back: sort in pandas after
    run(...), or pass sorts_everything=True. In a Statement you pass to derived(...), an
    ORDER_BY without LIMIT is refused even with sorts_everything=True: the order of rows there
    may not be kept, so a Statement that reads it can't rely on that order.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY(job_runs.job_id),
    ...     ORDER_BY(descending("minutes")),
    ...     LIMIT(3),
    ... )))
    SELECT
      job_runs.job_id,
      SUM(job_runs.duration_mins) AS minutes
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    GROUP BY
      job_runs.job_id
    ORDER BY
      minutes DESC
    LIMIT 3
    """
    items = _flatten(columns)
    if not items:
        _misuse(what="ORDER_BY was given nothing to sort by.", why="It needs a column.",
                fix='Pass columns, output names or descending(...), such as '
                'ORDER_BY(descending("runs")).')
    for item in items:
        if not isinstance(item, (Column, str, Ordering)):
            refuse_what_the_other_edition_made(item, "ORDER_BY")
            _misuse(what=f"ORDER_BY was given {item!r}.",
                    why="It sorts by columns or output names.",
                    fix="Pass a column, an output name, or descending(...).")
    trees = [ordered(item, "ORDER_BY(...)") for item in items]
    return Clause("ORDER_BY", sort_keys=trees, sorts_everything=sorts_everything)


def LIMIT(n):
    """Return at most n rows.

    >>> print(to_hive(statement(SELECT(jobs.job_name), FROM(jobs), LIMIT(2))))
    SELECT
      jobs.job_name
    FROM ops.jobs AS jobs
    LIMIT 2
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        _misuse(what=f"LIMIT({n!r}) needs a whole number of rows, 1 or more.",
                why="It is how many rows come back at most.", fix="Write it like LIMIT(20).",
                error=ValueError)
    return Clause("LIMIT", n=n)


def _write_clause(call: str, table) -> Clause:
    """The clause for INSERT_OVERWRITE(table) or INSERT_INTO(table), once the table is checked."""
    table = _need_table(table, f"{call}(...)")
    if table._statement is not None or table._date_partition is None:
        _misuse(
            what=f"{call}({table._alias}) needs a Saved table with a Date partition.",
            why="A write fills one day of a real table, so the table needs a Date partition "
            "to write the day into.",
            fix="Pass the Saved table's own Table reference, with date_partition=... set.",
            error=ValueError,
        )
    return Clause(call, table=table)


def INSERT_OVERWRITE(table):
    """Write the Statement's rows into one day of a Saved table, replacing that day.

    It goes first, before SELECT. The day written is the one day the Statement reads, so loop
    over by_day(s) to write several. Columns are matched to the Saved table by name, and the
    Toolbox puts them in the table's order, leaving out its Date partition. Re-running a day
    replaces it rather than adding to it, so a day can safely be sent again; to add rows to a
    day instead, use INSERT_INTO. If your warehouse runs Hive 2.3 or 3.1 under Tez (ask whoever
    looks after it), a day that now comes back empty may keep its old rows (HIVE-18702). After editing a Saved table's Table
    reference, check it with check_table_reference(t, send=...).

    >>> daily_runs = Table("mart.daily_runs", date_partition="dt",
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"})
    >>> print(to_hive(statement(
    ...     INSERT_OVERWRITE(daily_runs),
    ...     SELECT(job_runs.job_id, AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24")),
    ...     GROUP_BY(job_runs.dt, job_runs.job_id),
    ... )))
    INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt = '2026-09-24')
    SELECT
      job_runs.job_id,
      COUNT(*) AS runs
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24'
    GROUP BY
      job_runs.dt,
      job_runs.job_id
    """
    return _write_clause("INSERT_OVERWRITE", table)


def INSERT_INTO(table):
    """Add rows to a day of a Saved table, keeping its rows; sent twice, it adds twice.

    It follows every rule of INSERT_OVERWRITE: it goes first, it writes the one day the
    Statement reads, and its columns are matched by name. The difference is what happens to
    the rows already in that day: INSERT_OVERWRITE replaces them, INSERT_INTO keeps them and
    adds more. Use it when a day's rows come from more than one table: send INSERT_OVERWRITE
    for the day first, from the first table, then INSERT_INTO from each other table. Sending
    the same INSERT_INTO twice adds its rows twice, so to redo a day, start again from its
    INSERT_OVERWRITE. Below, a day of failed runs gets the runs with a high alert added.

    >>> run_alerts = example_database.run_alerts
    >>> runs_to_review = Table("mart.runs_to_review", date_partition="dt",
    ...     columns={"run_id": "bigint", "dt": "string"})
    >>> print(to_hive(statement(
    ...     INSERT_INTO(runs_to_review),
    ...     SELECT_DISTINCT(run_alerts.run_id),
    ...     FROM(run_alerts),
    ...     WHERE(equals(run_alerts.dt, "2026-09-24"), equals(run_alerts.severity, "high")),
    ... )))
    INSERT INTO mart.runs_to_review PARTITION(dt = '2026-09-24')
    SELECT DISTINCT
      run_alerts.run_id
    FROM ops.run_alerts AS run_alerts
    WHERE
      run_alerts.dt = '2026-09-24' AND run_alerts.severity = 'high'
    """
    return _write_clause("INSERT_INTO", table)


# --- statement(...) ------------------------------------------------------------------------


def _check_order(clauses) -> None:
    for clause in clauses:
        if not isinstance(clause, Clause):
            refuse_what_the_other_edition_made(clause, "statement")
            _misuse(
                what=f"statement(...) was given {clause!r}, which isn't a clause.",
                why="A Statement is a list of clause functions such as SELECT(...) and "
                "FROM(...).",
                fix="Wrap it in its clause, such as WHERE(equals(...)).",
            )
    places = [clause._place() for clause in clauses]
    ranks = [ORDER.index(place) for place in places]
    # Only a join may come more than once: not two writes, nor SELECT with SELECT_DISTINCT.
    for place in ORDER:
        found = [clause._name for clause in clauses if clause._place() == place]
        if place != "JOIN" and len(found) > 1:
            _misuse(
                what=f"statement(...) has {' and '.join(found)}, but a Statement has only one "
                f"{place} clause.",
                why="A Statement is one query, so it has one of each clause (only JOINs may "
                "repeat), and it writes at most once.",
                fix="Keep one of them. Put all conditions in one WHERE, and send a second "
                "write as a Statement of its own.",
                error=ValueError,
            )
    if ranks != sorted(ranks):
        _misuse(
            what="statement(...) has its clauses out of SQL order: "
            + ", ".join(clause._name for clause in clauses) + ".",
            why="A Statement reads in SQL order, one clause each.",
            fix="Order them as INSERT_OVERWRITE or INSERT_INTO, SELECT, FROM, JOIN..., WHERE, "
            "GROUP_BY, HAVING, ORDER_BY, LIMIT, and put all conditions in one WHERE.",
            error=ValueError,
        )
    for needed in ("SELECT", "FROM"):
        if needed not in places:
            _misuse(what=f"statement(...) has no {needed}(...).",
                    why="Every Statement says what it returns and which table it reads.",
                    fix="Add SELECT(...) and FROM(...).", error=ValueError)


def statement(*clauses, returns_all_rows=False):
    """Assemble clause functions, in SQL order, into a Statement.

    It runs the Guards and Load limits that need the whole Statement. to_hive(s) gives the
    Hive string, and run(s, send=...) sends it. returns_all_rows=True drops the automatic
    LIMIT, if set_load_limits(rows=...) has set one.

    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id, job_runs.status),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ... )))
    SELECT
      job_runs.run_id,
      job_runs.status
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
    """
    _check_order(clauses)
    s = Statement()
    s._clauses = clauses
    s._returns_all_rows = returns_all_rows
    write = next((c for c in clauses if c._name in WRITES), None)
    s._write = write.table if write else None
    # How the write was called, for messages: INSERT_INTO(daily_runs).
    s._write_call = f"{write._name}({write.table._alias})" if write else None
    s._replaces_day = write is not None and write._name == "INSERT_OVERWRITE"
    select = next(c for c in clauses if c._name.startswith("SELECT"))
    s._outputs, s._distinct = select.outputs, select.distinct
    s._reads = [c for c in clauses if c._name == "FROM" or c._name in JOINS]
    s._where = _clause_part(clauses, "WHERE", "conditions")
    s._having = _clause_part(clauses, "HAVING", "conditions")
    s._group_by = _resolve_group_by(s, _clause_part(clauses, "GROUP_BY", "group_columns"))
    order = next((c for c in clauses if c._name == "ORDER_BY"), None)
    s._order_by = order.sort_keys if order else []
    s._limit = next((c.n for c in clauses if c._name == "LIMIT"), None)
    _check_tables(s)
    _run_guards(s)
    _run_load_limits(s, order)
    return s


def _clause_part(clauses, name: str, part: str) -> list:
    return next((getattr(c, part) for c in clauses if c._name == name), [])


def _resolve_group_by(s: Statement, items: list) -> list[Column]:
    by_name = {name: column for column, name in s._outputs}
    resolved = []
    for item in items:
        if isinstance(item, str) and item not in by_name:
            _misuse(
                what=f"GROUP_BY({item!r}): SELECT has no column called {item!r}.",
                why="A name in GROUP_BY stands for a calculation named in SELECT.",
                fix=f"Use one of: {', '.join(by_name)}.",
                error=ValueError,
            )
        resolved.append(by_name[item] if isinstance(item, str) else item)
    return resolved


def derived_tables(s: Statement) -> list[Table]:
    """Every Derived table a Statement reads, directly or not, each after those it reads."""
    found = []
    for read in s._reads:
        table = read.table
        if table._statement is None:
            continue
        for inner in [*derived_tables(table._statement), table]:
            if not any(inner._statement is seen._statement for seen in found):
                found.append(inner)
    return found


def _check_tables(s: Statement) -> None:
    aliases = [read.table._alias for read in s._reads]
    twice = sorted({alias for alias in aliases if aliases.count(alias) > 1})
    if twice:
        _misuse(
            what=f"statement(...) reads two tables called {', '.join(twice)}.",
            why="In the SQL a table is called by its short name, so the two would be mixed up.",
            fix=f'Give one a second name with AS, such as AS({twice[0]}, "earlier").',
            error=ValueError,
        )
    names = {}
    for table in derived_tables(s):
        if table._name in names and names[table._name] is not table._statement:
            _misuse(
                what=f"statement(...) reads two different Derived tables called {table._name!r}.",
                why="Each becomes a named part of the same Hive string, so the names must differ.",
                fix="Give one of them another name in derived(...).",
                error=ValueError,
            )
        names[table._name] = table._statement
    used = set()
    for tree in _trees(s):
        used |= {column.table for column in tree.find_all("Column") if column.table}
    unread = sorted(used - set(aliases))
    if unread:
        _misuse(
            what=f"statement(...) uses columns of {', '.join(unread)}, which it doesn't read.",
            why="A Statement can only use columns of the tables in its FROM and JOINs.",
            fix=f"Add {unread[0]} with FROM(...) or JOIN(...), or use another table's column.",
            error=ValueError,
        )
    for condition in s._where:
        if condition._aggregate:
            _misuse(
                what=f"WHERE has {condition!r}, which tests a count or a sum.",
                why="WHERE tests single rows, before any counting; Hive would refuse it.",
                fix="Move it to HAVING(...), which tests groups after GROUP_BY.",
                error=ValueError,
            )


def _trees(s: Statement) -> list[Node]:
    trees = [column._tree for column, _ in s._outputs]
    trees += [c._tree for c in s._where + s._having]
    trees += [read.on._tree for read in s._reads if read.on is not None]
    trees += [column._tree for column in s._group_by] + list(s._order_by)
    return trees


def _run_guards(s: Statement) -> None:
    _guard_group_by(s)
    for read in s._reads:
        if read._name != "LEFT_JOIN":
            continue
        for condition in s._where:
            if read.table._alias in condition._tables() and not condition._tests_for_null:
                guard_left_join_then_where(read.table._alias, repr(condition),
                                           read.keeps_only_matches)
    if s._write is not None:
        table = s._write
        expected = [c for c in table._columns if c != table._date_partition]
        names = [name for _, name in s._outputs]
        missing = [c for c in expected if c not in names]
        extra = [n for n in names if n not in expected]
        if missing or extra:
            guard_write_lines_up(s._write_call, table._alias, missing, extra)


def _guard_group_by(s: Statement) -> None:
    aggregates = any(column._aggregate for column, _ in s._outputs)
    if not (aggregates or s._group_by or s._having):
        return
    groups = [column._tree for column in s._group_by]
    grouped = {(c.table, c.name) for tree in groups for c in tree.find_all("Column")}
    missing = []
    for column, _ in s._outputs:
        if column._aggregate or any(column._tree == tree for tree in groups):
            continue
        used = {(c.table, c.name) for c in column._tree.find_all("Column")}
        if not used <= grouped:
            missing.append(repr(column))
    if missing:
        guard_missing_group_by(missing)


def read_spans(s: Statement) -> list[tuple[Clause, object]]:
    """Each read of a partitioned table in `s`, with the days its bounds let through."""
    inner = [read.on for read in s._reads if read._name == "JOIN"]
    everywhere = combined_spans(s._where + inner)
    found = []
    for read in s._reads:
        table = read.table
        if table._statement is not None or table._date_partition is None:
            continue
        spans = everywhere
        if read._name == "LEFT_JOIN":
            spans = combined_spans([read.on] + (s._where + inner if read.keeps_only_matches
                                                else []))
        found.append((read, spans.get((table._alias, table._date_partition))))
    return found


def _run_load_limits(s: Statement, order: Clause | None) -> None:
    for read, span in read_spans(s):
        if span is None or not span.is_bounded():
            table = read.table
            load_limit_date_bound(read._call(), table._alias, table._name,
                                  table._date_partition, read.reads_all_partitions)
    if order is not None and s._limit is None:
        load_limit_order_by(order.sorts_everything)


# --- derived(...) --------------------------------------------------------------------------


def _derived_key(s: Statement) -> list[str] | None:
    names = [name for _, name in s._outputs]
    if s._distinct:
        return names
    if s._group_by:
        key = []
        for group in s._group_by:
            match = [n for column, n in s._outputs if column._tree == group._tree]
            if not match:
                return None
            key.append(match[0])
        return key
    if any(column._aggregate for column, _ in s._outputs):
        return []
    if len(s._reads) != 1 or s._reads[0].table._key is None:
        return None
    source = s._reads[0].table
    plain = {column._name: n for column, n in s._outputs if column._table is source}
    if all(k in plain for k in source._key):
        return [plain[k] for k in source._key]
    return None


def derived(name, statement):
    """Name a Statement so another Statement can read it like a table.

    You then use its output columns like a Table reference's, as runs_per_job.runs, and a typo
    in one is caught the same way. The Toolbox writes it at the top of the Hive, as WITH
    runs_per_job AS (...). The warehouse usually works it out again each time the Statement
    reads it, so if it gets slow, write it to a Saved table instead. Its key is its GROUP_BY
    columns.

    >>> runs_per_job = derived("runs_per_job", statement(
    ...     SELECT(job_runs.job_id, AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY(job_runs.job_id),
    ... ))
    >>> print(to_hive(statement(
    ...     SELECT(jobs.job_name, runs_per_job.runs),
    ...     FROM(runs_per_job),
    ...     JOIN(jobs, ON=equals(jobs.job_id, runs_per_job.job_id)),
    ... )))
    WITH runs_per_job AS (
      SELECT
        job_runs.job_id,
        COUNT(*) AS runs
      FROM ops.job_runs AS job_runs
      WHERE
        job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
      GROUP BY
        job_runs.job_id
    )
    SELECT
      jobs.job_name,
      runs_per_job.runs
    FROM runs_per_job
    JOIN ops.jobs AS jobs
      ON jobs.job_id = runs_per_job.job_id
    """
    if not isinstance(name, str) or not SIMPLE_NAME.fullmatch(name):
        _misuse(what=f"derived({name!r}, ...) needs a plain name.",
                why="The name is how the SQL calls it.",
                fix='Use letters, digits and _, such as derived("latest", ...).',
                error=ValueError)
    if not isinstance(statement, Statement) or statement._ddl is not None:
        refuse_what_the_other_edition_made(statement, "derived")
        _misuse(what=f"derived({name!r}, ...) was given {statement!r}.",
                why="derived names a Statement made by statement(...).",
                fix="Pass statement(SELECT(...), FROM(...), ...).")
    if statement._write is not None:
        _misuse(what=f"derived({name!r}, ...) was given a write.",
                why="A Statement that writes a Saved table returns no rows to read.",
                fix="Read the Saved table through its own Table reference instead.",
                error=ValueError)
    if statement._order_by and statement._limit is None:
        guard_order_by_in_derived_table(name)
    columns = {n: column._type for column, n in statement._outputs}
    table = Table(name, columns=columns, date_partition=None)
    table._statement = statement
    table._key = _derived_key(statement)
    table._not_adding_up_because = {
        n: column._not_adding_up_because
        for column, n in statement._outputs if not column._adds_up
    }
    return table


__all__ = [
    "SELECT",
    "SELECT_DISTINCT",
    "AS",
    "FROM",
    "JOIN",
    "LEFT_JOIN",
    "CROSS_JOIN",
    "WHERE",
    "GROUP_BY",
    "HAVING",
    "ORDER_BY",
    "LIMIT",
    "INSERT_OVERWRITE",
    "INSERT_INTO",
    "statement",
    "derived",
]
