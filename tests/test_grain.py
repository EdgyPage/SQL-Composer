"""The Re-aggregation suite: what re-grains, what refuses, and what the SQL says.

Every failure this file guards produces valid Hive that returns a plausible number, which
is why each test asserts on the emitted SQL or on a typed refusal attribute rather than on
"it did not raise". A `pytest.raises` on its own would pass just as happily against a
library that refused everything, so every refusal here is paired with the adjacent build
that must still succeed: the same Metric at its own stored Grain, the same shape against
atomic rows, or the same Source with a rule that does compose.

Assertions are on typed attributes (`err.metric`, `err.rule`, `err.stored_by`) and on SQL
fragments, never on refusal prose - `errors.py` owns the wording and a test that pins it
turns a copy edit into a red build.
"""
from __future__ import annotations

import datetime

import pytest
from sqlglot import exp

from declarations import REGISTRY
from declarations import deliveries as fixture
from sqlcomposer import compile as compiler
from sqlcomposer import grain
from sqlcomposer import model as m
from sqlcomposer.declaration import (
    Cardinality,
    Column,
    Join,
    Registry,
    Source,
    TimeBucket,
)
from sqlcomposer.errors import (
    GrainNotComparable,
    GrainTooFine,
    InvalidDeclaration,
    ReAggregationError,
    UnsafeReAggregation,
)

RUN_DATE = datetime.date(2026, 9, 17)
"""Fixed, never `date.today()`: a deferred Filter bound to a moving date would make the
golden fragments below move with the calendar."""

DAILY = fixture.DELIVERY_HEALTH_DAILY
"""The written Source. Its native Grain is `accountable_by_day`'s Grain, re-pointed at its
own columns - `(dt_day, carrier)` - which is what makes a re-grain out of it possible at
all."""

STORED_DAY = m.Grain.of(
    m.Dimension(DAILY.dt_day, TimeBucket.DAY, alias="dt_day"),
    fixture.WRITTEN_BY_CARRIER,
)
"""The daily Source's own Grain, spelled by a reading Case. Mutually coarsening with
`Registry.native_grain(DAILY)`, so `check_regrain` treats it as identity."""

STORED_WEEK = m.Grain.of(fixture.WRITTEN_BY_WEEK, fixture.WRITTEN_BY_CARRIER)
"""One bucket coarser than the Source was written at: the re-grain under test."""

WEEK_EXPRESSION = (
    "DATE_SUB(NEXT_DAY(DATE_FORMAT(`delivery_health_daily`.`dt_day`, "
    "'yyyy-MM-dd'), 'MO'), 7)"
)
DAY_EXPRESSION = "DATE_FORMAT(`delivery_health_daily`.`dt_day`, 'yyyy-MM-dd')"


def compiled(name: str, metric: m.Metric, target: m.Grain) -> compiler.Compiled:
    """One Metric at one Grain, through the whole read path.

    Through `compile_case` rather than `grain.plan_metric` directly, because the claim
    under test is about the SQL that reaches the warehouse, and the re-aggregation, the gate
    and the generation all sit between a MetricPlan and that text.
    """
    case = m.Case(name=name, metrics=m.by_name(metric), grain=target)
    return compiler.compile_case(REGISTRY, case, run_date=RUN_DATE)


# ======================================================================================
# A weekly Source another pipeline has already coarsened, for the two comparability
# refusals.
#
# Declared here rather than in declarations/deliveries.py because it exists only to be
# asked for at the wrong Grain: it is a Source this library does NOT write, so its Grain
# comes from `grain=` + `grain_buckets=` and `Registry.metric_behind` knows nothing about
# its columns. That is the shape that makes WEEK-against-MONTH reachable.
# ======================================================================================

CARRIER_WEEKLY = Source(
    db="mart",
    table="carrier_weekly",
    grain=("dt_week", "carrier_name"),
    grain_buckets=(("dt_week", TimeBucket.WEEK),),
    note="TEST FIXTURE. A weekly table coarsened by some other pipeline.",
    columns=(
        Column("dt_week", "STRING", nullable=False, note="yyyy-MM-dd, the Monday"),
        Column("carrier_name", "STRING", nullable=False),
        Column("attempts", "BIGINT"),
    ),
)

EXTERNAL_WEEKLY_ATTEMPTS = m.sum_of("external_weekly_attempts", CARRIER_WEEKLY.attempts)

EXTERNAL = Registry(name="test_grain.external").add(
    CARRIER_WEEKLY, EXTERNAL_WEEKLY_ATTEMPTS
).freeze()


def external_grain(bucket: TimeBucket) -> m.Grain:
    """The externally coarsened Source reported at one time bucket, carrier kept."""
    return m.Grain.of(
        m.Dimension(CARRIER_WEEKLY.dt_week, bucket, alias="dt_week"),
        m.Dimension(CARRIER_WEEKLY.carrier_name),
    )


# ======================================================================================
# SUM: the rule that does compose
# ======================================================================================


def test_sum_metric_re_grains_from_stored_days_to_weeks() -> None:
    """A SUM of a stored daily partial rolls up to weeks by summing the stored column.

    Breaks if the re-aggregation is dropped (the stored column projected bare, which Hive
    refuses but a GROUP BY change could hide), if the Metric is silently recomputed from the
    atomic Source instead of read from the written one, or if the native Grain stops being
    recovered from the writing Case.
    """
    weekly = compiled("fees_by_week", fixture.WEEKLY_FEES_CHARGED, STORED_WEEK)
    plan = weekly.plan.metrics[0]

    assert plan.rule is m.ReAggregation.SUM
    assert plan.native is not None, "the written Source must have a native Grain"
    assert plan.native.names == ("dt_day", "carrier")

    # Read from the stored partials, not recomputed from atomic rows.
    assert "FROM `mart`.`delivery_health_daily`" in weekly.sql
    assert "mart`.`deliveries`" not in weekly.sql
    assert (
        "SUM(`delivery_health_daily`.`fees_charged`) AS `weekly_fees_charged`"
        in weekly.sql
    )
    # One re-aggregation, not a re-aggregation of a re-aggregation.
    assert weekly.sql.count("SUM(") == 1
    assert WEEK_EXPRESSION in weekly.sql
    assert weekly.sql.count(WEEK_EXPRESSION) == 2, "SELECT and GROUP BY, by expression"


def test_the_same_sum_at_the_stored_grain_is_the_identity_read() -> None:
    """The adjacent build: the same Metric one bucket finer, where nothing rolls up.

    Pairs with the test above so the two differ only by Grain - which is what makes that
    one a test of re-graining rather than a test of SUM.
    """
    daily = compiled("fees_by_day", fixture.WEEKLY_FEES_CHARGED, STORED_DAY)
    plan = daily.plan.metrics[0]

    assert plan.rule is m.ReAggregation.SUM
    assert plan.native is not None and plan.native.names == ("dt_day", "carrier"), (
        "still read from stored partials - the pair differs only by Grain"
    )
    assert (
        "SUM(`delivery_health_daily`.`fees_charged`) AS `weekly_fees_charged`"
        in daily.sql
    )
    assert DAY_EXPRESSION in daily.sql
    assert WEEK_EXPRESSION not in daily.sql


# ======================================================================================
# COUNT(DISTINCT): the rule that does not
# ======================================================================================


def test_stored_count_distinct_refuses_to_roll_up_to_weeks() -> None:
    """Summing a stored COUNT(DISTINCT) is refused, by type and by attribute.

    The courier who worked Monday and Tuesday is one courier in the week and two in a sum
    of days. Hive computes that sum without complaint, so the refusal is the only thing
    between a contributor and a wrong number.
    """
    with pytest.raises(UnsafeReAggregation) as refused:
        compiled(
            "stored_couriers_by_week", fixture.STORED_ACTIVE_COURIERS, STORED_WEEK
        )

    error = refused.value
    assert error.metric == "stored_active_couriers"
    assert error.rule == m.ReAggregation.NONE.value
    assert error.stored_by is None, "this is the reading Metric's own rule refusing"
    assert error.native == str(REGISTRY.native_grain(DAILY))
    assert "dt_day_week" in error.target
    assert isinstance(error, ReAggregationError)


def test_the_same_stored_count_distinct_reads_back_at_its_own_grain() -> None:
    """The adjacent build: at the Grain it was written at, the stored value is readable.

    Without this, the refusal above would also pass against a library that refused every
    use of `stored_active_couriers`. One group holds one stored row, so `MIN` reads it
    back unchanged - Hive still wants an aggregate around a column outside the GROUP BY.
    """
    identity = compiled(
        "stored_couriers_by_day", fixture.STORED_ACTIVE_COURIERS, STORED_DAY
    )

    assert identity.plan.metrics[0].rule is m.ReAggregation.NONE
    assert (
        "MIN(`delivery_health_daily`.`active_couriers`) AS `stored_active_couriers`"
        in identity.sql
    )
    assert "SUM(`delivery_health_daily`.`active_couriers`)" not in identity.sql


def test_count_distinct_over_atomic_rows_is_computed_at_any_grain() -> None:
    """The other adjacent build: COUNT(DISTINCT) is not banned, re-aggregating it is.

    Against the atomic Source there is nothing to roll up - the distinct count is computed
    from rows at whatever Grain the Case asks for, weeks included.
    """
    case = m.Case(
        name="active_couriers_by_week_from_rows",
        metrics=m.by_name(fixture.ACTIVE_COURIERS),
        grain=m.Grain.of(fixture.BY_WEEK),
    )
    weekly = compiler.compile_case(REGISTRY, case, run_date=RUN_DATE)

    assert weekly.plan.metrics[0].native is None, "atomic rows have no stored Grain"
    assert (
        "COUNT(DISTINCT `deliveries`.`courier_id`) AS `active_couriers`" in weekly.sql
    )


# ======================================================================================
# RATIO: re-derived, never averaged
# ======================================================================================


def _division(compiled_case: compiler.Compiled) -> exp.Div:
    """The one division in a compiled statement, as an AST node."""
    divisions = list(compiled_case.ast.find_all(exp.Div))
    assert len(divisions) == 1, f"expected exactly one division, got {len(divisions)}"
    return divisions[0]


def _inside_an_aggregate(node: exp.Expr) -> bool:
    """True when `node` has an aggregate function among its ancestors.

    `AVG(numerator / denominator)` - the average of a row-level rate - is precisely a
    division nested inside an aggregate, and it is the wrong number this design refuses to
    have a spelling for.
    """
    parent = node.parent
    while parent is not None:
        if isinstance(parent, exp.AggFunc):
            return True
        parent = parent.parent
    return False


def test_ratio_re_grains_by_dividing_re_aggregated_parts() -> None:
    """A weekly rate is SUM(numerator) / SUM(denominator), not an average of daily rates.

    The stored `failure_rate` column is right there on the written Source and summing or
    averaging it produces a number every time; the assertion that it is never read is the
    point of this test, not decoration.
    """
    weekly = compiled(
        "failure_rate_by_week", fixture.WEEKLY_FAILURE_RATE, STORED_WEEK
    )
    plan = weekly.plan.metrics[0]

    assert plan.rule is m.ReAggregation.REDERIVE
    assert plan.parts is not None, "a REDERIVE plan carries its two component plans"
    numerator, denominator = plan.parts
    assert numerator.rule is m.ReAggregation.SUM
    assert denominator.rule is m.ReAggregation.SUM

    assert (
        "SUM(`delivery_health_daily`.`failed_deliveries`) / "
        "SUM(`delivery_health_daily`.`delivery_attempts`) AS `weekly_failure_rate`"
        in weekly.sql
    )
    assert "failure_rate`" not in weekly.sql.replace("`weekly_failure_rate`", ""), (
        "the stored daily rate column must not be read at all"
    )
    assert weekly.ast.find(exp.Avg) is None

    division = _division(weekly)
    assert isinstance(division.this, exp.AggFunc)
    assert isinstance(division.expression, exp.AggFunc)
    assert not _inside_an_aggregate(division)


def test_ratio_over_atomic_rows_divides_aggregates_not_row_values() -> None:
    """The same shape from atomic rows: two aggregates divided, never a per-row rate.

    A row-level `failure_reason IS NOT NULL / 1` averaged across rows is the classic
    average-of-averages, and it is structurally a division INSIDE an aggregate - which is
    what the last assertion rules out.
    """
    case = m.Case(
        name="failure_rate_by_day_from_rows",
        metrics=m.by_name(fixture.FAILURE_RATE),
        grain=m.Grain.of(fixture.BY_DAY),
    )
    daily = compiler.compile_case(REGISTRY, case, run_date=RUN_DATE)

    assert (
        "SUM(CASE WHEN NOT `deliveries`.`failure_reason` IS NULL THEN 1 ELSE 0 END) "
        "/ COUNT(*) AS `failure_rate`" in daily.sql
    )
    assert daily.ast.find(exp.Avg) is None

    division = _division(daily)
    assert isinstance(division.this, exp.AggFunc)
    assert isinstance(division.expression, exp.AggFunc)
    assert not _inside_an_aggregate(division)


# ======================================================================================
# The second door: a reading Metric that contradicts the Metric that wrote the column
# ======================================================================================


PROBE = Registry.from_modules(fixture, name="test_grain.probe").add(
    m.sum_of("summed_stored_rate", fixture.DELIVERY_HEALTH_DAILY.failure_rate),
).freeze()
"""A Registry carrying one deliberately wrong Declaration: a SUM over the stored ratio
column. It is well-formed, well-typed, and a wrong number - the only thing that knows so
is the rule the producing Metric carries."""


def test_summing_a_stored_ratio_is_refused_by_the_producing_metrics_rule() -> None:
    """`sum_of(DAILY.failure_rate)` is refused, and the refusal names who wrote the column.

    `check_regrain` alone cannot catch this: the reading Metric is a fresh Declaration
    claiming rule SUM about numbers it did not produce, and SUM composes. The refusal
    comes from `Registry.metric_behind` recovering the producing Metric.
    """
    case = m.Case(
        name="naive_weekly_rate",
        metrics=m.by_name("summed_stored_rate"),
        grain=STORED_WEEK,
    )

    with pytest.raises(UnsafeReAggregation) as refused:
        compiler.compile_case(PROBE, case, run_date=RUN_DATE)

    error = refused.value
    assert error.metric == "summed_stored_rate"
    assert error.stored_by == "failure_rate"
    assert error.rule == m.ReAggregation.REDERIVE.value, "the PRODUCING rule, not SUM"
    assert error.context["declared_rule"] == m.ReAggregation.SUM.value
    assert error.context["reading"] == "mart.delivery_health_daily.failure_rate"


def test_summing_a_stored_sum_in_the_same_registry_still_builds() -> None:
    """The adjacent build: in the very same Registry, a SUM over a SUM-written column works.

    Without this, the test above would pass against a library that refused every Metric
    declared over `mart.delivery_health_daily`.
    """
    case = m.Case(
        name="probe_weekly_fees",
        metrics=m.by_name(fixture.WEEKLY_FEES_CHARGED),
        grain=STORED_WEEK,
    )
    built = compiler.compile_case(PROBE, case, run_date=RUN_DATE)

    assert "SUM(`delivery_health_daily`.`fees_charged`)" in built.sql


# ======================================================================================
# A relabelling Dimension beside a rule that does not compose
#
# `plan_metric` asks `check_regrain` about the target Grain MINUS the Dimensions that only
# relabel the Metric's rows (`grain.determines`), and then asks a second question about the
# FULL target. Those are two different refusals of the same kind, and until a relabelling
# Dimension is in play they are indistinguishable: each one alone stops the same build.
#
# `mart.delivery_health_daily` declares no Join, so the fixture Registry cannot express a
# relabelling Dimension over it at all. `mart.carrier_tiers` below supplies one - declared
# from the tier side and therefore ONE_TO_MANY, exactly as `mart.carriers` is, so walked
# from the daily spine it inverts to MANY_TO_ONE and `determines` proves that grouping by
# `tier` attaches at most one value to each stored row.
# ======================================================================================


CARRIER_TIERS = Source(
    db="mart",
    table="carrier_tiers",
    one_row_per="carrier company",
    note="TEST FIXTURE. A lookup Source hanging off the written daily Source, so that a "
    "Dimension which only relabels its rows is expressible.",
    columns=(
        Column("carrier", "STRING", nullable=False),
        Column("tier", "STRING", note="gold | silver | bronze"),
    ),
    joins=(
        Join(
            to="mart.delivery_health_daily",
            keys=(("carrier", "carrier"),),
            cardinality=Cardinality.ONE_TO_MANY,
            name="tier_daily_rows",
        ),
    ),
)

BY_TIER = m.Dimension(CARRIER_TIERS.tier)
"""The relabelling Dimension: one tier per carrier, so it splits no stored row."""

RELABELLED = Registry.from_modules(fixture, name="test_grain.relabelled").add(
    CARRIER_TIERS
).freeze()

STORED_DAY_BY_TIER = m.Grain.of(*STORED_DAY.dimensions, BY_TIER)
"""The stored Grain itself, reported alongside the relabelling Dimension."""

STORED_WEEK_BY_TIER = m.Grain.of(*STORED_WEEK.dimensions, BY_TIER)
"""One bucket coarser, reported alongside the relabelling Dimension."""


def test_a_rolled_up_none_rule_is_refused_at_the_grain_that_actually_forced_it() -> None:
    """The re-aggregation door: a stored COUNT(DISTINCT) asked for at a coarser Grain.

    `check_regrain` reaches its coarsening branch, consults the Re-aggregation rule and
    refuses, and the Grain it names is the target with `tier` already dropped - because
    `tier` is provably not what makes this unsafe, and a refusal that listed it would send
    a contributor after the one Dimension here that is harmless.

    That naming is the whole assertion. The second refusal in `plan_metric` catches the
    same Case a line later and names the FULL Case Grain, so `tier` appearing in
    `error.target` means this branch stopped firing and the other one covered for it.
    """
    case = m.Case(
        name="stored_couriers_by_week_and_tier",
        metrics=m.by_name(fixture.STORED_ACTIVE_COURIERS),
        grain=STORED_WEEK_BY_TIER,
    )

    with pytest.raises(UnsafeReAggregation) as refused:
        compiler.compile_case(RELABELLED, case, run_date=RUN_DATE)

    error = refused.value
    assert error.metric == "stored_active_couriers"
    assert error.rule == m.ReAggregation.NONE.value
    assert error.stored_by is None, "this is the reading Metric's own rule refusing"
    assert error.native == str(RELABELLED.native_grain(DAILY))
    assert error.target == str(STORED_WEEK), (
        "the coarsening branch is asked about the target minus its relabelling "
        "Dimensions, and names what it was asked about"
    )
    assert "tier" not in error.target


def test_the_same_week_and_tier_grain_builds_for_a_metric_that_does_compose() -> None:
    """The adjacent build: the relabelling Dimension refuses nothing by itself.

    Same Registry, same Grain, same written Source - only the Re-aggregation rule differs.
    Without this, the refusal above would pass just as happily against a library that
    refused every Case reaching `mart.carrier_tiers`.
    """
    case = m.Case(
        name="fees_by_week_and_tier",
        metrics=m.by_name(fixture.WEEKLY_FEES_CHARGED),
        grain=STORED_WEEK_BY_TIER,
    )
    built = compiler.compile_case(RELABELLED, case, run_date=RUN_DATE)

    assert (
        "SUM(`delivery_health_daily`.`fees_charged`) AS `weekly_fees_charged`"
        in built.sql
    )
    assert "`carrier_tiers`.`tier` AS `tier`" in built.sql
    assert built.plan.metrics[0].rule is m.ReAggregation.SUM


def test_a_none_rule_at_its_stored_grain_is_refused_beside_a_relabelling_dimension() -> None:
    """The second door: nothing rolls up, and the Case is refused anyway.

    `check_regrain` sees the stored Grain on both sides once `tier` is dropped, so it
    returns `NONE` without refusing. `plan_metric` then asks the FULL Case Grain, and
    refuses - conservatively, because the value provably cannot change, but `MetricPlan`
    has no way to represent a `NONE` rule planned at a Grain wider than the stored one.

    The refusal names the full Grain, `tier` included, which is what distinguishes it from
    the coarsening branch above. If this stops firing, the plan is built instead and
    `MetricPlan.__post_init__` raises `InvalidDeclaration` - a different type, and this
    `pytest.raises` is what notices.
    """
    case = m.Case(
        name="stored_couriers_by_day_and_tier",
        metrics=m.by_name(fixture.STORED_ACTIVE_COURIERS),
        grain=STORED_DAY_BY_TIER,
    )

    with pytest.raises(UnsafeReAggregation) as refused:
        compiler.compile_case(RELABELLED, case, run_date=RUN_DATE)

    error = refused.value
    assert error.metric == "stored_active_couriers"
    assert error.rule == m.ReAggregation.NONE.value
    assert error.stored_by is None, "this is the reading Metric's own rule refusing"
    assert error.native == str(RELABELLED.native_grain(DAILY))
    assert error.target == str(STORED_DAY_BY_TIER)
    assert "tier" in error.target, "the full Case Grain, not the one check_regrain saw"


def test_the_same_stored_metric_without_the_relabelling_dimension_still_builds() -> None:
    """The adjacent build, differing from the refusal above by one Dimension and nothing
    else.

    Drop `tier` and the identity read comes back: one stored row per group, read through
    `MIN`. That is what makes the refusal above a refusal of the relabelling Dimension
    rather than a refusal of `stored_active_couriers`.
    """
    case = m.Case(
        name="stored_couriers_by_day_no_tier",
        metrics=m.by_name(fixture.STORED_ACTIVE_COURIERS),
        grain=STORED_DAY,
    )
    built = compiler.compile_case(RELABELLED, case, run_date=RUN_DATE)

    assert built.plan.metrics[0].rule is m.ReAggregation.NONE
    assert (
        "MIN(`delivery_health_daily`.`active_couriers`) AS `stored_active_couriers`"
        in built.sql
    )
    assert "carrier_tiers" not in built.sql


# ======================================================================================
# The comparability refusals, against a Source this library does not write
# ======================================================================================


def test_weeks_do_not_roll_up_into_months() -> None:
    """WEEK and MONTH are incomparable, because ISO weeks straddle month boundaries.

    Most tools emit this silently. `TimeBucket` makes the order partial on purpose, so the
    answer here is a refusal rather than a month that is short a few days at each end.
    """
    with pytest.raises(GrainNotComparable) as refused:
        grain.plan_metric(
            EXTERNAL,
            EXTERNAL_WEEKLY_ATTEMPTS,
            external_grain(TimeBucket.MONTH),
            spine=CARRIER_WEEKLY,
            path=(),
        )

    error = refused.value
    assert error.metric == "external_weekly_attempts"
    assert error.native == str(EXTERNAL.native_grain(CARRIER_WEEKLY))
    assert not TimeBucket.MONTH.comparable(TimeBucket.WEEK)


def test_the_same_weekly_source_reads_back_at_its_own_bucket() -> None:
    """The adjacent build: asked for at WEEK, the same Metric plans as an ordinary SUM."""
    plan = grain.plan_metric(
        EXTERNAL,
        EXTERNAL_WEEKLY_ATTEMPTS,
        external_grain(TimeBucket.WEEK),
        spine=CARRIER_WEEKLY,
        path=(),
    )

    assert plan.rule is m.ReAggregation.SUM
    assert plan.native is not None
    assert plan.native.names == ("dt_week", "carrier_name")


def test_a_weekly_source_asked_for_by_day_is_refused_as_too_fine() -> None:
    """Detail the Source has already thrown away is `GrainTooFine`, naming what is missing.

    The opposite direction from the re-aggregation refusals above, and a different fix: no
    Re-aggregation rule can recover days from weeks, so the remedy is to read the atomic
    Source instead.
    """
    with pytest.raises(GrainTooFine) as refused:
        grain.plan_metric(
            EXTERNAL,
            EXTERNAL_WEEKLY_ATTEMPTS,
            external_grain(TimeBucket.DAY),
            spine=CARRIER_WEEKLY,
            path=(),
        )

    assert refused.value.offending == ("dt_week",)


# ======================================================================================
# The `reaggregate` primitive itself
# ======================================================================================


def test_reaggregate_composes_only_the_rules_that_compose() -> None:
    """`grain.reaggregate` wraps SUM/MIN/MAX and refuses REDERIVE and NONE.

    A caller reaching `reaggregate` with REDERIVE has taken a shortcut past `rederive`, and the
    shortcut renders as `SUM(a / b)` - the average of a rate, arrived at from inside the
    library rather than from a Declaration.
    """
    column = fixture.DELIVERY_HEALTH_DAILY.fees_charged.to_sqlglot()

    assert isinstance(grain.reaggregate(m.ReAggregation.SUM, column), exp.Sum)
    assert isinstance(grain.reaggregate(m.ReAggregation.MIN, column), exp.Min)
    assert isinstance(grain.reaggregate(m.ReAggregation.MAX, column), exp.Max)

    for unsafe in (m.ReAggregation.REDERIVE, m.ReAggregation.NONE):
        with pytest.raises(UnsafeReAggregation):
            grain.reaggregate(unsafe, column)


# ======================================================================================
# Bucketing: the two columns Hive answers with a silent NULL
#
# Both refusals below were mutation-survivable - `bucket_expression` could bucket anything
# it was handed with the whole suite green - and both protect the same thing the rest of
# this module protects. A Grain column of NULLs is not a failed build: it is one group,
# every number in the Case summed into it, and a statement that runs.
# ======================================================================================


def test_bucketing_a_column_hive_cannot_read_as_a_date_refuses() -> None:
    """An epoch or `yyyyMMdd` integer is the common shape, and DATE_FORMAT over it returns
    NULL rather than raising - so the Case reports one row labelled NULL, with every
    delivery in it, and nothing anywhere says so.
    """
    epoch = Column("dt_epoch", "BIGINT")
    source = Source(db="mart", table="epoch_deliveries", columns=(epoch,))

    with pytest.raises(InvalidDeclaration) as refused:
        grain.bucket_expression(source.dt_epoch, TimeBucket.DAY)

    assert refused.value.subject == "mart.epoch_deliveries.dt_epoch"
    assert "BIGINT" in refused.value.problem

    # The adjacent build: the same bucket over the declared shapes Hive can read.
    for type_text in ("STRING", "DATE", "TIMESTAMP"):
        readable = Source(
            db="mart", table="ok_deliveries", columns=(Column("dt", type_text),)
        )
        assert grain.bucket_expression(readable.dt, TimeBucket.DAY) is not None


def test_an_hour_bucket_over_a_date_only_column_refuses() -> None:
    """A DATE carries no time of day, so `DATE_FORMAT(d, 'yyyy-MM-dd HH:00:00')` answers
    midnight for every row: twenty-four hourly buckets collapsed into one, labelled hourly
    and read as hourly.

    The refusal names the declared type because that is the fact that decides it - the same
    HOUR bucket over a TIMESTAMP column is exactly what it claims to be.
    """
    day_only = Source(db="mart", table="daily", columns=(Column("dt", "DATE"),))

    with pytest.raises(InvalidDeclaration) as refused:
        grain.bucket_expression(day_only.dt, TimeBucket.HOUR)

    assert refused.value.subject == "mart.daily.dt"
    assert "no time of day" in refused.value.problem

    # The adjacent builds: HOUR over a TIMESTAMP, and DAY over the same DATE column.
    stamped = Source(db="mart", table="stamped", columns=(Column("at", "TIMESTAMP"),))
    assert grain.bucket_expression(stamped.at, TimeBucket.HOUR) is not None
    assert grain.bucket_expression(day_only.dt, TimeBucket.DAY) is not None
