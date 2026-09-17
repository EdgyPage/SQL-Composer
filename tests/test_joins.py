"""The Join path suite: one path resolves, none refuses, several refuse, fan-out refuses.

Three of these four outcomes are refusals, and a refusal test that only asserts
`pytest.raises` would pass just as well against a library that refused every Case. So each
one here is paired with the build that must still succeed over the SAME edges: the
ambiguous pair resolves once `via=` pins a path, the disconnected Case sits in a Registry
where a connected Case still resolves, and the Fan-out refusal is next to the same edge
walked the harmless way.

The candidates an `AmbiguousJoinPath` carries are asserted by USING them - each one is fed
back as `via=` and must resolve to exactly that path. That is the claim the message makes
("paste one of these into `via=`"), and pinning the prose instead would prove nothing
about whether the paste works.
"""
from __future__ import annotations

import ast as python_ast
import datetime

import pytest

from declarations import REGISTRY
from declarations import deliveries as fixture
from sqlcomposer import compile as compiler
from sqlcomposer import joins
from sqlcomposer import model as m
from sqlcomposer.declaration import Cardinality, Column, Registry, Source
from sqlcomposer.errors import (
    AmbiguousJoinPath,
    FanOut,
    InvalidDeclaration,
    JoinError,
    NoJoinPath,
    UndeclaredSource,
    UnknownJoin,
)

RUN_DATE = datetime.date(2026, 9, 17)

BY_SITE = m.Case(
    name="attempts_by_site",
    metrics=m.by_name(fixture.DELIVERY_ATTEMPTS),
    grain=m.Grain.of(fixture.BY_DAY, fixture.BY_DESTINATION_SITE),
)
"""Reaches `mart.sites`, which two declared edges connect to `mart.deliveries` - the origin
site and the destination site. Deliberately carries no `via=`; the variants below add one."""


# ======================================================================================
# A Registry with one Source nothing joins, for the NoJoinPath refusal.
#
# Built from the fixture module rather than from scratch so the adjacent happy path runs
# against the same graph: if `mart.weather` refuses and `mart.customers` resolves in one
# Registry, the refusal is about the missing edge and not about the Registry.
# ======================================================================================

WEATHER = Source(
    db="mart",
    table="weather",
    one_row_per="site-day",
    note="TEST FIXTURE. Declared with no joins at all: nothing keys it to a delivery.",
    columns=(
        Column("dt", "STRING", partition=True, nullable=False),
        Column("conditions", "STRING", note="rain | snow | clear"),
    ),
)

ISLAND = Registry.from_modules(fixture, name="test_joins.island").add(WEATHER).freeze()


# ======================================================================================
# Exactly one path
# ======================================================================================


def test_a_single_declared_join_path_resolves_with_no_via() -> None:
    """One chain of declared edges connects the Case's Sources, so it is used as it is.

    Asserts the orientation too: `carrier_deliveries` is DECLARED from the carrier side as
    ONE_TO_MANY, and walked from a deliveries spine it must come back inverted to
    MANY_TO_ONE. The declared text and the walked Cardinality disagreeing is the whole
    reason Fan-out is decidable, and a regression that returned the declared orientation
    here would make the lookup direction look like a fan-out.
    """
    spine, path = joins.resolve(REGISTRY, fixture.ACCOUNTABLE_BY_DAY)

    assert spine.qualified == "mart.deliveries"
    assert joins.describe(path) == ("carrier_deliveries",)
    assert len(path) == 1
    step = path[0]
    assert (step.frm.qualified, step.to.qualified) == ("mart.deliveries", "mart.carriers")
    assert step.cardinality is Cardinality.MANY_TO_ONE
    assert REGISTRY.join("carrier_deliveries").cardinality is Cardinality.ONE_TO_MANY

    only = joins.candidates(
        REGISTRY, fixture.ACCOUNTABLE_BY_DAY.sources(REGISTRY), anchor=spine
    )
    assert len(only) == 1, "a second candidate would make this Case ambiguous"

    sql = compiler.compile_case(REGISTRY, fixture.ACCOUNTABLE_BY_DAY, run_date=RUN_DATE).sql
    assert (
        "INNER JOIN `mart`.`carriers` AS `carriers` ON "
        "`deliveries`.`carrier_id` = `carriers`.`carrier_id`" in sql
    )


# ======================================================================================
# No path
# ======================================================================================


def test_a_source_no_declared_edge_reaches_is_refused() -> None:
    """A Dimension on an unjoinable Source refuses, naming what could not be reached.

    Without the refusal the alternatives are a cross join (every delivery against every
    weather row) or a silently dropped Dimension. Both return numbers.
    """
    marooned = m.Case(
        name="attempts_by_weather",
        metrics=m.by_name(fixture.DELIVERY_ATTEMPTS),
        grain=m.Grain.of(fixture.BY_DAY, m.Dimension(WEATHER.conditions)),
    )

    with pytest.raises(NoJoinPath) as refused:
        joins.resolve(ISLAND, marooned)

    error = refused.value
    assert error.case == "attempts_by_weather"
    assert error.anchor == "mart.deliveries"
    assert error.unreachable == ("mart.weather",)
    assert isinstance(error, JoinError)
    assert joins.candidates(
        ISLAND, frozenset({fixture.DELIVERIES, WEATHER}), anchor=fixture.DELIVERIES
    ) == ()


def test_metrics_on_two_sources_with_nothing_to_reach_refuse_at_the_spine() -> None:
    """Several Metric homes and no Join path at all refuses the missing edge, not the spine.

    A Case whose Metrics measure two Sources has no spine until something names one, so
    `spine` enumerates one candidate per (spine, path) pair and refuses the choice. When
    nothing connects the Sources at all there are no pairs to enumerate, and listing zero
    of them would be an `AmbiguousJoinPath` reading "0 declared spines and Join paths
    connect the Sources", whose remedy is to copy one of the candidates it did not print.
    The missing edge is what a contributor has to declare, so it is what the refusal names.

    Distinct from the single-home Case above, which never gets this far: with one Metric
    home `spine` returns before any path is asked for, and `resolve` refuses instead.
    """
    marooned = m.Case(
        name="fleet_and_attempts_by_weather",
        metrics=m.by_name(fixture.DELIVERY_ATTEMPTS, fixture.CARRIER_FLEET_SIZE),
        grain=m.Grain.of(fixture.BY_CARRIER, m.Dimension(WEATHER.conditions)),
    )

    with pytest.raises(NoJoinPath) as refused:
        compiler.compile_case(ISLAND, marooned)

    error = refused.value
    assert error.case == "fleet_and_attempts_by_weather"
    assert error.anchor == "mart.carriers"
    assert error.unreachable == ("mart.weather",)
    assert "mart.weather" in str(error)

    # The adjacent build: the same two Metric homes over the same edges, with the Source
    # nothing reaches dropped - so the refusal is about `mart.weather` and not about the
    # Metrics straddling two Sources.
    reachable = marooned.variant(
        "fleet_and_attempts_by_carrier",
        grain=m.Grain.of(fixture.BY_CARRIER),
        anchor="mart.carriers",
        via=("carrier_deliveries",),
    )
    spine, path = joins.resolve(ISLAND, reachable)
    assert spine.qualified == "mart.carriers"
    assert joins.describe(path) == ("carrier_deliveries",)


def test_a_source_the_registry_does_not_carry_is_undeclared_not_unreachable() -> None:
    """A Source missing from the Registry is a Declaration mistake, not a missing edge.

    Two different mistakes with two different fixes, and they are told apart by which
    Registry the same Case is compiled against. `mart.weather` is declared in this module;
    ISLAND holds it and REGISTRY does not, which is exactly the shape of forgetting to list
    a declarations module in `Registry.from_modules`. Against REGISTRY the composer cannot
    see the Source at all and says so, listing what it can see; against ISLAND it can see
    it and reports the Join nothing declares. Reporting the first as "nothing reaches it"
    would send a contributor to declare a Join keyed to a Source the composer never loaded.
    """
    unregistered = m.Case(
        name="attempts_by_unregistered_weather",
        metrics=m.by_name(fixture.DELIVERY_ATTEMPTS),
        grain=m.Grain.of(fixture.BY_DAY, m.Dimension(WEATHER.conditions)),
    )

    with pytest.raises(UndeclaredSource) as refused:
        compiler.compile_case(REGISTRY, unregistered)

    error = refused.value
    assert error.qualified == "mart.weather"
    assert "mart.weather" in str(error)
    assert "mart.deliveries" in error.known and "mart.weather" not in error.known
    assert "declarations/__init__.py" in error.remedy

    # The same Case against the Registry that DOES carry the Source: the other mistake.
    with pytest.raises(NoJoinPath) as unreached:
        compiler.compile_case(ISLAND, unregistered)
    assert unreached.value.unreachable == ("mart.weather",)


def test_a_connected_source_in_the_same_registry_still_resolves() -> None:
    """The adjacent build: same Registry, same spine, a Source that IS reachable.

    This is what makes the refusal above a statement about `mart.weather` rather than
    about `ISLAND`.
    """
    connected = m.Case(
        name="attempts_by_segment",
        metrics=m.by_name(fixture.DELIVERY_ATTEMPTS),
        grain=m.Grain.of(fixture.BY_DAY, fixture.BY_SEGMENT),
    )

    spine, path = joins.resolve(ISLAND, connected)

    assert spine.qualified == "mart.deliveries"
    assert joins.describe(path) == ("delivery_customer",)


# ======================================================================================
# More than one path
# ======================================================================================


def test_two_join_paths_to_one_source_refuse_and_name_both_candidates() -> None:
    """Origin site or destination site? Two paths, two different numbers, so refuse.

    The candidates are the load-bearing half of this refusal, and they are asserted
    exactly: a regression that refused without listing them, or listed one, leaves a
    contributor with no way forward.
    """
    with pytest.raises(AmbiguousJoinPath) as refused:
        joins.resolve(REGISTRY, BY_SITE)

    error = refused.value
    assert error.case == "attempts_by_site"
    assert error.anchor == "mart.deliveries"
    assert error.candidates == (
        ("delivery_destination_site",),
        ("delivery_origin_site",),
    )


def test_every_listed_candidate_resolves_when_pasted_into_via() -> None:
    """Each candidate the refusal prints must work as `via=`, unchanged.

    The adjacent build for the ambiguity refusal, and the only honest test of the claim
    the message makes. Both paths are exercised, because listing a candidate that does
    not resolve is the same failure as listing none.
    """
    with pytest.raises(AmbiguousJoinPath) as refused:
        joins.resolve(REGISTRY, BY_SITE)

    for candidate in refused.value.candidates:
        pinned = BY_SITE.variant(f"attempts_via_{candidate[0]}", via=candidate)
        spine, path = joins.resolve(REGISTRY, pinned)

        assert spine.qualified == "mart.deliveries"
        assert joins.describe(path) == candidate

    destination = BY_SITE.variant(
        "attempts_by_destination_site", via=("delivery_destination_site",)
    )
    sql = compiler.compile_case(REGISTRY, destination, run_date=RUN_DATE).sql
    assert "`deliveries`.`destination_site_id` = `sites`.`site_id`" in sql
    assert "origin_site_id" not in sql


def test_a_stale_via_refuses_rather_than_falling_back_to_inference() -> None:
    """`via=` naming edges that form no path for this Case refuses, never re-infers.

    A `via=` left behind after a Declaration changed is exactly how a Case silently starts
    answering a different question. `delivery_customer` is a real edge and a real path -
    just not one that reaches `mart.sites`, which this Case needs.
    """
    stale = BY_SITE.variant("attempts_by_site_stale", via=("delivery_customer",))

    with pytest.raises(NoJoinPath) as refused:
        joins.resolve(REGISTRY, stale)

    assert refused.value.unreachable == ("mart.sites",)

    # The adjacent build: correcting the pin, and nothing else, resolves.
    corrected = stale.variant(
        "attempts_by_site_corrected", via=("delivery_destination_site",)
    )
    assert joins.describe(joins.resolve(REGISTRY, corrected)[1]) == (
        "delivery_destination_site",
    )


def test_a_via_naming_an_edge_that_does_not_exist_names_the_case() -> None:
    """A misspelled edge is `UnknownJoin` carrying the Case, not a fallback to inference."""
    typo = BY_SITE.variant("attempts_by_site_typo", via=("delivery_destination_sight",))

    with pytest.raises(UnknownJoin) as refused:
        joins.resolve(REGISTRY, typo)

    error = refused.value
    assert error.case == "attempts_by_site_typo"
    assert error.join == "delivery_destination_sight"
    assert "delivery_destination_site" in error.known

    # The adjacent build: the name the refusal offers is the one that works.
    spelled = typo.variant("attempts_by_site_spelled", via=("delivery_destination_site",))
    assert joins.resolve(REGISTRY, spelled)[1][0].name == "delivery_destination_site"


def test_a_via_naming_one_edge_twice_refuses_rather_than_deduplicating() -> None:
    """A Join name pinned twice is refused as written, never quietly collapsed to one.

    `via=` is matched as a set, and a set would swallow the duplicate - which is the one
    place where matching as a set could silently accept a `via=` that says something the
    composer did not do. A contributor who types one name twice meant two different edges,
    and the second traversal would in any case re-enter a Source the first already reached.
    So the repeated name is named back to them rather than deduplicated.
    """
    twice = BY_SITE.variant(
        "attempts_by_site_twice",
        via=("delivery_destination_site", "delivery_destination_site"),
    )

    with pytest.raises(NoJoinPath) as refused:
        compiler.compile_case(REGISTRY, twice)

    error = refused.value
    assert error.case == "attempts_by_site_twice"
    assert error.unreachable == ("delivery_destination_site",), (
        "the repeated Join name is the edit the contributor has to make"
    )
    assert "delivery_destination_site" in str(error)

    # The adjacent build: the same pin written once resolves, over that same edge.
    once = twice.variant("attempts_by_site_once", via=("delivery_destination_site",))
    assert joins.describe(joins.resolve(REGISTRY, once)[1]) == (
        "delivery_destination_site",
    )


def test_a_via_pinning_both_parallel_edges_names_the_one_it_cannot_walk() -> None:
    """Pasting BOTH printed candidates into one `via=` refuses, naming the second edge.

    The ambiguity refusal prints two candidates to choose between, and taking them as a
    list rather than as alternatives is the mistake this catches. The second edge re-enters
    `mart.sites`, which the first already reached, so it can never be walked - and every
    needed Source IS reached, so the Sources are not what the contributor has to fix. The
    pinned Join name left over is, and it is what the refusal carries. The other way to
    leave a name unwalkable is a gap - a pinned edge touching neither end of the reachable
    stretch - which reports the Sources it failed to reach, because there the Sources are
    the answer.
    """
    both = BY_SITE.variant(
        "attempts_by_site_both_edges",
        via=("delivery_destination_site", "delivery_origin_site"),
    )

    with pytest.raises(NoJoinPath) as refused:
        compiler.compile_case(REGISTRY, both)

    error = refused.value
    assert error.case == "attempts_by_site_both_edges"
    assert error.anchor == "mart.deliveries"
    assert error.unreachable == ("delivery_origin_site",), (
        "every needed Source is reached here, so a refusal that reported unreached "
        "Sources would report nothing at all"
    )
    assert "delivery_origin_site" in str(error)

    # The adjacent build: dropping the edge the refusal names resolves over the other one.
    kept = both.variant(
        "attempts_by_site_destination_only", via=("delivery_destination_site",)
    )
    assert joins.describe(joins.resolve(REGISTRY, kept)[1]) == (
        "delivery_destination_site",
    )


def test_metrics_straddling_two_sources_refuse_to_guess_a_spine() -> None:
    """Even with ONE path available, which end carries the FROM is still a choice.

    The Metrics measure different Sources, so the spine decides which side of the join is
    preserved - and for a `kind="left"` edge the two spellings are different SQL. The
    refusal fires with a single candidate JOIN PATH, which is the part a reading of
    "ambiguous
    means several paths" would miss - and it lists that path once per possible spine,
    because the spine is the choice being refused.
    """
    straddling = m.Case(
        name="attempts_and_fleet",
        metrics=m.by_name(fixture.DELIVERY_ATTEMPTS, fixture.CARRIER_FLEET_SIZE),
        grain=m.Grain.of(fixture.BY_CARRIER),
    )

    with pytest.raises(AmbiguousJoinPath) as refused:
        joins.resolve(REGISTRY, straddling)

    error = refused.value
    assert error.candidates == (("carrier_deliveries",), ("carrier_deliveries",))
    assert error.anchors == ("mart.carriers", "mart.deliveries")
    assert "mart.carriers" in error.anchor and "mart.deliveries" in error.anchor

    # ...and stating the spine does resolve it, so the refusal is escapable - each listed
    # spine giving the statement that spine names.
    for anchor in error.anchors:
        pinned = straddling.variant(
            f"attempts_and_fleet_from_{anchor}", via=("carrier_deliveries",), anchor=anchor
        )
        spine, path = joins.resolve(REGISTRY, pinned)
        assert spine.qualified == anchor
        assert joins.describe(path) == ("carrier_deliveries",)


def test_the_spine_is_not_decided_by_the_order_of_via() -> None:
    """`via` is matched as a set, so nothing inside it may decide which end is the spine.

    Reordering the same pinned edges must not change the statement. It used to: the spine
    was read off `via[0]`, so the same Case with the same declared edges compiled to two
    different FROM clauses - and with a `kind="left"` edge anywhere on the path, to two
    different numbers - decided by an order `joins.resolve` documents as meaningless.
    """
    straddling = m.Case(
        name="attempts_and_fleet_unordered",
        metrics=m.by_name(fixture.DELIVERY_ATTEMPTS, fixture.CARRIER_FLEET_SIZE),
        grain=m.Grain.of(fixture.BY_CARRIER),
        via=("carrier_deliveries",),
        anchor="mart.carriers",
    )
    reversed_pins = straddling.variant(
        "attempts_and_fleet_reversed", via=("delivery_customer", "carrier_deliveries")
    )

    assert joins.resolve(REGISTRY, straddling)[0].qualified == "mart.carriers"
    # The extra pinned edge is refused as a detour rather than silently trimmed, and the
    # refusal is about the edge set - never about which of them happened to be listed first.
    with pytest.raises(NoJoinPath) as refused:
        joins.resolve(REGISTRY, reversed_pins)
    assert refused.value.unreachable == ("mart.customers",)


def test_an_anchor_that_carries_no_metric_refuses() -> None:
    """The spine is the Source every Metric is measured relative to, so a lookup table in
    the FROM clause is a different statement wearing the same Declarations."""
    straddling = m.Case(
        name="attempts_and_fleet_bad_anchor",
        metrics=m.by_name(fixture.DELIVERY_ATTEMPTS, fixture.CARRIER_FLEET_SIZE),
        grain=m.Grain.of(fixture.BY_CARRIER),
        via=("carrier_deliveries",),
        anchor="mart.sites",
    )

    with pytest.raises(InvalidDeclaration) as refused:
        joins.resolve(REGISTRY, straddling)

    assert "mart.sites" in str(refused.value)
    assert refused.value.subject == "case:attempts_and_fleet_bad_anchor"


# ======================================================================================
# Fan-out
# ======================================================================================


def test_fan_out_refuses_a_metric_measured_across_the_one_to_many_edge() -> None:
    """A carrier's fleet size reported by delivery day is counted once per delivery.

    `mart.carriers` declares ONE_TO_MANY into `mart.deliveries`, so the spine is the
    carrier and the join multiplies its rows. `SUM(fleet_size)` over those joined rows is
    a perfectly valid statement returning a number several times too large.
    """
    inflated = m.Case(
        name="fleet_size_by_delivery_day",
        metrics=m.by_name(fixture.CARRIER_FLEET_SIZE),
        grain=m.Grain.of(fixture.BY_DAY),
    )

    with pytest.raises(FanOut) as refused:
        compiler.plan(REGISTRY, inflated)

    error = refused.value
    assert error.metric == "carrier_fleet_size"
    assert error.measures == "mart.carriers"
    assert error.join == "carrier_deliveries"
    assert error.cardinality == Cardinality.ONE_TO_MANY.value
    assert error.path == ("carrier_deliveries",)


def test_the_same_metric_on_its_own_source_still_builds() -> None:
    """The adjacent build: `carrier_fleet_size` is sound wherever it is not multiplied.

    Reported across a Dimension of its own Source there is no join at all, and the same
    Metric that refused above compiles.
    """
    sound = m.Case(
        name="fleet_size_by_tier",
        metrics=m.by_name(fixture.CARRIER_FLEET_SIZE),
        grain=m.Grain.of(m.Dimension(fixture.CARRIERS.carrier_tier)),
    )
    built = compiler.compile_case(REGISTRY, sound)

    assert "SUM(`carriers`.`fleet_size`) AS `carrier_fleet_size`" in built.sql
    assert "JOIN" not in built.sql


def test_the_same_edge_walked_the_other_way_is_a_harmless_lookup() -> None:
    """The adjacent build for the edge itself: delivery Metrics by carrier are fine.

    `accountable_by_day` crosses `carrier_deliveries` in the MANY_TO_ONE direction, where
    the carrier is a lookup that labels delivery rows rather than multiplying them. If
    this failed, the refusal above would be a refusal of the edge rather than of the
    direction.
    """
    spine, path = joins.resolve(REGISTRY, fixture.ACCOUNTABLE_BY_DAY)

    assert joins.describe(path) == ("carrier_deliveries",)
    assert joins.check_fan_out(spine, path, [fixture.DELIVERY_ATTEMPTS]) is None
    assert not joins.fans_out_between(spine, fixture.CARRIERS, path)


def test_fan_out_asks_the_metrics_question_not_the_spines() -> None:
    """One resolved path, two Metrics, two opposite answers - and both are right.

    A MANY_TO_ONE lookup hop hands the spine one carrier per delivery (no fan-out for a
    delivery Metric) while handing each carrier many deliveries (fan-out for a Metric
    measured on the carrier). The same path answering the same way for both would mean one
    of the two questions had quietly been dropped.
    """
    spine, path = joins.resolve(REGISTRY, fixture.ACCOUNTABLE_BY_DAY)

    joins.check_fan_out(spine, path, [fixture.DELIVERY_ATTEMPTS, fixture.FEES_CHARGED])

    with pytest.raises(FanOut) as refused:
        joins.check_fan_out(spine, path, [fixture.CARRIER_FLEET_SIZE])

    error = refused.value
    assert error.measures == "mart.carriers"
    assert error.join == "carrier_deliveries"
    assert error.cardinality == Cardinality.MANY_TO_ONE.value, (
        "the Cardinality as this path WALKS the edge, not as it was declared"
    )


def test_the_printed_candidates_are_valid_python_for_via() -> None:
    """The refusal's remedy, tested through the TEXT a human copies rather than the tuple.

    The message says the candidates are "ready to paste", and a one-edge path used to print
    as `via=('delivery_destination_site')` - a str, not a tuple. Pasting it made `Case.via`
    a string, `joins` iterated it character by character, and the build died with
    `UnknownJoin: pins join 'd'`. Every ambiguity the shipped fixture can produce is
    single-edge, so the only worked example of this workflow was the broken one.

    Round-tripping the typed `error.candidates` attribute cannot catch that, because the
    attribute was always right. This parses the printed string.
    """
    with pytest.raises(AmbiguousJoinPath) as refused:
        joins.resolve(REGISTRY, BY_SITE)

    printed = refused.value.context["candidates"]
    assert printed == (
        "via=('delivery_destination_site',); via=('delivery_origin_site',)"
    )

    for entry in printed.split("; "):
        pasted = python_ast.literal_eval(entry[len("via=") :])
        assert isinstance(pasted, tuple)

        pinned = BY_SITE.variant(f"attempts_pasted_{pasted[0]}", via=pasted)
        spine, path = joins.resolve(REGISTRY, pinned)
        assert joins.describe(path) == pasted
        assert spine.qualified == "mart.deliveries"


def test_a_pasted_candidate_with_its_comma_dropped_refuses_about_the_case() -> None:
    """The mistake the trailing comma prevents, and the refusal a contributor gets if they
    make it anyway: one that names the Case and the field, not a join called 'd'."""
    with pytest.raises(InvalidDeclaration) as refused:
        m.Case(
            name="attempts_pasted_badly",
            metrics=m.by_name(fixture.DELIVERY_ATTEMPTS),
            grain=m.Grain.of(fixture.BY_DAY, fixture.BY_DESTINATION_SITE),
            via="delivery_destination_site",  # type: ignore[arg-type]
        )

    assert refused.value.subject == "case:attempts_pasted_badly"
