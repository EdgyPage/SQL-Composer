"""Value tier: run the emitted SQL against real rows and check the NUMBERS.

Every other tier in this suite can only catch SQL that looks wrong. This one is the only
one that can catch a wrong *number*, which is the failure mode the whole library exists to
prevent - decision 3's four refusals each stand in for a query that runs, returns rows, and
is quietly wrong. A refusal is only worth having if the thing it refuses would really have
been wrong, so every refusal asserted here is paired with a companion test that executes
the naive query and shows the wrong number arriving. Without the companion, a refusal test
passes just as well against a library that refuses everything.

How this tier works, and what it costs:

* duckdb is TEST-ONLY. Nothing under `sqlcomposer/` imports it - `test_core_never_imports_duckdb`
  is the check, because the core is compile-only and connects to nothing.
* The fixture tables are built by walking `Registry.sources()` and translating each declared
  Hive type with sqlglot, not from hand-written DDL, so a column or a type only exists here
  because a Declaration says so. A fixture schema that has quietly stopped matching the
  Declarations proves things about itself.
* The SQL executed is the library's own Hive output, parsed as Hive and regenerated for
  duckdb by sqlglot. It is not rewritten, reformatted or hand-fixed - see `to_duckdb` for
  the single documented exception and why it does not weaken anything.
* Expected values are computed in plain Python from the same row tuples, by loops rather
  than by a second SQL query. A second query would share the bug.

Where Hive and duckdb genuinely disagree, this tier says so rather than asserting something
untrue: partition pruning has no duckdb analogue at all
(`test_partition_pruning_is_not_observable_here` is skipped, not faked), the WEEK bucket
comes back as a date value in duckdb where Hive types it STRING (normalised by `_as_date`,
and the type claim is left to the golden-SQL tier), and Hive's `INSERT OVERWRITE ...
PARTITION` has no duckdb form, so `_overwrite_partition` stands in for it using the
partition the library itself named.

The fixture rows are INVENTED, like the Declarations they populate. See
`declarations/deliveries.py`.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Sequence

import duckdb
import pytest
import sqlglot
from sqlglot import exp

import sqlcomposer
from declarations import REGISTRY
from declarations import deliveries as fixture
from sqlcomposer import compile_case, write
from sqlcomposer.declaration import Registry, Source
from sqlcomposer.errors import FanOut, UnsafeReAggregation
from sqlcomposer.model import Case, Dimension, Filter, Grain, by_name

# ======================================================================================
# The rows. Invented, like the Declarations they populate.
# ======================================================================================

RUN_DATE = datetime.date(2026, 9, 17)
"""Thursday. `LAST_7_DAYS` makes the window 2026-09-11..2026-09-17, which straddles exactly
two ISO weeks - 09-07 (Fri, Sat, Sun) and 09-14 (Mon..Thu). Two week buckets rather than one
is deliberate: a day-to-week re-grain that produces a single group cannot catch a bucket
expression that collapses everything into one."""

WINDOW = ("2026-09-11", "2026-09-17")

FAN_OUT_DAY = "2026-09-14"
"""The one day on which every carrier that delivered at all delivered exactly twice, which
is what makes the fan-out arithmetic an exact doubling rather than merely an inflation."""


@dataclass(frozen=True)
class CarrierRow:
    carrier_id: str
    carrier_name: str
    carrier_tier: str
    fleet_size: int
    is_test: int


@dataclass(frozen=True)
class DeliveryRow:
    dt: str
    carrier_id: str
    courier_id: str | None
    fee_amount: Decimal
    failure_reason: str | None
    late_flag: int


CARRIER_ROWS: tuple[CarrierRow, ...] = (
    CarrierRow("C1", "Aurora Logistics", "gold", 10, 0),
    CarrierRow("C2", "Bolt Freight", "gold", 4, 0),
    CarrierRow("C3", "Cedar Couriers", "silver", 7, 0),
    # Delivers nothing. It exists so the literal tests have a carrier whose name contains
    # both of the characters Hive escapes, without disturbing any delivery arithmetic.
    CarrierRow("C4", "O'Hara & Co \\ Ltd", "bronze", 12, 0),
    # is_test=1, so LIVE_CARRIERS must drop it and its 1000.00 fee with it.
    CarrierRow("C9", "Internal Test Carrier", "bronze", 99, 1),
)

DELIVERY_ROWS: tuple[DeliveryRow, ...] = (
    DeliveryRow("2026-09-11", "C1", "K1", Decimal("10.00"), None, 0),
    DeliveryRow("2026-09-11", "C1", "K2", Decimal("12.50"), "no_access", 1),
    DeliveryRow("2026-09-12", "C1", "K1", Decimal("9.00"), None, 0),
    DeliveryRow("2026-09-14", "C1", "K1", Decimal("20.00"), None, 0),
    DeliveryRow("2026-09-14", "C1", "K3", Decimal("5.25"), "address_unknown", 1),
    DeliveryRow("2026-09-15", "C1", "K1", Decimal("7.75"), None, 0),
    DeliveryRow("2026-09-15", "C1", "K2", Decimal("8.00"), None, 1),
    DeliveryRow("2026-09-17", "C1", "K1", Decimal("3.00"), "refused", 0),
    DeliveryRow("2026-09-13", "C2", "K4", Decimal("30.00"), None, 0),
    DeliveryRow("2026-09-14", "C2", "K4", Decimal("11.10"), None, 0),
    DeliveryRow("2026-09-14", "C2", "K5", Decimal("22.20"), "damaged", 1),
    DeliveryRow("2026-09-16", "C2", "K4", Decimal("1.05"), None, 0),
    DeliveryRow("2026-09-11", "C3", "K6", Decimal("50.00"), "weather", 1),
    DeliveryRow("2026-09-14", "C3", "K6", Decimal("2.00"), None, 0),
    DeliveryRow("2026-09-14", "C3", "K7", Decimal("4.00"), None, 0),
    # courier_id is declared nullable ("NULL before a courier is assigned"). Both engines
    # drop NULL from COUNT(DISTINCT), so this row contributes an attempt and no courier.
    DeliveryRow("2026-09-15", "C3", None, Decimal("1.00"), None, 0),
    DeliveryRow("2026-09-17", "C3", "K6", Decimal("6.00"), None, 0),
    DeliveryRow("2026-09-15", "C9", "K9", Decimal("1000.00"), None, 0),
    # Outside the window. A dropped WHERE clause shows up as these fees in a total.
    DeliveryRow("2026-09-10", "C1", "K1", Decimal("999.00"), None, 0),
    DeliveryRow("2026-09-18", "C1", "K1", Decimal("888.00"), None, 0),
)

SCAN_COUNT = 3
"""Constant across every row: `scan_events` is not what this module is checking, and a
varying value would only add arithmetic nobody reads."""


# ======================================================================================
# The Python oracle. Loops, not a second query - a second query would share the bug.
# ======================================================================================

_BY_ID = {carrier.carrier_id: carrier for carrier in CARRIER_ROWS}


def _live_window_rows() -> tuple[DeliveryRow, ...]:
    """The rows `ACCOUNTABLE_BY_DAY`'s two Filters leave: in window, non-test carrier."""
    return tuple(
        row
        for row in DELIVERY_ROWS
        if WINDOW[0] <= row.dt <= WINDOW[1] and not _BY_ID[row.carrier_id].is_test
    )


def _iso_monday(day: str) -> datetime.date:
    parsed = datetime.date.fromisoformat(day)
    return parsed - datetime.timedelta(days=parsed.weekday())


def _aggregate(rows: Iterable[DeliveryRow]) -> dict[str, Any]:
    rows = tuple(rows)
    attempts = len(rows)
    failed = sum(1 for row in rows if row.failure_reason is not None)
    couriers = {row.courier_id for row in rows if row.courier_id is not None}
    return {
        "active_couriers": len(couriers),
        "delivery_attempts": attempts,
        "failed_deliveries": failed,
        "failure_rate": failed / attempts,
        "fees_charged": sum((row.fee_amount for row in rows), Decimal("0.00")),
    }


def _expected(bucket) -> dict[tuple[Any, str], dict[str, Any]]:
    """`ACCOUNTABLE_*`'s expected output, keyed by (time bucket, carrier name).

    `bucket` maps a `yyyy-MM-dd` day string onto the Grain's time bucket, so the same
    oracle serves the daily Case and the weekly one and the two cannot drift apart.
    """
    grouped: dict[tuple[Any, str], list[DeliveryRow]] = {}
    for row in _live_window_rows():
        key = (bucket(row.dt), _BY_ID[row.carrier_id].carrier_name)
        grouped.setdefault(key, []).append(row)
    return {key: _aggregate(rows) for key, rows in grouped.items()}


EXPECTED_DAILY = _expected(lambda day: day)
EXPECTED_WEEKLY = _expected(_iso_monday)


# ======================================================================================
# The duckdb harness
# ======================================================================================


def to_duckdb(hive_sql: str) -> str:
    """Re-render the library's Hive output for duckdb, changing nothing else.

    One documented repair, and it is a sqlglot transpiler gap rather than anything the
    library did: sqlglot renders Hive's `NEXT_DAY(x, 'MO')` for duckdb as an `ISODOW(x)`
    expression without casting `x`, and duckdb has no `isodow(VARCHAR)` overload, so the
    statement fails to bind. Hive's own NEXT_DAY accepts the `yyyy-MM-dd` string that
    `grain.bucket_expression` feeds it, so the Hive SQL is correct as emitted. Adding the
    CAST changes the argument's type and not its value, and the resulting week buckets are
    asserted against `_iso_monday` independently, so the repair cannot hide a wrong bucket.
    """
    ast = sqlglot.parse_one(hive_sql, read="hive")
    for node in ast.find_all(exp.NextDay):
        node.set("this", exp.cast(node.this.copy(), "DATE"))
    return ast.sql(dialect="duckdb")


def query(connection: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    """Execute and return rows as dicts keyed by output column name.

    By name rather than by position on purpose: a test that unpacks a tuple positionally
    agrees with a SELECT list that has silently reordered, which is one of the mistakes
    this tier is here to catch.
    """
    cursor = connection.execute(sql)
    names = [description[0] for description in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def _duckdb_type(hive_type: str) -> str:
    return exp.DataType.build(hive_type, dialect="hive").sql(dialect="duckdb")


def _create_table(connection: duckdb.DuckDBPyConnection, source: Source) -> None:
    """Build the duckdb table from the Declaration, never from a hand-written DDL.

    A hand-written fixture schema drifts away from the Declarations and then proves
    something about itself instead of about the library.
    """
    columns = ", ".join(
        f'"{column.name}" {_duckdb_type(column.type)}' for column in source.columns
    )
    connection.execute(f'CREATE TABLE "{source.db}"."{source.table}" ({columns})')


def _insert(
    connection: duckdb.DuckDBPyConnection,
    source: Source,
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
) -> None:
    placeholders = ", ".join("?" for _ in columns)
    named = ", ".join(f'"{column}"' for column in columns)
    connection.executemany(
        f'INSERT INTO "{source.db}"."{source.table}" ({named}) VALUES ({placeholders})',
        [list(row) for row in rows],
    )


@pytest.fixture(name="warehouse")
def warehouse_fixture() -> Iterable[duckdb.DuckDBPyConnection]:
    """An in-memory warehouse holding every declared Source, populated with the rows above.

    Function-scoped and rebuilt per test: two of these tests write to
    `mart.delivery_health_daily`, and a shared connection would make their results depend on
    collection order.
    """
    connection = duckdb.connect()
    connection.execute("CREATE SCHEMA mart")
    for source in REGISTRY.sources():
        _create_table(connection, source)

    _insert(
        connection,
        fixture.CARRIERS,
        ("carrier_id", "carrier_name", "carrier_tier", "fleet_size", "is_test"),
        [
            (c.carrier_id, c.carrier_name, c.carrier_tier, c.fleet_size, c.is_test)
            for c in CARRIER_ROWS
        ],
    )
    _insert(
        connection,
        fixture.DELIVERIES,
        (
            "delivery_id", "order_id", "carrier_id", "courier_id", "origin_site_id",
            "destination_site_id", "customer_id", "dt", "failure_reason", "late_flag",
            "fee_amount", "scan_count", "promised_at", "delivered_at",
        ),
        [
            (
                f"D{index:03d}", f"O{index:03d}", row.carrier_id, row.courier_id,
                "SITE_A", "SITE_B", "CUST_1", row.dt, row.failure_reason, row.late_flag,
                row.fee_amount, SCAN_COUNT, f"{row.dt} 09:00:00",
                None if row.failure_reason else f"{row.dt} 10:00:00",
            )
            for index, row in enumerate(DELIVERY_ROWS)
        ],
    )
    try:
        yield connection
    finally:
        connection.close()


def _as_date(value: Any) -> datetime.date:
    """Normalise a time-bucket value across the two engines.

    Hive types every bucket `grain.bucket_expression` produces as a `yyyy-MM-dd` STRING.
    duckdb's transpiled WEEK bucket is arithmetic on a DATE and so comes back as a date
    value. That is a genuine dialect difference in the *type*; the claim this tier can check
    is the *value*, and the string-typing claim belongs to the golden-SQL tier.
    """
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value))


def _keyed(
    rows: Sequence[dict[str, Any]], bucket_column: str, as_date: bool = False
) -> dict[tuple[Any, str], dict[str, Any]]:
    key = (lambda value: _as_date(value)) if as_date else (lambda value: value)
    return {(key(row[bucket_column]), row["carrier"]): row for row in rows}


def _run_case(
    connection: duckdb.DuckDBPyConnection, case: Case, registry: Registry = REGISTRY
) -> list[dict[str, Any]]:
    compiled = compile_case(registry, case, run_date=RUN_DATE)
    return query(connection, to_duckdb(compiled.sql))


# ======================================================================================
# Fan-out: the one-to-many join that doubles a SUM
# ======================================================================================

# The naive query, written the way an analyst reaches for it: put the carrier's fleet size
# next to the deliveries it made. It is not generated by the library, because the library
# refuses to generate it; it exists so the refusal below has something to be a refusal OF.
# Grouped by carrier name so it lines up column-for-column with the Case the library DOES
# accept, two tests down.
NAIVE_FAN_OUT_SQL = f"""
    SELECT c.carrier_name AS carrier_name, SUM(c.fleet_size) AS carrier_fleet_size
      FROM mart.deliveries AS d
      JOIN mart.carriers  AS c ON d.carrier_id = c.carrier_id
     WHERE d.dt = '{FAN_OUT_DAY}'
     GROUP BY c.carrier_name
"""

DELIVERED_ON_FAN_OUT_DAY: dict[str, int] = {
    _BY_ID[row.carrier_id].carrier_name: _BY_ID[row.carrier_id].fleet_size
    for row in DELIVERY_ROWS
    if row.dt == FAN_OUT_DAY
}
"""Fleet size of each carrier that delivered on FAN_OUT_DAY - the undoubled truth."""


def test_the_naive_join_really_does_double_the_sum(warehouse) -> None:
    """The companion test, without which the refusal test below proves nothing.

    Three carriers delivered on FAN_OUT_DAY, twice each. Joining deliveries to carriers to
    read `fleet_size` counts every carrier once per delivery, so every figure comes back at
    exactly twice its true value - 42 vehicles reported across three carriers that own 21.
    Nothing errors, no row count looks odd, and the numbers are plausible. That is the whole
    argument for a build-time refusal rather than a warning.
    """
    # Every carrier that delivered that day delivered exactly twice; that is what makes the
    # inflation an exact doubling rather than merely "too big".
    attempts = {
        carrier: sum(1 for row in DELIVERY_ROWS
                     if row.dt == FAN_OUT_DAY and _BY_ID[row.carrier_id].carrier_name == carrier)
        for carrier in DELIVERED_ON_FAN_OUT_DAY
    }
    assert set(attempts.values()) == {2}
    assert sum(DELIVERED_ON_FAN_OUT_DAY.values()) == 21

    inflated = {
        row["carrier_name"]: row["carrier_fleet_size"]
        for row in query(warehouse, NAIVE_FAN_OUT_SQL)
    }
    assert inflated == {
        carrier: 2 * fleet for carrier, fleet in DELIVERED_ON_FAN_OUT_DAY.items()
    }
    assert sum(inflated.values()) == 42


def test_library_refuses_the_case_that_would_produce_that_doubling() -> None:
    """The same question, asked of the library, is a build-time refusal.

    `carrier_deliveries` is declared ONE_TO_MANY out of `mart.carriers`, which is the only
    thing in the system that knows the join multiplies the rows `carrier_fleet_size` is
    measured over. Asserted on typed attributes rather than on the message, so rewording a
    refusal does not fail a test about arithmetic.
    """
    doubling = Case(
        name="fleet_size_by_delivery_day",
        metrics=by_name(fixture.CARRIER_FLEET_SIZE),
        grain=Grain.of(fixture.BY_DAY),
    )
    with pytest.raises(FanOut) as refused:
        compile_case(REGISTRY, doubling, run_date=RUN_DATE)

    assert refused.value.metric == "carrier_fleet_size"
    assert refused.value.measures == fixture.CARRIERS.qualified
    assert refused.value.join == "carrier_deliveries"
    assert refused.value.cardinality == "1:N"


def test_library_returns_the_undoubled_figure(warehouse) -> None:
    """And the Metric is not simply unusable: asked at a Grain it survives, it is right.

    A library that refused everything would pass the test above and be worthless. This asks
    for the same Metric across a carrier Dimension - no join, so no multiplication - and
    executes it. Same output columns as the naive query above, same three carriers, and
    every figure is exactly half of the naive one: these are the two numbers the refusal
    chooses between.
    """
    by_carrier = Case(
        name="fleet_by_carrier",
        metrics=by_name(fixture.CARRIER_FLEET_SIZE),
        grain=Grain.of(Dimension(fixture.CARRIERS.carrier_name)),
    )
    got = {
        row["carrier_name"]: row["carrier_fleet_size"]
        for row in _run_case(warehouse, by_carrier)
    }
    assert got == {carrier.carrier_name: carrier.fleet_size for carrier in CARRIER_ROWS}
    assert sum(got.values()) == 132

    inflated = {
        row["carrier_name"]: row["carrier_fleet_size"]
        for row in query(warehouse, NAIVE_FAN_OUT_SQL)
    }
    assert set(inflated) == set(DELIVERED_ON_FAN_OUT_DAY)
    for carrier, doubled in inflated.items():
        assert got[carrier] == doubled / 2
        assert got[carrier] != doubled


def test_many_to_one_join_leaves_a_spine_metric_undoubled(warehouse) -> None:
    """The safe direction of the same edge, checked rather than assumed.

    `accountable_by_day` really does join `mart.carriers` - it has to, the Grain reports
    `carrier_name` - so its `fees_charged` is only correct because the edge is walked
    MANY_TO_ONE into a lookup. Compared against the same sum computed with no join at all.
    If the refusal machinery were simply refusing every join, this test would go red.
    """
    compiled = compile_case(REGISTRY, fixture.ACCOUNTABLE_BY_DAY, run_date=RUN_DATE)
    assert "JOIN" in compiled.sql

    joined = _run_case(warehouse, fixture.ACCOUNTABLE_BY_DAY)
    per_carrier: dict[str, Decimal] = {}
    for row in joined:
        per_carrier[row["carrier"]] = (
            per_carrier.get(row["carrier"], Decimal("0.00")) + row["fees_charged"]
        )

    live = ", ".join(
        f"'{carrier.carrier_id}'" for carrier in CARRIER_ROWS if not carrier.is_test
    )
    unjoined = query(
        warehouse,
        f"""
        SELECT carrier_id, SUM(fee_amount) AS fees
          FROM mart.deliveries
         WHERE dt BETWEEN '{WINDOW[0]}' AND '{WINDOW[1]}'
           AND carrier_id IN ({live})
         GROUP BY carrier_id
        """,
    )
    assert per_carrier == {
        _BY_ID[row["carrier_id"]].carrier_name: row["fees"] for row in unjoined
    }


# ======================================================================================
# The Case, executed
# ======================================================================================


def test_daily_case_values_match_the_python_oracle(warehouse) -> None:
    """Every output column of `accountable_by_day`, against numbers computed by hand.

    This is the broadest assertion in the file and the cheapest one to break: it fails if
    the window Filter stops excluding 2026-09-10 and 2026-09-18, if `live_carriers` stops
    excluding the test carrier and its 1000.00 fee, if the conditional aggregate behind
    `failed_deliveries` turns into a WHERE and narrows its neighbours, if COUNT(DISTINCT)
    stops dropping the NULL courier, or if any output column swaps places with another.
    """
    rows = _run_case(warehouse, fixture.ACCOUNTABLE_BY_DAY)
    got = _keyed(rows, "dt_day")

    assert set(got) == set(EXPECTED_DAILY)
    for key, expected in EXPECTED_DAILY.items():
        actual = got[key]
        assert actual["active_couriers"] == expected["active_couriers"], key
        assert actual["delivery_attempts"] == expected["delivery_attempts"], key
        assert actual["failed_deliveries"] == expected["failed_deliveries"], key
        assert actual["fees_charged"] == expected["fees_charged"], key
        assert actual["failure_rate"] == pytest.approx(expected["failure_rate"]), key

    # Named explicitly, because "excluded" is the kind of thing an oracle can agree with by
    # being wrong in the same direction.
    assert Decimal("1000.00") not in {row["fees_charged"] for row in rows}
    assert all(row["dt_day"] not in ("2026-09-10", "2026-09-18") for row in rows)


def test_week_buckets_are_the_iso_monday(warehouse) -> None:
    """The WEEK bucket lands on the Monday of the row's own ISO week, Sunday included.

    The window spans a Friday-to-Sunday tail and a full Monday-to-Thursday head, so an
    off-by-one in `NEXT_DAY(..., 'MO') - 7` moves the weekend rows into the wrong bucket and
    every weekly total with them.
    """
    rows = _run_case(warehouse, fixture.ACCOUNTABLE_BY_WEEK)
    buckets = {_as_date(row["dt_week"]) for row in rows}
    assert buckets == {datetime.date(2026, 9, 7), datetime.date(2026, 9, 14)}
    assert _iso_monday("2026-09-13") == datetime.date(2026, 9, 7)
    assert _iso_monday("2026-09-14") == datetime.date(2026, 9, 14)


def test_day_to_week_regrain_totals_are_arithmetically_correct(warehouse) -> None:
    """Weekly totals equal the daily totals summed into their week. All of them.

    Read from the atomic Source at both Grains, so this checks the bucketing and the
    aggregation rather than any re-aggregation: COUNT rolls up by SUM (`delivery_attempts`),
    SUM rolls up by SUM (`fees_charged`), and COUNT(DISTINCT) does NOT - `active_couriers` is
    asserted to be strictly less than the sum of its days for two carriers, which is the
    arithmetic behind the refusal two tests below.
    """
    weekly = _keyed(_run_case(warehouse, fixture.ACCOUNTABLE_BY_WEEK), "dt_week", True)
    daily = _keyed(_run_case(warehouse, fixture.ACCOUNTABLE_BY_DAY), "dt_day")

    summed_days: dict[tuple[Any, str], dict[str, Any]] = {}
    for (day, carrier), row in daily.items():
        key = (_iso_monday(day), carrier)
        bucket = summed_days.setdefault(
            key,
            {"delivery_attempts": 0, "failed_deliveries": 0,
             "fees_charged": Decimal("0.00"), "active_couriers": 0},
        )
        for column in bucket:
            bucket[column] += row[column]

    assert set(weekly) == set(summed_days) == set(EXPECTED_WEEKLY)
    for key, expected in EXPECTED_WEEKLY.items():
        assert weekly[key]["delivery_attempts"] == expected["delivery_attempts"], key
        assert weekly[key]["failed_deliveries"] == expected["failed_deliveries"], key
        assert weekly[key]["fees_charged"] == expected["fees_charged"], key
        # The additive Metrics also equal the days summed, which is the re-grain claim.
        assert weekly[key]["delivery_attempts"] == summed_days[key]["delivery_attempts"]
        assert weekly[key]["fees_charged"] == summed_days[key]["fees_charged"]

    distinct_shrinks = [
        key
        for key in weekly
        if weekly[key]["active_couriers"] < summed_days[key]["active_couriers"]
    ]
    assert len(distinct_shrinks) >= 2, (
        "the fixture must contain couriers working more than one day in a week, or the "
        "COUNT(DISTINCT) refusal has nothing to refuse"
    )


def test_weekly_ratio_is_rederived_and_not_an_average_of_daily_rates(warehouse) -> None:
    """A ratio at a coarser Grain is numerator-over-denominator, not the mean of the parts.

    Aurora's week of 2026-09-14 is the case that makes the difference visible: two failures
    in five attempts is 0.4, while the mean of its three daily rates (0.5, 0.0, 1.0) is 0.5.
    Both are plausible percentages and only one is the failure rate.
    """
    weekly = _keyed(_run_case(warehouse, fixture.ACCOUNTABLE_BY_WEEK), "dt_week", True)
    daily = _keyed(_run_case(warehouse, fixture.ACCOUNTABLE_BY_DAY), "dt_day")

    for key, row in weekly.items():
        assert row["failure_rate"] == pytest.approx(
            row["failed_deliveries"] / row["delivery_attempts"]
        ), key

    key = (datetime.date(2026, 9, 14), "Aurora Logistics")
    daily_rates = [
        row["failure_rate"] for (day, carrier), row in daily.items()
        if carrier == "Aurora Logistics" and _iso_monday(day) == key[0]
    ]
    assert sorted(daily_rates) == pytest.approx([0.0, 0.5, 1.0])
    mean_of_rates = sum(daily_rates) / len(daily_rates)
    assert weekly[key]["failure_rate"] == pytest.approx(0.4)
    assert mean_of_rates == pytest.approx(0.5)
    assert weekly[key]["failure_rate"] != pytest.approx(mean_of_rates)


# ======================================================================================
# Reading back a written Source
# ======================================================================================


def _overwrite_partition(
    connection: duckdb.DuckDBPyConnection,
    statement: write.Statement,
    select_sql: str,
) -> None:
    """Stand in for `INSERT OVERWRITE TABLE ... PARTITION(...)`, which duckdb has no form of.

    duckdb has no partitions, so the Hive statement cannot be executed as written. What it
    means - replace exactly the named partition, leave every other one alone - is a DELETE
    of that partition followed by an INSERT, and that is what this does. The partition
    column and its rendered literal come from `statement.partition`, so the library still
    chooses which rows are replaced; only the mechanism is the harness's.
    """
    target = REGISTRY.source(statement.target or "")
    where = " AND ".join(
        f'"{column}" = {rendered}' for column, rendered in statement.partition
    )
    trailing = ", ".join(rendered for _, rendered in statement.partition)
    connection.execute(f'DELETE FROM "{target.db}"."{target.table}" WHERE {where}')
    connection.execute(
        f'INSERT INTO "{target.db}"."{target.table}" '
        f"SELECT *, {trailing} FROM ({select_sql})"
    )


def _materialise_daily(connection: duckdb.DuckDBPyConnection) -> write.Statement:
    statement = write.insert_overwrite(
        REGISTRY, fixture.ACCOUNTABLE_BY_DAY, run_date=RUN_DATE
    )
    compiled = compile_case(REGISTRY, fixture.ACCOUNTABLE_BY_DAY, run_date=RUN_DATE)
    _overwrite_partition(connection, statement, to_duckdb(compiled.sql))
    return statement


def test_written_columns_land_in_their_declared_positions(warehouse) -> None:
    """Hive matches INSERT columns by position, so a reordered SELECT is a wrong number.

    The SELECT is inserted positionally, exactly as Hive would, and then read back BY NAME
    and compared to the oracle. Swap any two output columns and this fails with fees in the
    attempts column rather than with a type error - `fees_charged` and `failure_rate` are
    the only pair whose types would even complain.
    """
    _materialise_daily(warehouse)
    stored = _keyed(
        query(warehouse, 'SELECT * FROM "mart"."delivery_health_daily"'), "dt_day"
    )

    assert set(stored) == set(EXPECTED_DAILY)
    for key, expected in EXPECTED_DAILY.items():
        assert stored[key]["delivery_attempts"] == expected["delivery_attempts"], key
        assert stored[key]["failed_deliveries"] == expected["failed_deliveries"], key
        assert stored[key]["active_couriers"] == expected["active_couriers"], key
        assert stored[key]["fees_charged"] == expected["fees_charged"], key
        assert stored[key]["failure_rate"] == pytest.approx(expected["failure_rate"]), key
        assert stored[key]["dt"] == RUN_DATE.isoformat(), key


def test_weekly_from_the_written_daily_equals_weekly_from_atomic_rows(warehouse) -> None:
    """The point of the whole write path: two ways to the same number, and they agree.

    `accountable_by_day` writes the daily table; `weekly_health_from_daily` re-grains out of
    it by SUM and re-derives its ratio from the re-aggregated parts. Every Metric in that
    family is checked against the same quantity computed straight off the atomic rows by
    `accountable_by_week`. If the re-grain machinery let through a rule it could not prove -
    an averaged ratio, a COUNT rolled up by COUNT - these two columns of numbers stop
    matching, and nothing else in the suite would notice.
    """
    _materialise_daily(warehouse)

    atomic = _keyed(_run_case(warehouse, fixture.ACCOUNTABLE_BY_WEEK), "dt_week", True)
    rolled = _keyed(
        _run_case(warehouse, fixture.WEEKLY_HEALTH_FROM_DAILY), "dt_day_week", True
    )

    assert set(rolled) == set(atomic)
    assert len(rolled) == 6
    for key in atomic:
        assert rolled[key]["weekly_delivery_attempts"] == atomic[key]["delivery_attempts"]
        assert rolled[key]["weekly_failed_deliveries"] == atomic[key]["failed_deliveries"]
        assert rolled[key]["weekly_fees_charged"] == atomic[key]["fees_charged"]
        assert rolled[key]["weekly_failure_rate"] == pytest.approx(
            atomic[key]["failure_rate"]
        ), key


def test_summing_a_stored_distinct_count_is_wrong_and_is_refused(warehouse) -> None:
    """The refusal, and the wrong number it prevents, in one test.

    `active_couriers` is written into the daily table as a COUNT(DISTINCT). Summing it up to
    weeks counts a courier once per day worked. The first half executes that sum and shows
    it disagreeing with the truth; the second half asks the library for the same thing and
    gets `UnsafeReAggregation`, naming the rule rather than the symptom.
    """
    _materialise_daily(warehouse)

    summed = query(
        warehouse,
        """
        SELECT carrier, SUM(active_couriers) AS summed
          FROM mart.delivery_health_daily
         WHERE dt_day BETWEEN '2026-09-14' AND '2026-09-17'
         GROUP BY carrier
        """,
    )
    truth = {
        carrier: EXPECTED_WEEKLY[(datetime.date(2026, 9, 14), carrier)]["active_couriers"]
        for carrier in ("Aurora Logistics", "Cedar Couriers")
    }
    got = {row["carrier"]: row["summed"] for row in summed}
    assert got["Aurora Logistics"] == 5 and truth["Aurora Logistics"] == 3
    assert got["Cedar Couriers"] == 3 and truth["Cedar Couriers"] == 2

    rolled_up = Case(
        name="active_couriers_by_week",
        metrics=by_name(fixture.STORED_ACTIVE_COURIERS),
        grain=Grain.of(fixture.WRITTEN_BY_WEEK, fixture.WRITTEN_BY_CARRIER),
    )
    with pytest.raises(UnsafeReAggregation) as refused:
        compile_case(REGISTRY, rolled_up, run_date=RUN_DATE)
    assert refused.value.metric == "stored_active_couriers"
    assert refused.value.rule == "NONE"


def test_overwriting_the_partition_twice_converges(warehouse) -> None:
    """Decision 5's reason for INSERT OVERWRITE: a retry must not double the numbers.

    The scheduler owns retries, so the library's only defence is the write mode. Running the
    same write twice leaves the table identical; the second half appends the same SELECT
    instead, and every stored figure doubles - which is what a retry would cost under
    INSERT INTO.
    """
    statement = _materialise_daily(warehouse)
    assert statement.partition == (("dt", f"'{RUN_DATE.isoformat()}'"),)
    first = query(
        warehouse, 'SELECT * FROM "mart"."delivery_health_daily" ORDER BY dt_day, carrier'
    )

    _materialise_daily(warehouse)
    again = query(
        warehouse, 'SELECT * FROM "mart"."delivery_health_daily" ORDER BY dt_day, carrier'
    )
    assert again == first

    target = REGISTRY.source(statement.target or "")
    compiled = compile_case(REGISTRY, fixture.ACCOUNTABLE_BY_DAY, run_date=RUN_DATE)
    warehouse.execute(
        f'INSERT INTO "{target.db}"."{target.table}" '
        f"SELECT *, '{RUN_DATE.isoformat()}' FROM ({to_duckdb(compiled.sql)})"
    )
    appended = query(
        warehouse,
        'SELECT SUM(delivery_attempts) AS attempts FROM "mart"."delivery_health_daily"',
    )
    before = sum(row["delivery_attempts"] for row in first)
    assert appended[0]["attempts"] == 2 * before


# ======================================================================================
# Literals
# ======================================================================================


def _one_carrier_case(value: str) -> Case:
    return Case(
        name="one_carrier",
        metrics=by_name(fixture.CARRIER_FLEET_SIZE),
        grain=Grain.of(Dimension(fixture.CARRIERS.carrier_name)),
        filters=(Filter("named", fixture.CARRIERS.carrier_name.eq(value)),),
    )


def test_an_awkward_literal_matches_its_row_and_nothing_else(warehouse) -> None:
    """A value containing both characters Hive escapes survives the round trip intact.

    Escaping that mangles a value is as wrong as escaping that fails: over-escaping returns
    no rows, under-escaping returns every row, and both are silent. The value here holds a
    single quote and a backslash, and the row it must find is the only one that carries them.
    """
    rows = _run_case(warehouse, _one_carrier_case("O'Hara & Co \\ Ltd"))
    assert rows == [{"carrier_name": "O'Hara & Co \\ Ltd", "carrier_fleet_size": 12}]


def test_an_injection_attempt_matches_nothing(warehouse) -> None:
    """The predicate stays a predicate: `' OR 1=1 --` is a name, not a disjunction.

    Executed rather than inspected, so the assertion is about rows and not about quoting: if
    the literal ever broke out of its string, the WHERE clause would become a tautology and
    all five carriers would come back. The library builds this from `exp.Literal.string` on
    an AST node, never from interpolated text; duckdb re-escapes the same node for itself,
    which is why the round trip is evidence for the discipline rather than for Hive's
    escaping specifically - that belongs to the escaping matrix.
    """
    rows = _run_case(warehouse, _one_carrier_case("' OR 1=1 --"))
    assert rows == []
    assert len(query(warehouse, "SELECT * FROM mart.carriers")) == len(CARRIER_ROWS)


# ======================================================================================
# The tier's own boundaries
# ======================================================================================


def test_core_never_imports_duckdb() -> None:
    """duckdb is a test dependency. The core is compile-only and connects to nothing.

    A source scan rather than a `sys.modules` check: an import that only happens inside a
    function would not show up in a freshly imported module, and it would still be an import.
    """
    package = Path(sqlcomposer.__file__).parent
    offenders = [
        path.name
        for path in sorted(package.glob("*.py"))
        if "duckdb" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


@pytest.mark.skip(
    reason="duckdb has no partitions, so Hive partition pruning has no observable "
    "behaviour here. Whether `dt = '2026-09-17'` prunes or scans needs a Hive EXPLAIN, "
    "not a row count - the reason Column.literal emits a bare literal instead of a CAST "
    "is unfalsifiable in this tier and is asserted textually in the golden-SQL tier."
)
def test_partition_pruning_is_not_observable_here() -> None:
    """Placeholder for the one claim this tier cannot check, kept visible rather than dropped.

    A Hive-backed tier would run EXPLAIN on `accountable_by_day` and assert the plan touches
    seven partitions rather than the whole table. Delete the skip marker when there is a Hive
    to run it against.
    """
    raise AssertionError("needs a Hive backend")
