"""Declarations themselves: attribute access, their own shape, the TimeBucket order, and
generation.

Four things live here, and each one is a fact the rest of the library reads without
re-deriving:

* ATTRIBUTE ACCESS is refusal 4 of decision 3. `DELIVERIES.fee_amonut` must be an error when
  the declarations module imports, not a query against a column that exists and means
  something else. It had no test at all: both raise sites could be replaced by "return a
  ColumnRef for whatever you asked for" with the whole suite green, and the only remaining
  net was the `qualify()` gate - which was equally unevidenced.

* THE SHAPE OF A DECLARATION is what `Column`, `Join` and `Source` check on themselves, at
  import of the contributor's own file. Every one of those refusals was mutation-survivable:
  each `raise` in the three `__post_init__`s could be replaced by `pass` with the whole suite
  green, so a Declaration that had stopped being checked would not fail, it would be
  accepted - an unnamed column, a keyless join that cross-joins, a column declared twice.

* THE TIME BUCKET PARTIAL ORDER is a dict, `_COARSENS_FROM`, and `grain.check_regrain`'s
  entire decision table is driven off it. Only one row of it was asserted anywhere, so it
  could be rewritten to say that weeks roll up into quarters - the wrong number the partial
  order exists to prevent - without failing anything. The truth table below is six lines of
  data that pin every future edit to it.

* GENERATION is decision 8's first clause, "Declarations are generated from the warehouse".
  The round-trip here is also the check that generation and the Drift check read the same
  four facts about a column, since `verify.WarehouseColumn` is the input to both.
"""
from __future__ import annotations

import datetime
import decimal
import itertools

import pytest

from declarations import deliveries as fixture
from sqlcomposer import verify
from sqlcomposer.declaration import (
    Cardinality,
    Column,
    Join,
    RunDate,
    Source,
    TimeBucket,
    generate,
    hive_type,
)
from sqlcomposer.errors import (
    DuplicateDeclaration,
    InvalidDeclaration,
    LiteralTypeMismatch,
    UndeclaredColumn,
)

# ======================================================================================
# Attribute access, and the refusal under it
# ======================================================================================


def test_a_misspelled_column_refuses_and_names_the_near_miss() -> None:
    """`Source.column` refuses unconditionally and suggests what was probably meant.

    The suggestion is asserted because it is the whole remedy: the overwhelmingly common
    cause is a typo and the second most common is a renamed column, and a refusal that says
    only "no such column" sends a contributor to the warehouse rather than to the next line
    of their own file.
    """
    with pytest.raises(UndeclaredColumn) as refused:
        fixture.DELIVERIES.column("fee_amonut")

    error = refused.value
    assert error.source == "mart.deliveries"
    assert error.column == "fee_amonut"
    assert "fee_amount" in error.did_you_mean
    assert error.subject == "mart.deliveries.fee_amonut"

    # The adjacent build: the name the refusal offers resolves, so this is not a test of a
    # Source that refuses everything.
    assert fixture.DELIVERIES.column("fee_amount").qualified == "mart.deliveries.fee_amount"


def test_attribute_access_refuses_the_same_way() -> None:
    """`DELIVERIES.fee_amonut` is the spelling contributors actually write."""
    with pytest.raises(UndeclaredColumn) as refused:
        fixture.DELIVERIES.fee_amonut  # noqa: B018  (the access IS the assertion)

    assert refused.value.column == "fee_amonut"
    assert fixture.DELIVERIES.fee_amount.name == "fee_amount"


def test_getattr_with_a_default_swallows_the_refusal_and_column_does_not() -> None:
    """The documented wrinkle, asserted so it stays documented rather than discovered.

    `UndeclaredColumn` is also an `AttributeError` - it has to be, or `copy`, `pickle`,
    `dataclasses` and REPL completion break in ways far harder to diagnose. The price is
    that defensive probing silently loses the refusal, which is why `Source.column(name)`
    exists and why anywhere the refusal matters must use it.
    """
    assert getattr(fixture.DELIVERIES, "fee_amonut", "fell back") == "fell back"
    assert hasattr(fixture.DELIVERIES, "fee_amonut") is False

    with pytest.raises(UndeclaredColumn):
        fixture.DELIVERIES.column("fee_amonut")


def test_a_column_shadowed_by_a_source_field_is_reachable_by_name() -> None:
    """A declared column called `note` or `table` is shadowed by the dataclass field.

    Loud rather than silent - the attribute returns a str and fails the next type check -
    but `Source.column` is the escape hatch, and it is only an escape hatch if it works.
    """
    shadowed = Source(
        db="d",
        table="t",
        columns=(Column("note", "STRING"), Column("table", "STRING")),
    )

    assert shadowed.note == ""  # the dataclass field, not the column
    assert shadowed.column("note").qualified == "d.t.note"
    assert shadowed.column("table").type == "STRING"


def test_accepts_answers_no_for_a_value_that_cannot_become_a_literal() -> None:
    """`Column.accepts` is the public "could this value inhabit this column" question, and
    it has to agree with `Column.literal`, which is what actually refuses.

    Both are asserted because both are reachable: `literal` is the way a predicate takes,
    and `accepts` is the one a caller takes to ask without provoking a refusal. A non-finite
    number is admissible by TYPE - `isinstance(nan, float)` is True - and is still not a
    value any warehouse column can be compared against.
    """
    money = Column("fee", "DECIMAL(18,2)")

    assert money.accepts(decimal.Decimal("1.50")) is True
    assert money.accepts(float("nan")) is False
    assert money.accepts(float("inf")) is False
    assert money.accepts(decimal.Decimal("NaN")) is False
    assert money.accepts("1.50") is False

    with pytest.raises(LiteralTypeMismatch):
        money.literal(float("nan"))


def test_a_type_text_hive_cannot_parse_refuses_at_declaration() -> None:
    """A mistyped type fails where it is written, not three modules away at render."""
    with pytest.raises(InvalidDeclaration) as refused:
        Column("x", "NOPE")

    assert refused.value.subject == "type:NOPE"
    assert hive_type("DECIMAL(18,2)").sql(dialect="hive") == "DECIMAL(18, 2)"


# ======================================================================================
# The shape of a Declaration: what `__post_init__` refuses before anything indexes it
#
# Every refusal below was mutation-survivable before this section existed - each `raise`
# in `Column.__post_init__`, `Join.__post_init__` and `Source.__post_init__` could be
# replaced by `pass` with the whole suite green. They fire at import of a declarations
# module, which is the only moment at which a contributor is still looking at the line
# that is wrong, so each is paired with the adjacent build that does import.
# ======================================================================================


def test_a_column_with_no_name_refuses() -> None:
    """The name is the identity: it keys `_by_name`, every Lineage node and every message.

    An empty one is not a Column that is merely awkward to read, it is one nothing can
    index, and a `Source` holding two of them would collide silently.
    """
    with pytest.raises(InvalidDeclaration) as refused:
        Column("", "STRING")

    assert refused.value.subject == "column:<unnamed>"
    assert Column("x", "STRING").name == "x"  # the adjacent build


def test_a_column_named_with_a_leading_underscore_refuses() -> None:
    """Leading-underscore names are reserved by `Source.__getattr__`, which must let `copy`,
    `pickle` and REPL completion ask for `_by_name` and friends without being answered with
    a ColumnRef. A column declared `_dt` would therefore be reachable by `Source.column`
    and unreachable by attribute, which is a difference nobody would predict from the
    Declaration.
    """
    with pytest.raises(InvalidDeclaration) as refused:
        Column("_dt", "STRING")

    assert refused.value.subject == "column:_dt"
    assert "Source.column(name)" in refused.value.remedy
    assert Column("dt", "STRING").name == "dt"  # the adjacent build


def test_a_join_declared_with_no_keys_refuses() -> None:
    """A keyless join is a cross join, which multiplies every Metric on both sides - the
    Fan-out failure, arriving before `Cardinality` gets a chance to describe it."""
    with pytest.raises(InvalidDeclaration) as refused:
        Join(to="mart.sites", keys=(), cardinality=Cardinality.MANY_TO_ONE)

    assert refused.value.subject == "join:->mart.sites"
    keyed = Join(  # the adjacent build
        to="mart.sites",
        keys=(("destination_site_id", "site_id"),),
        cardinality=Cardinality.MANY_TO_ONE,
    )
    assert keyed.keys == (("destination_site_id", "site_id"),)


def test_a_join_kind_outside_inner_and_left_refuses() -> None:
    """`kind` is not a free-text passthrough to the generator.

    A RIGHT or FULL join has no defined Cardinality in the direction the composer walks, so
    Fan-out detection would be answering a question about a different statement than the
    one emitted. The two supported kinds are the two whose row behaviour the declared
    Cardinality still describes.
    """
    with pytest.raises(InvalidDeclaration) as refused:
        Join(
            to="mart.sites",
            keys=(("destination_site_id", "site_id"),),
            cardinality=Cardinality.MANY_TO_ONE,
            kind="right",  # type: ignore[arg-type]
        )

    assert refused.value.subject == "join:->mart.sites"
    assert "Fan-out" in refused.value.remedy
    left = Join(  # the adjacent build
        to="mart.sites",
        keys=(("destination_site_id", "site_id"),),
        cardinality=Cardinality.MANY_TO_ONE,
        kind="left",
    )
    assert left.kind == "left"


def test_a_source_missing_a_db_or_a_table_refuses() -> None:
    """`db.table` is the key the Registry, the Lineage graph and every refusal index by, so
    half of it is not a Source that is merely under-described."""
    for db, table in (("", "deliveries"), ("mart", "")):
        with pytest.raises(InvalidDeclaration) as refused:
            Source(db=db, table=table, columns=(Column("x", "STRING"),))

        assert refused.value.subject == f"source:{db}.{table}"

    assert Source(  # the adjacent build
        db="mart", table="deliveries", columns=(Column("x", "STRING"),)
    ).qualified == "mart.deliveries"


def test_one_source_declaring_a_column_twice_refuses() -> None:
    """`_by_name` is a dict, so the second declaration would win silently - and the two are
    never identical when this happens, or nobody would have written it twice. The type the
    rest of the library reads would be whichever came last in the file."""
    with pytest.raises(DuplicateDeclaration) as refused:
        Source(
            db="mart",
            table="deliveries",
            columns=(Column("dt", "STRING"), Column("dt", "DATE")),
        )

    assert refused.value.name == "mart.deliveries.dt"
    assert refused.value.kind == "column"


def test_grain_buckets_naming_a_column_outside_grain_refuses() -> None:
    """`grain_buckets` annotates a column of `grain`; it cannot introduce one.

    A bucket on a column the Grain does not carry describes a Grain this Source is not
    stored at, and `Registry.native_grain` would then report a Grain whose bucketing no
    column backs - the re-grain check's whole input, quietly wrong.
    """
    with pytest.raises(InvalidDeclaration) as refused:
        Source(
            db="mart",
            table="weekly",
            columns=(Column("dt_week", "STRING"), Column("carrier", "STRING")),
            grain=("carrier",),
            grain_buckets=(("dt_week", TimeBucket.WEEK),),
        )

    assert refused.value.subject == "source:mart.weekly"
    bucketed = Source(  # the adjacent build: the same bucket, with the column in `grain`
        db="mart",
        table="weekly",
        columns=(Column("dt_week", "STRING"), Column("carrier", "STRING")),
        grain=("dt_week", "carrier"),
        grain_buckets=(("dt_week", TimeBucket.WEEK),),
    )
    assert bucketed.grain_buckets == (("dt_week", TimeBucket.WEEK),)


def test_an_empty_in_list_refuses_rather_than_emitting_it() -> None:
    """`IN ()` is not valid Hive, and the way it arrives is a comprehension that came back
    empty - so the statement the contributor meant narrowed by something, and the one they
    would get narrows by nothing at all."""
    with pytest.raises(InvalidDeclaration) as refused:
        fixture.DELIVERIES.carrier_id.isin()

    assert refused.value.subject == "mart.deliveries.carrier_id"
    one = fixture.DELIVERIES.carrier_id.isin("c1")  # the adjacent build
    assert one.to_sqlglot().sql(dialect="hive") == "deliveries.carrier_id IN ('c1')"


def test_a_hand_written_date_against_a_text_column_refuses() -> None:
    """A `date` compared against a column declared STRING is far likelier to be a mistake
    than an intent, and Hive answers a DATE-to-STRING comparison with NULL rather than an
    error - every row dropped, no refusal anywhere.

    The one date that is allowed through is a `RunDate`, because the library formats it
    itself: a `dt` partition column declared STRING is the standard Hive shape, and the
    deferred date is the only one that reaches it from inside the library.
    """
    dt = Column("dt", "STRING", partition=True)

    with pytest.raises(LiteralTypeMismatch) as refused:
        dt.literal(datetime.date(2026, 1, 2))

    assert refused.value.declared_type == "STRING"
    deferred = dt.literal(RunDate(), run_date=datetime.date(2026, 1, 2))  # the adjacent build
    assert deferred.sql(dialect="hive") == "'2026-01-02'"


# ======================================================================================
# The TimeBucket partial order
# ======================================================================================

COARSENS: frozenset[tuple[TimeBucket, TimeBucket]] = frozenset(
    {
        # (coarser, finer): the coarser bucket can be computed from the finer one.
        (TimeBucket.HOUR, TimeBucket.HOUR),
        (TimeBucket.DAY, TimeBucket.HOUR),
        (TimeBucket.DAY, TimeBucket.DAY),
        (TimeBucket.WEEK, TimeBucket.HOUR),
        (TimeBucket.WEEK, TimeBucket.DAY),
        (TimeBucket.WEEK, TimeBucket.WEEK),
        (TimeBucket.MONTH, TimeBucket.HOUR),
        (TimeBucket.MONTH, TimeBucket.DAY),
        (TimeBucket.MONTH, TimeBucket.MONTH),
        (TimeBucket.QUARTER, TimeBucket.HOUR),
        (TimeBucket.QUARTER, TimeBucket.DAY),
        (TimeBucket.QUARTER, TimeBucket.MONTH),
        (TimeBucket.QUARTER, TimeBucket.QUARTER),
        (TimeBucket.YEAR, TimeBucket.HOUR),
        (TimeBucket.YEAR, TimeBucket.DAY),
        (TimeBucket.YEAR, TimeBucket.MONTH),
        (TimeBucket.YEAR, TimeBucket.QUARTER),
        (TimeBucket.YEAR, TimeBucket.YEAR),
    }
)
"""Every true `coarser.coarsens(finer)` pair, written out as data.

Read the absences: WEEK appears on the left over HOUR and DAY only, and nowhere on the
right except under itself. Weeks do not roll up into months, quarters or years, because an
ISO week straddles every one of those boundaries - which is the same argument the library
makes for WEEK against MONTH, applied to the two pairs nothing was asserting."""


@pytest.mark.parametrize(
    ("coarser", "finer"), list(itertools.product(TimeBucket, TimeBucket))
)
def test_the_time_bucket_order_is_exactly_this(coarser: TimeBucket, finer: TimeBucket) -> None:
    """All 36 ordered pairs against the table above.

    `grain.check_regrain`'s whole decision table is driven off this order, so an edit that
    "fixes" it to make a quarterly Case compile is an edit that makes a wrong number
    compile. Thirty-six assertions is the price of that not being possible quietly.
    """
    assert coarser.coarsens(finer) is ((coarser, finer) in COARSENS)


@pytest.mark.parametrize(
    ("left", "right"), list(itertools.product(TimeBucket, TimeBucket))
)
def test_comparable_is_coarsens_in_either_direction(
    left: TimeBucket, right: TimeBucket
) -> None:
    """`comparable` is what tells GrainTooFine apart from GrainNotComparable."""
    expected = (left, right) in COARSENS or (right, left) in COARSENS
    assert left.comparable(right) is expected


def test_weeks_and_months_are_incomparable_in_both_directions() -> None:
    """The named case, asserted by name so a reader meets the argument rather than a row.

    A week straddles a month boundary, so neither bucket can be computed from the other and
    neither `GrainTooFine` nor a re-aggregation is defined between them. Most tools answer this
    silently and wrongly.
    """
    assert TimeBucket.MONTH.coarsens(TimeBucket.WEEK) is False
    assert TimeBucket.WEEK.coarsens(TimeBucket.MONTH) is False
    assert TimeBucket.MONTH.comparable(TimeBucket.WEEK) is False

    # ...and the same for the two pairs that had no test at all.
    assert TimeBucket.QUARTER.coarsens(TimeBucket.WEEK) is False
    assert TimeBucket.YEAR.coarsens(TimeBucket.WEEK) is False
    assert TimeBucket.QUARTER.coarsens(TimeBucket.MONTH) is True


# ======================================================================================
# Generating a first draft
# ======================================================================================


def _described(source: Source) -> tuple[verify.WarehouseColumn, ...]:
    """The fixture Source as a warehouse DESCRIBE would report it: four facts per column."""
    return tuple(
        verify.WarehouseColumn(
            name=column.name,
            type=column.type,
            partition=column.partition,
            nullable=column.nullable,
        )
        for column in source.columns
    )


def test_a_generated_declaration_round_trips_every_fact_a_describe_reports() -> None:
    """Generate from the fixture's own columns, execute the text, compare.

    This pins that generation and the Drift check read the SAME four facts - name, type,
    partition, nullable - because `verify.WarehouseColumn` is the input to both. A
    generator that dropped `partition=True` would produce a Declaration that renders every
    literal for that column with a CAST and defeats pruning, and the drift report would
    then call the warehouse wrong.
    """
    text = generate("mart", "deliveries", _described(fixture.DELIVERIES))
    namespace: dict[str, object] = {}
    exec(compile(text, "<generated>", "exec"), namespace)  # noqa: S102 - that IS the test
    regenerated = namespace["DELIVERIES"]

    assert isinstance(regenerated, Source)
    assert regenerated.qualified == "mart.deliveries"
    assert _described(regenerated) == _described(fixture.DELIVERIES)


def test_generation_keeps_nothing_a_describe_cannot_report() -> None:
    """The hand annotations are absent, and visibly so.

    A generator that invented a Cardinality would be worse than none: Fan-out detection is
    exactly as good as that annotation, and one nobody checked reads identically to one
    somebody did. So `joins` is empty, `one_row_per` is empty, every `note` is empty, and
    the TODOs say which of those a reviewer owes.
    """
    text = generate("mart", "deliveries", _described(fixture.DELIVERIES))
    namespace: dict[str, object] = {}
    exec(compile(text, "<generated>", "exec"), namespace)  # noqa: S102
    regenerated = namespace["DELIVERIES"]

    assert regenerated.joins == ()
    assert regenerated.one_row_per == ""
    assert [column.note for column in regenerated.columns] == [""] * len(regenerated.columns)
    assert fixture.DELIVERIES.one_row_per and any(
        column.note for column in fixture.DELIVERIES.columns
    ), "the fixture must carry annotations, or this test asserts nothing"
    assert "TODO" in text and "Cardinality" in text


def test_generating_a_table_with_no_columns_refuses() -> None:
    """An empty DESCRIBE is a failed DESCRIBE, and a Source that declares nothing can
    reference nothing - so it is never what was meant."""
    with pytest.raises(InvalidDeclaration) as refused:
        generate("mart", "gone", ())

    assert refused.value.subject == "source:mart.gone"
