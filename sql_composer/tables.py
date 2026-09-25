"""Table references: Table, and the functions that read, write and check one.

A Table reference is one `Table(...)` call describing one table: its columns and their Hive
types, its Date partition, its key, and the columns that don't add up. Its columns are its
attributes (`job_runs.status`), so a typo fails at once, with the column list.

This file also holds the column object those attributes return, the one place values become
Hive literals, and the one place the Toolbox writes SQL text (`hive_text`).
"""

from __future__ import annotations

import copy
import datetime
import decimal
import difflib
import json
import keyword
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sqlglot import exp
from sqlglot.errors import ErrorLevel

from .refusals import (
    four_part_message,
    guard_none_in_condition,
    guard_not_a_number,
    guard_time_of_day,
)

TOOLBOX_VERSION = "2.0"

HIVE = "hive"
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
SIMPLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
TABLE_NAME = re.compile(r"[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)?")

# Hive's reserved words: a column with one of these names must be written in backticks.
HIVE_RESERVED = frozenset(
    """ALL ALTER AND ARRAY AS AUTHORIZATION BETWEEN BIGINT BINARY BOOLEAN BOTH BY CACHE CASE
    CAST CHAR COLUMN COMMIT CONF CONSTRAINT CREATE CROSS CUBE CURRENT CURRENT_DATE
    CURRENT_TIMESTAMP CURSOR DATABASE DATE DAYOFWEEK DECIMAL DELETE DESCRIBE DISTINCT DOUBLE
    DROP ELSE END EXCHANGE EXISTS EXTENDED EXTERNAL EXTRACT FALSE FETCH FLOAT FLOOR FOLLOWING
    FOR FOREIGN FROM FULL FUNCTION GRANT GROUP GROUPING HAVING IF IMPORT IN INNER INSERT INT
    INTEGER INTERSECT INTERVAL INTO IS JOIN LATERAL LEFT LESS LIKE LOCAL MACRO MAP MORE NONE
    NOT NULL NUMERIC OF ON ONLY OR ORDER OUT OUTER OVER PARTIALSCAN PARTITION PERCENT
    PRECEDING PRECISION PRESERVE PRIMARY PROCEDURE RANGE READS REDUCE REFERENCES REGEXP
    REVOKE RIGHT RLIKE ROLLBACK ROLLUP ROW ROWS SELECT SET SMALLINT START SYNC TABLE
    TABLESAMPLE THEN TIME TIMESTAMP TO TRANSFORM TRIGGER TRUE TRUNCATE UNBOUNDED UNION
    UNIQUEJOIN UPDATE USER USING UTC_TMESTAMP VALUES VARCHAR VIEWS WHEN WHERE WINDOW
    WITH""".split()
)

# Hive aggregate functions that sqlglot may not know as aggregates when named in hive_function.
HIVE_AGGREGATES = frozenset(
    """avg collect_list collect_set corr count covar_pop covar_samp histogram_numeric max min
    percentile percentile_approx stddev stddev_pop stddev_samp sum var_pop var_samp variance
    """.split()
)

NUMBER_TYPES = ("tinyint", "smallint", "int", "integer", "bigint", "float", "double", "decimal",
                "numeric", "real")
STRING_TYPES = ("string", "varchar", "char")


# --- The one place the Toolbox writes SQL text ---------------------------------------------


def hive_text(tree: exp.Expression, pretty: bool = False) -> str:
    """Write a sqlglot tree as Hive. Nothing else in the Toolbox calls `.sql()`."""
    return tree.sql(dialect=HIVE, pretty=pretty, unsupported_level=ErrorLevel.RAISE)


def identifier(name: str) -> exp.Identifier:
    """A name as Hive needs it: in backticks only when it isn't a plain word."""
    plain = SIMPLE_NAME.fullmatch(name) and name.upper() not in HIVE_RESERVED
    return exp.to_identifier(name, quoted=not plain)


# --- The call that made a calculation or condition, for the lineage -------------------------


def made_by(tree: exp.Expression, name: str, *args, **keywords) -> exp.Expression:
    """Note on `tree` the Toolbox call that made it, such as week_start(job_runs.dt).

    The note leaves the Hive unchanged. The lineage shows it, since it reads the way the
    Statement was written, where sqlglot may have rewritten the Hive.
    """
    parts = [_argument_text(arg) for arg in args]
    parts += [f"{key}={_argument_text(value)}" for key, value in keywords.items()
              if value is not None]
    tree.meta["call"] = f"{name}({', '.join(parts)})"
    return tree


def _argument_text(value) -> str:
    if hasattr(value, "_tree"):
        return readable(value._tree)
    if hasattr(value, "_target"):
        return f"descending({_argument_text(value._target)})"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_argument_text(item) for item in value) + "]"
    return repr(value)


def readable(tree: exp.Expression) -> str:
    """A calculation or condition as it was written: its Toolbox calls, else its Hive."""
    if "call" in tree.meta:
        return tree.meta["call"]
    copied = tree.copy()
    for node in list(copied.find_all(exp.Expression)):
        if node is not copied and "call" in node.meta:
            node.replace(exp.Var(this=node.meta["call"]))
    return hive_text(copied)


# --- Columns and calculations --------------------------------------------------------------


def _no_operator(symbol: str, instead: str) -> None:
    raise TypeError(
        four_part_message(
            what=f"A column was used with Python's {symbol}.",
            why="Python would compare the Python objects, not the values in the table, and "
            "the result would quietly be True or False instead of a condition.",
            fix=f"Use {instead}.",
            opt_out=None,
        )
    )


class Column:
    """One column of a table, or a calculation made from columns.

    Arithmetic works with Python's + - * / and comes out bracketed. Comparisons don't: use
    the condition functions, such as equals(...), instead of ==.
    """

    def __init__(self, tree, *, table=None, name=None, type=None, adds_up=True,
                 not_adding_up_because=None, aggregate=False, window=False):
        self._tree = tree
        self._table = table
        self._name = name
        self._type = type
        self._adds_up = adds_up
        self._not_adding_up_because = not_adding_up_because
        self._aggregate = aggregate
        self._window = window

    def __repr__(self) -> str:
        return hive_text(self._tree)

    __hash__ = object.__hash__

    def __eq__(self, other):
        _no_operator("==", "equals(column, value)")

    def __ne__(self, other):
        _no_operator("!=", "not_equals(column, value)")

    def __lt__(self, other):
        _no_operator("<", "less_than(column, value)")

    def __le__(self, other):
        _no_operator("<=", "at_most(column, value)")

    def __gt__(self, other):
        _no_operator(">", "more_than(column, value)")

    def __ge__(self, other):
        _no_operator(">=", "at_least(column, value)")

    def __and__(self, other):
        _no_operator("&", "all_of(...), or separate conditions in WHERE(...)")

    __rand__ = __and__

    def __or__(self, other):
        _no_operator("|", "any_of(...)")

    __ror__ = __or__

    def __invert__(self):
        _no_operator("~", "the opposite condition, such as not_equals(...) or is_not_null(...)")

    def __bool__(self):
        _no_operator("if, and, or or not", "a condition such as equals(...)")

    def __add__(self, other):
        return arithmetic(self, other, exp.Add, "+")

    def __radd__(self, other):
        return arithmetic(other, self, exp.Add, "+")

    def __sub__(self, other):
        return arithmetic(self, other, exp.Sub, "-")

    def __rsub__(self, other):
        return arithmetic(other, self, exp.Sub, "-")

    def __mul__(self, other):
        return arithmetic(self, other, exp.Mul, "*")

    def __rmul__(self, other):
        return arithmetic(other, self, exp.Mul, "*")

    def __truediv__(self, other):
        return arithmetic(self, other, exp.Div, "/")

    def __rtruediv__(self, other):
        return arithmetic(other, self, exp.Div, "/")

    def __neg__(self):
        return arithmetic(0, self, exp.Sub, "-")


def _bracketed(tree: exp.Expression) -> exp.Expression:
    if isinstance(tree, (exp.Add, exp.Sub, exp.Mul, exp.Div)):
        return exp.Paren(this=tree)
    return tree


def arithmetic(left, right, node, symbol: str) -> Column:
    """Build `left <symbol> right`, bracketing each side that is itself arithmetic."""
    sides = []
    for side in (left, right):
        if isinstance(side, Column):
            sides.append(side)
            continue
        if isinstance(side, bool) or not isinstance(side, (int, float, decimal.Decimal,
                                                               np.number)):
            raise TypeError(
                four_part_message(
                    what=f"{symbol} was used with {side!r}.",
                    why="Arithmetic on a column needs a number or another column.",
                    fix="Use a number, such as job_runs.duration_mins / 60.",
                    opt_out=None,
                )
            )
        sides.append(Column(literal(side, call=f"a {symbol} calculation", in_condition=False)))
    left, right = sides
    adds_up = left._adds_up and right._adds_up and node is not exp.Div
    because = "a division" if node is exp.Div else (
        left._not_adding_up_because or right._not_adding_up_because)
    return Column(
        node(this=_bracketed(left._tree.copy()), expression=_bracketed(right._tree.copy())),
        adds_up=adds_up,
        not_adding_up_because=None if adds_up else because,
        aggregate=left._aggregate or right._aggregate,
        window=left._window or right._window,
    )


def has_aggregate(tree: exp.Expression) -> bool:
    """True when the tree adds rows up (COUNT, SUM, ...) outside a window."""
    for node in tree.find_all(exp.AggFunc, exp.Anonymous):
        if node.find_ancestor(exp.Window):
            continue
        if isinstance(node, exp.AggFunc) or str(node.name).lower() in HIVE_AGGREGATES:
            return True
    return False


# --- Values ------------------------------------------------------------------------------


def type_family(hive_type: str | None) -> str | None:
    """The family of a Hive type: number, string, date, timestamp, boolean, or None."""
    if not hive_type:
        return None
    word = re.match(r"[a-z_]+", hive_type.strip().lower())
    word = word.group(0) if word else ""
    if word in NUMBER_TYPES or hive_type.strip().lower().startswith("double precision"):
        return "number"
    if word in STRING_TYPES:
        return "string"
    if word in ("date", "timestamp", "boolean"):
        return word
    return None


def _python_family(value) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float, decimal.Decimal)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, datetime.datetime):
        return "timestamp"
    return "date"


ACCEPTS = {
    "number": {"number"},
    "string": {"string", "date", "timestamp"},
    "date": {"date", "string", "timestamp"},
    "timestamp": {"timestamp", "date", "string"},
    "boolean": {"boolean"},
}


def _check_type(value, column: Column | None, call: str) -> None:
    family = type_family(column._type) if column is not None else None
    if family is None or _python_family(value) in ACCEPTS[family]:
        return
    raise TypeError(
        four_part_message(
            what=f"{call} compares {column!r}, a {column._type} column, with {value!r}.",
            why="Hive would quietly convert one side to the other's type, so the comparison "
            "could match nothing or the wrong rows.",
            fix=f"Pass a value of the column's own type, such as {_example_of(family)}.",
            opt_out=None,
        )
    )


def _example_of(family: str) -> str:
    return {
        "number": "42",
        "string": '"FAILED"',
        "date": '"2026-09-25"',
        "timestamp": '"2026-09-25 13:00:00"',
        "boolean": "True",
    }[family]


def date_format_of(column: Column | None) -> str:
    """The date pattern for values compared with this column."""
    table = column._table if column is not None else None
    if table is not None and table._date_partition == column._name:
        return table._date_format
    return DEFAULT_DATE_FORMAT


def is_date_partition(column: Column | None) -> bool:
    table = column._table if column is not None else None
    return table is not None and table._date_partition is not None and (
        table._date_partition == column._name)


def as_date(value, column: Column, call: str) -> datetime.date:
    """A value compared with a Date partition, as a Python date. Refuses what isn't a day."""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    pattern = column._table._date_format
    try:
        return datetime.datetime.strptime(str(value), pattern).date()
    except ValueError:
        pass
    example = datetime.date(2026, 9, 25).strftime(pattern)
    raise ValueError(
        four_part_message(
            what=f"{call} compares the Date partition {column!r} with {value!r}, which isn't "
            f"a day written like {example!r}.",
            why="Hive compares Date partition values as text, so a differently written day "
            "would match no days, or the wrong ones.",
            fix=f"Write the day as {example!r}, or pass a datetime.date.",
            opt_out=None,
        )
    )


def _number_text(value) -> str | None:
    """A number's Hive text, written by the Toolbox rather than by the value's own str()."""
    if isinstance(value, int):
        return int.__repr__(value)
    if isinstance(value, float):
        text = float.__repr__(value)
        return None if text in ("nan", "inf", "-inf") else text
    if not decimal.Decimal.is_finite(value):
        return None
    return decimal.Decimal.__format__(value, "f")


SINGLE_VALUES = (bool, int, float, decimal.Decimal, str, datetime.date)


def _plain(value):
    """A numpy or pandas value as the plain Python value it stands for."""
    if isinstance(value, np.datetime64):
        return pd.Timestamp(value)
    if isinstance(value, np.generic):
        return value.item()
    if value is pd.NaT or value is pd.NA:
        return None
    return value


def literal(value, *, call: str, column: Column | None = None, position: str = "the value",
            in_condition: bool = True) -> exp.Expression:
    """Turn a Python value into a Hive literal. The only way a value enters a Statement."""
    if isinstance(value, Column):
        return value._tree.copy()
    value = _plain(value)
    if value is None:
        if in_condition:
            guard_none_in_condition(call)
        return exp.Null()
    if not isinstance(value, SINGLE_VALUES):
        raise TypeError(
            four_part_message(
                what=f"{call} was given {value!r}, which isn't a single value.",
                why="A column is compared with one number, string, date or bool at a time.",
                fix="For several values use is_in(column, [...]); for a column pass the column.",
                opt_out=None,
            )
        )
    _check_type(value, column, call)
    if isinstance(value, bool):
        return exp.true() if value else exp.false()
    if isinstance(value, str):
        return exp.Literal.string(str.__str__(value))
    if isinstance(value, datetime.date):
        return exp.Literal.string(_date_text(value, column, call))
    text = _number_text(value)
    if text is None:
        guard_not_a_number(call, position, value)
    return exp.Literal.number(text)


def _date_text(value: datetime.date, column: Column | None, call: str) -> str:
    """A date as its day, or a timestamp in full when the column is typed as a timestamp."""
    if not isinstance(value, datetime.datetime):
        return value.strftime(date_format_of(column))
    if type_family(column._type if column is not None else None) == "timestamp":
        return value.isoformat(sep=" ")
    if value.time() != datetime.time(0, 0):
        guard_time_of_day(call, value)
    return value.date().strftime(date_format_of(column))


# --- Table ---------------------------------------------------------------------------------


def _refuse_table(what: str, why: str, fix: str):
    raise ValueError(four_part_message(what=what, why=why, fix=fix, opt_out=None))


def _check_date_format(date_format: str) -> None:
    rest = date_format
    for directive in ("%Y", "%m", "%d"):
        if rest.count(directive) != 1:
            _refuse_table(
                what=f"date_format={date_format!r} doesn't have {directive} exactly once.",
                why="A Date partition's pattern needs the year, the month and the day.",
                fix='Use Python\'s strptime pattern for the partition\'s days, such as "%Y%m%d".',
            )
        rest = rest.replace(directive, "")
    if "%" in rest or "'" in rest:
        _refuse_table(
            what=f"date_format={date_format!r} has something other than %Y, %m and %d.",
            why="Only the year, month and day can be turned into Hive's own pattern.",
            fix='Use only %Y, %m, %d and separators, such as "%Y%m%d" or "%Y/%m/%d".',
        )


def hive_date_pattern(date_format: str) -> str:
    """Python's "%Y-%m-%d" as Hive's "yyyy-MM-dd"."""
    return date_format.replace("%Y", "yyyy").replace("%m", "MM").replace("%d", "dd")


def _names(value, argument: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, (list, tuple)):
        _refuse_table(
            what=f"{argument}={value!r} isn't a list of column names.",
            why="The Toolbox reads it as the names of columns in this table.",
            fix=f'Write it as a list, such as {argument}=["run_id"].',
        )
    return list(value)


class Table:
    """A Table reference: one table's columns and types, Date partition and key.

    Its columns become attributes, so `job_runs.status` is checked when your script runs:
    a typo stops with the list of real columns. Write one per table, generated once by
    write_table_reference(...) and then yours to edit.

    - `columns` maps each column to its Hive type as Hive prints it ("bigint",
      "decimal(10,2)"), or None when you don't know it. A typed column gets its values checked.
    - `date_partition` is required: the one date column the table is partitioned by, which
      every Statement must bound at both ends, or None for a table that has none.
    - `key` lists the columns that pick out one row. JOIN warns when a join doesn't use all
      of them.
    - `does_not_add_up` lists columns that are averages, ratios or distinct counts, which
      sum_of(...) and average_of(...) refuse to add up.
    - `date_format` is needed only when the Date partition's days aren't written like
      "2026-09-25", for example date_format="%Y%m%d". The time zone is whatever the table
      uses; the Toolbox doesn't convert it.

    A column whose name is a Python word, such as `from`, is reached with getattr(t, "from").

    >>> job_runs
    Table('ops.job_runs', columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt)
    >>> job_runs.status
    job_runs.status
    >>> job_runs.stauts
    Traceback (most recent call last):
    ...
    AttributeError: job_runs has no column 'stauts'. Did you mean 'status'? Its columns are: run_id, job_id, status, duration_mins, avg_retry_secs, dt.
    """

    def __init__(self, name, columns, date_partition, key=None, does_not_add_up=(),
                 date_format=None):
        if not isinstance(name, str) or not TABLE_NAME.fullmatch(name):
            _refuse_table(
                what=f"Table({name!r}, ...) isn't a table name.",
                why="A Hive table name is letters, digits and _, optionally after a database "
                "name and a dot.",
                fix='Write it like "ops.job_runs".',
            )
        if not isinstance(columns, dict) or not columns:
            _refuse_table(
                what=f"Table({name!r}, columns=...) needs a dict of column names and types.",
                why="The columns are what a Statement can use.",
                fix='Write columns={"run_id": "bigint", "status": "string", ...}.',
            )
        self._name = name
        self._alias = name.split(".")[-1]
        self._columns = {str(column): kind for column, kind in columns.items()}
        self._date_partition = date_partition
        self._key = _names(key, "key") or None
        self._does_not_add_up = _names(does_not_add_up, "does_not_add_up")
        self._date_format = date_format or DEFAULT_DATE_FORMAT
        self._statement = None
        self._not_adding_up_because = {
            column: "listed in does_not_add_up in its Table reference"
            for column in self._does_not_add_up
        }
        self._check_own_columns(date_format)

    def _check_own_columns(self, date_format) -> None:
        named = {"date_partition": [] if self._date_partition is None else [
            self._date_partition]}
        named["key"] = self._key or []
        named["does_not_add_up"] = self._does_not_add_up
        for argument, names in named.items():
            for column in names:
                if column not in self._columns:
                    _refuse_table(
                        what=f"Table({self._name!r}): {argument} names {column!r}, which isn't "
                        "one of its columns.",
                        why="Every name there must be a column in columns={...}.",
                        fix=f"Use one of: {', '.join(self._columns)}.",
                    )
        if date_format is not None:
            if self._date_partition is None:
                _refuse_table(
                    what=f"Table({self._name!r}) has a date_format but no date_partition.",
                    why="date_format says how the Date partition's days are written.",
                    fix="Remove date_format, or name the date_partition.",
                )
            _check_date_format(date_format)

    def __getattr__(self, attribute: str) -> Column:
        columns = self.__dict__.get("_columns")
        if columns is None or attribute.startswith("__"):
            raise AttributeError(attribute)
        if attribute in columns:
            return self._column(attribute)
        close = difflib.get_close_matches(attribute, list(columns), n=1)
        hint = f" Did you mean {close[0]!r}?" if close else ""
        raise AttributeError(
            f"{self._alias} has no column {attribute!r}.{hint} Its columns are: "
            f"{', '.join(columns)}."
        )

    def _column(self, name: str) -> Column:
        because = self._not_adding_up_because.get(name)
        return Column(
            exp.column(identifier(name), table=identifier(self._alias)),
            table=self,
            name=name,
            type=self._columns[name],
            adds_up=because is None,
            not_adding_up_because=because,
        )

    def __dir__(self):
        return sorted(set(super().__dir__()) | set(self._columns))

    def __repr__(self) -> str:
        kind = "derived" if self._statement is not None else "Table"
        return f"{kind}({self._name!r}, columns: {', '.join(self._columns)})"


def aliased(table: Table, name: str) -> Table:
    """A copy of a table called `name` in the SQL, for AS(table, name)."""
    if not isinstance(name, str) or not SIMPLE_NAME.fullmatch(name):
        raise ValueError(
            four_part_message(
                what=f"AS({table._alias}, {name!r}): {name!r} can't name a table.",
                why="A table's second name is a plain word in the SQL.",
                fix='Use letters, digits and _, such as AS(job_runs, "earlier").',
                opt_out=None,
            )
        )
    copied = copy.copy(table)
    copied._alias = name
    return copied


def source(table: Table) -> exp.Expression:
    """How a table is named after FROM or JOIN."""
    if table._statement is not None:
        base = exp.Table(this=identifier(table._name))
        if table._alias == table._name:
            return base
    else:
        parts = table._name.split(".")
        base = exp.Table(this=identifier(parts[-1]),
                         db=identifier(parts[0]) if len(parts) == 2 else None)
    return exp.alias_(base, identifier(table._alias), table=True)


def all_columns(t):
    """Every column of a Table reference, in its order, for SELECT instead of `*`.

    >>> all_columns(jobs)
    [jobs.job_id, jobs.job_name, jobs.team, jobs.region]
    >>> print(to_hive(statement(SELECT(all_columns(jobs)), FROM(jobs), LIMIT(20))))
    SELECT
      jobs.job_id,
      jobs.job_name,
      jobs.team,
      jobs.region
    FROM ops.jobs AS jobs
    LIMIT 20
    """
    return [getattr(t, column) for column in t._columns]


def first_look(t):
    """A first look at a table: all its columns, and 20 of yesterday's rows.

    It is an ordinary Statement, bounded to the day before today like any other, so it is
    safe to run on a big table. Send it with run(first_look(t), send=...).

    >>> print(to_hive(first_look(job_runs)))
    SELECT
      job_runs.run_id,
      job_runs.job_id,
      job_runs.status,
      job_runs.duration_mins,
      job_runs.avg_retry_secs,
      job_runs.dt
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24'
    LIMIT 20
    """
    from .clauses import FROM, LIMIT, SELECT, WHERE, statement
    from .conditions import last_n_days

    clauses = [SELECT(all_columns(t)), FROM(t)]
    if t._date_partition is not None:
        clauses.append(WHERE(last_n_days(getattr(t, t._date_partition), 1)))
    return statement(*clauses, LIMIT(20))


# --- Reading a table's description from the warehouse ---------------------------------------


class Verdict:
    """What a check found, ready to print."""

    def __init__(self, ok: bool, lines: list[str]):
        self.ok = ok
        self.lines = lines

    def __repr__(self) -> str:
        return "\n".join(self.lines)

    __str__ = __repr__


def _describe(name: str, send) -> tuple[dict, list[str], list[str]]:
    """Send DESCRIBE: the columns with types, their comments, and the partition columns."""
    frame = send(hive_text(exp.Describe(this=exp.to_table(name))))
    columns, comments, partitions = {}, {}, []
    in_partitions = False
    for row in frame.itertuples(index=False):
        column = str(row[0] or "").strip()
        kind = str(row[1] or "").strip()
        comment = str(row[2] or "").strip() if len(row) > 2 else ""
        if column.startswith("#"):
            in_partitions = in_partitions or "partition" in column.lower()
            continue
        if not column:
            continue
        if in_partitions:
            partitions.append(column)
        elif column not in columns:
            columns[column] = kind
            comments[column] = "" if comment in ("None", "nan") else comment
    return columns, comments, partitions


def _newest_partition_value(name: str, column: str, send) -> str | None:
    """Send SHOW PARTITIONS and return the newest value of one partition column."""
    command = exp.Command(this="SHOW", expression=exp.Literal.string(
        "PARTITIONS " + hive_text(exp.to_table(name))))
    frame = send(hive_text(command))
    values = []
    for text in frame.iloc[:, 0]:
        for part in str(text).split("/"):
            key, _, value = part.partition("=")
            if key == column:
                values.append(value)
    return max(values) if values else None


def _day_format_of(value: str | None) -> str | None:
    """The date_format a partition value is written in, or None when it isn't a day."""
    for pattern in (DEFAULT_DATE_FORMAT, "%Y%m%d", "%Y/%m/%d"):
        try:
            datetime.datetime.strptime(value or "", pattern)
            return pattern
        except ValueError:
            continue
    return None


def write_table_reference(name, send):
    '''Write a new Table reference file for a table, from Hive's own description of it.

    It sends DESCRIBE and SHOW PARTITIONS through your `send` (they read the table's
    description, never its rows) and writes `<table>.py` in the folder you're working in.
    It never guesses the key or which columns don't add up: those are TODOs for you. The file
    is yours from then on, and this refuses to overwrite it.

    >>> path = write_table_reference("ops.run_alerts", send=example_database.send)
    >>> print(path.read_text())
    """ops.run_alerts - TODO: say in one line what one row is."""
    from sql_composer import Table
    <BLANKLINE>
    run_alerts = Table(
        "ops.run_alerts",
        columns={
            "alert_id": "bigint",
            "run_id": "bigint",
            "severity": "string",  # low / high
            "dt": "string",
        },
        date_partition="dt",
        key=None,  # TODO: the columns that pick out one row, such as key=["alert_id"]
        does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
    )
    <BLANKLINE>
    '''
    if not isinstance(name, str) or not TABLE_NAME.fullmatch(name):
        _refuse_table(
            what=f"write_table_reference({name!r}, ...) isn't a table name.",
            why="It needs the name Hive knows the table by.",
            fix='Write it like "ops.job_runs".',
        )
    short = name.split(".")[-1]
    variable = short if short.isidentifier() and not keyword.iskeyword(short) else f"t_{short}"
    path = Path(f"{variable}.py")
    if path.exists():
        raise FileExistsError(
            four_part_message(
                what=f"{path.resolve()} already exists, so nothing was written.",
                why="A Table reference is yours once written, and rewriting it would lose "
                "your key, filters and notes.",
                fix="Edit that file, or check it against the table with "
                "check_table_reference(t, send=...).",
                opt_out=None,
            )
        )
    columns, comments, partitions = _describe(name, send)
    date_lines = _date_partition_lines(name, partitions, send)
    path.write_text(_reference_text(name, variable, columns, comments, date_lines),
                    encoding="utf-8")
    return path


def _date_partition_lines(name: str, partitions: list[str], send) -> list[str]:
    if not partitions:
        return ["    date_partition=None,"]
    first = partitions[0]
    also = f"  # TODO check: also partitioned by {', '.join(partitions[1:])}" if len(
        partitions) > 1 else ""
    pattern = _day_format_of(_newest_partition_value(name, first, send))
    if pattern is None:
        return [f"    date_partition=None,  # TODO: partitioned by {', '.join(partitions)}; "
                "name the date one if there is one"]
    lines = [f'    date_partition="{first}",{also}']
    if pattern != DEFAULT_DATE_FORMAT:
        lines.append(f'    date_format="{pattern}",')
    return lines


def _reference_text(name, variable, columns, comments, date_lines) -> str:
    lines = [
        f'"""{name} - TODO: say in one line what one row is."""',
        "from sql_composer import Table",
        "",
        f"{variable} = Table(",
        f'    "{name}",',
        "    columns={",
    ]
    for column, kind in columns.items():
        comment = " ".join(comments.get(column, "").split())
        comment = f"  # {comment}" if comment else ""
        lines.append(f"        {json.dumps(column)}: {json.dumps(kind)},{comment}")
    first_key = next(iter(columns))
    lines += [
        "    },",
        *date_lines,
        f'    key=None,  # TODO: the columns that pick out one row, such as key=["{first_key}"]',
        "    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts",
        ")",
        "",
    ]
    return "\n".join(lines)


# --- Checking a Table reference against the warehouse ----------------------------------------


def _real_table(t, call: str) -> Table:
    if not isinstance(t, Table) or t._statement is not None:
        raise TypeError(
            four_part_message(
                what=f"{call} was given {t!r}.",
                why="It works on a real table's Table reference, not on a Derived table.",
                fix="Pass a Table reference, such as job_runs.",
                opt_out=None,
            )
        )
    return t


def check_key(t, send):
    """Check on the newest day that no two rows share the table's declared key.

    JOIN relies on a declared key to warn about repeated rows, and Hive never enforces one.
    This counts rows per key over one day (the newest in SHOW PARTITIONS), 20 at most.

    >>> check_key(job_runs, send=example_database.send)
    ops.job_runs: the key (run_id) holds on 2026-09-24.

    A wrong key shows the keys that repeat:

    >>> alerts = Table("ops.run_alerts", columns={"alert_id": "bigint", "run_id": "bigint",
    ...     "severity": "string", "dt": "string"}, date_partition="dt", key=["run_id"])
    >>> check_key(alerts, send=example_database.send)
    ops.run_alerts: the key (run_id) repeats on 2026-09-24. Keys with more than one row:
     run_id  copies
        101       3
        103       2
    """
    from .calculations import count_rows
    from .clauses import AS, FROM, GROUP_BY, HAVING, LIMIT, SELECT, WHERE, statement
    from .conditions import equals, more_than
    from .running import run

    t = _real_table(t, "check_key(...)")
    if not t._key:
        _refuse_table(
            what=f"check_key({t._alias}): its Table reference declares no key.",
            why="There is nothing to check.",
            fix='Add key=[...] to its Table(...) call, such as key=["run_id"].',
        )
    key = [getattr(t, column) for column in t._key]
    clauses = [SELECT(key, AS(count_rows(), "copies")), FROM(t)]
    when = ""
    if t._date_partition is not None:
        newest = _newest_partition_value(t._name, t._date_partition, send)
        if newest is None:
            return Verdict(False, [f"{t._name}: SHOW PARTITIONS found no days to check."])
        clauses.append(WHERE(equals(getattr(t, t._date_partition), newest)))
        when = f" on {newest}"
    clauses += [GROUP_BY(key), HAVING(more_than(count_rows(), 1)), LIMIT(20)]
    repeats = run(statement(*clauses), send=send)
    listed = ", ".join(t._key)
    if len(repeats) == 0:
        return Verdict(True, [f"{t._name}: the key ({listed}) holds{when}."])
    return Verdict(False, [
        f"{t._name}: the key ({listed}) repeats{when}. Keys with more than one row:",
        repeats.to_string(index=False),
    ])


def _same_type(first: str, second: str) -> bool:
    return "".join(first.lower().split()) == "".join(second.lower().split())


def check_table_reference(t, send):
    """Compare a Table reference with its table in Hive, and list what differs.

    It sends DESCRIBE and SHOW PARTITIONS through your `send`, and lists problems (which make
    Statements wrong) and notes (which may not matter), each with the line to change in the
    Table reference file. It never edits the file and never refuses anything: a table Hive
    can't describe, or a send that fails, is reported too. Comments, the key and
    does_not_add_up aren't compared.

    >>> check_table_reference(job_runs, send=example_database.send)
    ops.job_runs matches its Table reference.
    >>> old_jobs = Table("ops.jobs", columns={"job_id": "int", "job_name": "string",
    ...     "owner": "string", "team": "string"}, date_partition=None, key=["job_id"])
    >>> check_table_reference(old_jobs, send=example_database.send)
    ops.jobs differs from its Table reference.
    Problems:
      - job_id is bigint in the table: change its line to "job_id": "bigint",
      - owner isn't in the table: remove its line, or correct its name.
    Notes:
      - region is in the table but not in the Table reference: add "region": "string", if you want it.
    """
    t = _real_table(t, "check_table_reference(...)")
    try:
        columns, _, partitions = _describe(t._name, send)
    except Exception as error:  # it reports, and never raises: see the docstring
        return Verdict(False, [f"{t._name}: DESCRIBE failed, so nothing was compared. Check "
                               "the table's name, and that send works. It said:",
                               *_said(error)])
    problems, notes = _column_differences(t, columns)
    problems += _date_partition_problems(t, partitions, send)
    notes += _partition_notes(t, partitions)
    shared = [column for column in columns if column in t._columns]
    if shared != [column for column in t._columns if column in columns]:
        notes.append("The columns are in a different order from the table's, which matters "
                     "only if a Statement writes to this table. The table's order is: "
                     + ", ".join(shared) + ".")
    if not problems and not notes:
        return Verdict(True, [f"{t._name} matches its Table reference."])
    lines = [f"{t._name} differs from its Table reference."]
    for title, found in (("Problems:", problems), ("Notes:", notes)):
        if found:
            lines += [title] + [f"  - {line}" for line in found]
    return Verdict(not problems, lines)


def _column_differences(t: Table, columns: dict) -> tuple[list[str], list[str]]:
    """The problems and notes from comparing the columns and their types."""
    problems, notes = [], []
    for column, kind in t._columns.items():
        if column not in columns:
            problems.append(f"{column} isn't in the table: remove its line, or correct its name.")
        elif kind is not None and not _same_type(kind, columns[column]):
            problems.append(f"{column} is {columns[column]} in the table: change its line to "
                            f"{json.dumps(column)}: {json.dumps(columns[column])},")
    for column, kind in columns.items():
        if column not in t._columns:
            notes.append(f"{column} is in the table but not in the Table reference: add "
                         f"{json.dumps(column)}: {json.dumps(kind)}, if you want it.")
    return problems, notes


def _date_partition_problems(t: Table, partitions: list[str], send) -> list[str]:
    if t._date_partition is None:
        return []
    if t._date_partition not in partitions:
        now = f'"{partitions[0]}"' if partitions else "None"
        return [f"{t._date_partition} is no longer a partition column: change the line to "
                f"date_partition={now},"]
    try:
        newest = _newest_partition_value(t._name, t._date_partition, send)
    except Exception as error:  # check_table_reference reports, and never raises
        return [f"SHOW PARTITIONS failed, so {t._date_partition}'s days weren't checked. It "
                "said: " + " ".join(_said(error)).strip()]
    try:
        datetime.datetime.strptime(newest or "", t._date_format)
    except ValueError:
        pattern = _day_format_of(newest)
        if pattern == DEFAULT_DATE_FORMAT:
            fix = "remove the date_format line, since that is the usual way to write a day."
        elif pattern:
            fix = f'change the line to date_format="{pattern}",'
        else:
            fix = "change the line to date_partition=None,"
        return [f"the newest {t._date_partition}, {newest!r}, isn't written like "
                f"{t._date_format!r}: {fix}"]
    return []


def _said(error: Exception) -> list[str]:
    """What an error said, as indented lines for a Verdict."""
    text = str(error).strip() or "(no message)"
    return [f"    {type(error).__name__}:"] + [f"    {line.strip()}" for line in text.splitlines()]


def _partition_notes(t: Table, partitions: list[str]) -> list[str]:
    if t._date_partition is None and partitions:
        return [f"the table is partitioned by {', '.join(partitions)}: if one holds days, "
                "name it in date_partition=..."]
    others = [column for column in partitions if column != t._date_partition]
    if others:
        return [f"the table is also partitioned by {', '.join(others)}, which a Statement "
                "may bound too."]
    return []


def create_table(t, may_exist=False):
    """The CREATE TABLE Statement for a Saved table, from its Table reference.

    Send it once with run(create_table(t), send=...). Every column needs a type. If the
    table already exists, Hive refuses with AlreadyExistsException, so editing the Table
    reference and sending this again can't quietly look like it changed the table: drop the
    table on the server first, or compare them with check_table_reference(t, send=...).
    may_exist=True sends CREATE TABLE IF NOT EXISTS, which leaves an existing table alone.

    >>> daily_runs = Table("mart.daily_runs", date_partition="dt",
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"})
    >>> print(to_hive(create_table(daily_runs)))
    CREATE TABLE mart.daily_runs (
      job_id BIGINT,
      runs BIGINT
    )
    PARTITIONED BY (
      dt STRING
    )
    STORED AS ORC
    """
    from .clauses import Statement

    t = _real_table(t, "create_table(...)")
    untyped = [column for column, kind in t._columns.items() if not kind]
    if untyped:
        _refuse_table(
            what=f"create_table({t._alias}): {', '.join(untyped)} has no type.",
            why="Hive needs every column's type to create the table.",
            fix=f'Give each one its Hive type, such as {json.dumps(untyped[0])}: "string".',
        )
    parts = t._name.split(".")
    table = exp.Table(this=identifier(parts[-1]),
                      db=identifier(parts[0]) if len(parts) == 2 else None)
    columns = [_column_definition(t, c) for c in t._columns if c != t._date_partition]
    properties = [exp.FileFormatProperty(this=exp.Var(this="ORC"))]
    if t._date_partition is not None:
        partition = exp.Schema(expressions=[_column_definition(t, t._date_partition)])
        properties.insert(0, exp.PartitionedByProperty(this=partition))
    s = Statement()
    s._ddl = exp.Create(kind="TABLE", this=exp.Schema(this=table, expressions=columns),
                        properties=exp.Properties(expressions=properties), exists=may_exist)
    return s


def _column_definition(t: Table, column: str) -> exp.ColumnDef:
    try:
        kind = exp.DataType.build(t._columns[column], dialect=HIVE)
    except Exception:
        _refuse_table(
            what=f"create_table({t._alias}): {column}'s type {t._columns[column]!r} isn't a "
            "Hive type.",
            why="Hive needs a type it knows to create the column.",
            fix='Use a Hive type such as "string", "bigint", "double" or "decimal(10,2)".',
        )
    return exp.ColumnDef(this=identifier(column), kind=kind)
