"""Table references: Table, and the functions that read, write and check one.

A Table reference is one `Table(...)` call describing one table: its columns and their Hive
types, the columns it is partitioned by, its key, and the columns that don't add up. Its
columns are its attributes (`job_runs.status`), so a typo fails at once, with the column list.

This file also holds the column object those attributes return, and `literal(...)`, the one
place a Python value, such as "FAILED" or 42, enters a Statement.
"""

from __future__ import annotations

import copy
import datetime
import decimal
import difflib
import keyword
import re
import urllib.parse
import weakref
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

import numpy as np
import pandas as pd

from . import _FOLDER, describe, kinds
from .shared import escaped_literal, python_literal, split_table_name
from .writing import hive_text, readable_text
from .refusals import (
    CONTROL_CHARACTERS,
    arguments_of,
    guard_control_character,
    guard_none_in_condition,
    guard_not_a_number,
    guard_time_of_day,
    is_count,
    need_warehouse_call,
    refuse,
    refuse_removed_arguments,
    repeated,
)
from .trees import (
    ARITHMETIC,
    SIMPLE_NAME,
    Node,
    has_aggregate,
    is_hive_type,
    number,
    string,
)

if TYPE_CHECKING:  # clauses.py and conditions.py import this file
    from .clauses import Statement
    from .conditions import Condition

TABLE_NAME = re.compile(r"[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)?")

# The partition Hive lists for the rows whose partition column is NULL.
ROWS_WITH_NO_VALUE = "__HIVE_DEFAULT_PARTITION__"

NUMBER_TYPES = ("tinyint", "smallint", "int", "integer", "bigint", "float", "double", "decimal",
                "numeric", "real")
STRING_TYPES = ("string", "varchar", "char")


# --- The call that made a calculation or condition, for the lineage -------------------------


def made_by(tree: Node, name: str, *args: object, **keywords: object) -> Node:
    """Note on `tree` the Toolbox call that made it, such as week_start(job_runs.dt).

    The note leaves the Hive unchanged. The lineage shows it, since it reads the way the
    Statement was written, where the Hive may be written differently.
    """
    parts = [python_text(arg) for arg in args]
    parts += [f"{key}={python_text(value)}" for key, value in keywords.items()
              if value is not None]
    tree.meta["call"] = f"{name}({', '.join(parts)})"
    return tree


def python_text(value: object) -> str:
    """One argument of a Toolbox call, written back as Python, for the lineage and refusals."""
    # A column, condition or descending(...) is spotted by what it holds, not by its class:
    # a condition's class and descending's live in files that import this one.
    if hasattr(value, "_tree"):
        return readable(value._tree)
    if hasattr(value, "_target"):
        return f"descending({python_text(value._target)})"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(python_text(item) for item in value) + "]"
    return python_literal(value)


def readable(tree: Node) -> str:
    """A calculation or condition as it was written: its Toolbox calls, else its Hive.

    """
    if "call" in tree.meta:
        return tree.meta["call"]
    return readable_text(tree.replaced(_call_shown))


def _call_shown(node: Node) -> Node | None:
    """The Toolbox call that made a Node, to be written in its place, or None if none did."""
    return Node("Var", this=node.meta["call"]) if "call" in node.meta else None


# --- Columns and calculations --------------------------------------------------------------


def _no_operator(symbol: str, instead: str) -> NoReturn:
    refuse(
        what=f"A column was used with Python's {symbol}.",
        why="Python would compare the Python objects, not the values in the table, and "
        "the result would quietly be True or False instead of a condition.",
        fix=f"Use {instead}.",
    )


class Column:
    """One column of a table, or a calculation made from columns.

    >>> job_runs.duration_mins
    job_runs.duration_mins
    >>> sum_of(job_runs.duration_mins)
    SUM(job_runs.duration_mins)

    A Table reference's columns are its attributes, such as `job_runs.status`, and the
    calculation functions, such as sum_of(...), give back a Column too. Arithmetic works with
    Python's + - * /, bracketed as Python groups it. Comparisons don't: use the condition
    functions, such as equals(...), instead of ==. Write the name in a type hint, to say that
    a function of yours takes or gives back a Column:

    >>> def hours(minutes: Column) -> Column:
    ...     return minutes / 60
    >>> hours(job_runs.duration_mins)
    job_runs.duration_mins / 60
    >>> (job_runs.duration_mins + 1) * 2
    (job_runs.duration_mins + 1) * 2
    """

    def __init__(self, tree: Node, *, table: Table | None = None, name: str | None = None,
                 type: str | None = None, adds_up: bool = True,
                 not_adding_up_because: str | None = None) -> None:
        self._tree = tree
        self._table = table
        self._name = name
        self._type = type
        self._adds_up = adds_up
        self._not_adding_up_because = not_adding_up_because

    def __repr__(self) -> str:
        return hive_text(self._tree)

    def __str__(self) -> str:
        """Its Hive text, such as jobs.job_id, for an f-string of Hive written by hand."""
        return hive_text(self._tree)

    def __format__(self, spec: str) -> str:
        """Its Hive text, formatted as a str is, so f"{jobs.job_id:>20}" pads it."""
        return format(str(self), spec)

    @property
    def _aggregate(self) -> bool:
        """Whether it adds rows up, such as count_rows() or a sum inside a calculation."""
        return has_aggregate(self._tree)

    # Defining __eq__ below would make Python drop hashing; keep it, so a column can still
    # be a dict key or go in a set.
    __hash__ = object.__hash__

    def __eq__(self, other: object) -> NoReturn:
        _no_operator("==", "equals(column, value)")

    def __ne__(self, other: object) -> NoReturn:
        _no_operator("!=", "not_equals(column, value)")

    def __lt__(self, other: object) -> NoReturn:
        _no_operator("<", "less_than(column, value)")

    def __le__(self, other: object) -> NoReturn:
        _no_operator("<=", "at_most(column, value)")

    def __gt__(self, other: object) -> NoReturn:
        _no_operator(">", "more_than(column, value)")

    def __ge__(self, other: object) -> NoReturn:
        _no_operator(">=", "at_least(column, value)")

    def __and__(self, other: object) -> NoReturn:
        _no_operator("&", "all_of(...), or separate conditions in WHERE(...)")

    __rand__ = __and__

    def __or__(self, other: object) -> NoReturn:
        _no_operator("|", "any_of(...)")

    __ror__ = __or__

    def __invert__(self) -> NoReturn:
        _no_operator("~", "the opposite condition, such as not_equals(...) or is_not_null(...)")

    def __bool__(self) -> NoReturn:
        _no_operator("if, and, or or not", "a condition such as equals(...)")

    def __add__(self, other: Column | int | float) -> Column:
        return arithmetic(self, other, "Add", "+")

    def __radd__(self, other: int | float) -> Column:
        return arithmetic(other, self, "Add", "+")

    def __sub__(self, other: Column | int | float) -> Column:
        return arithmetic(self, other, "Sub", "-")

    def __rsub__(self, other: int | float) -> Column:
        return arithmetic(other, self, "Sub", "-")

    def __mul__(self, other: Column | int | float) -> Column:
        return arithmetic(self, other, "Mul", "*")

    def __rmul__(self, other: int | float) -> Column:
        return arithmetic(other, self, "Mul", "*")

    def __truediv__(self, other: Column | int | float) -> Column:
        return arithmetic(self, other, "Div", "/")

    def __rtruediv__(self, other: int | float) -> Column:
        return arithmetic(other, self, "Div", "/")

    def __neg__(self) -> Column:
        return arithmetic(0, self, "Sub", "-")


def _bracketed(tree: Node) -> Node:
    if tree.kind in ARITHMETIC:
        return Node("Paren", this=tree)
    return tree


def arithmetic(left: object, right: object, kind: str, symbol: str) -> Column:
    """Build `left <symbol> right`, bracketing each side that is itself arithmetic."""
    sides = []
    for side in (left, right):
        if isinstance(side, Column):
            sides.append(side)
            continue
        if isinstance(side, bool) or not isinstance(side, (int, float, decimal.Decimal,
                                                               np.number)):
            refuse(
                what=f"{symbol} was used with {side!r}.",
                why="Arithmetic on a column needs a number or another column.",
                fix="Use a number, such as job_runs.duration_mins / 60.",
                given=side, call=symbol,
            )
        sides.append(Column(literal(side, call=f"a {symbol} calculation", in_condition=False)))
    left, right = sides
    adds_up = left._adds_up and right._adds_up and kind != "Div"
    because = "a division" if kind == "Div" else (
        left._not_adding_up_because or right._not_adding_up_because)
    return Column(
        Node(kind, this=_bracketed(left._tree.copy()),
             expression=_bracketed(right._tree.copy())),
        adds_up=adds_up,
        not_adding_up_because=None if adds_up else because,
    )


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


def _python_family(value: bool | int | float | decimal.Decimal | str | datetime.date) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float, decimal.Decimal)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, datetime.datetime):
        return "timestamp"
    return "date"


def value_family(value: object) -> str | None:
    """The family of a value a calculation gives, such as one of first_match's: a column's,
    from its type, or a Python value's. None when it isn't known: NULL, a calculation with no
    type, or what isn't a single value, which literal(...) refuses."""
    if isinstance(value, Column):
        return type_family(value._type)
    value = _python_value(value)
    if value is None or not isinstance(value, SINGLE_VALUES):
        return None
    return _python_family(value)


# For each column type family, the kinds of Python value it may be compared with; they are
# also the families whose values can stand in one column, as first_match's values must.
COMPARABLE_VALUES = {
    "number": {"number"},
    "string": {"string", "date", "timestamp"},
    "date": {"date", "string", "timestamp"},
    "timestamp": {"timestamp", "date", "string"},
    "boolean": {"boolean"},
}


def _check_type(value: bool | int | float | decimal.Decimal | str | datetime.date,
                column: Column | None, call: str) -> None:
    family = type_family(column._type) if column is not None else None
    if family is None or _python_family(value) in COMPARABLE_VALUES[family]:
        return
    refuse(
        what=f"{call} compares {column!r}, a {column._type} column, with {value!r}.",
        why="The warehouse would convert one side to the other's type, so the comparison "
        "could quietly match nothing or the wrong rows, or stop with an error.",
        fix=f"Pass a value of the column's own type, such as {_example_of(family)}.",
    )


def _example_of(family: str) -> str:
    return {
        "number": "42",
        "string": '"FAILED"',
        "date": '"2026-09-25"',
        "timestamp": '"2026-09-25 13:00:00"',
        "boolean": "True",
    }[family]


def day_text(day: datetime.date) -> str:
    """A day as Hive text, such as 2026-09-25, its year always in four digits."""
    return f"{day.year:04d}-{day.month:02d}-{day.day:02d}"


def _number_text(value: int | float | decimal.Decimal) -> str | None:
    """A number's Hive text, written by the Toolbox rather than by the value's own str()."""
    # int.__repr__(value), not repr(value): a subclass of int could change its own repr,
    # and so change the Hive. The same goes for float, Decimal and, in literal(), str.
    if isinstance(value, int):
        return int.__repr__(value)
    if isinstance(value, float):
        text = float.__repr__(value)
        return None if text in ("nan", "inf", "-inf") else text
    if not decimal.Decimal.is_finite(value):
        return None
    return decimal.Decimal.__format__(value, "f")


SINGLE_VALUES = (bool, int, float, decimal.Decimal, str, datetime.date)


def _python_value(value: object) -> object:
    """A numpy or pandas value as the plain Python value it stands for."""
    if isinstance(value, np.datetime64):
        return pd.Timestamp(value)
    if isinstance(value, np.generic):
        return value.item()
    if value is pd.NaT or value is pd.NA:
        return None
    return value


def literal(value: object, *, call: str, column: Column | None = None,
            position: str = "the value", in_condition: bool = True) -> Node:
    """Turn a Python value into a Hive literal. The only way a value enters a Statement."""
    if isinstance(value, Column):
        return value._tree.copy()
    value = _python_value(value)
    if value is None:
        if in_condition:
            guard_none_in_condition(call)
        return Node("Null")
    if not isinstance(value, SINGLE_VALUES):
        refuse(
            what=f"{call} was given {value!r}, which isn't a single value.",
            why="A column is compared with one number, string, date or bool at a time.",
            fix="For several values use is_in(column, [...]); for a column pass the column.",
            given=value, call=call,
        )
    _check_type(value, column, call)
    if isinstance(value, bool):
        return Node("Boolean", this=value)
    if isinstance(value, str):
        return _string_literal(value, call, position)
    if isinstance(value, datetime.date):
        return string(_date_text(value, column, call))
    text = _number_text(value)
    if text is None:
        guard_not_a_number(call, position, value)
    return number(text, is_float=isinstance(value, float))


def _string_literal(value: str, call: str, position: str) -> Node:
    """A string as a Hive literal, refused if it holds a character the warehouse misreads."""
    for character in CONTROL_CHARACTERS:
        if character in value:
            guard_control_character(call, position, character)
    return string(str.__str__(value))


def _date_text(value: datetime.date, column: Column | None, call: str) -> str:
    """A date as its day, or a timestamp in full when the column is typed as a timestamp."""
    if not isinstance(value, datetime.datetime):
        return day_text(value)
    if type_family(column._type if column is not None else None) == "timestamp":
        return value.isoformat(sep=" ")
    if value.time() != datetime.time(0, 0):
        guard_time_of_day(call, value)
    return day_text(value.date())


# --- Table ---------------------------------------------------------------------------------


def _names(value: object, argument: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, (list, tuple)):
        refuse(
            what=f"{argument}={value!r} isn't a list of column names.",
            why="The Toolbox reads it as the names of columns in this table.",
            fix=f'Write it as a list, such as {argument}=["run_id"].',
            error=ValueError,
        )
    return list(value)


def _descriptions(name: str, value: object) -> dict[str, str]:
    """A Table reference's descriptions=, each column's description in words."""
    if value is None:
        return {}
    if not isinstance(value, dict) or not all(isinstance(text, str) for text in value.values()):
        refuse(
            what=f"Table({name!r}): descriptions={value!r} isn't a dict of columns and text.",
            why="Each description says in words what a column holds.",
            fix='Write it as descriptions={"status": "SUCCESS or FAILED"}.',
            error=ValueError,
        )
    return {str(column): text for column, text in value.items()}


class Table:
    """A Table reference: a table's columns, its partition columns and its key.

    >>> run_alerts = Table("ops.run_alerts", partitioned_by=["dt"], key=["alert_id"],
    ...     columns={"alert_id": "bigint", "severity": "string", "dt": "string"})
    >>> run_alerts
    Table('ops.run_alerts', columns: alert_id, severity, dt)

    Its columns become attributes, so `job_runs.status` is checked when your script runs:
    a typo stops with the list of real columns. Write one per table, generated once by
    write_table_reference(...) and then yours to edit.

    - `columns` maps each column to its Hive type as DESCRIBE, the command that lists a
      table's columns, prints it ("bigint",
      "decimal(10,2)"), or None when you don't know it. A typed column gets its values checked.
    - `partitioned_by` lists the columns the table is partitioned by, in the order Hive
      partitions it, such as ["dt"] or ["region", "load_id"], each a column in `columns`
      too; leave it out for a table that isn't partitioned. Each value of them is a folder
      of the table's files, a Partition, and a Statement reading the table must filter at
      least one of them (help(FROM)). A write fills the Partitions its rows hold, or the ones
      it names (help(INSERT_OVERWRITE)).
    - `key` lists the columns that pick out one row, the table's Key, for a table that has
      one; leave it out for one that hasn't. JOIN warns when a join doesn't use all of them;
      a write into a Saved table with a Key is refused unless the Toolbox can see each row it
      writes has a Key of its own (help(INSERT_OVERWRITE) says how); and create_table writes
      it into the table (help(create_table)). Hive never checks it.
    - `does_not_add_up` lists columns that are averages, ratios or distinct counts, which
      sum_of(...) and average_of(...) refuse to add up.
    - `descriptions` says in words what a column holds, such as {"status": "SUCCESS or
      FAILED"}, for the columns you want to describe. write_table_reference fills it from the
      comments DESCRIBE prints; it never changes the Hive.

    A Saved table, one your Statements write into, also says how it is stored, which
    create_table writes and check_table_reference compares with the table. Of these, a Saved
    table needs only `location`; a table someone else owns has none of them:

    - `location` is the table's own folder, exactly as create_table writes it, such as
      "/data/your_team/mart.db/daily_runs": the Toolbox adds nothing to it. Every Saved table
      is an external table: its files are yours, in that folder, and the warehouse only keeps
      a record of where. Two tables in one folder would read each other's files, so a Saved
      table whose folder is another's, or inside another's, is refused. A location such as
      "${hivevar:root}/mart.db/daily_runs" holds a Hive variable: send its SET first, with
      run_execute(hive_settings("root", sets={"root": {"hivevar:root": "/data/your_team"}}),
      execute), and check_table_reference then notes the table's folder rather than
      comparing it.
    - `purge=True` makes dropping the table delete its files too. purge=False keeps them in
      its folder, where a table created again reads them back: at once, or, for a
      partitioned table, its Partitions once repair_partitions(t) lists them; left out, the
      warehouse's own choice, which keeps them, is neither written nor checked.
    - `properties` holds any other table properties, the notes on a table the warehouse
      keeps by name, such as {"made_by": "daily_pipeline"}.
    - `stored_as` is the file format, "ORC" (the usual one) or "PARQUET", and `compression`
      how its files are packed: "SNAPPY", or ORC's "ZLIB" or Parquet's "GZIP", among others.
    - `bucketed_by` with `buckets` spreads each Partition's rows into that many files by the
      values of those columns, and `sorted_by` sorts the rows in each, so a join on them can
      pair file with file. Leave them out unless the table is big and joined on those
      columns: changing them means writing the table again.

    A column whose name is a Python word, such as `from`, is reached with getattr(t, "from").
    You never type backticks: the Hive puts a name in them where it needs them, such
    as `from`, `any` or `two words`, and leaves a plain name, such as dt, as it is.

    A table's text, in an f-string or from str(...), is the table as FROM writes it, ops.jobs
    AS jobs, for after FROM or JOIN in Hive you write by hand; DESCRIBE and SHOW PARTITIONS
    take the name alone, ops.jobs, which you write yourself. A column's text is the column as
    SELECT writes it, jobs.job_id, not ops.jobs.job_id, even where you reach it as
    ops.jobs.job_id: Hive names a column by its table's name after AS, and refuses a
    three-part name in a SELECT. help(unchecked_hive) shows them in use. A format spec works
    on them as on a str:

    >>> f"SELECT {jobs.job_id} FROM {jobs}"
    'SELECT jobs.job_id FROM ops.jobs AS jobs'
    >>> f"[{jobs.team:>12}]"
    '[   jobs.team]'

    A table alone on a cell's last line shows its repr, its name and its columns, and a column
    its text:

    >>> job_runs
    Table('ops.job_runs', columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt)
    >>> job_runs.status
    job_runs.status
    >>> job_runs.stauts
    Traceback (most recent call last):
    ...
    AttributeError: job_runs has no column 'stauts'. Did you mean 'status'? Its columns are: run_id, job_id, status, duration_mins, avg_retry_secs, dt.
    """

    def __init__(self, name: str, columns: dict[str, str | None], *,
                 partitioned_by: list[str] | None = None, key: list[str] | None = None,
                 does_not_add_up: list[str] | tuple[str, ...] = (),
                 location: str | None = None,
                 purge: bool | None = None, properties: dict[str, str] | None = None,
                 stored_as: str | None = None, compression: str | None = None,
                 bucketed_by: list[str] | None = None, buckets: int | None = None,
                 sorted_by: list[str] | None = None,
                 descriptions: dict[str, str] | None = None, **removed: object) -> None:
        _refuse_a_day_argument(name, removed)
        if not isinstance(name, str) or not TABLE_NAME.fullmatch(name):
            refuse(
                what=f"Table({name!r}, ...) isn't a table name.",
                why="A Hive table name is letters, digits and _, optionally after a database "
                "name and a dot.",
                fix='Write it like "ops.job_runs".',
                error=ValueError,
            )
        if not isinstance(columns, dict) or not columns:
            refuse(
                what=f"Table({name!r}, columns=...) needs a dict of column names and types.",
                why="The columns are what a Statement can use.",
                fix='Write columns={"run_id": "bigint", "status": "string", ...}.',
                error=ValueError,
            )
        for column, kind in columns.items():
            if kind is not None and not isinstance(kind, str):
                refuse(
                    what=f"Table({name!r}): {column}'s type is {kind!r}, not text.",
                    why="A column's type is written as DESCRIBE prints it, so the Toolbox "
                    "can check that the values you compare with it fit the type.",
                    fix='Write it as text, such as "bigint" for whole numbers or "string" for '
                    "text, or None if you don't know it.",
                )
        self._name = name
        self._alias = split_table_name(name)[1]
        self._columns = {str(column): kind for column, kind in columns.items()}
        self._key = _names(key, "key") or None
        self._does_not_add_up = _names(does_not_add_up, "does_not_add_up")
        self._statement = None
        self._not_adding_up_because = dict.fromkeys(
            self._does_not_add_up, "listed in does_not_add_up in its Table reference")
        self._partitioned_by = _names(partitioned_by, "partitioned_by")
        self._bucketed_by = _names(bucketed_by, "bucketed_by")
        self._sorted_by = _names(sorted_by, "sorted_by")
        self._descriptions = _descriptions(name, descriptions)
        self._check_own_columns()
        _check_partitions(self)
        _set_storage(self, location, purge, properties, stored_as, compression, buckets)
        _MADE.add(self)

    def _check_own_columns(self) -> None:
        named = {"key": self._key or []}
        named["does_not_add_up"] = self._does_not_add_up
        named["partitioned_by"] = self._partitioned_by
        named["bucketed_by"] = self._bucketed_by
        named["sorted_by"] = self._sorted_by
        named["descriptions"] = list(self._descriptions)
        for argument, names in named.items():
            for column in names:
                if column not in self._columns:
                    refuse(
                        what=f"Table({self._name!r}): {argument} names {column!r}, which isn't "
                        "one of its columns.",
                        why="Every name there must be a column in columns={...}.",
                        fix=f"Use one of: {', '.join(self._columns)}.",
                        error=ValueError,
                    )

    def __getattr__(self, attribute: str) -> Column:
        """A column of the table, by its name, such as job_runs.status."""
        columns = self.__dict__.get("_columns")
        if columns is None or attribute.startswith("__"):
            raise AttributeError(attribute)
        if attribute in columns:
            return self._column(attribute)
        close = difflib.get_close_matches(attribute, list(columns), n=1)
        hint = f" Did you mean {close[0]!r}?" if close else ""
        # Python 3.12 adds its own "Did you mean ...?" to an AttributeError raised here, after
        # the hint below, unless the error's obj is already set; obj=None sets it.
        # tests/test_docstrings.py runs Table's docstring example, which holds the one hint.
        raise AttributeError(
            f"{self._alias} has no column {attribute!r}.{hint} Its columns are: "
            f"{', '.join(columns)}.",
            obj=None,
        )

    def _column(self, name: str) -> Column:
        because = self._not_adding_up_because.get(name)
        return Column(
            Node("Column", name=name, table=self._alias),
            table=self,
            name=name,
            type=self._columns[name],
            adds_up=because is None,
            not_adding_up_because=because,
        )

    def __dir__(self) -> list[str]:
        """The table's attributes and its columns, so tab completion lists the columns."""
        return sorted(set(super().__dir__()) | set(self._columns))

    def __repr__(self) -> str:
        kind = "derived" if self._statement is not None else "Table"
        if is_unchecked(self):
            kind = "unchecked_derived"
        return f"{kind}({self._name!r}, columns: {', '.join(self._columns)})"

    def __str__(self) -> str:
        """Its Hive text as FROM writes it, such as ops.jobs AS jobs, for an f-string of Hive
        written by hand."""
        return hive_text(source(self))

    def __format__(self, spec: str) -> str:
        """Its Hive text, formatted as a str is, so f"{jobs:>20}" pads it."""
        return format(str(self), spec)


class UncheckedSelect:
    """The SELECT of an Unchecked derived table, as unchecked_derived(...) keeps it: its Hive
    text as written, and the tables the text reads. It stands where a Derived table made by
    derived(...) keeps its Statement, and no Guard, Warning or Load limit looks inside it."""

    def __init__(self, text: str, tables: list[str]) -> None:
        self._text = text  # the SELECT, as written, without a last ;
        self._tables = tables  # each table it reads, as database.name


def is_unchecked(table: Table) -> bool:
    """Whether a table is an Unchecked derived table, made by unchecked_derived(...)."""
    return isinstance(table._statement, UncheckedSelect)


# Each Table made and still in use, so a read of an Unchecked derived table can tell whether a
# table its Hive reads is partitioned, by that table's Table reference. Held weakly: a Table
# no longer in use drops out.
_MADE: weakref.WeakSet[Table] = weakref.WeakSet()


def partitioned_by_name(name: str) -> list[str] | None:
    """The partition columns of the table `name`, as database.name, by the Table references
    made for it: [] when each says it isn't partitioned, and None when none was made, so the
    Toolbox can't tell. Where two say different things, their partition columns are joined."""
    found = [table._partitioned_by for table in list(_MADE)
             if table._statement is None and table._name.lower() == name.lower()]
    if not found:
        return None
    return list(dict.fromkeys(column for columns in found for column in columns))


def _refuse_a_day_argument(name: object, removed: dict[str, object]) -> None:
    """Refuse date_partition= and date_format=, which 7.0 replaced, and any other name Table
    doesn't take."""
    gone = [argument for argument in ("date_partition", "date_format") if argument in removed]
    if gone:
        refuse(
            what=f"Table({name!r}) was given {gone[0]}=, which Toolbox 7.0 replaced.",
            why="Since 7.0 a table is partitioned by any columns, or none, and no column is a "
            "day to the Toolbox: partitioned_by= lists them, and a date is compared as it is "
            f"written. Table takes {arguments_of(Table)}.",
            fix='Write partitioned_by=["dt"] where it said date_partition="dt", leave it out '
            "where it said date_partition=None, and remove date_format=. CHANGES.md, under "
            "7.0, says more.",
        )
    refuse_removed_arguments(f"Table({name!r})", removed, Table)


# --- A Saved table's storage -----------------------------------------------------------------

# The file formats create_table writes, each with the table property that names its
# compression and the compressions it has.
FILE_FORMATS = {
    "ORC": ("orc.compress", ("NONE", "ZLIB", "SNAPPY", "LZO", "LZ4", "ZSTD")),
    "PARQUET": ("parquet.compression",
                ("UNCOMPRESSED", "SNAPPY", "GZIP", "LZO", "BROTLI", "LZ4", "ZSTD")),
}
# The table property that makes dropping an external table delete its files too.
PURGE = "external.table.purge"
# Why a Saved table needs a folder of its own, as the refusals and reports say it.
SHARING = ("two tables in one folder read each other's files, and an INSERT OVERWRITE of a "
           "Partition in one can delete the other's files for that Partition.")
# The fix for a table that isn't at its own folder: the admin module moves it.
MOVE_IT = "move it with admin.move_to_own_folder(t, query=...)"
# The fix for a table at its own folder whose layout the Toolbox doesn't write: the move's copy
# would go to that same folder, so the table is written again there.
WRITE_IT_AGAIN = ("it is at its own folder already, so write it again there: give its Table "
                  "reference purge=True and send admin.set_properties(t), drop it with "
                  "admin.drop_table(t), create it with create_table(t), and write its rows "
                  "again from their source")
# Each Saved table's own folder, by its name in lower case, so that two can't share one.
_FOLDERS: dict[str, str] = {}
# The storage options, which only one of the user's Saved tables has, in the order Table takes.
STORAGE = ("purge", "properties", "stored_as", "compression", "bucketed_by", "buckets",
           "sorted_by")


def _set_storage(t: Table, location: object, purge: object, properties: object,
                 stored_as: object, compression: object, buckets: object) -> None:
    """Check a Table reference's storage, and keep it. Only a Saved table has any."""
    t._purge = purge
    t._properties = {}
    t._stored_as = "ORC"
    t._compression = None
    t._buckets = buckets
    t._location = None
    values = {"purge": purge, "properties": properties, "stored_as": stored_as,
              "compression": compression, "bucketed_by": t._bucketed_by, "buckets": buckets,
              "sorted_by": t._sorted_by}
    given = [option for option in STORAGE if values[option] not in (None, [])]
    if location is None:
        if given:
            refuse(
                what=f"Table({t._name!r}) has {given[0]}= but no location=.",
                why=f"{given[0]}= is part of how one of your own Saved tables is stored, and "
                "each of those is in a folder of its own, its location=.",
                fix=f'Add location=..., such as location="/data/your_team/mart.db/daily_runs", '
                f"or remove {given[0]}=: a table someone else owns needs none of it.",
                error=ValueError,
            )
        return
    t._location = _checked_folder(t._name, location)
    if purge is not None and not isinstance(purge, bool):
        refuse(
            what=f"Table({t._name!r}): purge={purge!r} isn't True or False.",
            why="purge=True makes dropping the table delete its files too; purge=False keeps "
            "them, so the table can be made again over them.",
            fix="Write purge=True or purge=False, or leave it out for Hive's own choice, which "
            "keeps the files.",
            error=ValueError,
        )
    t._stored_as = _one_of(t._name, "stored_as", stored_as or "ORC", list(FILE_FORMATS))
    property_name, compressions = FILE_FORMATS[t._stored_as]
    if compression is not None:
        t._compression = _one_of(t._name, "compression", compression, list(compressions),
                                 f" for stored_as={t._stored_as!r}")
    t._properties = _checked_properties(t._name, properties, property_name)
    _check_buckets(t)


def _one_of(name: str, option: str, value: object, allowed: list[str],
            which: str = "") -> str:
    """A value that must be one of a few words, in capitals, whatever its case was."""
    if isinstance(value, str) and value.upper() in allowed:
        return value.upper()
    refuse(
        what=f"Table({name!r}): {option}={value!r} isn't one the Toolbox writes.",
        why=f"{option}= takes one of a few names Hive knows{which}.",
        fix="Use one of: " + ", ".join(f'"{word}"' for word in allowed) + ".",
        error=ValueError,
    )


def _checked_folder(name: str, location: object) -> str:
    """The Saved table's own folder, as written, refused where it is not a folder or would
    share one with another Saved table."""
    if not isinstance(location, str) or not location.strip() or any(
            character in location for character in CONTROL_CHARACTERS):
        refuse(
            what=f"Table({name!r}): location={location!r} isn't a folder.",
            why="location= is the table's own folder, written as text, such as "
            '"/data/your_team/mart.db/daily_runs".',
            fix="Write the folder as text, as your warehouse's DESCRIBE FORMATTED writes a "
            "Location.",
            error=ValueError,
        )
    folder = location.rstrip("/") or location
    # Compared without the storage's name, as hdfs:///data/... and /data/... are one folder.
    path = urllib.parse.urlsplit(folder).path
    for other, theirs in _FOLDERS.items():
        their_path = urllib.parse.urlsplit(theirs).path
        if other == name.lower() or not (path == their_path or path.startswith(
                their_path + "/") or their_path.startswith(path + "/")):
            continue
        where = ("the same folder as" if path == their_path else "inside the folder of"
                 if path.startswith(their_path + "/") else "around the folder of")
        refuse(
            what=f"Table({name!r}) would be at {folder}, {where} {other} ({theirs}).",
            why=f"Every Saved table needs a folder of its own: {SHARING}",
            fix="Give each its own folder in location=, such as "
            '"/data/your_team/mart.db/daily_runs" for mart.daily_runs.',
            error=ValueError,
        )
    _FOLDERS[name.lower()] = folder
    return folder


def _checked_properties(name: str, properties: object,
                        compression_property: str) -> dict[str, str]:
    """The table properties given, each a name and a value written as text."""
    if properties is None:
        return {}
    if not isinstance(properties, dict):
        refuse(
            what=f"Table({name!r}): properties={properties!r} isn't a dict.",
            why="properties= holds the table's other TBLPROPERTIES, each a name and a value.",
            fix='Write it like properties={"made_by": "daily_pipeline"}.',
            error=ValueError,
        )
    own_options = {PURGE: "purge=True or purge=False", "external": "nothing: create_table "
                   "always makes a Saved table external",
                   compression_property: 'compression=..., such as compression="SNAPPY"'}
    for key, value in properties.items():
        written = own_options.get(str(key).lower())
        if written is not None:
            refuse(
                what=f"Table({name!r}): properties= sets {key!r}.",
                why="The Toolbox writes that property itself, from its own argument of "
                "Table(...), so it is checked like the rest of the table's storage.",
                fix=f"Remove it from properties=, and write {written}.",
                error=ValueError,
            )
        if not isinstance(key, str) or not isinstance(value, str) or any(
                character in key + value for character in CONTROL_CHARACTERS):
            refuse(
                what=f"Table({name!r}): properties= has {key!r}: {value!r}.",
                why="Hive keeps each table property's name and value as text.",
                fix=f"Write both as printed text, such as {escaped_literal(str(key))}: "
                f"{escaped_literal(str(value))}.",
                error=ValueError,
            )
    return dict(properties)


def _check_partitions(t: Table) -> None:
    """Refuse a partitioned_by= that names a column twice, or one that holds no plain value."""
    _names_once(t, "partitioned_by", t._partitioned_by)
    for column in t._partitioned_by:
        if (t._columns[column] or "").strip().lower().startswith(("array", "map", "struct")):
            refuse(
                what=f"Table({t._name!r}): partitioned_by= names {column!r}, whose type is "
                f"{t._columns[column]}.",
                why="A Partition is a folder named by one plain value, such as region=eu.",
                fix="Partition by a column holding one plain value, such as a string.",
                error=ValueError,
            )


def _names_once(t: Table, argument: str, names: list[str]) -> None:
    """Refuse an `argument`= such as partitioned_by= that names a column twice."""
    twice = repeated(names)
    if twice:
        refuse(
            what=f"Table({t._name!r}): {argument}= names {twice[0]!r} twice.",
            why="Each column goes in it once.",
            fix=f"Name {twice[0]!r} once in {argument}=.",
            error=ValueError,
        )


def _check_buckets(t: Table) -> None:
    """Refuse Buckets that create_table couldn't write."""
    for argument, names in (("bucketed_by", t._bucketed_by), ("sorted_by", t._sorted_by)):
        _names_once(t, argument, names)
        # A Bucket holds the columns inside the files, so a Partition can't be one.
        inside = [column for column in names if column in t._partitioned_by]
        if inside:
            refuse(
                what=f"Table({t._name!r}): {argument}= names {inside[0]!r}, which is already "
                "a Partition.",
                why="A Partition is a folder of its own, not a column inside the files.",
                fix=f"Remove {inside[0]!r} from {argument}=.",
                error=ValueError,
            )
    has_buckets = t._buckets is not None
    if bool(t._bucketed_by) != has_buckets or (t._sorted_by and not t._bucketed_by):
        given = [argument for argument, value in (
            ("bucketed_by=", t._bucketed_by), ("buckets=", has_buckets),
            ("sorted_by=", t._sorted_by)) if value]
        missing = "buckets=" if t._bucketed_by else "bucketed_by="
        refuse(
            what=f"Table({t._name!r}) has {' and '.join(given)} but no {missing}.",
            why="Buckets spread each Partition's rows into a fixed number of files by some "
            "columns: "
            "bucketed_by= names the columns and buckets= the number, and sorted_by= sorts "
            "the rows inside each Bucket.",
            fix=f"Give both bucketed_by= and buckets=, such as bucketed_by=[\"{column_example(t)}"
            "\"], buckets=8, or remove the ones you gave.",
            error=ValueError,
        )
    if has_buckets and not is_count(t._buckets):
        refuse(
            what=f"Table({t._name!r}): buckets={t._buckets!r} isn't a whole number, 1 or more.",
            why="buckets= is how many files each Partition's rows are spread into.",
            fix="Write it like buckets=8.",
            error=ValueError,
        )


def column_example(t: Table) -> str:
    """A column of the table to show in a fix: its first that isn't a Partition."""
    return next((c for c in t._columns if c not in t._partitioned_by), next(iter(t._columns)))


def aliased(table: Table, name: object) -> Table:
    """A copy of a table called `name` in the SQL, for AS(table, name)."""
    if not isinstance(name, str) or not SIMPLE_NAME.fullmatch(name):
        refuse(
            what=f"AS({table._alias}, {name!r}): {name!r} can't name a table.",
            why="A table's second name is a plain word in the SQL.",
            fix='Use letters, digits and _, such as AS(job_runs, "earlier").',
            error=ValueError,
        )
    copied = copy.copy(table)
    copied._alias = name
    return copied


def table_node(name: str, **parts: object) -> Node:
    """A table as a Node, "ops.job_runs" split into its database and its name."""
    database, table = split_table_name(name)
    return Node("Table", db=database or None, name=table, **parts)


def source(table: Table) -> Node:
    """How a table is named after FROM or JOIN: its name, and AS its alias where it needs one."""
    if table._statement is not None and table._alias == table._name:
        return table_node(table._name)
    return table_node(table._name, alias=table._alias)


def all_columns(t: Table) -> list[Column]:
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
    return _columns_of(t, "all_columns(...)")


def _columns_of(t: object, call: str) -> list[Column]:
    """Every column of a Table reference, refusing what isn't one."""
    if not isinstance(t, Table):
        refuse(
            what=f"{call} was given {t!r}.",
            why="It reads the columns of a Table reference.",
            fix="Pass the Table reference itself, such as job_runs, not its name as text.",
            given=t, call=call,
        )
    return [t._column(column) for column in t._columns]


def first_look(t: Table) -> Statement:
    """A first look at a table: all its columns, and 20 of its rows.

    >>> print(to_hive(first_look(job_runs)))
    SELECT
      job_runs.run_id,
      job_runs.job_id,
      job_runs.status,
      job_runs.duration_mins,
      job_runs.avg_retry_secs,
      job_runs.dt
    FROM ops.job_runs AS job_runs
    LIMIT 20

    It is an ordinary Statement, with LIMIT 20. A partitioned table is read with
    reads_all_partitions=True: Hive stops reading once it has 20 rows, so it is safe on a big
    table too. Send it with run_query(first_look(t), query).
    """
    from .clauses import FROM, LIMIT, SELECT, statement

    return statement(SELECT(_columns_of(t, "first_look(...)")),
                     FROM(t, reads_all_partitions=bool(t._partitioned_by)), LIMIT(20))


# --- Reading a table's description from the warehouse ---------------------------------------


class Verdict:
    """What check_key(...), check_table_reference(...) or a comparison found, to print.

    >>> check_key(jobs, query=example_database.query)
    ops.jobs: the key (job_id) holds.

    Its `ok` is True when it found nothing wrong, and printing it shows what it found. The
    Verdict itself is true or false as its `ok` is, so `if check_key(...):` passes only when
    the key holds. Make one with check_key(...), check_table_reference(...), compare_hive(...) or
    compare_with_original(...), never Verdict(). Write the
    name in a type hint, to say that a function of yours gives back what one of them
    found:

    >>> def key_holds(t: Table) -> Verdict:
    ...     return check_key(t, query=example_database.query)
    >>> verdict = key_holds(jobs)
    >>> verdict.ok
    True
    >>> verdict
    ops.jobs: the key (job_id) holds.
    """

    def __init__(self, ok: bool, lines: list[str]) -> None:
        self.ok = ok
        self.lines = lines

    def __bool__(self) -> bool:
        """Its `ok`, so `if check_key(...):` reads as it says."""
        return self.ok

    def __repr__(self) -> str:
        return "\n".join(self.lines)

    __str__ = __repr__


def write_table_reference(name: str, *, query: Callable[[str], pd.DataFrame] | None = None,
                          folder: str | Path | None = None, **removed: object) -> Path:
    '''Write a table's Table reference as a file, such as ops__run_alerts.py.

    >>> path = write_table_reference("ops.run_alerts", query=example_database.query)
    >>> path.name
    'ops__run_alerts.py'

    It sends DESCRIBE through your `query` (it reads the table's description, never its
    rows) and writes the file in `folder`, such as "references", or in
    the folder you're working in when folder is left out. The file is imported as
    `from ops__run_alerts import run_alerts`, or `from references.ops__run_alerts import
    run_alerts` from a folder "references": two underscores join the database and the table,
    since a dot or a dash can't be in a name Python imports. The Table reference in
    it is named for the table alone, or t_<table> for a table named like a Python word, such
    as t_class. Each column's comment, which DESCRIBE prints, becomes its description, and
    the columns DESCRIBE lists the table as partitioned by become its partitioned_by=. It
    never guesses the key or which columns don't add up: those are TODOs for you. Below the Table reference,
    under its Aliases heading, you can add your own names for its columns and conditions, as
    its examples show. The file is yours from then on, and this refuses to overwrite it. The
    file it wrote:

    >>> print(path.read_text())
    """ops.run_alerts - TODO: say in one line what one row is."""
    from sqlglot_composer import Table
    <BLANKLINE>
    run_alerts = Table(
        "ops.run_alerts",
        columns={
            "alert_id": "bigint",
            "run_id": "bigint",
            "severity": "string",
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=None,  # TODO: the columns that pick out one row, such as key=["alert_id"]
        does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
        descriptions={
            "severity": "low / high",
        },
    )
    <BLANKLINE>
    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from ops__run_alerts import run_alerts, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
    # get back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = run_alerts.severity
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(run_alerts.severity, <value>)
    <BLANKLINE>
    '''
    refuse_removed_arguments("write_table_reference", removed, write_table_reference)
    need_warehouse_call("write_table_reference", "query", query, "It sends DESCRIBE through "
                        "your query, and reads what comes back.")
    if not isinstance(name, str) or not TABLE_NAME.fullmatch(name):
        refuse(
            what=f"write_table_reference({name!r}, ...) isn't a table name.",
            why="It needs the name the warehouse knows the table by.",
            fix='Write it like "ops.job_runs".',
            error=ValueError,
        )
    if "." not in name:
        refuse(
            what=f"write_table_reference({name!r}, ...) has no database name.",
            why="The file is named for the database and the table, such as ops__job_runs.py, "
            "and the Table reference reads the table wherever your query runs.",
            fix=f'Write the database first, like "ops.{name}".',
            error=ValueError,
        )
    database, short = split_table_name(name)
    variable = short if short.isidentifier() and not keyword.iskeyword(short) else f"t_{short}"
    where = Path(folder) if folder is not None else Path()
    if not where.is_dir():
        refuse(
            what=f"write_table_reference({name!r}, ..., folder={folder!r}): there is no "
            "such folder.",
            why="It writes the file into a folder that is there already, so a typo never "
            "makes a folder of its own.",
            fix='Make the folder first, or name one that is there, such as folder="references".',
            error=FileNotFoundError,
        )
    path = where / f"{database}__{short}.py"
    if path.exists():
        refuse(
            what=f"{path.name} already exists in {_folder_name(folder)}, so nothing was "
            "written.",
            why="A Table reference is yours once written, and rewriting it would lose "
            "your key, filters and notes.",
            fix="Edit that file, or check it against the table with "
            "check_table_reference(t, query=...).",
            error=FileExistsError,
        )
    call = f"write_table_reference({name!r}, ...)"
    described = describe.ask(name, query, call)
    columns, comments = described.columns, described.descriptions
    partitions = described.partitioned_by
    if not columns:
        refuse(
            what=f"{call}: DESCRIBE {name} listed no columns.",
            why="A Table reference is written from the table's columns.",
            fix="Check the table's name, and that your query returns what DESCRIBE prints.",
            error=ValueError,
        )
    module = path.stem if folder is None else f"{Path(folder).name}.{path.stem}"
    path.write_text(_reference_text(name, variable, columns, comments, partitions, module),
                    encoding="utf-8")
    return path


def _folder_name(folder: str | Path | None) -> str:
    """The folder write_table_reference writes into, as its refusals name it."""
    return "the folder you're working in" if folder is None else f"the folder {str(folder)!r}"


# The heading a Table reference's Aliases go under, ruled to the width of the file.
ALIASES_HEADING = "# --- Aliases " + "-" * 78


def _reference_text(name: str, variable: str, columns: dict[str, str],
                    comments: dict[str, str], partitions: list[str], module: str) -> str:
    """A Table reference file's text. `module` is the name the file is imported by, such as
    references.ops__job_runs, which its Aliases heading shows."""
    lines = [
        f'"""{name} - TODO: say in one line what one row is."""',
        f"from {_FOLDER} import Table",
        "",
        f"{variable} = Table(",
        f'    "{name}",',
        "    columns={",
    ]
    for column, kind in columns.items():
        lines.append(f"        {escaped_literal(column)}: {escaped_literal(kind)},")
    first_key = next(iter(columns))
    lines += [
        "    },",
        *([f"    partitioned_by={escaped_literal(partitions)},"] if partitions else []),
        f'    key=None,  # TODO: the columns that pick out one row, such as key=["{first_key}"]',
        "    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts",
    ]
    described = {column: " ".join(comments.get(column, "").split()) for column in columns}
    described = {column: text for column, text in described.items() if text}
    if described:
        lines += ["    descriptions={",
                  *[f"        {escaped_literal(column)}: {escaped_literal(text)},"
                    for column, text
                    in described.items()],
                  "    },"]
    # The examples' column: the first that is neither an id nor a partition column, if any.
    example = next((column for column in columns
                    if not column.endswith("_id") and column not in partitions), first_key)
    lines += [
        ")",
        "",
        ALIASES_HEADING,
        "# Your own names for this table's columns and conditions, written by hand below.",
        f"# Import one beside the table: from {module} import {variable}, <alias>",
        "#",
        "# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame "
        "you",
        "# get back, still call the column by its own name. To rename an output, use AS(...).",
        f"#     <alias> = {variable}.{example}",
        "# A condition Alias names a condition on this table alone, for WHERE or",
        "# count_rows(where=...). Add what it calls, such as equals, to the import at the top.",
        f"#     <alias> = equals({variable}.{example}, <value>)",
        "",
    ]
    return "\n".join(lines)


# --- Checking a Table reference against the warehouse ----------------------------------------


def _real_table(t: object, call: str) -> Table:
    if not isinstance(t, Table) or t._statement is not None:
        refuse(
            what=f"{call} was given {t!r}.",
            why="It works on a real table's Table reference, not on a table's name as "
            "text or on a Derived table.",
            fix="Pass a Table reference, such as job_runs.",
            given=t, call=call,
        )
    return t


def need_saved_table(t: object, what: str) -> Table:
    """The Table reference of one of the user's own Saved tables, which a call that changes a
    table takes; refused otherwise. `what` is the call, as in "admin.drop_partitions(...)" or
    "repair_partitions(...)".

    A Saved table is a Table reference with location=: one with none is a table someone else
    owns, which the Toolbox only reads.
    """
    t = _real_table(t, what)
    if t._location is None:
        refuse(
            what=f"{what} was given {t._name}, which isn't one of your Saved tables: its Table "
            "reference has no location=.",
            why="It changes a table, or what the warehouse keeps about it, so it takes only your "
            "own Saved tables, each in a folder of its own, its location=. A Table reference "
            "with no location= is a table someone else owns, and changing it could break their "
            "work.",
            fix=f"If {t._name} is yours, add location=... to its Table(...) call, its own "
            'folder, such as location="/data/your_team/mart.db/daily_runs". If it '
            "isn't yours, ask whoever owns it.",
            error=ValueError,
        )
    return t


def check_key(t: Table, *, query: Callable[[str], pd.DataFrame] | None = None,
              where: Condition | None = None, reads_all_partitions: bool = False,
              **removed: object) -> Verdict:
    """Check that no two rows share a table's key, on the rows where= picks.

    >>> check_key(job_runs, query=example_database.query,
    ...           where=equals(job_runs.dt, "2026-09-24"))
    ops.job_runs: the key (run_id) holds where job_runs.dt = '2026-09-24'.

    JOIN relies on a declared Key to warn about repeated rows, and a write into a Saved table
    to check its rows, and the warehouse never enforces one. This counts the rows per key and
    shows at most 20 keys that repeat. A partitioned table is checked on the rows `where`
    picks, such as where=equals(job_runs.dt, "2026-09-24"), since every Partition at once may
    be more than you want to read; reads_all_partitions=True checks them all. A table that
    isn't partitioned is checked whole.

    A wrong key shows the keys that repeat:

    >>> alerts = Table("ops.run_alerts", columns={"alert_id": "bigint", "run_id": "bigint",
    ...     "severity": "string", "dt": "string"}, partitioned_by=["dt"], key=["run_id"])
    >>> check_key(alerts, query=example_database.query, where=equals(alerts.dt, "2026-09-24"))
    ops.run_alerts: the key (run_id) repeats where run_alerts.dt = '2026-09-24'. Keys with more than one row:
     run_id  copies
        101       3
        103       2
    """
    refuse_removed_arguments("check_key", removed, check_key)
    need_warehouse_call("check_key", "query", query, "It counts repeated keys with a query, "
                        "which gives back rows.")
    from .calculations import count_rows
    from .clauses import AS, FROM, GROUP_BY, HAVING, LIMIT, SELECT, WHERE, statement
    from .conditions import Condition, more_than
    from .running import run_query

    t = _real_table(t, "check_key(...)")
    if not t._key:
        refuse(
            what=f"check_key({t._alias}): its Table reference declares no key.",
            why="There is nothing to check.",
            fix='Add key=[...] to its Table(...) call, such as key=["run_id"].',
            error=ValueError,
        )
    if where is not None and not isinstance(where, Condition):
        refuse(
            what=f"check_key({t._alias}, where={where!r}): where= isn't a condition.",
            why="where= picks the rows the key is checked on.",
            fix=f"Pass a condition, such as where=equals({t._alias}.<column>, <value>).",
            given=where, call="check_key",
        )
    if t._partitioned_by and where is None and not reads_all_partitions:
        column = f"{t._alias}.{t._partitioned_by[0]}"
        refuse(
            what=f"check_key({t._alias}): {t._name} is partitioned, and nothing says which "
            "Partitions to check.",
            why="Checking every Partition reads the whole table, which may be more than the "
            "cluster should read at once.",
            fix=f"Pass where=..., such as where=equals({column}, <value>), or "
            "reads_all_partitions=True to check them all.",
            error=ValueError,
        )
    key = [t._column(column) for column in t._key]
    clauses = [SELECT(key, AS(count_rows(), "copies")),
               FROM(t, reads_all_partitions=reads_all_partitions)]
    when = ""
    if where is not None:
        clauses.append(WHERE(where))
        when = f" where {where!r}"
    clauses += [GROUP_BY(key), HAVING(more_than(count_rows(), 1)), LIMIT(20)]
    repeats = run_query(statement(*clauses), query)
    if len(repeats.columns) == 0:
        refuse(
            what=f"check_key({t._alias}): your query gave back a DataFrame with no columns.",
            why="It reads the keys that repeat from the columns of what comes back, so with no "
            "columns it can't tell a key that holds from one that doesn't.",
            fix="Make your query return the warehouse's answer as it prints it, each column "
            "named.",
            error=ValueError,
        )
    listed = ", ".join(t._key)
    if len(repeats) == 0:
        return Verdict(True, [f"{t._name}: the key ({listed}) holds{when}."])
    return Verdict(False, [
        f"{t._name}: the key ({listed}) repeats{when}. Keys with more than one row:",
        repeats.to_string(index=False),
    ])


def _same_type(first: str, second: str) -> bool:
    return "".join(first.lower().split()) == "".join(second.lower().split())


def check_table_reference(t: Table, *, query: Callable[[str], pd.DataFrame] | None = None,
                          **removed: object) -> Verdict:
    """Compare a Table reference with its table as it is now, and list what differs.

    >>> check_table_reference(job_runs, query=example_database.query)
    ops.job_runs matches its Table reference.

    It sends DESCRIBE through your `query`, and lists problems (which make Statements wrong)
    and notes (which may not matter), each with the line to change in the Table reference
    file. The columns, their types and the columns the table is partitioned by come from
    DESCRIBE. It never edits the file, and refuses nothing but a missing query: a table the warehouse can't
    describe, or a query that fails, is reported too. Comments, the key and does_not_add_up
    aren't compared.

    For one of your Saved tables, one with location=, it sends DESCRIBE FORMATTED instead, and
    compares its storage too: that it is external, its folder, its file format and its
    Buckets, and purge, compression and properties where the Table reference gives them. A
    table that isn't at the folder location= names is a problem, as a table made by hand in a
    folder it shares with others is: two tables in one folder read each other's files, and an
    overwrite of a Partition in one can delete the other's.
    admin.move_to_own_folder(t, query=...) moves it. A location= holding a Hive variable, such
    as ${hivevar:root}, is noted rather than compared, since the warehouse reports the folder
    the variable stood for. DESCRIBE FORMATTED describes one
    table at a time, so another table that put its files in this table's own folder is
    reported when that other table is checked: check each of your Saved tables.

    A Table reference that differs gets the line to change for each difference:

    >>> old_jobs = Table("ops.jobs", columns={"job_id": "int", "job_name": "string",
    ...     "owner": "string", "team": "string"}, key=["job_id"])
    >>> check_table_reference(old_jobs, query=example_database.query)
    ops.jobs differs from its Table reference.
    Problems:
      - job_id is bigint in the table: change its line to "job_id": "bigint",
      - owner isn't in the table: remove its line, or correct its name.
    Notes:
      - region is in the table but not in the Table reference: add "region": "string", if you want it.
    """
    refuse_removed_arguments("check_table_reference", removed, check_table_reference)
    need_warehouse_call("check_table_reference", "query", query, "It sends DESCRIBE through "
                        "your query, and reads what comes back.")
    t = _real_table(t, "check_table_reference(...)")
    saved = t._location is not None
    command = "DESCRIBE FORMATTED" if saved else "DESCRIBE"
    try:
        described = describe.ask(t._name, query, "check_table_reference(...)", formatted=saved)
    except Exception as error:  # it reports, and never raises: see the docstring
        return Verdict(False, [f"{t._name}: {command} failed, so nothing was compared. Check "
                               "the table's name, and that your query works. It said:",
                               *_said(error)])
    columns, partitions = described.columns, described.partitioned_by
    if not columns:
        return Verdict(False, [f"{t._name}: {command} listed no columns, so nothing was "
                               "compared. Check the table's name, and that your query returns what "
                               f"{command} prints."])
    problems, notes = _column_differences(t, columns)
    problems += _partition_problems(t, partitions)
    if saved:
        storage_problems, storage_notes = _storage_problems(t, described)
        problems += storage_problems
        notes += storage_notes
    shared = [column for column in columns if column in t._columns]
    # The table lists its columns, then the ones it is partitioned by.
    in_order = [column for column in t._columns if column not in t._partitioned_by]
    if shared != [column for column in in_order + t._partitioned_by if column in columns]:
        notes.append("The columns are in a different order from the table's, which matters "
                     "only if a Statement writes to this table. The table's order is: "
                     + ", ".join(shared) + ".")
    if not problems and not notes:
        return Verdict(True, [f"{t._name} matches its Table reference."])
    verdict = "differs from" if problems else "matches"
    lines = [f"{t._name} {verdict} its Table reference."]
    for title, found in (("Problems:", problems), ("Notes:", notes)):
        if found:
            lines += [title] + [f"  - {line}" for line in found]
    return Verdict(not problems, lines)


def _column_differences(t: Table, columns: dict[str, str]) -> tuple[list[str], list[str]]:
    """The problems and notes from comparing the columns and their types."""
    problems, notes = [], []
    for column, kind in t._columns.items():
        if column not in columns:
            problems.append(f"{column} isn't in the table: remove its line, or correct its name.")
        elif kind is not None and not _same_type(kind, columns[column]):
            problems.append(f"{column} is {columns[column]} in the table: change its line to "
                            f"{escaped_literal(column)}: {escaped_literal(columns[column])},")
    for column, kind in columns.items():
        if column not in t._columns:
            notes.append(f"{column} is in the table but not in the Table reference: add "
                         f"{escaped_literal(column)}: {escaped_literal(kind)}, if you want it.")
    return problems, notes


def _partition_problems(t: Table, partitions: list[str]) -> list[str]:
    """A problem when the table is partitioned by other columns than partitioned_by= says."""
    if partitions == t._partitioned_by:
        return []
    if not partitions:
        return ["the table isn't partitioned: remove the line partitioned_by=."]
    return [f"the table is partitioned by {', '.join(partitions)}: change the line to "
            f"partitioned_by={escaped_literal(partitions)},"]


def _said(error: Exception) -> list[str]:
    """What an error said, as indented lines for a Verdict."""
    text = str(error).strip() or "(no message)"
    return [f"    {type(error).__name__}:"] + [f"    {line.strip()}" for line in text.splitlines()]


_SET_IT = "or set it with admin.set_properties(t)"


def _storage_problems(t: Table, described: describe.Description) -> tuple[list[str], list[str]]:
    """The problems, and the notes, from comparing a Saved table's storage with what
    DESCRIBE FORMATTED says of the table."""
    if described.location is None:
        # Not a note: nothing below was compared, so the table can't be said to match.
        return ["DESCRIBE FORMATTED listed no Location, so its storage wasn't compared: check "
                "that your query returns everything DESCRIBE FORMATTED prints."], []
    problems, notes = [], []
    managed = described.managed
    # A table the move can take to its own folder, writing it again as its Table reference
    # says; one at its own folder already is written again there instead.
    fix = MOVE_IT if managed or not same_folder(described.location, t._location) else (
        WRITE_IT_AGAIN)
    if managed:
        # Its folder is the warehouse's choice, so this says all the folder check would.
        problems.append("it is a managed table, whose files the warehouse keeps where it "
                        "chooses, where your Saved tables are external, each in a folder of its "
                        f"own: {MOVE_IT}, which copies its rows into a table create_table "
                        "makes.")
    else:
        location_problems, notes = _location_problems(t, described.location)
        problems += location_problems
    stored_as = described.stored_as
    if stored_as is not None and stored_as != t._stored_as:
        problems.append(f"the table is stored as {stored_as}: change the line to "
                        f'stored_as="{stored_as}",' if stored_as in FILE_FORMATS else
                        "the table's files are in a format the Toolbox doesn't write, not ORC "
                        f"or Parquet (its InputFormat is {stored_as}): {fix}"
                        + (", which writes it again as its Table reference says." if
                           fix is MOVE_IT else "."))
    problems += _property_problems(t, described.properties)
    problems += _buckets_problems(t, described)
    return problems, notes


def _property_problems(t: Table, properties: dict[str, str]) -> list[str]:
    """The problems from comparing purge, compression and the other table properties."""
    problems = []
    if t._purge is not None:
        purged = properties.get(PURGE, "").strip().lower() == "true"
        if purged != t._purge:
            state = "is" if purged else "isn't"
            problems.append(f"{PURGE} {state} true in the table: change the line to "
                            f"purge={purged}, {_SET_IT}.")
    wanted = dict(t._properties)
    if t._compression is not None:
        wanted = {FILE_FORMATS[t._stored_as][0]: t._compression, **wanted}
    for name, value in wanted.items():
        found = properties.get(name)
        is_compression = name == FILE_FORMATS[t._stored_as][0]
        if found is None and is_compression:
            problems.append(f"the table sets no {name}: remove the line compression=..., "
                            f"{_SET_IT}.")
        elif found is None:
            problems.append(f"the table has no property {name!r}: remove it from "
                            f"properties=, {_SET_IT}.")
        elif is_compression and found.upper() != value:
            problems.append(f"{name} is {found} in the table: change the line to "
                            f'compression="{found.upper()}",')
        elif not is_compression and found != value:
            problems.append(f"its property {name!r} is {found!r} in the table: change it in "
                            f"properties= to {escaped_literal(name)}: "
                            f"{escaped_literal(found)},")
    return problems


def _location_problems(t: Table, location: str) -> tuple[list[str], list[str]]:
    """The problems, and the notes, from comparing the folder the table is at with the one
    its Table reference's location= names: a problem when it isn't there, none when it is,
    and a note when location= holds a Hive variable, whose value only the warehouse knows."""
    if "${" in t._location:
        return [], [f"location= holds a Hive variable, so its folder wasn't compared; the "
                    f"table is at {location}."]
    if same_folder(location, t._location):
        return [], []
    return [f"it is at {location}, not at {t._location}, the folder location= names: change "
            f'the line to location="{location}", if that is the own folder of the table. '
            f"A folder that isn't a table's own may hold other tables' files: {SHARING} "
            f"{MOVE_IT[0].upper()}{MOVE_IT[1:]}."], []


def same_folder(found: str, wanted: str) -> bool:
    """Whether two folders are one: the warehouse writes a Location in full, as
    hdfs://namenode:8020/data/..., where a Table reference may write /data/... alone."""
    found_parts, wanted_parts = urllib.parse.urlsplit(found), urllib.parse.urlsplit(wanted)
    for part in ("scheme", "netloc"):
        found_part, wanted_part = getattr(found_parts, part), getattr(wanted_parts, part)
        if found_part and wanted_part and found_part.lower() != wanted_part.lower():
            return False
    return found_parts.path.rstrip("/") == wanted_parts.path.rstrip("/")


def _buckets_problems(t: Table, described: describe.Description) -> list[str]:
    """The problems from comparing the Buckets. The Partitions are compared for every table,
    by _partition_problems."""
    problems = []
    # The warehouse lists column names in lower case, so they are compared so.
    in_the_table = (described.buckets, described.bucketed_by, described.sorted_by)
    in_the_reference = (t._buckets, [c.lower() for c in t._bucketed_by],
                        [c.lower() for c in t._sorted_by])
    if in_the_table != in_the_reference:
        if in_the_table[0] is None:
            problems.append("the table has no Buckets: remove the lines bucketed_by=, buckets= "
                            "and sorted_by=.")
        else:
            number, bucketed_by, sorted_by = in_the_table
            sorted_text = f", sorted by {', '.join(sorted_by)}" if sorted_by else ""
            sorted_line = f", sorted_by={escaped_literal(sorted_by)}" if sorted_by else ""
            problems.append(f"the table is bucketed by {', '.join(bucketed_by)} into {number} "
                            f"Buckets{sorted_text}: change the lines to bucketed_by="
                            f"{escaped_literal(bucketed_by)}, buckets={number}{sorted_line},")
    return problems


def create_table(t: Table, may_exist: bool = False) -> Statement:
    """The CREATE EXTERNAL TABLE Statement for a Saved table, in a folder of its own.

    >>> daily_runs = Table("mart.daily_runs", partitioned_by=["dt"],
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/mart.db/daily_runs")
    >>> print(to_hive(create_table(daily_runs)))
    CREATE EXTERNAL TABLE mart.daily_runs (
      job_id BIGINT,
      runs BIGINT
    )
    PARTITIONED BY (
      dt STRING
    )
    STORED AS ORC
    LOCATION '/data/your_team/mart.db/daily_runs'

    A Saved table is one your Statements write into. Send it once with
    run_execute(create_table(t), execute). The table is external: its files are yours, in its own
    folder, the Table reference's location=, and the warehouse only keeps a record of
    where. It is stored as the Table reference says (help(Table) lists how), and a Table
    reference with no location= is refused. A location= holding a Hive variable, such as
    "${hivevar:root}/mart.db/daily_runs", needs its SET sent first, with
    run_execute(hive_settings("root", sets={"root": {"hivevar:root": "/data/your_team"}}),
    execute), and check_table_reference then notes the table's folder rather than
    comparing it. Every column needs a type Hive has, spelled as
    DESCRIBE prints it, such as int, string, double or decimal(10,2); it refuses any other,
    and a struct whose names are reserved words, and says what to write. If the table
    already exists, the warehouse refuses to create it again. Without that refusal, you could
    edit the Table reference, send this again, and think the table had changed when it hadn't.
    Compare the two with
    check_table_reference(t, query=...); add new columns with admin.add_columns(t, query=...),
    or, to start the table again, drop it with admin.drop_table(t) (from sqlglot_composer
    import admin).
    may_exist=True sends CREATE EXTERNAL TABLE IF NOT EXISTS, which leaves an existing table
    alone, so it is safe to send again, as at the top of a pipeline that runs every day. It
    doesn't check that the table there matches its Table reference: check_table_reference
    does. Where a table is made again at a folder whose files stayed, repair_partitions(t)
    finds its Partitions.

    A Table reference with a Key, such as key=["job_id", "dt"], gets
    PRIMARY KEY (job_id, dt) DISABLE NOVALIDATE after its columns, which Hive keeps for whoever
    reads the table and never checks: the Toolbox checks the Key itself, before each write.

    A table partitioned by region, then by day, in Parquet files, whose files go when it is
    dropped:

    >>> region_runs = Table("mart.region_runs", partitioned_by=["region", "dt"],
    ...     columns={"job_id": "bigint", "region": "string", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/mart.db/region_runs", purge=True, stored_as="PARQUET",
    ...     compression="SNAPPY")
    >>> print(to_hive(create_table(region_runs)))
    CREATE EXTERNAL TABLE mart.region_runs (
      job_id BIGINT,
      runs BIGINT
    )
    PARTITIONED BY (
      region STRING,
      dt STRING
    )
    STORED AS PARQUET
    LOCATION '/data/your_team/mart.db/region_runs'
    TBLPROPERTIES (
      'external.table.purge'='true',
      'parquet.compression'='SNAPPY'
    )
    """
    from .upkeep import ddl_statement  # here, not at the top: upkeep.py imports this file

    t = _real_table(t, "create_table(...)")
    untyped = [column for column, kind in t._columns.items() if not kind]
    if untyped:
        refuse(
            what=f"create_table({t._alias}): {', '.join(untyped)} has no type.",
            why="Hive needs every column's type to create the table.",
            fix="Give each one its Hive type, such as "
            f'{escaped_literal(untyped[0])}: "string".',
            error=ValueError,
        )
    partitions = t._partitioned_by
    columns = [column_definition(t, c) for c in t._columns if c not in partitions]
    partitioned_by = [column_definition(t, c) for c in partitions]
    if t._location is None:
        refuse(
            what=f"create_table({t._alias}): its Table reference has no location=.",
            why="Each of your Saved tables is an external table, in a folder of its own: its "
            "location=.",
            fix="Add location=... to its Table(...) call, its own folder, such as "
            'location="/data/your_team/mart.db/daily_runs".',
            error=ValueError,
        )
    return ddl_statement(kinds.CREATE, Node(
        "Create", target=table_node(t._name), columns=columns, partitioned_by=partitioned_by,
        exists=may_exist, bucketed_by=list(t._bucketed_by), sorted_by=list(t._sorted_by),
        buckets=t._buckets, stored_as=t._stored_as, location=t._location,
        properties=property_pairs(t), key=t._key))


def property_pairs(t: Table) -> list[tuple[str, str]]:
    """A Saved table's table properties as its Table reference gives them, each (name,
    value): purge= as external.table.purge, compression= by its file format's name for it,
    then properties=."""
    pairs = [] if t._purge is None else [(PURGE, "true" if t._purge else "false")]
    if t._compression is not None:
        pairs.append((FILE_FORMATS[t._stored_as][0], t._compression))
    return pairs + list(t._properties.items())


class NamedPartitions:
    """The Partitions a call names on a Saved table, with partition={...}, as partitions_named
    gives them back.

    `tree` is PARTITION(region = 'EU', dt): each partition column, with its value where
    partition= names one and by its name alone where it doesn't, or None for a table that
    isn't partitioned. `values` holds each partition column partition= names, in the table's
    order, with its value as Hive text, such as {"region": "'EU'"}; empty when it names none.
    """

    def __init__(self, tree: Node | None, values: dict[str, str]) -> None:
        self.tree = tree
        self.values = values


def partitions_named(t: Table, partition: object, call: str, left_out: str
                     ) -> NamedPartitions:
    """The one check of partition={...}, which a write and compute_statistics both take: each
    name a partition column of `t`, together the first of its partitioned_by, each with one
    value. None names no Partition, so each partition column is by its name alone. `call` and
    `left_out` word the refusals: the function given partition=, such as "INSERT_OVERWRITE",
    and what it does with a partition column partition= doesn't name, after "then"."""
    columns = t._partitioned_by
    if partition is None:
        named = {}
    else:
        named = _checked_partition(t, partition, call, left_out)
    values = {name: hive_text(value) for name, value in named.items()}
    if not columns:
        return NamedPartitions(None, values)
    return NamedPartitions(Node("Partition", expressions=[
        Node("EQ", this=Node("Column", name=column), expression=named[column])
        if column in named else Node("Column", name=column)
        for column in columns]), values)


def _checked_partition(t: Table, partition: object, call: str, left_out: str
                       ) -> dict[str, Node]:
    """partitions_named's checks of a partition= that was given: each column it names, in
    partitioned_by order, with its value as a Hive literal."""
    columns = t._partitioned_by
    if not columns:
        refuse(
            what=f"{call}({t._alias}, partition=...): {t._name} isn't partitioned.",
            why="partition= names values of a table's partition columns, and its Table "
            "reference has no partitioned_by=.",
            fix=f"Leave partition= out, as in {call}({t._alias}): the table is one whole, with "
            "no Partitions to name.",
            error=ValueError,
        )
    example = f'{call}({t._alias}, partition={{"{columns[0]}": ...}})'
    if not isinstance(partition, dict):
        refuse(
            what=f"{call}({t._alias}, partition={python_text(partition)}): partition= is a dict "
            "of partition columns and their values.",
            why="It names Partitions by their partition columns: each column it names, with "
            "one value of it.",
            fix=f"Write it like {example}, or leave partition= out: {left_out}.",
            given=partition, call=call,
        )
    if not partition:
        refuse(
            what=f"{call}({t._alias}, partition={{}}) names no Partition.",
            why="partition= names Partitions by their partition columns, each with one value, "
            "and an empty dict gives none.",
            fix=f"Name one, as in {example}, or leave partition= out: {left_out}.",
            error=ValueError,
        )
    unknown = [name for name in partition if name not in columns]
    if unknown:
        refuse(
            what=f"{call}({t._alias}, partition=...) names {', '.join(map(repr, unknown))}, "
            f"which isn't a partition column of {t._name}.",
            why="partition= gives values only to the columns the table is partitioned by.",
            fix=f"Name its partition columns, in its partitioned_by: {', '.join(columns)}.",
            error=ValueError,
        )
    first = columns[:len(partition)]
    skipped = [name for name in first if name not in partition]
    if skipped:
        later = [name for name in columns
                 if name in partition and columns.index(name) > columns.index(skipped[0])]
        refuse(
            what=f"{call}({t._alias}, partition=...) names {', '.join(partition)}, but not "
            f"{', '.join(skipped)}, which comes before it in {t._name}'s partitioned_by "
            f"({', '.join(columns)}).",
            why="Hive takes the partition columns in order: first the ones partition= gives a "
            "value, then the others by name alone, so a column after one with no value can't "
            "have one either.",
            fix=f"Give {', '.join(skipped)} a value too, or leave {', '.join(later)} out as "
            f"well: {left_out}.",
            error=ValueError,
        )
    named = {}
    for name in first:
        value = partition[name]
        if value is None or isinstance(value, Column):
            given = "None" if value is None else f"the column {python_text(value)}"
            refuse(
                what=f"{call}({t._alias}, partition=...) gives {name} {given}, not a value.",
                why="partition= names one Partition of each column it gives, by a value Hive "
                "writes as it is, such as 'EU' or 20260924: a column, or None, names none.",
                fix=f"Give {name} a value, such as a string or a number, or leave {name} out: "
                f"{left_out}.",
                error=ValueError,
            )
        named[name] = literal(value, call=f"{call}({t._alias}, partition=...)",
                              column=t._column(name), position=f"the value of {name}",
                              in_condition=False)
    return named


# Types people often write for one create_table takes, and the one to write instead.
_NEAREST_TYPE = {
    "integer": "int", "long": "bigint", "short": "smallint", "byte": "tinyint", "real": "float",
    "double precision": "double", "decimal": "decimal(10,0)", "numeric": "decimal(10,0)",
    "dec": "decimal(10,0)", "text": "string", "bool": "boolean", "datetime": "timestamp",
    "varchar": "varchar(50)", "char": "char(3)",
}
# Of those, the ones whose fix is to write their length.
_NEEDS_LENGTH = ("varchar", "char")


def column_definition(t: Table, column: str, call: str | None = None) -> Node:
    """One column of CREATE TABLE, its type checked now, so a wrong one stops create_table, or
    `call`, such as admin.add_columns(...), which adds it."""
    call = call or f"create_table({t._alias})"
    kind = t._columns[column]
    if not is_hive_type(kind):
        written = " ".join(kind.lower().split())
        nearest = _NEAREST_TYPE.get(written)
        length = "its length, such as " if written in _NEEDS_LENGTH else ""
        refuse(
            what=f"{call}: {column}'s type {kind!r} isn't one create_table can use.",
            why="create_table takes only the types Hive has, spelled as "
            "DESCRIBE prints them, such as int rather than integer, and with their sizes "
            "written out, such as decimal(10,2), so the table it makes matches its Table "
            "reference.",
            fix=(f"For {kind!r}, write {length}{nearest!r}. " if nearest else "")
            + "Use string, bigint, int, smallint, tinyint, double, float, boolean, date, "
            "timestamp or binary; decimal, varchar or char with its sizes, such as "
            "decimal(10,2), varchar(50) or char(3), up to decimal(38,s), varchar(65535) and "
            "char(255); or an array, map or struct holding them, such as array<string>, "
            "map<string,int> or struct<name:string,runs:int>. A map's key is a single value, "
            "such as string, and a struct's names are plain words, not reserved words, "
            "such as date or user.",
            error=ValueError,
        )
    return Node("ColumnDef", name=column, type=kind)
