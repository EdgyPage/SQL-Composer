"""The Registry: what it refuses at `add()`, and what `freeze()` checks across Declarations.

Nothing in this file compiles SQL. Every test here is about a refusal that fires before any
statement exists, and every one of them was mutation-survivable before this module existed -
`freeze()`'s three cross-Declaration checks could each be replaced by `return`, and
`_add_named`'s `RegistryFrozen` and `DuplicateDeclaration` could both be replaced by `pass`,
with the whole suite green.

So could the four by-name LOOKUPS, which is the other half of what a Registry is: `metric`,
`filter`, `case` and `join` could each return None for a name nothing carries, and the only
evidence of it would be an AttributeError a frame or two later naming this library rather
than the misspelling. They are asserted at the end of this file.

Each test builds its own throwaway Registry rather than using the shared fixture, because the
subject is a Registry in a state the shared one may never be in - unfrozen, half-declared, or
contradicting itself. The fixture Registry is frozen at import and correct by construction,
which is exactly why it cannot evidence any of this.

Two conventions the reader should expect, both from the suite's house style:

* every refusal is asserted on TYPED ATTRIBUTES (`error.name`, `error.case`), never on prose;
* every refusal is paired with the ADJACENT BUILD - the almost-identical Declaration that is
  correct and does freeze - so that none of these is a test of a Registry that refuses
  everything.
"""
from __future__ import annotations

import pytest

from sqlcomposer.declaration import (
    Cardinality,
    Column,
    Join,
    Registry,
    Source,
    TimeBucket,
)
from sqlcomposer.errors import (
    DuplicateDeclaration,
    EmptyTagFamily,
    InvalidDeclaration,
    RegistryFrozen,
    RegistryNotFrozen,
    UndeclaredColumn,
    UndeclaredSource,
    UnknownCase,
    UnknownFilter,
    UnknownJoin,
    UnknownMetric,
)
from sqlcomposer.model import (
    Case,
    Dimension,
    Grain,
    by_name,
    by_tag,
    count_distinct,
    count_rows,
    sum_of,
)

# ======================================================================================
# INVENTED FIXTURE, third of three. Deliberately tiny: every Source here exists to be the
# left or right side of exactly one refusal.
# ======================================================================================

ORDERS = Source(
    db="raw",
    table="orders",
    one_row_per="order line",
    columns=(
        Column("order_id", "STRING", nullable=False),
        Column("courier_id", "STRING", nullable=True, note="NULL until one is assigned"),
        Column("amount", "DECIMAL(18,2)", nullable=False),
        Column("dt", "STRING", partition=True, nullable=False, note="yyyy-MM-dd"),
    ),
    joins=(
        Join(
            to="raw.couriers",
            keys=(("courier_id", "courier_id"),),
            cardinality=Cardinality.MANY_TO_ONE,
            name="order_courier",
        ),
    ),
)

COURIERS = Source(
    db="raw",
    table="couriers",
    one_row_per="courier",
    columns=(
        Column("courier_id", "STRING", nullable=False),
        Column("city", "STRING"),
    ),
)

AMOUNT = sum_of("orders_amount", ORDERS.amount, tags=("money",))
SEEN = count_rows("orders_seen", ORDERS, tags=("volume",))

BY_CITY = Case(name="orders_by_city", metrics=by_name(AMOUNT), grain=Grain.of(COURIERS.city))


def built() -> Registry:
    """A correct, UNFROZEN Registry. Every test starts from this and breaks one thing."""
    return Registry(name="registry-tests").add(ORDERS, COURIERS, AMOUNT, SEEN, BY_CITY)


# ======================================================================================
# Sealing
# ======================================================================================


def test_the_adjacent_build_freezes_chains_and_is_idempotent() -> None:
    """The baseline every refusal below is measured against.

    `freeze()` returns self so `Registry.from_modules(...).freeze()` reads as one
    expression, and calling it twice is a no-op rather than a second pass of the checks.
    """
    registry = built()
    assert registry.frozen is False

    frozen = registry.freeze()
    assert frozen is registry
    assert registry.frozen is True
    assert registry.freeze() is registry


@pytest.mark.parametrize(
    ("kind", "make"),
    [
        ("Source", lambda: Source(db="raw", table="late", columns=(Column("x", "STRING"),))),
        ("Metric", lambda: sum_of("late_metric", ORDERS.amount, tags=("money",))),
        ("Case", lambda: Case(name="late_case", metrics=by_name(AMOUNT), grain=Grain())),
    ],
)
def test_declaring_anything_after_freeze_refuses(kind: str, make) -> None:
    """A Metric declared late joins the NEXT run of a Case and not this one.

    That is the whole argument for sealing, and it is not hygiene: the number moves with
    nothing in the diff to point at, because the Case that reports it was never edited.
    All four declarable kinds go through one `_add_named`, so one mutation disabled the
    guard for every one of them - which is why each is asserted separately here.
    """
    registry = built()
    declared = make()
    registry.add(declared)  # the adjacent build: before freeze() this is ordinary

    sealed = Registry(name="sealed").add(ORDERS, COURIERS, AMOUNT, SEEN, BY_CITY).freeze()

    with pytest.raises(RegistryFrozen) as refused:
        sealed.add(declared)

    assert refused.value.kind == kind


def test_a_late_metric_would_otherwise_grow_a_tag_family_mid_process() -> None:
    """The consequence, spelled out: the family a Case resolves must not change under it.

    `resolved_metrics` is called at compile time, so without the seal the same Case object
    answers with one column set before an `add()` and another after it, inside one process.
    """
    registry = built().freeze()
    before = registry.case("orders_by_city").output_names(registry)

    with pytest.raises(RegistryFrozen):
        registry.add(count_rows("orders_late", ORDERS, tags=("money",)))

    assert registry.case("orders_by_city").output_names(registry) == before


def test_operations_that_need_the_cross_checks_refuse_an_unfrozen_registry() -> None:
    """The mirror of sealing: reading a Registry whose cross-checks never ran."""
    unfrozen = built()

    with pytest.raises(RegistryNotFrozen) as refused:
        unfrozen.joins()
    assert refused.value.operation == "Registry.joins"

    with pytest.raises(RegistryNotFrozen):
        unfrozen.nullable_join_keys()


# ======================================================================================
# Duplicates
# ======================================================================================


def test_two_sources_sharing_a_bare_table_name_refuse() -> None:
    """This refusal is the premise of the library's whole alias-free column qualification.

    Every column node is `table.column` with no alias, and `Registry.source_of_table`
    resolves a bare table name back to its Source. Two `deliveries` tables in two databases
    would make both of those answer for whichever was added last - runnable SQL over the
    wrong table, and a Lineage graph pointing at the wrong Declaration.
    """
    other_orders = Source(db="mart", table="orders", columns=(Column("order_id", "STRING"),))

    with pytest.raises(DuplicateDeclaration) as refused:
        built().add(other_orders)

    assert refused.value.name == "orders"
    assert refused.value.kind == "Source table name"

    # The adjacent build: the same Source under a table name nothing else uses is fine.
    renamed = Source(db="mart", table="orders_v2", columns=(Column("order_id", "STRING"),))
    assert built().add(renamed).source("mart.orders_v2") is renamed


@pytest.mark.parametrize(
    ("kind", "first", "second"),
    [
        (
            "Metric",
            lambda: sum_of("orders_amount", ORDERS.amount),
            lambda: count_rows("orders_amount", ORDERS),
        ),
        (
            "Case",
            lambda: Case(name="twice", metrics=by_name(AMOUNT), grain=Grain()),
            lambda: Case(name="twice", metrics=by_name(SEEN), grain=Grain()),
        ),
    ],
)
def test_two_declarations_of_one_kind_sharing_a_name_refuse(kind, first, second) -> None:
    """Names are the join key between the SQL, the Lineage artifact and the review diff.

    A collision silently shadows one of the two, and every one of those three then describes
    a different thing than the statement does.
    """
    registry = Registry(name=f"dup-{kind}").add(ORDERS, COURIERS)
    registry.add(first())

    with pytest.raises(DuplicateDeclaration) as refused:
        registry.add(second())

    assert refused.value.kind == kind


def test_adding_the_identical_object_twice_is_not_a_duplicate() -> None:
    """`Registry.from_modules` scans module globals, and one object can be bound twice."""
    registry = built()
    registry.add(AMOUNT, AMOUNT)
    assert registry.metric("orders_amount") is AMOUNT


def test_two_joins_resolving_to_one_name_refuse() -> None:
    """A second edge under one name would silently overwrite the first in `Registry._joins`,
    and every `via=` naming it would lead somewhere else - along an edge with a different
    Cardinality, so with a different row count and no refusal anywhere."""
    twice = Source(
        db="raw",
        table="orders_two_edges",
        columns=(
            Column("courier_id", "STRING"),
            Column("other_courier_id", "STRING"),
        ),
        joins=(
            Join(
                to="raw.couriers",
                keys=(("courier_id", "courier_id"),),
                cardinality=Cardinality.MANY_TO_ONE,
                name="shared_name",
            ),
            Join(
                to="raw.couriers",
                keys=(("other_courier_id", "courier_id"),),
                cardinality=Cardinality.ONE_TO_MANY,
                name="shared_name",
            ),
        ),
    )

    with pytest.raises(DuplicateDeclaration) as refused:
        Registry(name="dup-join").add(twice, COURIERS).freeze()

    assert refused.value.kind == "Join"
    assert refused.value.name == "shared_name"


def test_an_unnamed_join_is_named_after_the_pair_it_connects() -> None:
    """The adjacent build for the one above: one edge per pair needs no explicit name."""
    registry = built().freeze()
    assert [step.name for step in registry.joins()] == ["order_courier"]
    assert registry.join("order_courier").to.qualified == "raw.couriers"


# ======================================================================================
# freeze(): the cross-Declaration checks
# ======================================================================================


def test_a_join_to_a_source_nobody_declared_refuses() -> None:
    """A Join's far side may not exist yet when the Join is constructed, which is the whole
    reason these checks are deferred to freeze() rather than run in `__post_init__`."""
    dangling = Source(
        db="raw",
        table="dangling",
        columns=(Column("k", "STRING"),),
        joins=(
            Join(to="raw.nowhere", keys=(("k", "k"),), cardinality=Cardinality.MANY_TO_ONE),
        ),
    )

    with pytest.raises(UndeclaredSource) as refused:
        Registry(name="dangling").add(dangling).freeze()

    assert refused.value.qualified == "raw.nowhere"


def test_a_join_key_absent_from_either_side_refuses() -> None:
    """A key that exists on neither side is a join on nothing, which is a cross join."""
    wrong_key = Source(
        db="raw",
        table="wrong_key",
        columns=(Column("k", "STRING"),),
        joins=(
            Join(
                to="raw.couriers",
                keys=(("k", "courier_ident"),),
                cardinality=Cardinality.MANY_TO_ONE,
                name="wrong_key_edge",
            ),
        ),
    )

    with pytest.raises(UndeclaredColumn) as refused:
        Registry(name="wrong-key").add(wrong_key, COURIERS).freeze()

    assert refused.value.source == "raw.couriers"
    assert refused.value.column == "courier_ident"
    assert "courier_id" in refused.value.did_you_mean


def test_a_written_by_naming_no_case_refuses() -> None:
    written = Source(
        db="mart",
        table="orders_daily",
        written_by="no_such_case",
        columns=(Column("city", "STRING"), Column("orders_amount", "DECIMAL(18,2)")),
    )

    with pytest.raises(UnknownCase) as refused:
        Registry(name="no-writer").add(ORDERS, COURIERS, AMOUNT, written).freeze()

    assert refused.value.case == "no_such_case"


def test_a_written_by_naming_a_case_that_writes_nothing_refuses() -> None:
    """`native_grain` would otherwise report a Grain taken from a Case that writes nothing -
    a claim about the rows of this table made by a statement that never touches it."""
    written = Source(
        db="mart",
        table="orders_daily",
        written_by="orders_by_city",
        columns=(Column("city", "STRING"), Column("orders_amount", "DECIMAL(18,2)")),
    )

    with pytest.raises(InvalidDeclaration) as refused:
        built().add(written).freeze()

    assert refused.value.subject == "source:mart.orders_daily"
    assert "writes nothing" in refused.value.problem


def test_a_written_by_naming_a_case_that_writes_a_different_table_refuses() -> None:
    """The stale backlink: a Declaration copied for a second table, `written_by` left as it
    was. Both tables then claim one Case, and only one of them is right.

    Unrefused, the copied table takes its native Grain and its `metric_behind` answers from
    a Case that writes somewhere else entirely - so the re-grain check runs against the
    Grain of the wrong table's rows, and a stored partial sums across a Grain nobody wrote
    it at.
    """
    written = Source(
        db="mart",
        table="orders_daily",
        written_by="write_orders_daily",
        columns=(Column("city", "STRING"), Column("orders_amount", "DECIMAL(18,2)")),
    )
    writer = Case(
        name="write_orders_daily",
        metrics=by_name(AMOUNT),
        grain=Grain.of(Dimension(COURIERS.city, alias="city")),
        writes_to=written,
    )
    copied = Source(
        db="mart",
        table="orders_daily_v2",
        written_by="write_orders_daily",  # the line that was not edited with the table name
        columns=(Column("city", "STRING"), Column("orders_amount", "DECIMAL(18,2)")),
    )

    with pytest.raises(InvalidDeclaration) as refused:
        built().add(written, writer, copied).freeze()

    assert refused.value.subject == "source:mart.orders_daily_v2"
    assert "mart.orders_daily" in refused.value.problem  # the table the Case really writes

    # The adjacent build: the same pair without the copy freezes, and the backlink resolves.
    registry = built().add(written, writer).freeze()
    assert registry.writing_case(written) is writer


def test_a_written_target_missing_a_column_of_its_writers_grain_refuses() -> None:
    """`native_grain` reads the writing Case's Grain and looks each Dimension up as a COLUMN
    of the written table, because the Grain of those rows is the one the table can be read
    back at.

    A target whose Declaration has drifted from the Case that fills it - a column renamed in
    the warehouse, the Declaration regenerated, the Case not touched - has no such column.
    Answering with the Case's Dimension anyway would publish a native Grain naming a column
    the table does not have, and every `GrainTooFine` and `GrainNotComparable` message about
    it would name a column no contributor can find.
    """
    drifted = Source(
        db="mart",
        table="orders_daily",
        written_by="write_orders_daily",
        columns=(Column("town", "STRING"), Column("orders_amount", "DECIMAL(18,2)")),
    )
    writer = Case(
        name="write_orders_daily",
        metrics=by_name(AMOUNT),
        grain=Grain.of(Dimension(COURIERS.city, alias="city")),
        writes_to=drifted,
    )
    registry = built().add(drifted, writer).freeze()

    with pytest.raises(InvalidDeclaration) as refused:
        registry.native_grain(drifted)

    assert refused.value.subject == "source:mart.orders_daily"
    assert "city" in refused.value.problem

    # The adjacent build: the same Case over a target that declares the column answers with
    # the Grain its rows are actually stored at.
    matching = Source(
        db="mart",
        table="orders_daily",
        written_by="write_orders_daily",
        columns=(Column("city", "STRING"), Column("orders_amount", "DECIMAL(18,2)")),
    )
    fixed = Case(
        name="write_orders_daily",
        metrics=by_name(AMOUNT),
        grain=Grain.of(Dimension(COURIERS.city, alias="city")),
        writes_to=matching,
    )
    assert str(built().add(matching, fixed).freeze().native_grain(matching)) == "(city)"


def test_a_case_whose_target_does_not_name_it_back_refuses() -> None:
    """The direction that was missing, and the one the wrong number came through.

    Everything downstream reads only the Source's half: `native_grain` and `metric_behind`
    both start at `Registry.writing_case(source)`, which returns None when `written_by` is
    unset. So a target this library writes whose Declaration omits the backlink has NO
    native Grain, and the unsafe-re-grain refusal is silently disabled for every Metric
    that reads it - a stored COUNT(DISTINCT) then sums across days with nothing to stop it.
    """
    target = Source(
        db="mart",
        table="orders_daily",
        columns=(Column("city", "STRING"), Column("orders_amount", "DECIMAL(18,2)")),
    )
    writer = Case(
        name="write_orders_daily",
        metrics=by_name(AMOUNT),
        grain=Grain.of(Dimension(COURIERS.city, alias="city")),
        writes_to=target,
    )

    with pytest.raises(InvalidDeclaration) as refused:
        Registry(name="one-way").add(ORDERS, COURIERS, AMOUNT, target, writer).freeze()

    assert refused.value.subject == "case:write_orders_daily"
    assert "written_by" in refused.value.remedy

    # The adjacent build: the same declarations with the backlink freeze, and the Grain the
    # refusal exists to protect is then known.
    linked = Source(
        db="mart",
        table="orders_daily",
        written_by="write_orders_daily",
        columns=(Column("city", "STRING"), Column("orders_amount", "DECIMAL(18,2)")),
    )
    fixed_writer = Case(
        name="write_orders_daily",
        metrics=by_name(AMOUNT),
        grain=Grain.of(Dimension(COURIERS.city, alias="city")),
        writes_to=linked,
    )
    registry = (
        Registry(name="two-way").add(ORDERS, COURIERS, AMOUNT, linked, fixed_writer).freeze()
    )
    assert str(registry.native_grain(linked)) == "(city)"
    assert registry.metric_behind(linked.orders_amount) is AMOUNT


def test_two_cases_writing_one_target_cannot_both_be_declared() -> None:
    """Only one Case can be named by a target's `written_by`, so the pair cannot agree.

    Two Cases writing one Partition overwrite each other on every run, and which numbers
    survive depends on the order of a statement list written somewhere else entirely.
    """
    target = Source(
        db="mart",
        table="orders_daily",
        written_by="writer_one",
        columns=(Column("city", "STRING"), Column("orders_amount", "DECIMAL(18,2)")),
    )
    grain = Grain.of(Dimension(COURIERS.city, alias="city"))
    one = Case(name="writer_one", metrics=by_name(AMOUNT), grain=grain, writes_to=target)
    two = Case(name="writer_two", metrics=by_name(AMOUNT), grain=grain, writes_to=target)

    with pytest.raises(InvalidDeclaration) as refused:
        Registry(name="two-writers").add(ORDERS, COURIERS, AMOUNT, target, one, two).freeze()

    assert refused.value.subject == "case:writer_two"


def test_a_case_writing_a_source_the_registry_never_got_refuses_at_freeze() -> None:
    """`writes_to` holds the Source OBJECT, so a Case can point at a target the Registry
    was never given: built inline in the Case, or bound to a private name that
    `from_modules`' module scan steps over. `freeze()` resolves that target back through
    `Registry.source` rather than trusting the object in hand, because everything
    downstream - the Drift check, `native_grain`, the column list a write is checked
    against - reads the Registry's Declaration and not this one.

    The lookup's refusal is what makes that a named refusal at import. Without it the
    resolution answers None and the very next line reads `None.written_by`, an
    AttributeError that names neither the Case nor the table it could not find.
    """
    unheld = Source(
        db="mart",
        table="orders_daily",
        written_by="write_orders_daily",
        columns=(Column("city", "STRING"), Column("orders_amount", "DECIMAL(18,2)")),
    )
    writer = Case(
        name="write_orders_daily",
        metrics=by_name(AMOUNT),
        grain=Grain.of(Dimension(COURIERS.city, alias="city")),
        writes_to=unheld,
    )

    # `writer` is added; `unheld`, the Source it writes, deliberately is not.
    with pytest.raises(UndeclaredSource) as refused:
        built().add(writer).freeze()

    assert refused.value.qualified == "mart.orders_daily"
    assert "mart.orders_daily" in str(refused.value)  # the name reaches the reader
    assert "raw.orders" in refused.value.known

    # The adjacent build: the same pair with the target declared freezes, and the lookup
    # then answers with the Registry's own Declaration of it.
    registry = built().add(unheld, writer).freeze()
    assert registry.source("mart.orders_daily") is unheld


def test_a_stale_via_naming_no_declared_edge_refuses_at_import() -> None:
    """A `via=` left behind after a Join was renamed must not survive to compile time: the
    module that declares the Case is the file that has to change."""
    stale = Case(
        name="stale_via",
        metrics=by_name(AMOUNT),
        grain=Grain.of(COURIERS.city),
        via=("order_courrier",),
    )

    with pytest.raises(UnknownJoin) as refused:
        built().add(stale).freeze()

    assert refused.value.case == "stale_via"
    assert refused.value.join == "order_courrier"
    assert "order_courier" in refused.value.known


def test_an_anchor_naming_no_declared_source_refuses_at_import() -> None:
    """Whether the anchor is a Source the Case's Metrics measure is `joins.spine`'s
    question; whether it is a declared Source at all is this one's, and answering it here
    turns a typo into an import-time refusal."""
    typo = Case(
        name="bad_anchor",
        metrics=by_name(AMOUNT),
        grain=Grain.of(COURIERS.city),
        anchor="raw.oders",
    )

    with pytest.raises(UndeclaredSource) as refused:
        built().add(typo).freeze()

    assert refused.value.qualified == "raw.oders"

    # The adjacent build: the spelling that exists freezes.
    spelled = Case(
        name="good_anchor",
        metrics=by_name(AMOUNT),
        grain=Grain.of(COURIERS.city),
        anchor="raw.orders",
    )
    assert built().add(spelled).freeze().case("good_anchor").anchor == "raw.orders"


def test_a_case_asking_for_a_tag_no_metric_carries_refuses_at_import() -> None:
    """Checked per Tag, never over the union - which is the whole reason Tag can be a plain
    `str`. A Case naming two Tags with one misspelled would otherwise resolve to a family
    missing half its Metrics and report fewer columns than its author intended, silently.
    """
    typo = Case(
        name="misspelled_family",
        metrics=by_tag("money", "volumne"),
        grain=Grain.of(COURIERS.city),
    )

    with pytest.raises(EmptyTagFamily) as refused:
        built().add(typo).freeze()

    assert refused.value.tag == "volumne"
    assert refused.value.case == "misspelled_family"
    assert "volume" in refused.value.known


# ======================================================================================
# Tag families
# ======================================================================================


def test_tagged_refuses_each_empty_tag_even_when_another_matched() -> None:
    """The same check reached directly, and the half a Case-level check cannot make: a
    selection resolved at compile time can name a Tag no Case ever mentioned."""
    registry = built().freeze()

    with pytest.raises(EmptyTagFamily) as refused:
        registry.tagged("money", "delivery_helth")

    assert refused.value.tag == "delivery_helth"

    # The adjacent build: the family that does exist still resolves, whole.
    assert [metric.name for metric in registry.tagged("money", "volume")] == [
        "orders_amount",
        "orders_seen",
    ]


def test_a_selection_carries_the_case_name_into_the_refusal() -> None:
    """`by_tag(...).resolve(registry, case=...)` is the compile-time door, and the refusal
    a contributor reads has to name the Case rather than only the Tag."""
    with pytest.raises(EmptyTagFamily) as refused:
        by_tag("money", "delivery_helth").resolve(built().freeze(), case="some_case")

    assert refused.value.case == "some_case"
    assert refused.value.subject == "some_case.metrics"


# ======================================================================================
# Lookups: the names that resolve to nothing
#
# Every lookup on the Registry refuses rather than returning None, and these are the two
# whose callers hold a STRING that came from somewhere else - a column node off a bare
# table name, and a `db.table.column` node read back out of a checked-in artifact. A None
# from either is dereferenced one line later, with the typo now several frames away.
#
# The four by-name lookups below are the same promise for the four declarable kinds. Each
# was mutation-survivable: every one of them could return None with the whole suite green,
# because the suite only ever asked them for names that exist.
# ======================================================================================


@pytest.mark.parametrize(
    ("look_up", "error", "attribute", "known_member"),
    [
        (lambda r: r.metric("orders_amonut"), UnknownMetric, "metric", "orders_amount"),
        (lambda r: r.filter("no_such_filter"), UnknownFilter, "filter", None),
        (lambda r: r.case("orders_by_cities"), UnknownCase, "case", "orders_by_city"),
        (lambda r: r.join("order_couriers"), UnknownJoin, "join", "order_courier"),
    ],
)
def test_a_by_name_lookup_that_resolves_to_nothing_refuses(
    look_up, error, attribute, known_member
) -> None:
    """One `except` per kind, and the known names printed beside the one that missed.

    These are the calls a tool makes - `tools/smoke.py`, a CI script, a REPL session -
    holding a name typed by a human or read out of a config file. Answering None sends that
    None into `case.grain` or `metric.source` one frame later, where the traceback names
    this library's internals rather than the misspelling that caused it.

    `known` is asserted because it is the whole remedy for the overwhelmingly common cause:
    a Metric that was renamed, or a Case whose name is plural in one file and singular in
    another.
    """
    registry = built().freeze()

    with pytest.raises(error) as refused:
        look_up(registry)

    assert getattr(refused.value, attribute) in str(refused.value)
    if known_member is not None:
        assert known_member in refused.value.known

    # The adjacent build: the names that do exist resolve to the declared objects.
    assert registry.metric("orders_amount") is AMOUNT
    assert registry.case("orders_by_city") is BY_CITY
    assert registry.join("order_courier").name == "order_courier"


def test_a_bare_table_name_no_source_carries_refuses() -> None:
    """`source_of_table` is the inverse of the library's alias-free column qualification.

    Every column node the library emits is `table.column` with no alias - that is what
    `add()`'s refusal of two Sources sharing a bare table name buys - so a bare name is
    what a reader of one of those nodes holds, and this is the call that turns it back into
    a Declaration. A name no Source carries is a node built against Declarations that have
    since moved, and answering None hands that reader a None to dereference instead.

    The refusal lists the BARE names it knows rather than qualified ones, because a bare
    name is what the caller asked with and `db.table` is not a spelling they could have
    meant here.
    """
    registry = built().freeze()

    with pytest.raises(UndeclaredSource) as refused:
        registry.source_of_table("order")

    assert refused.value.qualified == "order"
    assert "order" in str(refused.value)  # the name reaches the reader
    assert refused.value.known == ("couriers", "orders")

    # The adjacent build: the name that exists resolves to the Declaration itself.
    assert registry.source_of_table("orders") is ORDERS


@pytest.mark.parametrize(
    "node",
    [
        "orders_amount",  # an output name where a column node was expected
        "raw.orders.",  # the column half lost
        "raw..amount",  # the table half lost
        "orders.amount",  # the db half lost - see the docstring's last paragraph
        "",  # an empty string where a node was expected
    ],
)
def test_a_malformed_column_node_is_refused_naming_the_text_it_was_read_as(node) -> None:
    """`resolve_column` is the door a Manifest and the static Lineage artifact come back in
    through: on disk a node is only a string, and this is what re-resolves it against
    today's Declarations. So a node that is not `db.table.column` at all is a real thing to
    meet - a hand-edited artifact, one written by an older layout, or a truncated file.

    What the refusal has to name is the text AS IT WAS READ, verbatim. Split first and
    checked afterwards, a two-part node reaches the Source lookup as `db.table` with a
    piece invented or dropped, and the refusal then names a table nobody wrote and nobody
    can find in the file they have to fix.

    Which is why the assertion is on the exact string rather than only on the type. Drop
    this check and `orders_amount` is looked up as `orders_amount.`, `` as `.`, and
    `raw.orders.` reaches a Source that DOES exist and comes back as `UndeclaredColumn`
    about a column named `''` - three different lies about one malformed file.
    `orders.amount` is the one shape where the Source lookup would refuse identically,
    and it is here for the shape rather than as evidence.
    """
    registry = built().freeze()

    with pytest.raises(UndeclaredSource) as refused:
        registry.resolve_column(node)

    assert refused.value.qualified == node
    assert repr(node) in str(refused.value)  # verbatim, so it can be found in the artifact

    # The adjacent build: the well-formed node round-trips back to the declared column.
    assert registry.resolve_column("raw.orders.amount") == ORDERS.amount


# ======================================================================================
# Reports the Registry makes rather than refusals it raises
# ======================================================================================


def test_nullable_join_keys_reports_an_inner_key_still_declared_nullable() -> None:
    """The one hole in decision 3 the library knowingly leaves open, and its diagnosis.

    An inner Join keyed on a nullable column drops rows on BOTH sides, deflating every
    Metric that reaches across it - and the composer emits that SQL, because a generated
    Declaration reports almost everything nullable and refusing would block every first
    draft. This report is the mitigation, so it has to be right: it names the Join and the
    column, which is what a reviewer needs to go and check the warehouse.
    """
    registry = built().freeze()

    assert registry.nullable_join_keys() == (
        ("order_courier", ORDERS.courier_id),
    )


def test_tightening_the_annotation_empties_the_report_and_a_left_join_is_excluded() -> None:
    """Both directions out of the report, so it is not merely a list of every key.

    `nullable=False` is the hand annotation that resolves it. `kind="left"` is excluded
    because a left join keyed on a nullable column keeps its left rows: the NULLs simply do
    not match, which is what a left join is for.
    """
    tightened = Source(
        db="raw",
        table="orders_tight",
        columns=(
            Column("courier_id", "STRING", nullable=False),
            Column("amount", "DECIMAL(18,2)", nullable=False),
        ),
        joins=(
            Join(
                to="raw.couriers",
                keys=(("courier_id", "courier_id"),),
                cardinality=Cardinality.MANY_TO_ONE,
                name="tight_edge",
            ),
        ),
    )
    left_joined = Source(
        db="raw",
        table="orders_left",
        columns=(Column("courier_id", "STRING"), Column("amount", "DECIMAL(18,2)")),
        joins=(
            Join(
                to="raw.couriers",
                keys=(("courier_id", "courier_id"),),
                cardinality=Cardinality.MANY_TO_ONE,
                name="left_edge",
                kind="left",
            ),
        ),
    )

    registry = Registry(name="nullable").add(tightened, left_joined, COURIERS).freeze()
    assert registry.nullable_join_keys() == ()


def test_the_schema_covers_every_declared_source() -> None:
    """The qualify() gate is only a gate against the WHOLE declared schema.

    qualify()'s star expansion silently no-ops on an incomplete schema rather than raising,
    so a `schema()` narrowed to "the Sources this Case touches" would turn the resolution
    gate into a pretty-printer without saying so. This is the test that fails if anyone
    narrows it.
    """
    registry = built().freeze()
    schema = registry.schema_dict()

    for source in registry.sources():
        assert source.table in schema[source.db]
        assert set(schema[source.db][source.table]) == {
            column.name for column in source.columns
        }


def test_native_grain_is_none_for_an_atomic_source_and_a_grain_when_declared() -> None:
    """The permissive default, asserted so that it stays a decision rather than an accident.

    A Source with neither `grain` nor `written_by` is treated as atomic, which disables the
    re-grain check for it - the one permissive default in the design, and why declaring
    `grain` on a Source another pipeline has already coarsened matters.
    """
    external = Source(
        db="raw",
        table="orders_weekly_external",
        grain=("week", "city"),
        grain_buckets=(("week", TimeBucket.WEEK),),
        columns=(
            Column("week", "STRING"),
            Column("city", "STRING"),
            Column("amount", "DECIMAL(18,2)"),
        ),
    )
    registry = Registry(name="external").add(ORDERS, COURIERS, external).freeze()

    assert registry.native_grain(ORDERS) is None
    assert str(registry.native_grain(external)) == "(week, city)"
    assert registry.native_grain(external).time_bucket is TimeBucket.WEEK


def test_a_declared_grain_naming_a_column_the_source_does_not_have_refuses() -> None:
    """A Grain over a column that does not exist would be compared against every reading
    Case's Grain and answer False, which reads as `GrainNotComparable` about the wrong
    thing."""
    with pytest.raises(UndeclaredColumn) as refused:
        Source(
            db="raw",
            table="bad_grain",
            grain=("weak",),
            columns=(Column("week", "STRING"),),
        )

    assert refused.value.column == "weak"
    assert "week" in refused.value.did_you_mean


def test_a_source_cannot_declare_both_a_grain_and_a_writer() -> None:
    """A written Source takes its Grain from the Case that writes it, so a declared `grain`
    beside `written_by` is two answers to one question."""
    with pytest.raises(InvalidDeclaration) as refused:
        Source(
            db="mart",
            table="both",
            grain=("city",),
            written_by="orders_by_city",
            columns=(Column("city", "STRING"),),
        )

    assert refused.value.subject == "source:mart.both"


def test_count_distinct_is_declared_with_the_rule_that_cannot_roll_up() -> None:
    """A Registry-level sanity check on the constructors the fixtures above lean on: the
    Re-aggregation rule is never defaultable to a wrong one."""
    metric = count_distinct("distinct_couriers", ORDERS.courier_id)
    assert metric.reaggregation.is_provable is False
