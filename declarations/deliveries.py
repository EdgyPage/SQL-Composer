"""INVENTED FIXTURE - a delivery-operations warehouse that does not exist.

Nothing in this module was generated from a real warehouse. Every table, column, type,
Cardinality and business rule here was made up to exercise the composer end to end: the
user was asked for a real table to declare against, declined, and asked for the library to
be built anyway. Treat it as a worked example and a test fixture, never as documentation of
anyone's schema. A real Declaration is generated from the warehouse, checked in, and then
hand-annotated - see README.md.

What the fixture is shaped to prove, in the order a reader meets it:

* the Fan-out refusal has something real to fire on, because `mart.carriers` declares a
  ONE_TO_MANY edge into `mart.deliveries`: a Metric measured on the carrier and reported by
  delivery day is inflated once per delivery, and is refused rather than emitted;
* the ambiguity refusal has something real to fire on, because a delivery has both an
  origin site and a destination site, so two declared edges connect `mart.deliveries` to
  `mart.sites` and a Case reaching sites has to say which one it means;
* the Re-aggregation refusal has something real to fire on, because `active_couriers` is a
  COUNT(DISTINCT) that is written into `mart.delivery_health_daily` and cannot be rolled up
  out of it - `STORED_ACTIVE_COURIERS` is declared here so that mistake can be made on
  purpose, and it is deliberately carried by no Tag family;
* the horizontal-scaling claim is checkable, because `ACCOUNTABLE_BY_DAY` /
  `ACCOUNTABLE_BY_WEEK` differ only by Grain and `ACCOUNTABLE_BY_DAY` /
  `OPERATIONAL_BY_DAY` differ only by Tag family. Declaring a new Metric with one of those
  Tags joins every Case asking for it, with no Case edited.

The Metrics span every Re-aggregation rule the design names: SUM (`fees_charged`), COUNT
rolling up by SUM (`delivery_attempts`), MIN and MAX (`first_promised_at`,
`last_delivered_at`), REDERIVE (`failure_rate`) and NONE (`active_couriers`).
"""
from __future__ import annotations

from sqlcomposer.declaration import (
    Cardinality,
    Column,
    Join,
    RunDate,
    Source,
    TimeBucket,
)
from sqlcomposer.model import (
    Case,
    Dimension,
    Filter,
    Grain,
    ReAggregation,
    by_tag,
    count_distinct,
    count_rows,
    max_of,
    min_of,
    ratio,
    sum_of,
)

# ======================================================================================
# Tags. Module-level constants so a Tag family is greppable; Tag is a plain `str`, and the
# typo safety comes from Registry.tagged refusing each Tag that matches nothing.
# ======================================================================================

ACCOUNTABLE = "accountable"
"""Numbers a delivery operation is answerable for: volumes, failures, money, reach."""

OPERATIONAL = "operational"
"""Numbers the shift lead watches during the day. Overlaps ACCOUNTABLE deliberately -
`delivery_attempts` carries both, which is what makes the two families a real selection
rather than a partition."""

CARRIER_PROFILE = "carrier_profile"
"""Facts about the carrier company itself, measured on `mart.carriers`. No Case reports
this family, because every Case here is anchored on deliveries and reaching a carrier
Metric from there multiplies it once per delivery. tools/smoke.py asks for it on purpose,
to show the Fan-out refusal firing."""

WEEKLY_REAGGREGATED = "weekly_reaggregated"
"""Metrics that read the written daily table rather than the atomic Source."""


# ======================================================================================
# Sources
# ======================================================================================

CARRIERS = Source(
    db="mart",
    table="carriers",
    one_row_per="carrier company",
    note="Slowly changing, overwritten nightly. No history.",
    columns=(
        Column("carrier_id", "STRING", nullable=False),
        Column("carrier_name", "STRING", nullable=False),
        Column("carrier_tier", "STRING", note="gold | silver | bronze"),
        Column("fleet_size", "BIGINT", note="vehicles, not people"),
        Column("is_test", "BIGINT", nullable=False, note="1 for internal test carriers"),
    ),
    joins=(
        # Declared from the carrier's side, and therefore ONE_TO_MANY: one carrier has many
        # deliveries. Walked from a deliveries spine it inverts to MANY_TO_ONE, which is
        # the harmless lookup direction. Walked the declared way it fans the carrier out
        # once per delivery, which is exactly what `check_fan_out` refuses.
        Join(
            to="mart.deliveries",
            keys=(("carrier_id", "carrier_id"),),
            cardinality=Cardinality.ONE_TO_MANY,
            name="carrier_deliveries",
        ),
    ),
)

SITES = Source(
    db="mart",
    table="sites",
    one_row_per="depot or drop-off site",
    columns=(
        Column("site_id", "STRING", nullable=False),
        Column("site_name", "STRING", nullable=False),
        Column("region", "STRING"),
        Column("country", "STRING", note="ISO 3166-1 alpha-2"),
    ),
)

CUSTOMERS = Source(
    db="mart",
    table="customers",
    one_row_per="billing customer",
    columns=(
        Column("customer_id", "STRING", nullable=False),
        Column("customer_name", "STRING"),
        Column("segment", "STRING", note="enterprise | smb | consumer"),
    ),
)

DELIVERIES = Source(
    db="mart",
    table="deliveries",
    one_row_per="delivery attempt",
    note="One row per attempt, not per parcel: a reattempted parcel appears twice.",
    columns=(
        Column("delivery_id", "STRING", nullable=False),
        Column("order_id", "STRING", nullable=False),
        Column("carrier_id", "STRING", nullable=False),
        Column("courier_id", "STRING", note="the person; NULL before a courier is assigned"),
        Column("origin_site_id", "STRING", nullable=False),
        Column("destination_site_id", "STRING", nullable=False),
        Column("customer_id", "STRING", nullable=False),
        Column("dt", "STRING", partition=True, nullable=False, note="yyyy-MM-dd, attempt date"),
        Column("failure_reason", "STRING", note="NULL means the parcel was delivered"),
        Column("late_flag", "BIGINT", nullable=False, note="1 when delivered after promised_at"),
        Column("fee_amount", "DECIMAL(18,2)", nullable=False, note="carrier fee, in EUR"),
        Column("scan_count", "BIGINT", nullable=False, note="handheld scans on this attempt"),
        Column("promised_at", "TIMESTAMP", nullable=False),
        Column("delivered_at", "TIMESTAMP", note="NULL when the attempt failed"),
    ),
    joins=(
        # Two edges to the same Source, which is the whole reason a Join carries a name and
        # a Case pins `via=` with edge names rather than table names.
        Join(
            to="mart.sites",
            keys=(("origin_site_id", "site_id"),),
            cardinality=Cardinality.MANY_TO_ONE,
            name="delivery_origin_site",
            note="where the attempt was loaded",
        ),
        Join(
            to="mart.sites",
            keys=(("destination_site_id", "site_id"),),
            cardinality=Cardinality.MANY_TO_ONE,
            name="delivery_destination_site",
            note="where the attempt was headed",
        ),
        Join(
            to="mart.customers",
            keys=(("customer_id", "customer_id"),),
            cardinality=Cardinality.MANY_TO_ONE,
            name="delivery_customer",
        ),
    ),
)

DELIVERY_HEALTH_DAILY = Source(
    db="mart",
    table="delivery_health_daily",
    written_by="accountable_by_day",
    note="Written by the composer. Its Grain is the writing Case's Grain, never declared "
    "here - see Registry.native_grain.",
    columns=(
        # Non-Partition columns, in this order, ARE `ACCOUNTABLE_BY_DAY.output_names`.
        # Hive matches INSERT columns by position, so adding an `accountable` Metric
        # anywhere breaks this write loudly until the table is regenerated. That break is
        # the review signal, not an accident.
        Column("dt_day", "STRING", nullable=False, note="yyyy-MM-dd; the Grain, not the Partition"),
        Column("carrier", "STRING", nullable=False),
        Column("active_couriers", "BIGINT", note="a stored COUNT(DISTINCT): does not roll up"),
        Column("delivery_attempts", "BIGINT"),
        Column("failed_deliveries", "BIGINT"),
        Column("failure_rate", "DOUBLE"),
        Column("fees_charged", "DECIMAL(18,2)"),
        Column("dt", "STRING", partition=True, nullable=False, note="yyyy-MM-dd, the run date"),
    ),
)


# ======================================================================================
# Filters
# ======================================================================================

FAILURE_TO_DELIVER = Filter(
    name="failure_to_deliver",
    predicate=DELIVERIES.failure_reason.is_not_null(),
    note="A Filter over the shared delivery Source, not a Metric. Recorded assumption: "
    "the business means 'the attempt did not deliver the parcel', and `failure_reason` is "
    "NULL exactly when it did.",
)

DELIVERED_LATE = Filter(
    name="delivered_late",
    predicate=DELIVERIES.late_flag.eq(1),
    note="The warehouse computes lateness; the composer cannot, because a Predicate "
    "compares a column to a value and never to another column.",
)

LAST_7_DAYS = Filter(
    name="last_7_delivery_days",
    predicate=DELIVERIES.dt.between(RunDate() - 6, RunDate()),
    note="A Partition-column predicate against bare literals, so Hive prunes. Holds a "
    "RunDate, so every Case carrying it needs run_date= at compile time.",
)

LIVE_CARRIERS = Filter(
    name="live_carriers",
    predicate=CARRIERS.is_test.eq(0),
    note="Excludes internal test carriers. Drags mart.carriers into the Join path of any "
    "Case that uses it, which is why Filters count towards Case.sources().",
)

LAST_7_WRITTEN_DAYS = Filter(
    name="last_7_written_days",
    predicate=DELIVERY_HEALTH_DAILY.dt.between(RunDate() - 6, RunDate()),
    note="The same window, against the written table's own Partition column.",
)


# ======================================================================================
# Metrics. Declared against the one Source each measures.
# ======================================================================================

DELIVERY_ATTEMPTS = count_rows(
    "delivery_attempts",
    DELIVERIES,
    tags=(ACCOUNTABLE, OPERATIONAL),
    note="COUNT(*) of attempts. Rolls up by SUM, not by COUNT.",
)

FAILED_DELIVERIES = count_rows(
    "failed_deliveries",
    DELIVERIES,
    when=FAILURE_TO_DELIVER,
    tags=(ACCOUNTABLE,),
    note="A conditional aggregate, never a WHERE clause - a WHERE here would narrow every "
    "other Metric in the same Case.",
)

LATE_DELIVERIES = count_rows(
    "late_deliveries",
    DELIVERIES,
    when=DELIVERED_LATE,
    tags=(OPERATIONAL,),
)

FAILURE_RATE = ratio(
    "failure_rate",
    FAILED_DELIVERIES,
    DELIVERY_ATTEMPTS,
    tags=(ACCOUNTABLE,),
    note="Re-derived from re-aggregated parts at every Grain. There is no AVG in this "
    "library and no way to spell an average of averages.",
)

LATE_RATE = ratio(
    "late_rate",
    LATE_DELIVERIES,
    DELIVERY_ATTEMPTS,
    tags=(OPERATIONAL,),
)

FEES_CHARGED = sum_of(
    "fees_charged",
    DELIVERIES.fee_amount,
    tags=(ACCOUNTABLE,),
    note="The plain additive case: SUM rolls up to any coarser Grain.",
)

SCAN_EVENTS = sum_of(
    "scan_events",
    DELIVERIES.scan_count,
    tags=(OPERATIONAL,),
)

ACTIVE_COURIERS = count_distinct(
    "active_couriers",
    DELIVERIES.courier_id,
    tags=(ACCOUNTABLE,),
    note="Re-aggregation rule NONE, with no override available. The same courier working "
    "Monday and Tuesday is one courier in the week and two in a sum of days.",
)

FIRST_PROMISED_AT = min_of(
    "first_promised_at",
    DELIVERIES.promised_at,
    tags=(OPERATIONAL,),
)

LAST_DELIVERED_AT = max_of(
    "last_delivered_at",
    DELIVERIES.delivered_at,
    tags=(OPERATIONAL,),
)

CARRIER_FLEET_SIZE = sum_of(
    "carrier_fleet_size",
    CARRIERS.fleet_size,
    tags=(CARRIER_PROFILE,),
    note="Measured on mart.carriers. Sound on its own; reported next to a delivery "
    "Dimension it is counted once per delivery, which joins.check_fan_out refuses.",
)

# -- Metrics that read the written daily table -----------------------------------------

WEEKLY_DELIVERY_ATTEMPTS = sum_of(
    "weekly_delivery_attempts",
    DELIVERY_HEALTH_DAILY.delivery_attempts,
    tags=(WEEKLY_REAGGREGATED,),
    note="Sums stored partial counts. The rename is required: Metric names are unique "
    "across the Registry, and this one measures a different Source than its namesake.",
)

WEEKLY_FAILED_DELIVERIES = sum_of(
    "weekly_failed_deliveries",
    DELIVERY_HEALTH_DAILY.failed_deliveries,
    tags=(WEEKLY_REAGGREGATED,),
)

WEEKLY_FEES_CHARGED = sum_of(
    "weekly_fees_charged",
    DELIVERY_HEALTH_DAILY.fees_charged,
    tags=(WEEKLY_REAGGREGATED,),
)

WEEKLY_FAILURE_RATE = ratio(
    "weekly_failure_rate",
    WEEKLY_FAILED_DELIVERIES,
    WEEKLY_DELIVERY_ATTEMPTS,
    tags=(WEEKLY_REAGGREGATED,),
    note="SUM(failed) / SUM(attempts), never AVG(failure_rate). The stored daily rate "
    "column is not read at all.",
)

STORED_ACTIVE_COURIERS = sum_of(
    "stored_active_couriers",
    DELIVERY_HEALTH_DAILY.active_couriers,
    rule=ReAggregation.NONE,
    note="Carried by NO Tag, so no Case picks it up by accident. The stored column holds a "
    "distinct count, and `rule=NONE` is the honest statement that summing it is wrong. "
    "tools/smoke.py reports it above its stored Grain on purpose, to show the refusal.",
)


# ======================================================================================
# Dimensions
# ======================================================================================

BY_DAY = Dimension(DELIVERIES.dt, TimeBucket.DAY)
BY_WEEK = Dimension(DELIVERIES.dt, TimeBucket.WEEK)
BY_CARRIER = Dimension(CARRIERS.carrier_name, alias="carrier")
BY_DESTINATION_SITE = Dimension(SITES.site_name, alias="destination_site")
BY_SEGMENT = Dimension(CUSTOMERS.segment)

WRITTEN_BY_WEEK = Dimension(DELIVERY_HEALTH_DAILY.dt_day, TimeBucket.WEEK)
WRITTEN_BY_CARRIER = Dimension(DELIVERY_HEALTH_DAILY.carrier)


# ======================================================================================
# Cases
#
# The first four are the horizontal-scaling proof: two pairs differing only by Grain, two
# pairs differing only by Tag family. Read the `variant()` calls as the diff they are.
# ======================================================================================

ACCOUNTABLE_BY_DAY = Case(
    name="accountable_by_day",
    metrics=by_tag(ACCOUNTABLE),
    grain=Grain.of(BY_DAY, BY_CARRIER),
    filters=(LAST_7_DAYS, LIVE_CARRIERS),
    writes_to=DELIVERY_HEALTH_DAILY,
    note="The daily table every weekly question is built on.",
)

ACCOUNTABLE_BY_WEEK = ACCOUNTABLE_BY_DAY.variant(
    "accountable_by_week",
    grain=Grain.of(BY_WEEK, BY_CARRIER),
    note="Differs from accountable_by_day ONLY by Grain. Reads the atomic Source, so the "
    "weekly COUNT(DISTINCT) is computed rather than rolled up.",
)

OPERATIONAL_BY_DAY = ACCOUNTABLE_BY_DAY.variant(
    "operational_by_day",
    metrics=by_tag(OPERATIONAL),
    note="Differs from accountable_by_day ONLY by Tag family.",
)

OPERATIONAL_BY_WEEK = OPERATIONAL_BY_DAY.variant(
    "operational_by_week",
    grain=Grain.of(BY_WEEK, BY_CARRIER),
    note="Closes the square: by Grain from operational_by_day, by Tag from "
    "accountable_by_week.",
)

FAILURES_BY_SITE_AND_SEGMENT = Case(
    name="failures_by_site_and_segment",
    metrics=by_tag(ACCOUNTABLE),
    grain=Grain.of(BY_DAY, BY_DESTINATION_SITE, BY_SEGMENT),
    filters=(LAST_7_DAYS,),
    # Two edges reach mart.sites, so the composer refuses to pick. This is what it printed.
    via=("delivery_customer", "delivery_destination_site"),
    note="Where failures land, and whose parcels they were. FAILURE_TO_DELIVER is NOT a "
    "Case-level Filter here, although the question is about failures: the ACCOUNTABLE "
    "family already contains `failed_deliveries`, which is scoped by that same Filter, and "
    "narrowing the Case by it too would make that conditional aggregate a tautology - "
    "`failed_deliveries` would equal `delivery_attempts` and `failure_rate` would be 1.0 on "
    "every row. `ScopeCollision` refuses that; the scoping belongs on the Metric, and the "
    "denominator stays honest.",
)

WEEKLY_HEALTH_FROM_DAILY = Case(
    name="weekly_health_from_daily",
    metrics=by_tag(WEEKLY_REAGGREGATED),
    grain=Grain.of(WRITTEN_BY_WEEK, WRITTEN_BY_CARRIER),
    filters=(LAST_7_WRITTEN_DAYS,),
    note="Reads the table accountable_by_day writes. Every Metric here rolls up by SUM or "
    "is re-derived from two that do; the stored COUNT(DISTINCT) is not in this family, "
    "and asking for it raises UnsafeReAggregation.",
)
