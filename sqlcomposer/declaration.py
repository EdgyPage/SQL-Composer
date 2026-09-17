"""Declarations: the checked-in, authoritative statement of the warehouse.

A Source IS its Declaration. CONTEXT.md defines Source as "a physical table the composer
may read from or write to" and Declaration as "the checked-in statement of a Source's
columns, their types, its partitioning and its joins" - two angles on one object, because
in a library that "will not reference anything absent from it" the only Source that can
exist is a declared one. So `declaration.py` is the module and `Source` is the class, and
no separate Declaration type is spent.

Columns are reached by attribute access (`DELIVERIES.fee_amount`) so a typo is an error
when the declarations module imports, not a wrong-column statement that returns plausible
numbers. What comes back is a `ColumnRef` carrying the whole Declaration rather than a
name, and that is the load-bearing consequence: a predicate built from a ColumnRef knows
whether its column is a Partition column, so it can render a pruning-safe bare literal
without the author knowing that rule exists. `exp.convert(date(2026, 1, 2))` emits
`CAST('2026-01-02' AS DATE)`, and that CAST inside a Hive PARTITION predicate defeats
partition pruning.

`Column.literal()` is the only public way from a Python value to an AST node. Because it
is the only way, the no-string-interpolation rule of decision 10 is structural rather
than a convention a contributor has to remember: there is no supported way to put a value
into a statement except through a column that knows its own type and partitioning.

`Cardinality` and `TimeBucket` live here rather than in model.py because both are declared
facts about a Source, and putting them here is what removes the declaration/model import
cycle. model.py re-exports them.
"""
from __future__ import annotations

import difflib
import functools
import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Literal, Sequence, Union

from sqlglot import exp
from sqlglot.errors import ParseError
from sqlglot.schema import MappingSchema

from sqlcomposer.errors import (
    DuplicateDeclaration,
    EmptyTagFamily,
    InvalidDeclaration,
    LiteralTypeMismatch,
    RegistryFrozen,
    RegistryNotFrozen,
    UnboundRunDate,
    UndeclaredColumn,
    UndeclaredSource,
    UnknownCase,
    UnknownFilter,
    UnknownJoin,
    UnknownMetric,
)

if TYPE_CHECKING:  # model.py imports this module; the Registry only indexes its objects
    from sqlcomposer.model import Case, Filter, Grain, Metric
    from sqlcomposer.verify import WarehouseColumn

__all__ = [
    "HiveType",
    "hive_type",
    "python_types_for",
    "generate",
    "Cardinality",
    "TimeBucket",
    "RunDate",
    "Value",
    "Predicate",
    "Column",
    "ColumnRef",
    "Join",
    "JoinStep",
    "JoinPath",
    "Source",
    "Registry",
]


# ======================================================================================
# Hive types
# ======================================================================================

HiveType = str
"""A Hive type written exactly as the warehouse declares it: "STRING", "BIGINT",
"DECIMAL(18,2)". A plain `str` rather than a wrapper class - validation and the
python-type mapping are module functions, so the vocabulary gains no noun for something
that is already a string in every DDL a contributor reads."""


@functools.lru_cache(maxsize=None)
def hive_type(text: HiveType) -> exp.DataType:
    """Parse a declared Hive type, raising `InvalidDeclaration` on nonsense.

    Cached because it is called once per Column per import and the parse is the only
    validation a hand-annotated Declaration gets for free: `exp.DataType.build("NOPE",
    dialect="hive")` raises ParseError, so a mistyped type fails at import rather than at
    render, three modules away from the line that caused it.
    """
    try:
        return exp.DataType.build(text, dialect="hive")
    except ParseError as err:  # pragma: no cover - exercised by tests/test_declaration.py
        raise InvalidDeclaration(
            subject=f"type:{text}",
            problem=f"{text!r} is not a Hive type sqlglot can parse: {err}",
            remedy="use the type text the warehouse DESCRIBE reports, e.g. STRING, "
            "BIGINT, DECIMAL(18,2), TIMESTAMP",
        ) from err


_TEXT_TYPES = {exp.DataType.Type.TEXT, exp.DataType.Type.VARCHAR, exp.DataType.Type.CHAR}
_INT_TYPES = {
    exp.DataType.Type.TINYINT,
    exp.DataType.Type.SMALLINT,
    exp.DataType.Type.INT,
    exp.DataType.Type.BIGINT,
}
_REAL_TYPES = {
    exp.DataType.Type.FLOAT,
    exp.DataType.Type.DOUBLE,
    exp.DataType.Type.DECIMAL,
}


_NUMERIC_TEXT = re.compile(r"^-?\d+(\.\d+)?([eE][+-]?\d+)?$")
"""The only shape a numeric literal node is allowed to carry.

sqlglot stores a number literal as the TEXT it was handed (`Literal(this=str(value),
is_string=False)`) and emits it verbatim with no escaping - a number is not a string, so
there is nothing for the generator to escape. That makes `str(value)` the one way in this
library by which arbitrary characters could reach the SQL as syntax, because `Column.accepts`
constrains a value's TYPE and says nothing about the characters its `__str__` produces. An
`int` subclass whose `__str__` returns `"0 OR 1=1"` is a well-typed BIGINT.

So the text is formatted by `_numeric_literal` from the value's own numeric content rather
than taken from `str()`, and then matched against this pattern before it becomes a node. The
guarantee is structural: a node that does not match never exists."""


def _numeric_literal(value: int | float | Decimal, *, column: str, declared_type: HiveType) -> exp.Literal:
    """A number as a literal node, from text this library formats and validates itself.

    `int(...)`, `float(...)` and `Decimal(...)` are re-applied first so that a subclass
    overriding `__str__` or `__format__` cannot contribute a single character: what is
    formatted is a plain built-in holding the same number. `repr` for a float is its
    shortest round-tripping form, and `format(..., "f")` for a Decimal avoids the exponent
    spellings (`1E+3`) that read as an identifier in some Hive versions.

    Non-finite values never reach here - `Column.accepts` refuses them - so no branch of
    this produces `inf` or `NaN`.
    """
    if isinstance(value, bool):  # pragma: no cover - callers route bool through exp.convert
        raise LiteralTypeMismatch(column=column, declared_type=declared_type, value=value)
    if isinstance(value, int):
        text = format(int(value), "d")
    elif isinstance(value, Decimal):
        text = format(Decimal(value), "f")
    else:
        text = repr(float(value))
    if not _NUMERIC_TEXT.match(text):
        raise LiteralTypeMismatch(
            column=column,
            declared_type=declared_type,
            value=value,
            reason=f"{type(value).__name__} value renders as {text!r}, which is not a "
            "numeric literal",
        )
    return exp.Literal.number(text)


def _is_finite(value: Any) -> bool:
    """False for a NaN or an infinity, of either numeric type.

    Neither is a meaningful comparand for a warehouse column, and both are silent: `exp.convert`
    maps a NaN to `NULL`, so `fee_amount > NaN` becomes `fee_amount > NULL`, which is never
    true and reports zero rows rather than an error; on a Partition column the same value
    renders as the bare token `nan`, which Hive reads as a column reference.
    """
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Decimal):
        return value.is_finite()
    return True


def python_types_for(text: HiveType) -> tuple[type, ...]:
    """The Python types a value may have to be compared against this declared type.

    Deliberately coarse. It catches `dt.eq(20260917)` against a STRING partition column,
    which Hive answers with NULL rather than an error - the row silently vanishes and the
    Case reports zero. It does not catch `dt.eq("2026/09/17")` against a `yyyy-MM-dd`
    partition column, because both are `str`; partition literal formats live in
    `Column.note` and are checked by nothing. An empty tuple means the declared type
    admits no literal comparison at all (ARRAY, MAP, STRUCT, BINARY).
    """
    kind = hive_type(text).this
    if kind in _TEXT_TYPES:
        return (str,)
    if kind in _INT_TYPES:
        return (int,)
    if kind in _REAL_TYPES:
        return (int, float, Decimal)
    if kind is exp.DataType.Type.BOOLEAN:
        return (bool,)
    if kind is exp.DataType.Type.DATE:
        return (date,)
    if kind in (exp.DataType.Type.TIMESTAMP, exp.DataType.Type.TIMESTAMPTZ):
        return (datetime, date)
    return ()


# ======================================================================================
# Declared facts that are not themselves Declarations
# ======================================================================================


class Cardinality(Enum):
    """The declared row relationship between two Sources across a Join.

    Oriented: it reads left-to-right along the Join as declared, and `inverted()` gives it
    read from the other side. This is the single declared fact that both detects Fan-out
    and proves that a Dimension on a far Source only relabels rows rather than refining
    them - a Dimension reached over MANY_TO_ONE does not make a Metric's Grain finer.
    """

    ONE_TO_ONE = "1:1"
    MANY_TO_ONE = "N:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_MANY = "N:N"

    def inverted(self) -> Cardinality:
        """The same edge read from the other side."""
        return _INVERTED_CARDINALITY[self]

    @property
    def fans_out(self) -> bool:
        """True when traversing this edge multiplies the rows of the left-hand Source."""
        return self in (Cardinality.ONE_TO_MANY, Cardinality.MANY_TO_MANY)

    @property
    def determines_right(self) -> bool:
        """True when each left row has at most one right row, so the right Source's
        columns relabel rather than refine."""
        return self in (Cardinality.MANY_TO_ONE, Cardinality.ONE_TO_ONE)


_INVERTED_CARDINALITY: dict[Cardinality, Cardinality] = {
    Cardinality.ONE_TO_ONE: Cardinality.ONE_TO_ONE,
    Cardinality.MANY_TO_ONE: Cardinality.ONE_TO_MANY,
    Cardinality.ONE_TO_MANY: Cardinality.MANY_TO_ONE,
    Cardinality.MANY_TO_MANY: Cardinality.MANY_TO_MANY,
}


class TimeBucket(Enum):
    """Time truncation applied to a Dimension's column.

    A PARTIAL order, deliberately. DAY coarsens to WEEK, and DAY coarsens to MONTH to
    QUARTER to YEAR - but WEEK and MONTH are incomparable, because ISO weeks straddle
    month boundaries and rolling weeks into months is a wrong number that most tools emit
    silently. `comparable()` returning False is what makes grain.py refuse rather than
    guess.
    """

    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"

    def coarsens(self, other: TimeBucket) -> bool:
        """True when this bucket is `other` or a bucket `other` rolls up into."""
        return other in _COARSENS_FROM[self]

    def comparable(self, other: TimeBucket) -> bool:
        """True when one of the two buckets rolls up into the other, in either direction."""
        return self.coarsens(other) or other.coarsens(self)


_COARSENS_FROM: dict[TimeBucket, frozenset[TimeBucket]] = {
    TimeBucket.HOUR: frozenset({TimeBucket.HOUR}),
    TimeBucket.DAY: frozenset({TimeBucket.HOUR, TimeBucket.DAY}),
    TimeBucket.WEEK: frozenset({TimeBucket.HOUR, TimeBucket.DAY, TimeBucket.WEEK}),
    TimeBucket.MONTH: frozenset({TimeBucket.HOUR, TimeBucket.DAY, TimeBucket.MONTH}),
    TimeBucket.QUARTER: frozenset(
        {TimeBucket.HOUR, TimeBucket.DAY, TimeBucket.MONTH, TimeBucket.QUARTER}
    ),
    TimeBucket.YEAR: frozenset(
        {
            TimeBucket.HOUR,
            TimeBucket.DAY,
            TimeBucket.MONTH,
            TimeBucket.QUARTER,
            TimeBucket.YEAR,
        }
    ),
}


# ======================================================================================
# The one deferred value
# ======================================================================================


@dataclass(frozen=True)
class RunDate:
    """The date a statement is being built for, as a value a Filter can hold.

    The only deferred value in the library, and the only noun here that CONTEXT.md does
    not carry. It earns its place because the alternative is worse in kind rather than in
    degree: without it, every dated Case is either hand-edited per run or has a date
    formatted into its SQL text, and decision 10 has no enforcement left. Its whole
    surface is an integer offset and `resolve()`.
    """

    offset_days: int = 0

    def __sub__(self, days: int) -> RunDate:
        return RunDate(self.offset_days - days)

    def __add__(self, days: int) -> RunDate:
        return RunDate(self.offset_days + days)

    def resolve(self, run_date: date) -> date:
        """The concrete date this stands for, given the date the build is running for."""
        return run_date + timedelta(days=self.offset_days)

    def __str__(self) -> str:
        if self.offset_days == 0:
            return "run_date"
        return f"run_date{self.offset_days:+d}"


Value = Union[str, int, float, Decimal, bool, date, datetime, None, RunDate]
"""Everything a predicate builder accepts on the right-hand side of a comparison. There is
no raw-SQL member and no `ColumnRef` member: column-to-column comparisons belong in a Join,
where a Cardinality can be declared for them."""


def _resolve_value(value: Value, run_date: date | None, *, subject: str, text: str) -> Any:
    """Turn a possibly-deferred value into a concrete one, refusing an unbound RunDate."""
    if isinstance(value, RunDate):
        if run_date is None:
            raise UnboundRunDate(subject=subject, text=text)
        return value.resolve(run_date)
    return value


def _is_deferred(*values: Value) -> bool:
    return any(isinstance(value, RunDate) for value in values)


def _show(value: Value) -> str:
    return str(value) if isinstance(value, RunDate) else repr(value)


# ======================================================================================
# Predicate
# ======================================================================================


@dataclass(frozen=True, eq=False)
class Predicate:
    """A boolean sqlglot expression that has not been built yet, plus what it reads.

    Three reasons it is a type rather than a bare `exp.Condition`:

    * it can hold a `RunDate`, so a dated Filter is declared once and bound per run
      instead of being edited per run or formatted into SQL text;
    * `columns` is known without walking an AST, and those ColumnRefs are simultaneously
      the Lineage edges of a Filter and the scope of the Drift check;
    * `text` gives refusals and the Lineage text tree something readable to print that is
      not generated SQL.

    Equality is identity (`eq=False`), because two Predicates built the same way hold
    different closure objects and structural comparison would be a lie. Compare `.text`.

    There is no `from_sql` and there never will be: sqlglot escapes string-literal nodes
    and nothing else, so a predicate parsed from text bypasses the whole guarantee.
    """

    build: Callable[[date | None], exp.Condition]
    columns: frozenset[ColumnRef]
    text: str
    deferred: bool = False

    def to_sqlglot(self, *, run_date: date | None = None) -> exp.Condition:
        """Build the condition. Raises `UnboundRunDate` if deferred and `run_date` is None."""
        return self.build(run_date)

    @property
    def sources(self) -> frozenset[Source]:
        """The Sources this predicate reads, which is what tells joins.py what it drags in."""
        return frozenset(ref.source for ref in self.columns)

    def __and__(self, other: Predicate | Filter) -> Predicate:
        return _combine(self, other, "AND")

    def __or__(self, other: Predicate | Filter) -> Predicate:
        return _combine(self, other, "OR")

    def __invert__(self) -> Predicate:
        inner = self

        def build(run_date: date | None) -> exp.Condition:
            return exp.not_(inner.build(run_date))

        return Predicate(
            build=build,
            columns=inner.columns,
            text=f"NOT ({inner.text})",
            deferred=inner.deferred,
        )

    def __str__(self) -> str:
        return self.text


def _as_predicate(value: Predicate | Filter) -> Predicate:
    """Accept either a Predicate or a Filter wherever a predicate is expected.

    A Filter is a *named* Predicate, so requiring `.predicate` at every combination site
    would be ceremony with no guarantee attached. Duck-typed rather than isinstance-tested
    so that declaration.py need not import model.py.
    """
    if isinstance(value, Predicate):
        return value
    predicate = getattr(value, "predicate", None)
    if isinstance(predicate, Predicate):
        return predicate
    raise TypeError(f"expected a Predicate or Filter, got {type(value).__name__}")


def _combine(left: Predicate, right: Predicate | Filter, op: Literal["AND", "OR"]) -> Predicate:
    other = _as_predicate(right)
    joiner = exp.and_ if op == "AND" else exp.or_

    def build(run_date: date | None) -> exp.Condition:
        return joiner(left.build(run_date), other.build(run_date))

    return Predicate(
        build=build,
        columns=left.columns | other.columns,
        text=f"({left.text}) {op} ({other.text})",
        deferred=left.deferred or other.deferred,
    )


# ======================================================================================
# Column and ColumnRef
# ======================================================================================


@dataclass(frozen=True)
class Column:
    """One column of a Source, generated from the warehouse and hand-annotated.

    `nullable` defaults to True because that is what a warehouse DESCRIBE reports;
    tightening it to False is a hand annotation, and it is what lets the composer refuse
    an inner Join keyed on a column Hive would silently drop rows for.

    `partition` is load-bearing beyond documentation: it changes how a value compared to
    this column is rendered, because `exp.convert`'s CAST defeats Hive partition pruning.

    `note` is the place a partition column's literal format is written down. Nothing
    checks it, which is exactly why it must be written down.
    """

    name: str
    type: HiveType
    partition: bool = False
    nullable: bool = True
    note: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise InvalidDeclaration(
                subject="column:<unnamed>",
                problem="a Column was declared with an empty name",
                remedy="give it the name the warehouse reports",
            )
        if self.name.startswith("_"):
            raise InvalidDeclaration(
                subject=f"column:{self.name}",
                problem=f"column {self.name!r} starts with an underscore",
                remedy="attribute access on a Source reserves leading-underscore names so "
                "that copy and pickle keep working; rename the column or read it with "
                "Source.column(name)",
            )
        hive_type(self.type)  # refuses at import if the declared type is not parseable

    def accepts(self, value: Value) -> bool:
        """True when a Python value could inhabit this column's declared Hive type.

        A non-finite float or Decimal is refused here rather than rendered, because both
        spellings of it are silent wrong numbers rather than errors: `exp.convert(nan)` is
        `NULL`, so a comparison against it matches no row and the Case reports zeros, and
        on a Partition column the same value renders as the bare token `nan`, which Hive
        resolves as a column reference. A NaN arriving from a `0/0` or an upstream pandas
        aggregation is the realistic source, and there is nothing it could correctly mean
        here.
        """
        if value is None or isinstance(value, RunDate):
            return True
        if not _is_finite(value):
            return False
        allowed = python_types_for(self.type)
        if not allowed:
            return False
        if isinstance(value, bool) and bool not in allowed:
            return False
        return isinstance(value, allowed)

    def literal(self, value: Value, *, run_date: date | None = None, subject: str = "") -> exp.Expr:
        """The ONLY way from a Python value to an AST node.

        On a Partition column this emits a bare, uncast literal whose text matches the
        declared type, because `exp.convert(date(2026, 1, 2))` renders
        `CAST('2026-01-02' AS DATE)` and that CAST inside a PARTITION predicate defeats
        pruning - a full-table scan that returns the right answer slowly, or the wrong one
        if the scan times out and someone narrows it by hand.

        Everywhere else it is `exp.convert`, whose CAST is correct and wanted: a typed
        comparison against a TIMESTAMP column should be a TIMESTAMP.

        A NUMBER never goes through `exp.convert` on either branch. `exp.convert` funnels
        numbers into `exp.Literal.number(str(value))`, which stores that text verbatim and
        emits it unescaped - so `str()` would be the one way by which a value's own code
        could put syntax into the SQL. `_numeric_literal` formats the text from the value's
        numeric content instead and validates the result, which makes the no-interpolation
        rule of decision 10 structural here too rather than a property of `str()`.
        """
        where = subject or f"column:{self.name}"
        from_run_date = isinstance(value, RunDate)
        concrete = _resolve_value(value, run_date, subject=where, text=_show(value))
        if concrete is None:
            return exp.null()
        kind = hive_type(self.type).this
        if kind in _TEXT_TYPES and isinstance(concrete, date):
            # A date partition column declared STRING is the standard Hive shape, and a
            # RunDate is the only date this library defers. Rendering it as ISO text keeps
            # the comparison inside the declared type - `exp.convert` would CAST it to DATE
            # and compare a DATE against a STRING, which Hive answers with NULL.
            # A literal date written by hand against a text column is still refused: it is
            # far more likely to be a mistake than an intent.
            if not from_run_date:
                raise LiteralTypeMismatch(column=where, declared_type=self.type, value=concrete)
            return exp.Literal.string(_partition_text(concrete))
        if not _is_finite(concrete):
            # Refused before the declared-type check so the message names what is actually
            # wrong: a NaN against a DECIMAL column IS of an admissible Python type, and
            # "cannot inhabit DECIMAL(18,2)" would send a contributor to the Declaration.
            raise LiteralTypeMismatch(
                column=where,
                declared_type=self.type,
                value=concrete,
                reason=f"{type(concrete).__name__} value {concrete!r} is not finite, and "
                "neither a NaN nor an infinity is a meaningful comparand for a warehouse "
                "column",
            )
        if not self.accepts(concrete):
            raise LiteralTypeMismatch(column=where, declared_type=self.type, value=concrete)
        if isinstance(concrete, (int, float, Decimal)) and not isinstance(concrete, bool):
            return _numeric_literal(concrete, column=where, declared_type=self.type)
        if not self.partition:
            return exp.convert(concrete)
        if kind is exp.DataType.Type.BOOLEAN:
            return exp.convert(concrete)
        return exp.Literal.string(_partition_text(concrete))

    def to_sqlglot(self) -> exp.DataType:
        """The declared type as a sqlglot node, for CTAS column specs and drift compares."""
        return hive_type(self.type)


def _partition_text(value: Any) -> str:
    """Render a partition value as the string Hive compares a partition column against."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


@dataclass(frozen=True)
class ColumnRef:
    """A Column bound to the Source that declares it. What attribute access returns.

    Identity here is Lineage identity: `qualified` is `db.table.column`, so the string a
    contributor types in a Declaration is the same string that appears in the graph, the
    DOT export and the drift report. Nothing in the library re-derives it.

    The predicate builders are the only supported way a value enters a statement. Each one
    goes through `Column.literal`, so partition-safe rendering and the declared-type
    check happen whether or not the author knows they exist.

    sqlglot note, verified against 30.18.0: `exp.Column` offers `eq/neq/isin/is_/between/
    like` but NOT `gt/lt/gte/lte`; those are built as `exp.GT(this=..., expression=...)`.
    Hiding that asymmetry is half the reason this class has methods at all.
    """

    source: Source
    column: Column

    # -- identity ----------------------------------------------------------------------

    @property
    def qualified(self) -> str:
        """`db.table.column` - the Lineage node id, used verbatim everywhere."""
        return f"{self.source.qualified}.{self.column.name}"

    @property
    def name(self) -> str:
        return self.column.name

    @property
    def type(self) -> HiveType:
        return self.column.type

    @property
    def partition(self) -> bool:
        return self.column.partition

    @property
    def nullable(self) -> bool:
        return self.column.nullable

    def to_sqlglot(self) -> exp.Column:
        """A fresh table-qualified column node, `table.column`.

        Qualified by the bare table name, never by an alias: the Registry refuses two
        Sources sharing a bare table name, so the bare name is unique within any Case, and
        `qualify()` supplies `AS \\`table\\`` in the FROM clause itself.
        """
        return exp.column(self.column.name, table=self.source.table)

    def literal(self, value: Value, *, run_date: date | None = None) -> exp.Expr:
        """This column's literal rendering of a value. See `Column.literal`."""
        return self.column.literal(value, run_date=run_date, subject=self.qualified)

    def __str__(self) -> str:
        return self.qualified

    # -- predicates --------------------------------------------------------------------

    def _check(self, *values: Value) -> None:
        """Validate every non-deferred value now, so a mistyped comparison is an error at
        import rather than three modules away at compile time.

        A Predicate holds a builder closure so it can bind a RunDate per run, and that
        alone would defer the declared-type check to the moment SQL is generated. This
        runs the same rendering eagerly and throws the node away, which costs one AST node
        per declared predicate and buys back the import-time refusal that makes attribute
        access worth having.
        """
        for value in values:
            if not isinstance(value, RunDate):
                self.literal(value)

    def _compare(self, node: type[exp.Expression], op: str, value: Value) -> Predicate:
        ref = self
        self._check(value)

        def build(run_date: date | None) -> exp.Condition:
            return node(this=ref.to_sqlglot(), expression=ref.literal(value, run_date=run_date))

        return Predicate(
            build=build,
            columns=frozenset({ref}),
            text=f"{ref.qualified} {op} {_show(value)}",
            deferred=_is_deferred(value),
        )

    def eq(self, value: Value) -> Predicate:
        """`column = value`. NULL never equals anything - use `is_null()` for that."""
        return self._compare(exp.EQ, "=", value)

    def ne(self, value: Value) -> Predicate:
        """`column <> value`. Excludes NULL rows too, which is usually not what a
        contributor means; combine with `is_null()` when NULLs should survive."""
        return self._compare(exp.NEQ, "<>", value)

    def gt(self, value: Value) -> Predicate:
        """`column > value`."""
        return self._compare(exp.GT, ">", value)

    def ge(self, value: Value) -> Predicate:
        """`column >= value`."""
        return self._compare(exp.GTE, ">=", value)

    def lt(self, value: Value) -> Predicate:
        """`column < value`."""
        return self._compare(exp.LT, "<", value)

    def le(self, value: Value) -> Predicate:
        """`column <= value`."""
        return self._compare(exp.LTE, "<=", value)

    def isin(self, *values: Value) -> Predicate:
        """`column IN (...)`. Refuses an empty list, which Hive cannot parse and which
        almost always means a list was built from an empty collection by mistake."""
        if not values:
            raise InvalidDeclaration(
                subject=self.qualified,
                problem="isin() was called with no values",
                remedy="pass at least one value; an empty IN list is not valid Hive and "
                "usually means a list comprehension came back empty",
            )
        ref = self
        self._check(*values)

        def build(run_date: date | None) -> exp.Condition:
            return ref.to_sqlglot().isin(
                *(ref.literal(value, run_date=run_date) for value in values)
            )

        return Predicate(
            build=build,
            columns=frozenset({ref}),
            text=f"{ref.qualified} IN ({', '.join(_show(v) for v in values)})",
            deferred=_is_deferred(*values),
        )

    def not_in(self, *values: Value) -> Predicate:
        """`NOT column IN (...)`. Drops NULL rows, like every NOT IN in SQL."""
        return ~self.isin(*values)

    def between(self, low: Value, high: Value) -> Predicate:
        """`column BETWEEN low AND high`, inclusive at both ends."""
        ref = self
        self._check(low, high)

        def build(run_date: date | None) -> exp.Condition:
            return exp.Between(
                this=ref.to_sqlglot(),
                low=ref.literal(low, run_date=run_date),
                high=ref.literal(high, run_date=run_date),
            )

        return Predicate(
            build=build,
            columns=frozenset({ref}),
            text=f"{ref.qualified} BETWEEN {_show(low)} AND {_show(high)}",
            deferred=_is_deferred(low, high),
        )

    def like(self, pattern: str) -> Predicate:
        """`column LIKE pattern`. The pattern is escaped as a string literal like any
        other value, so a `'` in it cannot break out."""
        ref = self

        def build(run_date: date | None) -> exp.Condition:
            return exp.Like(this=ref.to_sqlglot(), expression=exp.Literal.string(pattern))

        return Predicate(
            build=build,
            columns=frozenset({ref}),
            text=f"{ref.qualified} LIKE {pattern!r}",
        )

    def is_null(self) -> Predicate:
        """`column IS NULL`."""
        ref = self

        def build(run_date: date | None) -> exp.Condition:
            return ref.to_sqlglot().is_(exp.null())

        return Predicate(
            build=build, columns=frozenset({ref}), text=f"{ref.qualified} IS NULL"
        )

    def is_not_null(self) -> Predicate:
        """`column IS NOT NULL`."""
        ref = self

        def build(run_date: date | None) -> exp.Condition:
            return exp.not_(ref.to_sqlglot().is_(exp.null()))

        return Predicate(
            build=build, columns=frozenset({ref}), text=f"{ref.qualified} IS NOT NULL"
        )


# ======================================================================================
# Joins
# ======================================================================================


@dataclass(frozen=True)
class Join:
    """One declared edge out of the Source that carries it.

    `to` is a `db.table` string rather than a Source object so two Declarations may join
    each other without an import cycle between declaration modules. It is resolved - and
    its keys checked against both sides - once, at `Registry.freeze()`.

    `name` is not cosmetic. Two Sources can be joined two ways (a delivery's origin city
    and its destination city), so a Case pinning a Join path with `via=` has to name edges,
    not nodes. When left empty the Registry names the edge `db.left->db.right`; declare a
    name explicitly the moment a second edge joins the same pair.
    """

    to: str
    keys: tuple[tuple[str, str], ...]
    cardinality: Cardinality
    name: str = ""
    kind: Literal["inner", "left"] = "inner"
    note: str = ""

    def __post_init__(self) -> None:
        if not self.keys:
            raise InvalidDeclaration(
                subject=f"join:->{self.to}",
                problem="a Join was declared with no keys",
                remedy="declare the (left_column, right_column) pairs the join is on; a "
                "keyless join is a cross join and inflates every Metric on both sides",
            )
        if self.kind not in ("inner", "left"):
            raise InvalidDeclaration(
                subject=f"join:->{self.to}",
                problem=f"unknown join kind {self.kind!r}",
                remedy="use 'inner' or 'left'; a right or full outer join has no defined "
                "Cardinality for Fan-out detection",
            )


@dataclass(frozen=True)
class JoinStep:
    """One traversal of a declared Join, oriented.

    The universal currency for Join paths: `Registry.joins()` hands back every declared
    Join already in this form, oriented as declared, and `inverted()` gives the reverse
    traversal with its Cardinality flipped and its keys swapped. `name` is invariant under
    inversion, because a Join path is pinned by naming edges and an edge is one edge
    whichever way you walk it.
    """

    name: str
    frm: Source
    to: Source
    keys: tuple[tuple[ColumnRef, ColumnRef], ...]
    cardinality: Cardinality
    kind: Literal["inner", "left"] = "inner"

    def inverted(self) -> JoinStep:
        """The same edge walked the other way."""
        return JoinStep(
            name=self.name,
            frm=self.to,
            to=self.frm,
            keys=tuple((right, left) for left, right in self.keys),
            cardinality=self.cardinality.inverted(),
            kind=self.kind,
        )

    @property
    def fans_out(self) -> bool:
        """True when walking this step multiplies the rows of `frm`."""
        return self.cardinality.fans_out

    def on(self) -> exp.Condition:
        """The ON condition, built from ColumnRef nodes on both sides - never from text."""
        conditions = [left.to_sqlglot().eq(right.to_sqlglot()) for left, right in self.keys]
        condition = conditions[0]
        for extra in conditions[1:]:
            condition = exp.and_(condition, extra)
        return condition

    def __str__(self) -> str:
        return f"{self.frm.qualified} -({self.cardinality.value})-> {self.to.qualified}"


JoinPath = tuple[JoinStep, ...]
"""The chain of declared Joins connecting the Sources a Case needs, in the order they are
walked from the spine. A tuple rather than a class: CONTEXT.md defines a Join path as a
chain of declared joins, and a chain of things is a sequence. An empty tuple is the
single-Source case and is completely ordinary."""


# ======================================================================================
# Source
# ======================================================================================


@dataclass(frozen=True)
class Source:
    """A physical table the composer may read from or write to - and its Declaration.

    Columns are reached by attribute access, so `DELIVERIES.fee_amonut` is an error when
    the declarations module imports rather than a statement against a column that does not
    exist. The refusal names near-miss columns, because the overwhelmingly common cause is
    a typo and the second most common is a column that was renamed.

    Two fields deserve explanation:

    `one_row_per` is prose and is never parsed. It exists because it is the one line a
    reviewer can check a declared Cardinality against, and Fan-out detection is only ever
    as good as that Cardinality.

    `grain` is what makes a re-grain decidable. `None` means atomic rows, where rolling up
    is always safe. A tuple names the columns a pre-aggregated Source is already collapsed
    to, which is the only situation in which a Metric's Re-aggregation rule can be
    violated. For a Source this library writes, set `written_by` instead and let the
    producing Case's Grain be authoritative - a declared `grain` that disagrees with its
    producer is refused at `freeze()`.

    Attribute-access caveat: a declared column whose name collides with a field of this
    class (`db`, `table`, `columns`, `joins`, `grain`, `note`, ...) is shadowed and must be
    read with `Source.column("name")`. That is loud rather than silent - the attribute
    returns a str or a tuple and fails the next type check - but it is a wrinkle worth
    knowing before meeting it.
    """

    db: str
    table: str
    columns: tuple[Column, ...]
    joins: tuple[Join, ...] = ()
    grain: tuple[str, ...] | None = None
    grain_buckets: tuple[tuple[str, TimeBucket], ...] = ()
    written_by: str | None = None
    one_row_per: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if not self.db or not self.table:
            raise InvalidDeclaration(
                subject=f"source:{self.db}.{self.table}",
                problem="a Source needs both a db and a table name",
                remedy="declare both; the qualified name is the key everything indexes by",
            )
        by_name: dict[str, Column] = {}
        for column in self.columns:
            if column.name in by_name:
                raise DuplicateDeclaration(kind="column", name=f"{self.qualified}.{column.name}")
            by_name[column.name] = column
        object.__setattr__(self, "_by_name", by_name)

        if self.grain is not None and self.written_by is not None:
            raise InvalidDeclaration(
                subject=f"source:{self.qualified}",
                problem="both grain and written_by are declared",
                remedy="a Source this library writes takes its Grain from the Case that "
                "writes it; declare `grain` only for a pre-aggregated Source produced "
                "outside the composer",
            )
        for name in self.grain or ():
            if name not in by_name:
                raise UndeclaredColumn(
                    source=self.qualified,
                    column=name,
                    did_you_mean=difflib.get_close_matches(name, by_name, n=3, cutoff=0.6),
                )
        for name, _bucket in self.grain_buckets:
            if name not in (self.grain or ()):
                raise InvalidDeclaration(
                    subject=f"source:{self.qualified}",
                    problem=f"grain_buckets names {name!r}, which is not in grain",
                    remedy="every bucketed column must also appear in `grain`",
                )

    # -- identity ----------------------------------------------------------------------

    @property
    def qualified(self) -> str:
        """`db.table` - the key the Registry and every refusal message index by."""
        return f"{self.db}.{self.table}"

    def __str__(self) -> str:
        return self.qualified

    # -- columns -----------------------------------------------------------------------

    def __getattr__(self, name: str) -> ColumnRef:
        """Declared columns by attribute; `UndeclaredColumn` for anything else.

        Leading-underscore names are refused as a plain AttributeError before the column
        map is even consulted, because `__getattr__` runs during unpickling and copying,
        before `_by_name` exists - without that guard those recurse instead of failing.
        """
        if name.startswith("_"):
            raise AttributeError(name)
        by_name: dict[str, Column] = object.__getattribute__(self, "_by_name")
        column = by_name.get(name)
        if column is None:
            raise UndeclaredColumn(
                source=self.qualified,
                column=name,
                did_you_mean=difflib.get_close_matches(name, by_name, n=3, cutoff=0.6),
            )
        return ColumnRef(source=self, column=column)

    def column(self, name: str) -> ColumnRef:
        """Look a column up by name, refusing unconditionally when it is not declared.

        The dynamic-access door, and the escape hatch for a column whose name collides
        with a field of this class. Prefer this over `getattr` anywhere the refusal
        matters: `UndeclaredColumn` is also an AttributeError, so `getattr(src, "typo",
        default)` yields the default instead of raising.
        """
        by_name: dict[str, Column] = object.__getattribute__(self, "_by_name")
        column = by_name.get(name)
        if column is None:
            raise UndeclaredColumn(
                source=self.qualified,
                column=name,
                did_you_mean=difflib.get_close_matches(name, by_name, n=3, cutoff=0.6),
            )
        return ColumnRef(source=self, column=column)

    def has(self, name: str) -> bool:
        """True when this Source declares a column of that name."""
        return name in object.__getattribute__(self, "_by_name")

    def refs(self) -> tuple[ColumnRef, ...]:
        """Every declared column of this Source, as ColumnRefs, in declaration order."""
        return tuple(ColumnRef(source=self, column=column) for column in self.columns)

    @property
    def partition_columns(self) -> tuple[Column, ...]:
        """The Partition columns, in declaration order - the order a PARTITION clause needs."""
        return tuple(column for column in self.columns if column.partition)

    def __dir__(self) -> list[str]:
        """Include declared column names so REPL and IDE completion see them."""
        return sorted(set(super().__dir__()) | set(object.__getattribute__(self, "_by_name")))

    # -- joins -------------------------------------------------------------------------

    def join_to(self, qualified: str) -> tuple[Join, ...]:
        """Every Join this Source declares towards a qualified name. Usually zero or one;
        two means the pair needs named edges and a Case must pin one with `via=`."""
        return tuple(join for join in self.joins if join.to == qualified)

    # -- sqlglot -----------------------------------------------------------------------

    def to_sqlglot(self) -> exp.Table:
        """`exp.table_(table, db=db)` - a fresh node each call, never shared between trees."""
        return exp.table_(self.table, db=self.db)

    def schema_entry(self) -> dict[str, HiveType]:
        """`{column_name: TYPE}` - this Source's leaf of the MappingSchema nested dict."""
        return {column.name: column.type for column in self.columns}


# ======================================================================================
# Generating a first draft of a Declaration
# ======================================================================================


_GENERATED_HEADER = '''"""GENERATED from the warehouse. Hand-annotate, then commit.

Everything a DESCRIBE can report is here and everything it cannot is marked TODO. The
TODOs are not cosmetic - a Declaration without them compiles, and each one that stays
unanswered is a refusal this library cannot make:

* `cardinality` on each Join is the whole of Fan-out detection. Nothing else knows it.
* `one_row_per` is the one line a reviewer checks a declared Cardinality against.
* `nullable=False` is a hand annotation. A DESCRIBE reports almost everything nullable,
  and an inner Join keyed on a nullable column drops rows on both sides; ask
  `Registry.nullable_join_keys()` for what is still untightened.
* a Partition column's literal format belongs in its `note`, where nothing checks it,
  which is exactly why it has to be written down.
"""
from __future__ import annotations

from sqlcomposer.declaration import Column, Source
'''
"""The import line names only what a generated draft uses, so the file lints clean the
moment it is written. A Join needs `Cardinality` and `Join` added to it, which the TODO
beside `joins=()` says."""


def _identifier(table: str) -> str:
    """A module-level name for a generated Source: the table name, shouted."""
    cleaned = "".join(character if character.isalnum() else "_" for character in table)
    return cleaned.upper() if cleaned[:1].isalpha() else f"T_{cleaned.upper()}"


def generate(
    db: str,
    table: str,
    columns: Sequence[WarehouseColumn],
    *,
    module: bool = True,
) -> str:
    """A first-draft Declaration for one warehouse table, as Python source text.

    Decision 8's first clause - "Declarations are generated from the warehouse, checked in,
    hand-annotated" - in the only form a compile-only library can honour it: this takes the
    columns, it does not go and get them. `tools/generate_declarations.py` takes the same
    injected `describe` callable `verify.verify` takes, so nothing in the core connects to
    a warehouse here either.

    It is the exact mirror of the Drift check, and deliberately so: `verify` compares a
    Declaration against `WarehouseColumn(name, type, partition, nullable)` and this writes
    a Declaration from the same four facts. One shape, read in both directions - so a
    regenerated Declaration and a clean drift report cannot disagree about what a column is.

    What it CANNOT know is left as a TODO rather than guessed: `joins=()`, `one_row_per=""`
    and every `note`. A generated `nullable=` is copied through as the warehouse reports it,
    which is almost always `True` and is the annotation a reviewer tightens first.

    `module=False` returns just the `NAME = Source(...)` statement, for appending a table to
    a declarations module that already exists.
    """
    if not columns:
        raise InvalidDeclaration(
            subject=f"source:{db}.{table}",
            problem=f"the warehouse reported no columns for {db}.{table}",
            remedy="check the table name and that the DESCRIBE succeeded; a Source with no "
            "columns can reference nothing and is never what was meant",
        )
    lines = [f"{_identifier(table)} = Source("]
    lines.append(f"    db={db!r},")
    lines.append(f"    table={table!r},")
    lines.append('    one_row_per="",  # TODO: prose. What is one row of this table?')
    lines.append("    columns=(")
    for column in columns:
        parts = [f"{column.name!r}", f"{column.type!r}"]
        if column.partition:
            parts.append("partition=True")
        if not column.nullable:
            parts.append("nullable=False")
        lines.append(f"        Column({', '.join(parts)}),")
    lines.append("    ),")
    lines.append("    # TODO: one Join per declared edge, each with its keys and its")
    lines.append("    # Cardinality, which is the whole of Fan-out detection. Add")
    lines.append("    # `Cardinality, Join` to the import above and write them as")
    lines.append("    # Join(to='db.table', keys=(('left', 'right'),),")
    lines.append("    #      cardinality=Cardinality.MANY_TO_ONE, name='...')")
    lines.append("    joins=(),")
    lines.append(")")
    body = "\n".join(lines) + "\n"
    return f"{_GENERATED_HEADER}\n\n{body}" if module else body


# ======================================================================================
# Registry
# ======================================================================================


class Registry:
    """The index of everything declared, and the one concept here the glossary does not
    carry.

    It exists because a Case names a Tag family rather than a list of Metrics, so a newly
    declared Metric must be findable without editing any Case, and nothing in the glossary
    owns that lookup. The alternative is a module-level global populated by import side
    effects - still a concept, just invisible, order-dependent and hostile to tests. So it
    is explicit and injected: every function that needs it takes it as its first argument.

    It absorbs three more jobs that would otherwise each want a type of their own: it is
    the MappingSchema exporter for the qualify() gate, it is where a Tag family resolves,
    and `freeze()` is the single moment cross-Declaration facts are checked.

    Sealing is not hygiene. A Metric registered after a Case resolved its family joins the
    next run and not this one, and the number changes with nothing in the diff to point at.
    """

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._sources: dict[str, Source] = {}
        self._by_table: dict[str, Source] = {}
        self._metrics: dict[str, Metric] = {}
        self._filters: dict[str, Filter] = {}
        self._cases: dict[str, Case] = {}
        self._joins: dict[str, JoinStep] = {}
        self._frozen = False

    def __repr__(self) -> str:
        return (
            f"Registry({self.name!r}, sources={len(self._sources)}, "
            f"metrics={len(self._metrics)}, cases={len(self._cases)}, "
            f"frozen={self._frozen})"
        )

    # -- declaring ---------------------------------------------------------------------

    def add(self, *declared: Any) -> Registry:
        """Index anything declared, dispatching on type. Returns self, so calls chain.

        Accepts `Source`, `Metric`, `Filter` and `Case`; anything else is a TypeError.
        model.py is imported inside this method rather than at module scope: model.py
        imports this module, and a call-time import cannot cycle because by the time
        anyone holds a Metric, model.py has finished importing.
        """
        from sqlcomposer.model import Case, Filter, Metric  # local: see docstring

        for item in declared:
            if isinstance(item, Source):
                self._add_named(self._sources, item.qualified, item, "Source")
                if item.table in self._by_table and self._by_table[item.table] is not item:
                    raise DuplicateDeclaration(kind="Source table name", name=item.table)
                self._by_table[item.table] = item
            elif isinstance(item, Metric):
                self._add_named(self._metrics, item.name, item, "Metric")
            elif isinstance(item, Filter):
                self._add_named(self._filters, item.name, item, "Filter")
            elif isinstance(item, Case):
                self._add_named(self._cases, item.name, item, "Case")
            else:
                raise TypeError(
                    f"Registry.add accepts Source, Metric, Filter and Case, not "
                    f"{type(item).__name__}"
                )
        return self

    def _add_named(self, into: dict[str, Any], key: str, item: Any, kind: str) -> None:
        if self._frozen:
            raise RegistryFrozen(kind=kind, name=key)
        existing = into.get(key)
        if existing is not None and existing is not item:
            raise DuplicateDeclaration(kind=kind, name=key)
        into[key] = item

    @classmethod
    def from_modules(cls, *modules: ModuleType, name: str = "default") -> Registry:
        """Collect every Source, Metric, Filter and Case bound to a public module-level
        name, in module order then alphabetical name order.

        This is what makes horizontal Tag scaling cost no ceremony: declare a Metric in a
        declarations module and every Case asking for its family picks it up, with no
        `register()` call to forget and no Case edited.

        It is genuine magic and it has one genuine hole: an object built inside a function
        or a comprehension, or bound to a private name, is never seen, and the failure is
        silent absence from a Tag family. `EmptyTagFamily` catches the case where a Tag
        matches nothing at all, but a Metric that is merely one of five missing raises
        nothing. Declare at module level.

        Does NOT freeze. Call `freeze()` explicitly once every declarations module has
        been imported, so a caller can still `.add()` a test fixture on top.
        """
        from sqlcomposer.model import Case, Filter, Metric  # local: see add()

        registry = cls(name=name)
        wanted = (Source, Metric, Filter, Case)
        for module in modules:
            found = [
                value
                for key, value in sorted(vars(module).items())
                if not key.startswith("_") and isinstance(value, wanted)
            ]
            registry.add(*found)
        return registry

    # -- freezing ----------------------------------------------------------------------

    @property
    def frozen(self) -> bool:
        return self._frozen

    def require_frozen(self, operation: str) -> None:
        """Refuse an operation that must not run against an unchecked Registry."""
        if not self._frozen:
            raise RegistryNotFrozen(operation=operation)

    def freeze(self) -> Registry:
        """Run every cross-Declaration check once, then refuse further `add()`.

        Declarations are built incrementally at import time, so a Join's far side may not
        exist yet when the Join is constructed. This is the moment all of it is checked:
        join targets resolve, join keys exist on both sides, join names are unique, a
        written Source's Grain agrees with the Case that writes it, every `via=` names a
        real edge, and every Tag a Case asks for is carried by at least one Metric.

        Returns self, so `Registry.from_modules(...).freeze()` reads as one expression.
        """
        if self._frozen:
            return self
        self._joins = self._build_join_steps()
        self._check_written_sources()
        self._check_cases()
        self._frozen = True
        return self

    def _build_join_steps(self) -> dict[str, JoinStep]:
        steps: dict[str, JoinStep] = {}
        for source in self.sources():
            for join in source.joins:
                target = self._sources.get(join.to)
                if target is None:
                    raise UndeclaredSource(qualified=join.to, known=sorted(self._sources))
                keys: list[tuple[ColumnRef, ColumnRef]] = []
                for left_name, right_name in join.keys:
                    keys.append((source.column(left_name), target.column(right_name)))
                # Deliberately NOT refused here: an inner Join keyed on a nullable column
                # silently drops rows on both sides, but a generated Declaration reports
                # almost everything nullable, so refusing would block every first-draft
                # Declaration and the escape (kind="left") changes the semantics rather
                # than documenting them. Tightening `nullable=False` is the hand
                # annotation; `nullable_join_keys()` reports what is still untightened.
                name = join.name or f"{source.qualified}->{target.qualified}"
                if name in steps:
                    raise DuplicateDeclaration(kind="Join", name=name)
                steps[name] = JoinStep(
                    name=name,
                    frm=source,
                    to=target,
                    keys=tuple(keys),
                    cardinality=join.cardinality,
                    kind=join.kind,
                )
        return steps

    def _check_written_sources(self) -> None:
        """Check the write->read link in BOTH directions, so it is total rather than a hint.

        `Source.written_by` and `Case.writes_to` are two halves of one fact, and everything
        downstream reads only the first: `native_grain` and `metric_behind` both start at
        `writing_case(source)`, so a target this library writes whose Declaration omits
        `written_by` reports no native Grain at all - which silently disables the
        unsafe-re-grain refusal for every Metric that reads it. That is the flagship wrong
        number (a stored COUNT(DISTINCT) summed across days) arriving through the ordinary
        declaration API with nothing to catch it, so the Case direction is checked here too.

        Both directions refuse the same way, because both are the same mistake seen from
        opposite ends. Two Cases pointing `writes_to` at one target are refused as part of
        it: only one of them can be named by the target's `written_by`, and two Cases
        writing one Partition overwrite each other on every run.
        """
        for source in self.sources():
            if source.written_by is None:
                continue
            case = self._cases.get(source.written_by)
            if case is None:
                raise UnknownCase(case=source.written_by, known=sorted(self._cases))
            if case.writes_to is None:
                raise InvalidDeclaration(
                    subject=f"source:{source.qualified}",
                    problem=f"{source.qualified} says it is written by {case.name!r}, but "
                    "that Case declares no `writes_to` and writes nothing",
                    remedy=f"give {case.name!r} `writes_to=<this Source>`, or drop "
                    "`written_by`; a Grain taken from a Case that writes nothing is not the "
                    "Grain of this table's rows",
                )
            if case.writes_to.qualified != source.qualified:
                raise InvalidDeclaration(
                    subject=f"source:{source.qualified}",
                    problem=f"{source.qualified} says it is written by {case.name!r}, but "
                    f"that Case writes to {case.writes_to.qualified}",
                    remedy="point `written_by` at the Case that actually writes this "
                    "Source, or correct that Case's `writes_to`",
                )
        for case in self.cases():
            if case.writes_to is None:
                continue
            target = self.source(case.writes_to.qualified)
            if target.written_by != case.name:
                raise InvalidDeclaration(
                    subject=f"case:{case.name}",
                    problem=f"Case {case.name!r} writes {target.qualified}, but that Source "
                    f"declares written_by={target.written_by!r}",
                    remedy=f"declare {target.qualified} with written_by={case.name!r}; "
                    "without that backlink the composer does not know the Grain its rows "
                    "are collapsed to, and every re-grain refusal for Metrics reading it is "
                    "silently disabled",
                )

    def _check_cases(self) -> None:
        for case in self.cases():
            for join_name in case.via:
                if join_name not in self._joins:
                    raise UnknownJoin(
                        case=case.name, join=join_name, known=sorted(self._joins)
                    )
            if case.anchor is not None and case.anchor not in self._sources:
                # Whether the anchor is a Source this Case's Metrics measure is a question
                # for `joins.spine`, which has the resolved family; whether it is a declared
                # Source at all is a question this has the answer to, and answering it here
                # turns a typo into an import-time refusal.
                raise UndeclaredSource(qualified=case.anchor, known=sorted(self._sources))
            for tag in case.metrics.tags:
                self._tagged_one(tag, case=case.name)

    # -- lookups -----------------------------------------------------------------------

    def source(self, qualified: str) -> Source:
        """A Source by `db.table`. Raises `UndeclaredSource`."""
        found = self._sources.get(qualified)
        if found is None:
            raise UndeclaredSource(qualified=qualified, known=sorted(self._sources))
        return found

    def sources(self) -> tuple[Source, ...]:
        """Every declared Source, sorted by qualified name for a stable artifact."""
        return tuple(self._sources[key] for key in sorted(self._sources))

    def source_of_table(self, table: str) -> Source:
        """Resolve a bare table name - as it appears in `exp.Column.table` - to its Source.

        Unambiguous because `add()` refuses two Sources sharing a bare table name; that
        refusal is what lets every column node in the library be qualified by the bare
        name and still resolve.
        """
        found = self._by_table.get(table)
        if found is None:
            raise UndeclaredSource(qualified=table, known=sorted(self._by_table))
        return found

    def resolve_column(self, qualified: str) -> ColumnRef:
        """`db.table.column` back to a ColumnRef. The inverse of `ColumnRef.qualified`.

        Used when a Manifest or a static Lineage artifact is read back from disk, where
        nodes exist only as strings.
        """
        db, _, rest = qualified.partition(".")
        table, _, column = rest.partition(".")
        if not db or not table or not column:
            raise UndeclaredSource(qualified=qualified, known=sorted(self._sources))
        return self.source(f"{db}.{table}").column(column)

    def metric(self, name: str) -> Metric:
        """A Metric by name. Raises `UnknownMetric`."""
        found = self._metrics.get(name)
        if found is None:
            raise UnknownMetric(metric=name, known=sorted(self._metrics))
        return found

    def metrics(self) -> tuple[Metric, ...]:
        """Every declared Metric, sorted by name."""
        return tuple(self._metrics[key] for key in sorted(self._metrics))

    def tagged(self, *tags: str, case: str | None = None) -> tuple[Metric, ...]:
        """Every Metric carrying any of these Tags, deduplicated and sorted by name.

        Each Tag is checked individually: a Tag carried by no Metric raises
        `EmptyTagFamily` even when the other Tags in the same call matched plenty. That is
        the whole reason Tag can be a plain `str` - checked over the union instead, a Case
        naming two Tags with one misspelled would resolve to a family missing half its
        Metrics and report fewer columns than its author intended, silently.

        Sorted by name rather than declaration order so the SQL, the golden tests and the
        git-tracked Lineage artifact do not move when an import order changes.
        """
        selected: dict[str, Metric] = {}
        for tag in tags:
            for metric in self._tagged_one(tag, case=case):
                selected[metric.name] = metric
        return tuple(selected[key] for key in sorted(selected))

    def _tagged_one(self, tag: str, *, case: str | None) -> tuple[Metric, ...]:
        found = tuple(metric for metric in self.metrics() if tag in metric.tags)
        if not found:
            raise EmptyTagFamily(tag=tag, known=sorted(self.tags()), case=case)
        return found

    def tags(self) -> frozenset[str]:
        """Every Tag carried by at least one declared Metric."""
        return frozenset(tag for metric in self._metrics.values() for tag in metric.tags)

    def filter(self, name: str) -> Filter:
        """A Filter by name. Raises `UnknownFilter`."""
        found = self._filters.get(name)
        if found is None:
            raise UnknownFilter(filter=name, known=sorted(self._filters))
        return found

    def filters(self) -> tuple[Filter, ...]:
        """Every declared Filter, sorted by name."""
        return tuple(self._filters[key] for key in sorted(self._filters))

    def case(self, name: str) -> Case:
        """A Case by name. Raises `UnknownCase`."""
        found = self._cases.get(name)
        if found is None:
            raise UnknownCase(case=name, known=sorted(self._cases))
        return found

    def cases(self) -> tuple[Case, ...]:
        """Every declared Case, sorted by name."""
        return tuple(self._cases[key] for key in sorted(self._cases))

    def join(self, name: str) -> JoinStep:
        """A declared Join by name, oriented as declared. Raises `UnknownJoin`."""
        self.require_frozen("Registry.join")
        found = self._joins.get(name)
        if found is None:
            raise UnknownJoin(case="(lookup)", join=name, known=sorted(self._joins))
        return found

    def joins(self) -> tuple[JoinStep, ...]:
        """Every declared Join, oriented as declared, sorted by name."""
        self.require_frozen("Registry.joins")
        return tuple(self._joins[key] for key in sorted(self._joins))

    def joins_from(self, source: Source) -> tuple[JoinStep, ...]:
        """Every edge leaving `source`, in whichever orientation leaves it.

        A declared edge is walkable both ways, so this returns the declared step when
        `source` declares it and the inverted step when `source` is on the far side. Its
        `name` is the same either way, which is what makes `via=` direction-independent.
        """
        self.require_frozen("Registry.joins_from")
        out: list[JoinStep] = []
        for step in self.joins():
            if step.frm.qualified == source.qualified:
                out.append(step)
            elif step.to.qualified == source.qualified:
                out.append(step.inverted())
        return tuple(out)

    def nullable_join_keys(self) -> tuple[tuple[str, ColumnRef], ...]:
        """Every inner-Join key still declared nullable, as (join name, column).

        Not a refusal, and deliberately so: a Declaration generated from the warehouse
        reports almost everything nullable, so refusing here would block every first-draft
        Declaration, and the only escape (`kind="left"`) changes the join's semantics
        rather than documenting them. This is the list a reviewer walks when hand-
        annotating - an inner join keyed on a nullable column drops rows on both sides and
        deflates every Metric that reaches across it.
        """
        self.require_frozen("Registry.nullable_join_keys")
        out: list[tuple[str, ColumnRef]] = []
        for step in self.joins():
            if step.kind != "inner":
                continue
            for left, right in step.keys:
                for ref in (left, right):
                    if ref.nullable:
                        out.append((step.name, ref))
        return tuple(out)

    # -- derived facts -----------------------------------------------------------------

    def writing_case(self, source: Source) -> Case | None:
        """The Case that writes this Source, if one is declared.

        The hop that lets a re-grain check know the Grain a stored Metric was written at,
        and that lets a Manifest trace through a written table to the true upstream.
        """
        if source.written_by is None:
            return None
        return self.case(source.written_by)

    def native_grain(self, source: Source) -> Grain | None:
        """The Grain this Source's rows are already collapsed to, or None for atomic rows.

        Derived from the writing Case when there is one, so a written Source's Grain
        cannot drift from its producer. The returned Grain's Dimensions point at THIS
        Source's own columns, matched to the producing Case's output names - which is what
        a later Case re-graining off the written table has to reason about.

        For a pre-aggregated Source produced outside the composer, built from the declared
        `grain` and `grain_buckets` instead.

        Every Dimension is aliased to the column it reads, in both branches, so the Grain
        publishes the names this table's own DESCRIBE reports. That is not cosmetic: this
        Grain is what `UnsafeReAggregation`, `GrainTooFine` and `GrainNotComparable` print
        as `native=`, and what the Lineage records as a Metric's `native` attribute. Left
        to `Dimension.name`'s default, a stored DAY-bucketed column called `dt_day` would
        publish as `dt_day_day` and every one of those messages would name a column no
        contributor can find. Bucketing still has to be re-stated by the reading Case -
        `Dimension.coarsens_to` compares columns and buckets and ignores aliases, so the
        alias changes what a refusal says and nothing about what it refuses.
        """
        from sqlcomposer.model import Dimension, Grain  # local: model imports this module

        case = self.writing_case(source)
        if case is not None:
            dimensions = []
            for dimension in case.grain.dimensions:
                if not source.has(dimension.name):
                    raise InvalidDeclaration(
                        subject=f"source:{source.qualified}",
                        problem=f"{source.qualified} is written by {case.name!r} at a Grain "
                        f"including {dimension.name!r}, but declares no such column",
                        remedy="regenerate the Declaration for the written table, or "
                        "correct the writing Case's Grain",
                    )
                stored = source.column(dimension.name)
                dimensions.append(
                    Dimension(column=stored, bucket=dimension.bucket, alias=stored.name)
                )
            return Grain(dimensions=tuple(dimensions))
        if source.grain is None:
            return None
        buckets = dict(source.grain_buckets)
        return Grain(
            dimensions=tuple(
                Dimension(
                    column=source.column(name), bucket=buckets.get(name), alias=name
                )
                for name in source.grain
            )
        )

    def metric_behind(self, ref: ColumnRef) -> Metric | None:
        """The Metric that produced this column of a written Source, if any.

        The hop that turns "an average of averages is wrong" from a slogan into a raise:
        given a column of a written table, it recovers the Metric - and therefore the
        Re-aggregation rule - that put the numbers there. Matched by output name, which is
        why `Case.output_names()` must stay stable.
        """
        case = self.writing_case(ref.source)
        if case is None:
            return None
        for metric in case.resolved_metrics(self):
            if metric.name == ref.name:
                return metric
        return None

    def referenced_columns(self) -> frozenset[ColumnRef]:
        """Every column some declared Case actually reaches.

        The scope of the Drift check: a warehouse change to a column no Case reads is
        informational, and scoping the check here is what stops every unrelated schema
        change from blocking every build.
        """
        refs: set[ColumnRef] = set()
        for case in self.cases():
            refs |= case.referenced_columns(self)
        return frozenset(refs)

    # -- sqlglot export ----------------------------------------------------------------

    def schema_dict(self) -> dict[str, dict[str, dict[str, HiveType]]]:
        """`{db: {table: {column: TYPE}}}` - the nested shape sqlglot wants."""
        out: dict[str, dict[str, dict[str, HiveType]]] = {}
        for source in self.sources():
            out.setdefault(source.db, {})[source.table] = source.schema_entry()
        return out

    def schema(self) -> MappingSchema:
        """The MappingSchema for the qualify() gate and for lineage cross-checks.

        Always built from every declared Source, never a subset. qualify()'s star
        expansion silently no-ops on an incomplete schema rather than raising, so a partial
        schema turns the resolution gate into a no-op without saying so.
        """
        return MappingSchema(self.schema_dict(), dialect="hive")
