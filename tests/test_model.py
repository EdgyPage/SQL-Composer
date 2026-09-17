"""The invariants the model types check on themselves, none of which had a test.

Every refusal here fires in a `__post_init__`, which means at IMPORT time for anything
declared at module level - the moment a contributor's own file is the thing on screen. That
is the whole argument for putting them there rather than in the compiler, and it is why an
untested one is worse than it looks: a `__post_init__` that has stopped refusing does not
fail, it accepts.

Each of the following was verified mutation-survivable before this module existed - the
guard could be made unreachable and the whole suite stayed green:

* `Metric.__post_init__`'s six shape refusals, including the one-Source invariant that stops
  a Metric measuring one table while being scoped by a Filter on another;
* `Grain`'s duplicate-output-name refusal, and `Grain.time_bucket`'s two-bucket refusal;
* `Dimension.coarsens_to`'s bucket-mismatch branch - the one that makes dropping a bucket
  `GrainNotComparable` rather than a column of NULLs;
* `MetricSelection`'s exclusion refusals;
* `CasePlan.__post_init__`'s structural re-verification, which is the documented net under a
  hand-assembled plan.
"""
from __future__ import annotations

import dataclasses
import datetime

import pytest

from declarations import REGISTRY
from declarations import deliveries as fixture
from sqlcomposer import compile as compiler
from sqlcomposer import grain as grain_module
from sqlcomposer.declaration import TimeBucket
from sqlcomposer.errors import (
    EmptyTagFamily,
    GrainNotComparable,
    InvalidDeclaration,
    PlanInvariantViolated,
    UnknownMetric,
)
from sqlcomposer.model import (
    Aggregate,
    Case,
    CasePlan,
    Dimension,
    Grain,
    Metric,
    MetricPlan,
    ReAggregation,
    by_name,
    by_tag,
    count_distinct,
    count_rows,
    ratio,
    sum_of,
)

RUN_DATE = datetime.date(2026, 9, 17)


# ======================================================================================
# Metric: a shape that cannot be compiled honestly is refused where it is written
# ======================================================================================


def test_a_metric_scoped_by_a_filter_on_another_source_refuses() -> None:
    """The one-Source invariant, and the wrong number it prevents.

    `count_rows("x", DELIVERIES, when=LIVE_CARRIERS)` reads plausibly and renders as
    `SUM(CASE WHEN carriers.is_test = 0 THEN 1 ELSE 0 END)`. What that number means then
    depends on whether the Case happens to join `mart.carriers` at all, and if it does, on
    whether that join fanned out - so one Metric has two values depending on a decision
    taken in a different file. A Metric is declared against the ONE Source it measures.
    """
    with pytest.raises(InvalidDeclaration) as refused:
        count_rows("attempts_on_live_carriers", fixture.DELIVERIES, when=fixture.LIVE_CARRIERS)

    assert refused.value.subject == "metric:attempts_on_live_carriers"
    assert "mart.carriers" in refused.value.problem
    assert "mart.deliveries" in refused.value.problem

    # The adjacent build: the same scoping as a CASE-level Filter is exactly where a
    # predicate on another Source belongs, and it compiles.
    scoped_case = Case(
        name="attempts_live_only",
        metrics=by_name(fixture.DELIVERY_ATTEMPTS),
        grain=Grain.of(fixture.BY_CARRIER),
        filters=(fixture.LIVE_CARRIERS,),
    )
    assert "`carriers`.`is_test` = 0" in compiler.compile_case(REGISTRY, scoped_case).sql


def test_a_metric_scoped_by_a_filter_on_its_own_source_is_ordinary() -> None:
    """The adjacent build for the invariant above, so it is not a refusal of everything."""
    metric = count_rows("failed_attempts", fixture.DELIVERIES, when=fixture.FAILURE_TO_DELIVER)

    assert metric.source.qualified == "mart.deliveries"
    assert compiler.compile_metric_only(REGISTRY, metric) == (
        "SUM(CASE WHEN NOT deliveries.failure_reason IS NULL THEN 1 ELSE 0 END)"
    )


def test_a_ratio_needs_exactly_two_components() -> None:
    with pytest.raises(InvalidDeclaration) as refused:
        Metric(name="lopsided", aggregate=Aggregate.RATIO, parts=None)

    assert "two component Metrics" in refused.value.problem


def test_a_ratio_carrying_a_column_refuses() -> None:
    """A ratio measures its components. A column beside them is a second answer to the
    question of what it reads, and the renderer would ignore it."""
    with pytest.raises(InvalidDeclaration) as refused:
        Metric(
            name="rate_with_column",
            aggregate=Aggregate.RATIO,
            parts=(fixture.FAILED_DELIVERIES, fixture.DELIVERY_ATTEMPTS),
            column=fixture.DELIVERIES.fee_amount,
        )

    assert "not a column" in refused.value.problem


def test_a_ratio_carrying_a_scoped_filter_refuses() -> None:
    """A `when` on a ratio was ACCEPTED and then silently discarded from the SQL.

    `grain.aggregate_expression`'s RATIO branch renders the two components and divides them;
    there is no expression of the ratio itself for a condition to wrap. So the Filter
    vanished from the statement while `Metric.columns` still reported its columns - and the
    builder-derived Lineage, which decision 6 makes authoritative and decision 7 makes a
    git-tracked artifact, claimed an edge the statement did not have. Review could not catch
    it either, because review reads that artifact.
    """
    with pytest.raises(InvalidDeclaration) as refused:
        dataclasses.replace(
            fixture.FAILURE_RATE, name="late_failure_rate", when=fixture.DELIVERED_LATE
        )

    assert refused.value.subject == "metric:late_failure_rate"
    assert "delivered_late" in refused.value.problem

    # The adjacent build: scoping the NUMERATOR is the thing that was meant, and it does
    # appear in the SQL.
    late_failures = count_rows(
        "late_failures", fixture.DELIVERIES, when=fixture.DELIVERED_LATE
    )
    rate = ratio("late_failure_rate", late_failures, fixture.DELIVERY_ATTEMPTS)
    assert "late_flag" in compiler.compile_metric_only(REGISTRY, rate)


def test_a_non_ratio_carrying_components_refuses() -> None:
    with pytest.raises(InvalidDeclaration) as refused:
        Metric(
            name="sum_with_parts",
            aggregate=Aggregate.SUM,
            column=fixture.DELIVERIES.fee_amount,
            parts=(fixture.FAILED_DELIVERIES, fixture.DELIVERY_ATTEMPTS),
        )

    assert "component Metrics" in refused.value.problem


def test_a_ratio_whose_components_measure_different_sources_refuses() -> None:
    """One side of such a quantity is always inflated by the Join that brings the other in."""
    with pytest.raises(InvalidDeclaration) as refused:
        ratio("cross_source", fixture.DELIVERY_ATTEMPTS, fixture.CARRIER_FLEET_SIZE)

    assert "mart.carriers" in refused.value.problem
    assert "pre-aggregate" in refused.value.remedy


def test_a_ratio_over_a_component_that_cannot_roll_up_refuses() -> None:
    """A COUNT(DISTINCT) denominator makes the ratio unusable above its native Grain, and
    `REDERIVE` would claim otherwise at every Grain."""
    with pytest.raises(InvalidDeclaration) as refused:
        ratio("per_courier", fixture.DELIVERY_ATTEMPTS, fixture.ACTIVE_COURIERS)

    assert "active_couriers" in refused.value.problem
    assert refused.value.subject == "metric:per_courier"


def test_a_metric_with_no_name_refuses() -> None:
    """The name is the output column, the Lineage node id and the key `by_name` selects on,
    so an unnamed Metric is one nothing downstream can refer to - and an INSERT whose column
    is called `''`."""
    with pytest.raises(InvalidDeclaration) as refused:
        Metric(name="", aggregate=Aggregate.SUM, column=fixture.DELIVERIES.fee_amount)

    assert refused.value.subject == "metric:"
    assert sum_of("f", fixture.DELIVERIES.fee_amount).name == "f"  # the adjacent build


def test_an_aggregate_that_needs_a_column_refuses_without_one() -> None:
    with pytest.raises(InvalidDeclaration) as refused:
        Metric(name="sum_of_nothing", aggregate=Aggregate.SUM, of_source=fixture.DELIVERIES)

    assert "needs a column" in refused.value.problem


def test_a_count_of_rows_must_say_whose_rows() -> None:
    with pytest.raises(InvalidDeclaration) as refused:
        Metric(name="count_of_what", aggregate=Aggregate.COUNT)

    assert "which Source" in refused.value.problem


def test_the_re_aggregation_rule_is_never_defaultable_to_a_wrong_one() -> None:
    """COUNT rolls up by SUM, not by COUNT, and that is the non-obvious one."""
    assert count_rows("n", fixture.DELIVERIES).reaggregation is ReAggregation.SUM
    assert sum_of("f", fixture.DELIVERIES.fee_amount).reaggregation is ReAggregation.SUM
    assert (
        count_distinct("c", fixture.DELIVERIES.courier_id).reaggregation is ReAggregation.NONE
    )
    assert fixture.FAILURE_RATE.reaggregation is ReAggregation.REDERIVE


# ======================================================================================
# Grain and Dimension
# ======================================================================================


def test_two_dimensions_publishing_one_name_refuse() -> None:
    """An output name is simultaneously a Lineage node id, a SELECT column and - because
    Hive matches INSERT columns by position - the position of every column after it. Two
    Dimensions collapsing to one name shifts every subsequent column of a write by one."""
    with pytest.raises(InvalidDeclaration) as refused:
        Grain.of(
            Dimension(fixture.DELIVERIES.dt, TimeBucket.DAY),
            Dimension(fixture.DELIVERIES.dt, TimeBucket.DAY),
        )

    assert "dt_day" in refused.value.problem

    # The adjacent build: an explicit alias resolves it, and both columns survive.
    resolved = Grain.of(
        Dimension(fixture.DELIVERIES.dt, TimeBucket.DAY),
        Dimension(fixture.DELIVERIES.dt, TimeBucket.WEEK, alias="dt_week_start"),
    )
    assert resolved.names == ("dt_day", "dt_week_start")


def test_an_alias_colliding_with_another_dimensions_default_name_refuses() -> None:
    """The collision a reader is least likely to see: an explicit alias that happens to be
    the name another Dimension publishes by default."""
    with pytest.raises(InvalidDeclaration):
        Grain.of(
            Dimension(fixture.DELIVERIES.dt, TimeBucket.DAY),
            Dimension(fixture.CARRIERS.carrier_name, alias="dt_day"),
        )


def test_a_grain_with_two_bucketed_dimensions_has_no_single_time_bucket() -> None:
    """Guessing one is how a re-grain check quietly starts permitting things: every
    coarsening comparison would then be answered against half the Grain."""
    two_buckets = Grain.of(
        Dimension(fixture.DELIVERIES.dt, TimeBucket.DAY),
        Dimension(fixture.DELIVERIES.promised_at, TimeBucket.WEEK),
    )

    with pytest.raises(InvalidDeclaration) as refused:
        two_buckets.time_bucket

    assert "more than one Dimension is time-bucketed" in refused.value.problem

    # The adjacent build: one bucketed Dimension answers, and none answers None.
    assert Grain.of(fixture.BY_DAY, fixture.BY_CARRIER).time_bucket is TimeBucket.DAY
    assert Grain.of(fixture.BY_CARRIER).time_bucket is None


def test_a_bucketed_and_an_unbucketed_dimension_do_not_coarsen_each_other() -> None:
    """The branch that makes a dropped bucket loud.

    `DATE_FORMAT(dt, 'yyyy-MM-dd')` and a bare `dt` are not the same column of output, and
    a stored DAY-bucketed column read back unbucketed is not the identity read it looks
    like. Answering True in either direction here is how that becomes a silent re-grain.
    """
    bucketed = Dimension(fixture.DELIVERY_HEALTH_DAILY.dt_day, TimeBucket.DAY)
    bare = Dimension(fixture.DELIVERY_HEALTH_DAILY.dt_day)

    assert bucketed.coarsens_to(bare) is False
    assert bare.coarsens_to(bucketed) is False

    # ...while the bucket order itself is one-directional, and a different column never
    # coarsens at all.
    day = Dimension(fixture.DELIVERIES.dt, TimeBucket.DAY)
    week = Dimension(fixture.DELIVERIES.dt, TimeBucket.WEEK)
    assert day.coarsens_to(week) is True
    assert week.coarsens_to(day) is False
    assert day.coarsens_to(Dimension(fixture.DELIVERIES.promised_at, TimeBucket.DAY)) is False
    assert bare.coarsens_to(Dimension(fixture.DELIVERY_HEALTH_DAILY.dt_day)) is True


def test_dropping_the_bucket_on_a_written_source_is_grain_not_comparable() -> None:
    """The same branch reached through the refusal it exists to raise.

    `mart.delivery_health_daily` is written at `(dt_day@DAY, carrier)`. Reading it at
    `(dt_day, carrier)` with no bucket is neither a re-aggregation nor a request for detail
    gone - the two Grains do not nest in either direction - so it is `GrainNotComparable`,
    which is the loud version of a mistake whose quiet version is a column of NULLs.
    """
    unbucketed = Grain.of(
        fixture.DELIVERY_HEALTH_DAILY.dt_day, fixture.WRITTEN_BY_CARRIER
    )

    with pytest.raises(GrainNotComparable) as refused:
        grain_module.plan_metric(
            REGISTRY,
            fixture.WEEKLY_DELIVERY_ATTEMPTS,
            unbucketed,
            spine=fixture.DELIVERY_HEALTH_DAILY,
            path=(),
        )

    assert refused.value.metric == "weekly_delivery_attempts"
    assert "dt_day" in refused.value.native

    # The adjacent build: carrying the same bucket the writing Case did is the identity
    # read, and planning it succeeds.
    stored = Grain.of(
        Dimension(fixture.DELIVERY_HEALTH_DAILY.dt_day, TimeBucket.DAY),
        fixture.WRITTEN_BY_CARRIER,
    )
    planned = grain_module.plan_metric(
        REGISTRY,
        fixture.WEEKLY_DELIVERY_ATTEMPTS,
        stored,
        spine=fixture.DELIVERY_HEALTH_DAILY,
        path=(),
    )
    assert planned.rule is ReAggregation.SUM


# ======================================================================================
# MetricSelection
# ======================================================================================


def test_an_exclusion_that_matches_nothing_refuses() -> None:
    """A stale exclusion has quietly stopped excluding, which is a family that grew back.

    The realistic arrival is a rename: the Metric is still in the family under its new name
    and the `without(...)` beside it now names nothing, so the Case reports a column its
    author believed was removed.
    """
    selection = by_tag(fixture.ACCOUNTABLE).without("active_courier", because="typo")

    with pytest.raises(UnknownMetric) as refused:
        selection.resolve(REGISTRY)

    assert refused.value.metric == "active_courier"
    assert "active_couriers" in refused.value.known

    # The adjacent build: the correct spelling does exclude, and nothing else moves.
    corrected = by_tag(fixture.ACCOUNTABLE).without("active_couriers", because="typo fixed")
    names = [metric.name for metric in corrected.resolve(REGISTRY)]
    assert "active_couriers" not in names
    assert "delivery_attempts" in names


def test_an_exclusion_with_no_reason_refuses() -> None:
    """An unexplained exclusion is indistinguishable from a mistake in six months, and the
    diff is the only place the reason can live."""
    with pytest.raises(InvalidDeclaration) as refused:
        by_tag(fixture.ACCOUNTABLE).without("active_couriers", because="")

    assert refused.value.subject == "metric selection"


def test_a_selection_that_excludes_everything_refuses_rather_than_reporting_nothing() -> None:
    """A Case with no numbers is not a narrower Case; it is a Case that does not work."""
    everything = [metric.name for metric in REGISTRY.tagged(fixture.WEEKLY_REAGGREGATED)]
    emptied = by_tag(fixture.WEEKLY_REAGGREGATED).without(*everything, because="all of them")

    with pytest.raises(EmptyTagFamily):
        emptied.resolve(REGISTRY, case="emptied")


# ======================================================================================
# Case
# ======================================================================================


def test_a_case_with_no_name_refuses() -> None:
    """The Case name keys its Lineage artifact, its Manifest and the `written_by` backlink a
    written Source points at, so an unnamed Case is one none of those can name."""
    with pytest.raises(InvalidDeclaration) as refused:
        Case(
            name="",
            metrics=by_name(fixture.DELIVERY_ATTEMPTS),
            grain=Grain.of(fixture.BY_DAY),
        )

    assert refused.value.subject == "case:<unnamed>"


def test_a_grain_that_is_not_a_grain_refuses() -> None:
    """`grain=` takes a Grain, or a tuple of Dimensions it makes one from. Anything else -
    a string naming a column, the shape every other tool in this space accepts - is refused
    where it is written.

    A Grain is what the re-grain proof is run against; a str would answer `.dimensions` with
    an AttributeError several frames into planning, naming `grain.py` rather than the line
    the contributor wrote.
    """
    with pytest.raises(InvalidDeclaration) as refused:
        Case(
            name="grain_as_text",
            metrics=by_name(fixture.DELIVERY_ATTEMPTS),
            grain="dt",  # type: ignore[arg-type]
        )

    assert refused.value.subject == "case:grain_as_text"

    # The adjacent build: a tuple of Dimensions IS accepted, and becomes a Grain.
    from_tuple = Case(
        name="grain_as_tuple",
        metrics=by_name(fixture.DELIVERY_ATTEMPTS),
        grain=(fixture.BY_DAY,),  # type: ignore[arg-type]
    )
    assert isinstance(from_tuple.grain, Grain)


def test_metrics_given_as_a_plain_list_refuse() -> None:
    """`metrics=` takes a MetricSelection, which is the type that defers resolution until
    compile time - and deferring it is what makes a newly declared Metric join every Case
    asking for its Tag family with no Case edited.

    A list of Metric objects is the shape that silently opts out of that: it would resolve
    once, at import, and the horizontal-scaling claim would quietly stop being true for
    every Case written that way.
    """
    with pytest.raises(InvalidDeclaration) as refused:
        Case(
            name="metrics_as_list",
            metrics=[fixture.DELIVERY_ATTEMPTS],  # type: ignore[arg-type]
            grain=Grain.of(fixture.BY_DAY),
        )

    assert refused.value.subject == "case:metrics_as_list"
    assert "by_tag" in refused.value.remedy


def test_a_via_written_without_its_trailing_comma_refuses() -> None:
    """`via=('one_edge')` is a str, and every character of it would be read as a Join name.

    This is the form a contributor produces by pasting a one-edge candidate out of an
    `AmbiguousJoinPath`, which is why the refusal prints `via=('x',)` - and why a bare str
    is refused here, where the Case is still the subject, rather than three frames later as
    `UnknownJoin: pins join 'd'`.
    """
    with pytest.raises(InvalidDeclaration) as refused:
        Case(
            name="pasted_wrong",
            metrics=by_name(fixture.DELIVERY_ATTEMPTS),
            grain=Grain.of(fixture.BY_DAY),
            via="delivery_destination_site",  # type: ignore[arg-type]
        )

    assert refused.value.subject == "case:pasted_wrong"
    assert "trailing comma" in refused.value.remedy


def test_variant_inherits_the_join_answers_and_never_the_write_target() -> None:
    """`via` and `anchor` are answers about the declared Join graph, which a re-grain does
    not change. `writes_to` is not inherited, because two Cases writing one Partition
    overwrite each other every run - and `freeze()` now refuses that outright."""
    parent = fixture.FAILURES_BY_SITE_AND_SEGMENT
    child = parent.variant("failures_by_site_and_segment_weekly", grain=Grain.of(fixture.BY_WEEK))

    assert child.via == parent.via
    assert child.anchor == parent.anchor
    assert child.writes_to is None
    assert fixture.ACCOUNTABLE_BY_DAY.writes_to is not None, (
        "the parent must write, or this asserts nothing"
    )
    assert fixture.ACCOUNTABLE_BY_WEEK.writes_to is None


# ======================================================================================
# CasePlan: the net under a hand-assembled plan
# ======================================================================================


def _plan() -> CasePlan:
    """A real plan for a real Case, which each test below breaks one field of."""
    return compiler.plan(REGISTRY, fixture.ACCOUNTABLE_BY_DAY, run_date=RUN_DATE)


def test_a_plan_built_through_the_supported_entry_point_constructs_cleanly() -> None:
    """The adjacent build for everything below: `compile.plan` produces a valid plan."""
    plan = _plan()

    assert plan.spine.qualified == "mart.deliveries"
    assert plan.join_names == ("carrier_deliveries",)
    assert plan.sources == (fixture.DELIVERIES, fixture.CARRIERS)


def test_a_path_whose_first_step_does_not_leave_the_spine_refuses() -> None:
    """The path is the proof joins.py searched for, and a plan renders what its path says.

    A step leaving a Source the path has not reached becomes a JOIN clause against a table
    that is not in the statement - which sqlglot's gate would catch - or, worse, one that is
    in it for another reason, which nothing would.
    """
    plan = _plan()

    with pytest.raises(PlanInvariantViolated) as refused:
        dataclasses.replace(plan, spine=fixture.SITES)

    assert refused.value.invariant == "path chains from the spine"
    assert refused.value.case == "accountable_by_day"


def test_a_path_that_re_enters_a_source_refuses() -> None:
    """A repeated Source needs a self-join alias, which this library does not emit - so the
    second JOIN would silently be the same table under the same name, and every predicate
    on it would apply to both."""
    plan = _plan()
    there = plan.path[0]
    back = there.inverted()

    with pytest.raises(PlanInvariantViolated) as refused:
        dataclasses.replace(plan, path=(there, back))

    assert refused.value.invariant == "path visits each Source once"


def test_a_metric_plan_proved_at_another_grain_refuses() -> None:
    """The re-grain proof and the emitted GROUP BY would otherwise describe different
    numbers - which is the exact reason `compile.render` takes a plan rather than a Case."""
    plan = _plan()
    elsewhere = Grain.of(fixture.BY_WEEK, fixture.BY_CARRIER)
    mis_targeted = dataclasses.replace(plan.metrics[0], target=elsewhere)

    with pytest.raises(PlanInvariantViolated) as refused:
        dataclasses.replace(plan, metrics=(mis_targeted,) + plan.metrics[1:])

    assert refused.value.invariant == "every MetricPlan targets the Case's Grain"


def test_a_plan_claiming_none_at_a_coarser_grain_refuses() -> None:
    """`MetricPlan`'s own invariant: a rule of NONE is only representable at the Grain the
    numbers are stored at, because there is no expression that rolls them up."""
    stored = Grain.of(
        Dimension(fixture.DELIVERY_HEALTH_DAILY.dt_day, TimeBucket.DAY),
        fixture.WRITTEN_BY_CARRIER,
    )
    coarser = Grain.of(fixture.WRITTEN_BY_WEEK, fixture.WRITTEN_BY_CARRIER)

    with pytest.raises(InvalidDeclaration) as refused:
        MetricPlan(
            metric=fixture.STORED_ACTIVE_COURIERS,
            target=coarser,
            rule=ReAggregation.NONE,
            native=stored,
        )

    assert "UnsafeReAggregation" in refused.value.remedy

    # The adjacent build: the same plan at its own stored Grain is exactly the identity
    # read, and constructs.
    assert (
        MetricPlan(
            metric=fixture.STORED_ACTIVE_COURIERS,
            target=stored,
            rule=ReAggregation.NONE,
            native=stored,
        ).rule
        is ReAggregation.NONE
    )


def test_a_rederive_plan_without_its_component_plans_refuses() -> None:
    """A REDERIVE plan and its two component plans are one fact in two halves.

    `grain.render_metric` reads the parts to rebuild `numerator / denominator`; a REDERIVE
    plan carrying none has nothing to divide, and one carrying parts under any other rule
    claims a re-derivation the renderer will not perform. Either half alone is a plan that
    renders a different Metric than it proves.
    """
    target = Grain.of(fixture.BY_DAY, fixture.BY_CARRIER)

    with pytest.raises(InvalidDeclaration) as refused:
        MetricPlan(metric=fixture.FAILURE_RATE, target=target, rule=ReAggregation.REDERIVE)

    assert refused.value.subject == "metricplan:failure_rate"
    assert "`parts`" in refused.value.remedy

    parts = (
        MetricPlan(metric=fixture.FAILED_DELIVERIES, target=target, rule=ReAggregation.SUM),
        MetricPlan(metric=fixture.DELIVERY_ATTEMPTS, target=target, rule=ReAggregation.SUM),
    )

    # The other half: component plans under a rule that does not re-derive.
    with pytest.raises(InvalidDeclaration):
        MetricPlan(
            metric=fixture.FAILURE_RATE,
            target=target,
            rule=ReAggregation.SUM,
            parts=parts,
        )

    # The adjacent build: the two halves together construct.
    assert (
        MetricPlan(
            metric=fixture.FAILURE_RATE,
            target=target,
            rule=ReAggregation.REDERIVE,
            parts=parts,
        ).parts
        == parts
    )
