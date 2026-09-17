"""Drift: what the warehouse did to the Declarations overnight, and what may break a build.

A Declaration is authoritative, which means it can be wrong. `verify` re-reads the
warehouse through an injected `Describe` - the core connects to nothing - and diffs. Two
properties decide whether the check survives contact with a real warehouse, and both are
what this module pins:

* SCOPED. Only a column some declared Case actually reaches can fail a build. A warehouse
  with four hundred columns per table drifts constantly in ways no Case cares about, and a
  check that blocks on all of them is a check somebody switches off in week two.
* CLASSIFIED. An added column is informational and never raises. A dropped or retyped
  column that a Case reads is a build-breaker - the retype being the worse of the two,
  because the Case keeps working and returns numbers that mean something else.

Every `Describe` here is synthetic: it starts from the Declaration itself and applies one
edit, so each test names exactly one difference and a failure says which. The Declarations
it reads are `declarations/`, the invented fixture - chosen over a hand-built Registry
because the scope question needs columns that really are unreferenced (`carrier_tier`,
`fleet_size`: no Case reports the CARRIER_PROFILE family) sitting next to columns several
Cases really do read.

One test here is a characterization test of a KNOWN HOLE rather than of a guarantee - see
`test_a_dropped_join_key_is_reported_but_not_classified_breaking`. It is written down
because the hole is silent, not because it is wanted.
"""
from __future__ import annotations

from typing import Callable, Mapping, Sequence

import pytest

from declarations import deliveries
from sqlcomposer.declaration import Registry, Source
from sqlcomposer.errors import BreakingDrift
from sqlcomposer.verify import (
    Describe,
    DriftKind,
    WarehouseColumn,
    cases_using,
    compare,
    referenced_columns,
    verify,
)

Edit = Callable[[list[WarehouseColumn]], list[WarehouseColumn]]


# ======================================================================================
# A synthetic warehouse: the Declarations, plus one deliberate difference
# ======================================================================================


def declared(source: Source) -> list[WarehouseColumn]:
    """What DESCRIBE would report if the warehouse still agreed with the Declaration."""
    return [
        WarehouseColumn(
            name=column.name,
            type=column.type,
            partition=column.partition,
            nullable=column.nullable,
        )
        for column in source.columns
    ]


def warehouse(edits: Mapping[str, Edit] | None = None) -> Describe:
    """A `Describe` that echoes the Declarations, with `edits` applied per `db.table`.

    Built this way round - start from the truth, apply one edit - so that every test
    contains exactly one difference and every assertion about "nothing else drifted" is
    checking something real rather than an incomplete hand-written column list.
    """
    applied = dict(edits or {})

    def describe(source: Source) -> Sequence[WarehouseColumn]:
        columns = declared(source)
        edit = applied.get(source.qualified)
        return edit(columns) if edit is not None else columns

    return describe


def drop(name: str) -> Edit:
    return lambda columns: [column for column in columns if column.name != name]


def retype(name: str, new_type: str) -> Edit:
    def edit(columns: list[WarehouseColumn]) -> list[WarehouseColumn]:
        return [
            WarehouseColumn(column.name, new_type, column.partition, column.nullable)
            if column.name == name
            else column
            for column in columns
        ]

    return edit


def add(column: WarehouseColumn) -> Edit:
    return lambda columns: columns + [column]


def departition(name: str) -> Edit:
    def edit(columns: list[WarehouseColumn]) -> list[WarehouseColumn]:
        return [
            WarehouseColumn(column.name, column.type, False, column.nullable)
            if column.name == name
            else column
            for column in columns
        ]

    return edit


def loosen_nullability(name: str) -> Edit:
    def edit(columns: list[WarehouseColumn]) -> list[WarehouseColumn]:
        return [
            WarehouseColumn(column.name, column.type, column.partition, True)
            if column.name == name
            else column
            for column in columns
        ]

    return edit


def only(report_items: Sequence[object]) -> object:
    """The single item, with the whole list in the failure message when there is not one."""
    assert len(report_items) == 1, [str(item) for item in report_items]
    return report_items[0]


# ======================================================================================
# The baseline. Without this one, every test below could be passing for the wrong reason.
# ======================================================================================


def test_a_warehouse_that_matches_the_declarations_reports_no_drift(registry: Registry) -> None:
    """Echoing the Declarations back must produce nothing at all - not "nothing breaking".

    If this fails, the fixture's `declared()` and the comparison disagree about something
    structural, and every classification assertion below is measuring that instead of what
    it claims to.
    """
    report = verify(registry, warehouse())

    assert report.items == ()
    assert report.clean
    assert report.to_text() == "no drift: every Declaration matches the warehouse"
    report.raise_if_breaking()


def test_describe_is_called_once_for_every_declared_source(registry: Registry) -> None:
    """The scope of the read is the Declarations, so a Source nobody looked at cannot be
    silently exempt from the check."""
    seen: list[str] = []
    echo = warehouse()

    def describe(source: Source) -> Sequence[WarehouseColumn]:
        seen.append(source.qualified)
        return echo(source)

    verify(registry, describe)

    assert sorted(seen) == sorted(source.qualified for source in registry.sources())
    assert len(seen) == len(set(seen))


# ======================================================================================
# An added column is informational
# ======================================================================================


def test_an_added_column_is_informational_and_never_breaks_a_build(registry: Registry) -> None:
    """Somebody added a column. No Case can reference it - a Case reaches a column only
    through a Declaration - so the only honest classification is "worth knowing"."""
    report = verify(
        registry,
        warehouse({"mart.deliveries": add(WarehouseColumn("parcel_weight_kg", "DOUBLE"))}),
    )
    item = only(report.items)

    assert item.kind is DriftKind.ADDED
    assert item.source == "mart.deliveries"
    assert item.column == "parcel_weight_kg"
    assert item.actual == "DOUBLE"
    assert item.referenced is False
    assert item.breaking is False
    assert report.breaking == ()
    assert not report.clean
    report.raise_if_breaking()


def test_an_addition_still_shows_up_in_the_report_text(registry: Registry) -> None:
    """The informational section is what earns the check its keep: it is where "somebody
    added the column you have been asking for" appears. A check that only ever says nothing
    or fails teaches people to ignore it."""
    report = verify(
        registry,
        warehouse({"mart.sites": add(WarehouseColumn("timezone", "STRING"))}),
    )
    text = report.to_text()

    assert "informational" in text
    assert "BREAKING" not in text
    assert "mart.sites.timezone" in text


# ======================================================================================
# A dropped or retyped column a Case depends on is a build-breaker
# ======================================================================================


def test_a_dropped_column_a_case_depends_on_is_a_build_breaker(registry: Registry) -> None:
    """`carrier_name` is the column behind the `carrier` Dimension of four Cases. Gone from
    the warehouse, every one of them fails at runtime - and the build is the cheaper place
    to find that out."""
    report = verify(
        registry, warehouse({"mart.carriers": drop("carrier_name")})
    )
    item = only(report.items)

    assert item.kind is DriftKind.DROPPED
    assert item.column == "carrier_name"
    assert item.declared == "STRING"
    assert item.actual is None
    assert item.referenced is True
    assert item.breaking is True
    assert "accountable_by_day" in item.used_by
    assert report.breaking == (item,)

    with pytest.raises(BreakingDrift) as refusal:
        report.raise_if_breaking()
    message = str(refusal.value)
    assert "mart.carriers.carrier_name" in message
    assert "accountable_by_day" in message


def test_a_retyped_column_a_case_depends_on_is_a_build_breaker(registry: Registry) -> None:
    """The worse of the two failures, and the reason a retype cannot be a warning: the SQL
    still runs. `SUM(fee_amount)` over a STRING column returns a number in Hive, and the
    money report keeps publishing it."""
    report = verify(
        registry, warehouse({"mart.deliveries": retype("fee_amount", "STRING")})
    )
    item = only(report.items)

    assert item.kind is DriftKind.RETYPED
    assert item.column == "fee_amount"
    assert item.declared == "DECIMAL(18,2)"
    assert item.actual == "STRING"
    assert item.breaking is True
    assert "accountable_by_day" in item.used_by

    with pytest.raises(BreakingDrift):
        report.raise_if_breaking()


def test_a_missing_source_is_breaking_and_does_not_hide_other_drift(
    registry: Registry,
) -> None:
    """One DESCRIBE that raises must not abort the other forty. The exception text is
    carried through because a permission error and a dropped table look identical here and
    only the message tells them apart."""
    def describe(source: Source) -> Sequence[WarehouseColumn]:
        if source.qualified == "mart.deliveries":
            raise RuntimeError("Table or view not found: mart.deliveries")
        return warehouse({"mart.sites": add(WarehouseColumn("timezone", "STRING"))})(source)

    report = verify(registry, describe)
    missing = [item for item in report.items if item.kind is DriftKind.SOURCE_MISSING]
    elsewhere = [item for item in report.items if item.kind is DriftKind.ADDED]

    assert len(missing) == 1
    assert missing[0].source == "mart.deliveries"
    assert missing[0].column is None
    assert "Table or view not found" in (missing[0].actual or "")
    assert missing[0].breaking is True
    assert elsewhere and elsewhere[0].column == "timezone"


def test_a_column_that_stops_being_a_partition_column_is_a_build_breaker(
    registry: Registry,
) -> None:
    """The query keeps working and quietly scans the whole table, and the literal format
    the composer renders for that column is no longer the pruning-safe one."""
    report = verify(registry, warehouse({"mart.deliveries": departition("dt")}))
    item = only(report.items)

    assert item.kind is DriftKind.PARTITIONING_CHANGED
    assert (item.declared, item.actual) == ("partition", "not partition")
    assert item.breaking is True
    assert "accountable_by_day" in item.used_by


def test_a_nullability_change_is_reported_but_never_breaks_a_build(registry: Registry) -> None:
    """A generated Declaration reports almost everything nullable and the annotation that
    tightens it is a hand edit, so a nullability diff is the one field the warehouse is
    least authoritative about. Reported, never raised."""
    report = verify(
        registry, warehouse({"mart.carriers": loosen_nullability("carrier_name")})
    )
    item = only(report.items)

    assert item.kind is DriftKind.NULLABILITY_CHANGED
    assert (item.declared, item.actual) == ("not nullable", "nullable")
    assert item.referenced is True, "carrier_name IS read by a Case"
    assert item.breaking is False, "...and a nullability change still must not break"
    report.raise_if_breaking()


# ======================================================================================
# Scope: a change to a column no Case references is noise
# ======================================================================================


def test_a_dropped_column_no_case_references_is_not_a_build_breaker(registry: Registry) -> None:
    """`carrier_tier` is declared and nothing reports it - no Case asks for the
    CARRIER_PROFILE family. The same DROPPED kind that breaks the build for `carrier_name`
    must not break it here, or the check blocks on every unrelated schema change and gets
    switched off."""
    assert "carrier_tier" not in referenced_columns(registry).get("mart.carriers", frozenset())

    report = verify(registry, warehouse({"mart.carriers": drop("carrier_tier")}))
    item = only(report.items)

    assert item.kind is DriftKind.DROPPED, "the drop is still reported"
    assert item.referenced is False
    assert item.used_by == ()
    assert item.breaking is False
    assert report.breaking == ()
    assert "informational" in report.to_text()
    report.raise_if_breaking()


def test_a_retyped_column_no_case_references_is_not_a_build_breaker(registry: Registry) -> None:
    """Same edit, same kind, opposite verdict from the referenced case above: the only
    difference is whether a Case reads the column. That difference IS the scope rule."""
    unreferenced = verify(
        registry, warehouse({"mart.carriers": retype("fleet_size", "INT")})
    )
    referenced = verify(
        registry, warehouse({"mart.carriers": retype("is_test", "STRING")})
    )

    assert only(unreferenced.items).kind is DriftKind.RETYPED
    assert only(unreferenced.items).breaking is False
    assert only(referenced.items).kind is DriftKind.RETYPED
    assert only(referenced.items).breaking is True
    assert "accountable_by_day" in only(referenced.items).used_by


def test_the_scope_is_the_columns_declared_cases_actually_reach(registry: Registry) -> None:
    """Metric columns, Grain columns and Filter columns - resolved through the Tag family,
    so a Metric that joined a family today widens the scope today with no Case edited."""
    scope = referenced_columns(registry)

    assert "fee_amount" in scope["mart.deliveries"], "a Metric column"
    assert "dt" in scope["mart.deliveries"], "a Grain and Filter column"
    assert "is_test" in scope["mart.carriers"], "a Filter column"
    assert "fleet_size" not in scope["mart.carriers"], "CARRIER_PROFILE: no Case reports it"
    assert cases_using(registry, deliveries.DELIVERIES.fee_amount) == (
        "accountable_by_day",
        "accountable_by_week",
        "failures_by_site_and_segment",
    )
    assert cases_using(registry, deliveries.CARRIERS.fleet_size) == ()


def test_a_dropped_join_key_is_reported_but_not_classified_breaking(registry: Registry) -> None:
    """A KNOWN HOLE, written down rather than wanted.

    `Case.referenced_columns` is Metric, Grain and Filter columns; it does NOT include Join
    keys, although every Case whose Join path is walked reaches them. So dropping
    `carrier_id` - which every carrier join is keyed on - is reported as informational, and
    a build that only fails on `breaking` items goes green on a change that breaks four
    Cases at runtime.

    If this test starts failing because the item became breaking, that is an improvement:
    delete the test, do not widen the assertion.
    """
    report = verify(registry, warehouse({"mart.carriers": drop("carrier_id")}))
    item = only(report.items)

    assert item.kind is DriftKind.DROPPED
    assert item.column == "carrier_id"
    assert item.referenced is False
    assert item.breaking is False


# ======================================================================================
# Comparison details that decide whether the report is signal or noise
# ======================================================================================


def test_two_spellings_of_one_type_are_not_drift(registry: Registry) -> None:
    """`decimal(18, 2)` and `DECIMAL(18,2)` are the same type, and a report that flags them
    every morning is a report nobody reads."""
    respelled = verify(
        registry, warehouse({"mart.deliveries": retype("fee_amount", "decimal(18, 2)")})
    )

    assert respelled.clean


def test_a_genuinely_different_type_is_still_drift(registry: Registry) -> None:
    """The guard on the normaliser above: folding case and whitespace must not fold two
    different types onto one string."""
    report = verify(
        registry, warehouse({"mart.deliveries": retype("fee_amount", "DECIMAL(9,2)")})
    )

    assert only(report.items).kind is DriftKind.RETYPED


def test_a_partition_column_listed_twice_by_describe_is_not_drift(registry: Registry) -> None:
    """Hive's plain DESCRIBE lists a Partition column twice - once in the column list and
    once under `# Partition Information` - and the second entry usually does not say it is
    a Partition column. Taking the last entry produces a spurious PARTITIONING_CHANGED on
    `mart.deliveries.dt` every single run, which is exactly the noise that gets a drift
    check disabled.
    """
    def describe(source: Source) -> Sequence[WarehouseColumn]:
        columns = declared(source)
        repeated = [
            WarehouseColumn(column.name, column.type, False, column.nullable)
            for column in columns
            if column.partition
        ]
        return columns + repeated

    assert verify(registry, describe).clean


def test_one_column_changed_two_ways_produces_two_findings(registry: Registry) -> None:
    """A column that was both retyped and de-partitioned is two facts. Collapsing them
    would hide whichever one the reader happened to care about."""
    report = verify(
        registry,
        warehouse(
            {
                "mart.deliveries": lambda columns: departition("dt")(
                    retype("dt", "DATE")(columns)
                )
            }
        ),
    )

    assert {item.kind for item in report.items} == {
        DriftKind.RETYPED,
        DriftKind.PARTITIONING_CHANGED,
    }
    assert all(item.breaking for item in report.items)


def test_compare_diffs_one_source_without_reading_the_warehouse(registry: Registry) -> None:
    """The unit underneath `verify`: hand it a column list and it reports the difference,
    which is how a contributor checks one table without a connection."""
    items = compare(
        registry,
        deliveries.SITES,
        [WarehouseColumn("site_id", "STRING", nullable=False)],
    )

    assert [(item.kind, item.column) for item in items] == [
        (DriftKind.DROPPED, "country"),
        (DriftKind.DROPPED, "region"),
        (DriftKind.DROPPED, "site_name"),
    ]
    assert [item.breaking for item in items] == [False, False, True]


def test_the_report_is_ordered_and_groups_breaking_findings_first(registry: Registry) -> None:
    """A drift report is read by a human under time pressure, and re-read tomorrow against
    yesterday's. Source-then-column order makes it diffable; breaking-first makes it
    actionable."""
    report = verify(
        registry,
        warehouse(
            {
                "mart.carriers": drop("carrier_name"),
                "mart.sites": add(WarehouseColumn("timezone", "STRING")),
                "mart.deliveries": retype("fee_amount", "STRING"),
            }
        ),
    )
    text = report.to_text()

    assert [(item.source, item.column) for item in report.breaking] == [
        ("mart.carriers", "carrier_name"),
        ("mart.deliveries", "fee_amount"),
    ]
    assert text.index("BREAKING") < text.index("informational")
    assert text.index("mart.deliveries.fee_amount") < text.index("mart.sites.timezone")
    assert "drift: 3 item(s), 2 breaking" in text

    with pytest.raises(BreakingDrift) as refusal:
        report.raise_if_breaking()
    message = str(refusal.value)
    assert "mart.carriers" in message and "mart.deliveries" in message
