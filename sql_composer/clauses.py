# SQL Composer 2.0, exported 2026-09-25 20:53 - generated from dev, do not edit
"""Clause functions: SELECT, FROM, JOIN, WHERE and the rest, assembled by statement(...).

A Statement is a list of clause functions written in SQL order, one per SQL clause:

    statement(SELECT(...), FROM(job_runs), WHERE(...), GROUP_BY(...))

statement(...) runs the Guards and Load limits that need the whole Statement, and
to_hive(...) turns it into the Hive string. derived(name, statement) names a Statement so
another Statement can read it like a table.
"""

from __future__ import annotations

from sqlglot import exp

from .calculations import Ordering, ordered
from .conditions import Condition, combined_spans
from .refusals import (
    four_part_message,
    guard_cross_join,
    guard_left_join_then_where,
    guard_missing_group_by,
    guard_order_by_in_derived_table,
    guard_unnamed_calculation,
    guard_write_lines_up,
    load_limit_date_bound,
    load_limit_order_by,
    warning_repeated_rows,
)
from .tables import SIMPLE_NAME, Column, Table, aliased, hive_text, identifier

TOOLBOX_VERSION = "2.0"

ORDER = ["INSERT_OVERWRITE", "SELECT", "FROM", "JOIN", "WHERE", "GROUP_BY", "HAVING",
         "ORDER_BY", "LIMIT"]
JOINS = ("JOIN", "LEFT_JOIN", "CROSS_JOIN")


def _misuse(what: str, why: str, fix: str, error=TypeError):
    raise error(four_part_message(what=what, why=why, fix=fix, opt_out=None))


class Clause:
    """One clause of a Statement, made by a clause function such as SELECT(...)."""

    def __init__(self, name: str, **parts):
        self._name = name
        self.__dict__.update(parts)

    def _rank(self) -> int:
        return ORDER.index("JOIN" if self._name in JOINS else self._name.replace("_DISTINCT", ""))

    def _call(self) -> str:
        """How this clause was written, for messages: FROM(job_runs), JOIN(jobs, ON=...)."""
        on = ", ON=..." if getattr(self, "on", None) is not None else ""
        return f"{self._name}({self.table._alias}{on})"

    def __repr__(self) -> str:
        return f"<{self._name} clause - put it in statement(...)>"


class Named:
    """A column or calculation with the name it gets in the result. Made by AS(...)."""

    def __init__(self, column: Column, name: str):
        self._column = column
        self._name = name

    def __repr__(self) -> str:
        return hive_text(exp.alias_(self._column._tree.copy(), identifier(self._name)))


class Statement:
    """A query, assembled by statement(...). to_hive(s) gives its Hive string."""

    _ddl = None

    def __repr__(self) -> str:
        if self._ddl is not None:
            return "<Statement - print(to_hive(s)) shows it>"
        reads = ", ".join(read.table._name for read in self._reads)
        return f"<Statement reading {reads} - print(to_hive(s)) shows its Hive>"


# --- Naming things -------------------------------------------------------------------------


def AS(expression, name):
    """Give a calculation its name in the result, or a table a second name.

    Every calculation in SELECT needs a name, which becomes its column in pandas. Arithmetic
    uses Python's + - * / and comes out bracketed. Hive's / always gives a decimal number
    (7 / 2 is 3.5), and gives NULL rather than an error when dividing by zero.

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
        _misuse(
            what=f"{call}({table._alias}, ON={on!r}): ON= isn't a condition.",
            why="ON= says which rows of the two tables belong together.",
            fix=f"Pass a condition, such as ON=equals({table._alias}.job_id, job_runs.job_id).",
        )
    return on


def _matched_columns(table: Table, on: Condition) -> list[str]:
    """The columns of `table` that ON= pins with an equals at its top level."""
    parts = list(on._tree.flatten()) if isinstance(on._tree, exp.And) else [on._tree]
    matched = set()
    for part in parts:
        if not isinstance(part, exp.EQ):
            continue
        for mine, other in ((part.this, part.expression), (part.expression, part.this)):
            if isinstance(mine, exp.Column) and mine.table == table._alias and not (
                    isinstance(other, exp.Column) and other.table == table._alias):
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
            _misuse(
                what=f"GROUP_BY was given {item!r}.",
                why="It groups by columns, or by the name of a calculation in SELECT.",
                fix='Pass columns or output names, such as GROUP_BY(job_runs.status, "week").',
            )
    return Clause("GROUP_BY", items=items)


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
    Hive sorts everything on one machine: sort in pandas after run(...), or pass
    sorts_everything=True. In a Statement you pass to derived(...), an ORDER_BY without
    LIMIT is refused even with sorts_everything=True: Hive ignores the order of rows there,
    so a Statement that reads it can't rely on that order.

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
            _misuse(what=f"ORDER_BY was given {item!r}.",
                    why="It sorts by columns or output names.",
                    fix="Pass a column, an output name, or descending(...).")
    trees = [ordered(item, "ORDER_BY(...)") for item in items]
    return Clause("ORDER_BY", trees=trees, sorts_everything=sorts_everything)


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


def INSERT_OVERWRITE(table):
    """Write the Statement's rows into one day of a Saved table, replacing that day.

    It goes first, before SELECT. The day written is the one day the Statement reads, so
    loop over by_day(s) to write several. Columns are matched to the Saved table by name,
    and the Toolbox puts them in the table's order, leaving out its Date partition.
    Re-running a day replaces it rather than adding to it. On Hive 2.3 and 3.1 under Tez, a
    day that now comes back empty may keep its old rows (HIVE-18702). After editing a Saved
    table's Table reference, check it with check_table_reference(t, send=...).

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
    table = _need_table(table, "INSERT_OVERWRITE(...)")
    if table._statement is not None or table._date_partition is None:
        _misuse(
            what=f"INSERT_OVERWRITE({table._alias}) needs a Saved table with a Date partition.",
            why="A write replaces one day of a real table, so the table needs a Date "
            "partition to write the day into.",
            fix="Pass the Saved table's own Table reference, with date_partition=... set.",
            error=ValueError,
        )
    return Clause("INSERT_OVERWRITE", table=table)


# --- statement(...) ------------------------------------------------------------------------


def _check_order(clauses) -> None:
    for clause in clauses:
        if not isinstance(clause, Clause):
            _misuse(
                what=f"statement(...) was given {clause!r}, which isn't a clause.",
                why="A Statement is a list of clause functions such as SELECT(...) and "
                "FROM(...).",
                fix="Wrap it in its clause, such as WHERE(equals(...)).",
            )
    ranks = [clause._rank() for clause in clauses]
    names = [clause._name for clause in clauses]
    once = [n for n in set(names) if n not in JOINS and names.count(n) > 1]
    if ranks != sorted(ranks) or once:
        _misuse(
            what="statement(...) has its clauses out of SQL order, or one clause twice: "
            + ", ".join(names) + ".",
            why="A Statement reads in SQL order, one clause each.",
            fix="Order them as INSERT_OVERWRITE, SELECT, FROM, JOIN..., WHERE, GROUP_BY, "
            "HAVING, ORDER_BY, LIMIT, and put all conditions in one WHERE.",
            error=ValueError,
        )
    present = {ORDER[rank] for rank in ranks}
    for needed in ("SELECT", "FROM"):
        if needed not in present:
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
    s._write = next((c.table for c in clauses if c._name == "INSERT_OVERWRITE"), None)
    select = next(c for c in clauses if c._name.startswith("SELECT"))
    s._outputs, s._distinct = select.outputs, select.distinct
    s._reads = [c for c in clauses if c._name == "FROM" or c._name in JOINS]
    s._where = _clause_part(clauses, "WHERE", "conditions")
    s._having = _clause_part(clauses, "HAVING", "conditions")
    s._group_by = _resolve_group_by(s, _clause_part(clauses, "GROUP_BY", "items"))
    order = next((c for c in clauses if c._name == "ORDER_BY"), None)
    s._order_by = order.trees if order else []
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
        used |= {column.table for column in tree.find_all(exp.Column) if column.table}
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


def _trees(s: Statement) -> list[exp.Expression]:
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
            if read.table._alias in condition._tables() and condition._kind != "is_null":
                guard_left_join_then_where(read.table._alias, repr(condition),
                                           read.keeps_only_matches)
    if s._write is not None:
        table = s._write
        expected = [c for c in table._columns if c != table._date_partition]
        names = [name for _, name in s._outputs]
        missing = [c for c in expected if c not in names]
        extra = [n for n in names if n not in expected]
        if missing or extra:
            guard_write_lines_up(table._alias, missing, extra)


def _guard_group_by(s: Statement) -> None:
    aggregates = any(column._aggregate for column, _ in s._outputs)
    if not (aggregates or s._group_by or s._having):
        return
    groups = [column._tree for column in s._group_by]
    grouped = {(c.table, c.name) for tree in groups for c in tree.find_all(exp.Column)}
    missing = []
    for column, _ in s._outputs:
        if column._aggregate or any(column._tree == tree for tree in groups):
            continue
        used = {(c.table, c.name) for c in column._tree.find_all(exp.Column)}
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

    You then use its output columns like a Table reference's, as runs_per_job.runs, and a
    typo in one is caught the same way. The Toolbox writes it at the top of the Hive, as
    WITH runs_per_job AS (...). Hive works it out again each time the Statement reads it,
    so if it gets slow, write it to a Saved table instead. Its key is its GROUP_BY columns.

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
    "statement",
    "derived",
]
