"""Golden snapshots of the exact Hive text every fixture Case compiles to.

These are the refactor net. Nothing here asserts that a number is right - the refusal tests
and the value tests do that. What these assert is that a change nobody intended to make to
the emitted SQL cannot land silently: rename a Metric, reorder a Tag family, swap a bucket
mask, upgrade sqlglot, and the diff in review is the SQL itself rather than a paragraph in a
pull request claiming nothing changed.

Three things follow from that purpose and shape every test below.

**The expected SQL lives in this file, not beside it.** A `.sql` fixture directory turns a
behavioural change into a diff a reviewer has to go and find. Inline, the change and its
consequence are on one screen. `_sql()` exists only to make that inline form readable: the
library emits one very long line, and a one-line golden produces a one-line diff that no one
can read. Each golden is written as the chunks of that line, joined back with single spaces,
so the diff is per-clause while the comparison stays byte-exact.

**The goldens are written against the QUALIFIED tree.** `compile.qualify_gate` backtick-
quotes every identifier and aliases every table by its bare name before generation, so that
is the form the library emits and the form these snapshots must carry. Golden text without
backticks means somebody removed the resolution gate.

**Regenerating a golden is not the same as approving it.** The temptation with a snapshot
test is to re-run the generator and commit whatever comes out, at which point the snapshot
has stopped being evidence of anything. The final section of this module exists for that
moment. Those tests compile fresh SQL and assert the design claims the goldens happen to
encode - horizontal scaling by Tag and by Grain, bare literals on a Partition predicate,
determinism across hash seeds - so they fail when the library changes and keep failing after
someone re-records the text.
"""
from __future__ import annotations

import datetime
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import sqlglot
from sqlglot import exp

from declarations import deliveries
from sqlcomposer import compile as compiler
from sqlcomposer import write
from sqlcomposer.declaration import Registry

REPO_ROOT = Path(__file__).resolve().parent.parent

GOLDEN_RUN_DATE = datetime.date(2026, 9, 17)
"""Pinned here as well as in the `run_date` fixture, because a golden is only a golden
against a known date and a test that read the date from somewhere editable would drift with
it. The two must agree; `test_golden_run_date_matches_the_shared_fixture` checks that."""


def _sql(*chunks: str) -> str:
    """Join golden chunks back into the single line the library actually emits.

    The chunks are a presentation device and nothing else: `" ".join(chunks)` must reproduce
    the emitted SQL byte for byte, so a golden can only be written for SQL whose tokens are
    separated by exactly one space and which contains no newline. Every statement this
    library emits satisfies that - `compile.render` is one `.sql()` call with no `pretty=`.

    The guard below is the price of the convenience. Without it a chunk with a stray leading
    space, or an empty one, would silently insert a double space into the expected text and
    turn a real mismatch into a confusing one.
    """
    for index, chunk in enumerate(chunks):
        assert chunk, f"golden chunk {index} is empty"
        assert chunk == chunk.strip(), f"golden chunk {index} has edge whitespace: {chunk!r}"
    return " ".join(chunks)


# ======================================================================================
# The goldens.
#
# Six Cases, covering what the fixture was built to span: a single-Source Case
# (weekly_health_from_daily), a joined Case (accountable_by_day), a Case whose Join path is
# pinned with `via=` (failures_by_site_and_segment), both Grains of the day/week pair, and
# both Tag families.
# ======================================================================================

ACCOUNTABLE_BY_DAY_SQL = _sql(
    "SELECT DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd') AS `dt_day`,",
    "`carriers`.`carrier_name` AS `carrier`, COUNT(DISTINCT `deliveries`.`courier_id`) AS",
    "`active_couriers`, COUNT(*) AS `delivery_attempts`, SUM(CASE WHEN NOT",
    "`deliveries`.`failure_reason` IS NULL THEN 1 ELSE 0 END) AS `failed_deliveries`,",
    "SUM(CASE WHEN NOT `deliveries`.`failure_reason` IS NULL THEN 1 ELSE 0 END) /",
    "COUNT(*) AS `failure_rate`, SUM(`deliveries`.`fee_amount`) AS `fees_charged`",
    "FROM `mart`.`deliveries` AS `deliveries`",
    "INNER JOIN `mart`.`carriers` AS `carriers` ON `deliveries`.`carrier_id` =",
    "`carriers`.`carrier_id`",
    "WHERE `deliveries`.`dt` BETWEEN '2026-09-11' AND '2026-09-17' AND",
    "`carriers`.`is_test` = 0",
    "GROUP BY DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd'), `carriers`.`carrier_name`",
)

ACCOUNTABLE_BY_WEEK_SQL = _sql(
    "SELECT DATE_SUB(NEXT_DAY(DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd'), 'MO'), 7) AS",
    "`dt_week`, `carriers`.`carrier_name` AS `carrier`, COUNT(DISTINCT",
    "`deliveries`.`courier_id`) AS `active_couriers`, COUNT(*) AS `delivery_attempts`,",
    "SUM(CASE WHEN NOT `deliveries`.`failure_reason` IS NULL THEN 1 ELSE 0 END) AS",
    "`failed_deliveries`, SUM(CASE WHEN NOT `deliveries`.`failure_reason` IS NULL THEN 1",
    "ELSE 0 END) / COUNT(*) AS `failure_rate`, SUM(`deliveries`.`fee_amount`) AS",
    "`fees_charged`",
    "FROM `mart`.`deliveries` AS `deliveries`",
    "INNER JOIN `mart`.`carriers` AS `carriers` ON `deliveries`.`carrier_id` =",
    "`carriers`.`carrier_id`",
    "WHERE `deliveries`.`dt` BETWEEN '2026-09-11' AND '2026-09-17' AND",
    "`carriers`.`is_test` = 0",
    "GROUP BY DATE_SUB(NEXT_DAY(DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd'), 'MO'), 7),",
    "`carriers`.`carrier_name`",
)

OPERATIONAL_BY_DAY_SQL = _sql(
    "SELECT DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd') AS `dt_day`,",
    "`carriers`.`carrier_name` AS `carrier`, COUNT(*) AS `delivery_attempts`,",
    "MIN(`deliveries`.`promised_at`) AS `first_promised_at`,",
    "MAX(`deliveries`.`delivered_at`) AS `last_delivered_at`, SUM(CASE WHEN",
    "`deliveries`.`late_flag` = 1 THEN 1 ELSE 0 END) AS `late_deliveries`, SUM(CASE WHEN",
    "`deliveries`.`late_flag` = 1 THEN 1 ELSE 0 END) / COUNT(*) AS `late_rate`,",
    "SUM(`deliveries`.`scan_count`) AS `scan_events`",
    "FROM `mart`.`deliveries` AS `deliveries`",
    "INNER JOIN `mart`.`carriers` AS `carriers` ON `deliveries`.`carrier_id` =",
    "`carriers`.`carrier_id`",
    "WHERE `deliveries`.`dt` BETWEEN '2026-09-11' AND '2026-09-17' AND",
    "`carriers`.`is_test` = 0",
    "GROUP BY DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd'), `carriers`.`carrier_name`",
)

OPERATIONAL_BY_WEEK_SQL = _sql(
    "SELECT DATE_SUB(NEXT_DAY(DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd'), 'MO'), 7) AS",
    "`dt_week`, `carriers`.`carrier_name` AS `carrier`, COUNT(*) AS `delivery_attempts`,",
    "MIN(`deliveries`.`promised_at`) AS `first_promised_at`,",
    "MAX(`deliveries`.`delivered_at`) AS `last_delivered_at`, SUM(CASE WHEN",
    "`deliveries`.`late_flag` = 1 THEN 1 ELSE 0 END) AS `late_deliveries`, SUM(CASE WHEN",
    "`deliveries`.`late_flag` = 1 THEN 1 ELSE 0 END) / COUNT(*) AS `late_rate`,",
    "SUM(`deliveries`.`scan_count`) AS `scan_events`",
    "FROM `mart`.`deliveries` AS `deliveries`",
    "INNER JOIN `mart`.`carriers` AS `carriers` ON `deliveries`.`carrier_id` =",
    "`carriers`.`carrier_id`",
    "WHERE `deliveries`.`dt` BETWEEN '2026-09-11' AND '2026-09-17' AND",
    "`carriers`.`is_test` = 0",
    "GROUP BY DATE_SUB(NEXT_DAY(DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd'), 'MO'), 7),",
    "`carriers`.`carrier_name`",
)

FAILURES_BY_SITE_AND_SEGMENT_SQL = _sql(
    "SELECT DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd') AS `dt_day`, `sites`.`site_name`",
    "AS `destination_site`, `customers`.`segment` AS `segment`, COUNT(DISTINCT",
    "`deliveries`.`courier_id`) AS `active_couriers`, COUNT(*) AS `delivery_attempts`,",
    "SUM(CASE WHEN NOT `deliveries`.`failure_reason` IS NULL THEN 1 ELSE 0 END) AS",
    "`failed_deliveries`, SUM(CASE WHEN NOT `deliveries`.`failure_reason` IS NULL THEN 1",
    "ELSE 0 END) / COUNT(*) AS `failure_rate`, SUM(`deliveries`.`fee_amount`) AS",
    "`fees_charged`",
    "FROM `mart`.`deliveries` AS `deliveries`",
    "INNER JOIN `mart`.`customers` AS `customers` ON `deliveries`.`customer_id` =",
    "`customers`.`customer_id`",
    "INNER JOIN `mart`.`sites` AS `sites` ON `deliveries`.`destination_site_id` =",
    "`sites`.`site_id`",
    "WHERE `deliveries`.`dt` BETWEEN '2026-09-11' AND '2026-09-17'",
    "GROUP BY DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd'), `sites`.`site_name`,",
    "`customers`.`segment`",
)
"""No `AND NOT failure_reason IS NULL` in the WHERE clause, although the Case is about
failures. `failed_deliveries` is scoped by that same Filter, so narrowing the Case by it too
would make the conditional aggregate a tautology: `failed_deliveries` would equal
`delivery_attempts` and `failure_rate` would read 1.0 on every row. `ScopeCollision` refuses
that shape now; this golden is what the honest version looks like, with the denominator
still counting every attempt."""

WEEKLY_HEALTH_FROM_DAILY_SQL = _sql(
    "SELECT DATE_SUB(NEXT_DAY(DATE_FORMAT(`delivery_health_daily`.`dt_day`,",
    "'yyyy-MM-dd'), 'MO'), 7) AS `dt_day_week`, `delivery_health_daily`.`carrier` AS",
    "`carrier`, SUM(`delivery_health_daily`.`delivery_attempts`) AS",
    "`weekly_delivery_attempts`, SUM(`delivery_health_daily`.`failed_deliveries`) AS",
    "`weekly_failed_deliveries`, SUM(`delivery_health_daily`.`failed_deliveries`) /",
    "SUM(`delivery_health_daily`.`delivery_attempts`) AS `weekly_failure_rate`,",
    "SUM(`delivery_health_daily`.`fees_charged`) AS `weekly_fees_charged`",
    "FROM `mart`.`delivery_health_daily` AS `delivery_health_daily`",
    "WHERE `delivery_health_daily`.`dt` BETWEEN '2026-09-11' AND '2026-09-17'",
    "GROUP BY DATE_SUB(NEXT_DAY(DATE_FORMAT(`delivery_health_daily`.`dt_day`,",
    "'yyyy-MM-dd'), 'MO'), 7), `delivery_health_daily`.`carrier`",
)

ACCOUNTABLE_BY_DAY_INSERT_SQL = _sql(
    "INSERT OVERWRITE TABLE mart.delivery_health_daily PARTITION(dt = '2026-09-17')",
    "SELECT DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd') AS `dt_day`,",
    "`carriers`.`carrier_name` AS `carrier`, COUNT(DISTINCT `deliveries`.`courier_id`) AS",
    "`active_couriers`, COUNT(*) AS `delivery_attempts`, SUM(CASE WHEN NOT",
    "`deliveries`.`failure_reason` IS NULL THEN 1 ELSE 0 END) AS `failed_deliveries`,",
    "SUM(CASE WHEN NOT `deliveries`.`failure_reason` IS NULL THEN 1 ELSE 0 END) /",
    "COUNT(*) AS `failure_rate`, SUM(`deliveries`.`fee_amount`) AS `fees_charged`",
    "FROM `mart`.`deliveries` AS `deliveries`",
    "INNER JOIN `mart`.`carriers` AS `carriers` ON `deliveries`.`carrier_id` =",
    "`carriers`.`carrier_id`",
    "WHERE `deliveries`.`dt` BETWEEN '2026-09-11' AND '2026-09-17' AND",
    "`carriers`.`is_test` = 0",
    "GROUP BY DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd'), `carriers`.`carrier_name`",
)

READ_GOLDENS: dict[str, str] = {
    "accountable_by_day": ACCOUNTABLE_BY_DAY_SQL,
    "accountable_by_week": ACCOUNTABLE_BY_WEEK_SQL,
    "operational_by_day": OPERATIONAL_BY_DAY_SQL,
    "operational_by_week": OPERATIONAL_BY_WEEK_SQL,
    "failures_by_site_and_segment": FAILURES_BY_SITE_AND_SEGMENT_SQL,
    "weekly_health_from_daily": WEEKLY_HEALTH_FROM_DAILY_SQL,
}
"""Case name -> its golden SELECT. Keyed by name so
`test_every_declared_case_has_a_golden` can compare against the Registry: a Case added to
the fixture without a snapshot would otherwise never be reviewed as SQL at all."""


def _compiled_sql(registry: Registry, case_name: str, run_date: datetime.date) -> str:
    """Compile one named Case and return only its text. The whole read path, every time."""
    return compiler.compile_case(registry, registry.case(case_name), run_date=run_date).sql


# ======================================================================================
# One test per Case. Each is the snapshot plus the one structural fact that makes the
# snapshot worth having for that particular Case.
# ======================================================================================


def test_accountable_by_day_matches_golden(registry: Registry, run_date: datetime.date) -> None:
    """The joined Case: two Sources, two Case-level Filters, DAY bucket.

    Breaks on almost anything: a renamed Metric, a reordered Tag family (Metrics sort by
    name, so `active_couriers` must lead), a lost backtick from the resolution gate, a
    conditional aggregate that leaked into the WHERE clause, a join rendered as a comma
    join, or a `CAST` appearing around the Partition literals.
    """
    assert _compiled_sql(registry, "accountable_by_day", run_date) == ACCOUNTABLE_BY_DAY_SQL


def test_accountable_by_week_matches_golden(registry: Registry, run_date: datetime.date) -> None:
    """The same Case re-grained. The COUNT(DISTINCT) survives only because this Case reads
    the atomic Source; computed off the written daily table it would be refused, which is
    what `weekly_health_from_daily` is shaped to show.

    Breaks if the WEEK bucket stops anchoring to Monday - `NEXT_DAY(..., 'MO')` minus seven
    days is the anchoring, and an off-by-one there moves every weekly number by a day with
    no other visible symptom.
    """
    assert _compiled_sql(registry, "accountable_by_week", run_date) == ACCOUNTABLE_BY_WEEK_SQL


def test_operational_by_day_matches_golden(registry: Registry, run_date: datetime.date) -> None:
    """The second Tag family at the first Grain.

    `delivery_attempts` carries both Tags, so it appears in this golden and in
    `accountable_by_day`'s. That overlap is the point: the families are a selection, not a
    partition, and a change that turned `Registry.tagged` into a partition would drop this
    Metric from one of the two and be caught here.
    """
    assert _compiled_sql(registry, "operational_by_day", run_date) == OPERATIONAL_BY_DAY_SQL


def test_operational_by_week_matches_golden(registry: Registry, run_date: datetime.date) -> None:
    """The fourth corner of the square, reached by `variant()` twice over.

    Its value is action-at-a-distance: this Case names only a Grain, and everything else in
    its SQL is inherited from `accountable_by_day` through two `variant()` calls. An edit to
    the parent that nobody expected to reach here shows up in this diff.
    """
    assert _compiled_sql(registry, "operational_by_week", run_date) == OPERATIONAL_BY_WEEK_SQL


def test_failures_by_site_and_segment_matches_golden(
    registry: Registry, run_date: datetime.date
) -> None:
    """Three Sources over a Join path pinned by `via=`, and a Filter that narrows the Case.

    Two declared edges reach `mart.sites`, so this Case only compiles at all because
    `via=("delivery_customer", "delivery_destination_site")` names one. The golden pins
    which: the ON clause must read `destination_site_id = site_id`. Silently resolving to
    `delivery_origin_site` instead would still produce runnable SQL and entirely wrong rows,
    and that substitution is exactly what this snapshot catches.

    It also pins JOIN order, which `via=` deliberately does NOT decide: `via` is matched as
    a set, and a Join path's steps are ordered greedily by Join name among the edges whose
    near end has been reached. That is what gives one edge set exactly one spelling, so a
    golden
    does not move when a contributor reorders the names inside `via=`.
    """
    sql = _compiled_sql(registry, "failures_by_site_and_segment", run_date)
    assert sql == FAILURES_BY_SITE_AND_SEGMENT_SQL
    assert "`deliveries`.`origin_site_id`" not in sql


def test_weekly_health_from_daily_matches_golden(
    registry: Registry, run_date: datetime.date
) -> None:
    """The single-Source Case: no JOIN at all, reading the table `accountable_by_day` writes.

    Two facts this snapshot holds that no other does. There is no INNER JOIN in it, so a
    change that made `joins.resolve` return a spurious step would break it. And
    `weekly_failure_rate` is `SUM(failed) / SUM(attempts)` - the stored `failure_rate`
    column is never read. A re-derivation quietly replaced by `AVG(failure_rate)`, or by
    `SUM(failure_rate)`, is a well-formed query returning a wrong number, and the text is
    the only place it is visible.
    """
    sql = _compiled_sql(registry, "weekly_health_from_daily", run_date)
    assert sql == WEEKLY_HEALTH_FROM_DAILY_SQL
    assert "JOIN" not in sql
    assert "`delivery_health_daily`.`failure_rate`" not in sql


def test_accountable_by_day_insert_overwrite_matches_golden(
    registry: Registry, run_date: datetime.date
) -> None:
    """The write statement, which is the only other SQL surface the library emits.

    INSERT OVERWRITE into a dated Partition is what makes a scheduler retry converge instead
    of double-count, so the mode and the static `PARTITION(dt = '2026-09-17')` are both part
    of the contract rather than decoration. The partition literal is bare on purpose: a
    `CAST('2026-09-17' AS DATE)` there defeats Hive partition pruning on every subsequent
    read of the table, and `exp.convert` on a `date` produces exactly that CAST.

    The SELECT half is byte-identical to `accountable_by_day`'s golden, asserted below, so
    that a divergence between what a Case reports and what it writes cannot appear.
    """
    statement = write.insert_overwrite(
        registry, deliveries.ACCOUNTABLE_BY_DAY, run_date=run_date
    )
    assert statement.sql == ACCOUNTABLE_BY_DAY_INSERT_SQL
    assert statement.sql.endswith(ACCOUNTABLE_BY_DAY_SQL)
    assert statement.target == "mart.delivery_health_daily"
    assert statement.partition == (("dt", "'2026-09-17'"),)


# ======================================================================================
# Properties that hold across every golden.
# ======================================================================================


@pytest.mark.parametrize(
    ("case_name", "golden"), sorted(READ_GOLDENS.items()), ids=sorted(READ_GOLDENS)
)
def test_golden_parses_back_as_hive(
    registry: Registry, case_name: str, golden: str
) -> None:
    """Every golden survives a round trip through sqlglot's own Hive parser.

    The library generates SQL; it never reads it back. So generation could emit something
    structurally broken - an unbalanced backtick, a clause in the wrong place - and every
    equality assertion above would still pass, because the golden would have been
    regenerated from the same broken generator. Parsing with an independent front end is the
    check that the text is a Hive statement and not merely a string this library agrees with
    itself about.

    The output column names are re-read from the parsed tree rather than from the builder,
    which is what makes this more than a syntax check: `Case.output_names` is simultaneously
    the SELECT order and the INSERT column order, and Hive matches INSERT columns by
    position. If the emitted text ever stopped declaring the names the Case promises, a
    write into `mart.delivery_health_daily` would put every column in the wrong slot.

    Byte-exact re-rendering is deliberately NOT asserted. sqlglot 30.18.0 parses Hive
    `DATE_SUB(x, 7)` into `TsOrDsAdd` and regenerates it as `DATE_ADD(x, 7 * -1)`, so the
    week goldens do not survive a render/parse/render identity. That is sqlglot normalising
    its own input, not this library emitting something wrong.
    """
    parsed = sqlglot.parse_one(golden, dialect="hive")
    assert isinstance(parsed, exp.Select)
    assert tuple(parsed.named_selects) == registry.case(case_name).output_names(registry)


def test_insert_golden_parses_back_as_hive(registry: Registry) -> None:
    """The write golden, through the same independent front end.

    Separate from the parametrized test above because it must come back as an `exp.Insert`
    carrying an `exp.Partition`. An INSERT that parsed back as a bare SELECT would mean the
    overwrite was lost, and losing it turns a scheduler retry from converging into
    double-counting - the single failure mode write mode exists to prevent.

    The Partition is looked up with `find`, not read off `Insert.args["partition"]`: write.py
    builds the tree with the Partition on the Insert, and sqlglot 30.18.0 parses the same
    text back with it hanging off the target Table instead. Both render identically, so the
    asymmetry is sqlglot's business - but a test that assumed the builder's shape would fail
    for a reason that has nothing to do with this library.
    """
    parsed = sqlglot.parse_one(ACCOUNTABLE_BY_DAY_INSERT_SQL, dialect="hive")
    assert isinstance(parsed, exp.Insert)
    assert parsed.args.get("overwrite") is True
    partition = parsed.find(exp.Partition)
    assert partition is not None
    assert [predicate.sql(dialect="hive") for predicate in partition.expressions] == [
        "dt = '2026-09-17'"
    ]
    assert isinstance(parsed.expression, exp.Select)
    assert tuple(parsed.expression.named_selects) == deliveries.ACCOUNTABLE_BY_DAY.output_names(
        registry
    )


def test_every_declared_case_has_a_golden(registry: Registry) -> None:
    """A Case added to the fixture without a snapshot is a Case nobody reviews as SQL.

    The Registry scans module globals, so declaring a Case is a one-line edit with no
    registration step. That is the horizontal-scaling mechanism and it is also how a Case
    slips past this file. Comparing the two sets makes the omission a failure with the
    missing name in the message.
    """
    declared = {case.name for case in registry.cases()}
    assert declared == set(READ_GOLDENS), (
        f"cases without a golden: {sorted(declared - set(READ_GOLDENS))}; "
        f"goldens without a case: {sorted(set(READ_GOLDENS) - declared)}"
    )


def test_golden_run_date_matches_the_shared_fixture(run_date: datetime.date) -> None:
    """The date the goldens were taken against and the date the suite compiles with.

    Every golden carries `'2026-09-11'` and `'2026-09-17'` as literal text. If the shared
    fixture moved, every snapshot in this file would fail at once with a diff that looked
    like a library change rather than a fixture change. This test fails first, and says so.
    """
    assert run_date == GOLDEN_RUN_DATE


# ======================================================================================
# The claims the goldens encode.
#
# These compile fresh SQL rather than reading the constants above, which makes them fail
# twice over: immediately, when a library change breaks the claim, and again afterwards if
# someone regenerates the snapshots and commits the output. A snapshot test that is only
# ever re-recorded stops being evidence; these are what is left when that happens.
# ======================================================================================

_DAY_BUCKET = "DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd')"
_WEEK_BUCKET = "DATE_SUB(NEXT_DAY(DATE_FORMAT(`deliveries`.`dt`, 'yyyy-MM-dd'), 'MO'), 7)"


@pytest.mark.parametrize(
    ("day_case", "week_case"),
    [
        ("accountable_by_day", "accountable_by_week"),
        ("operational_by_day", "operational_by_week"),
    ],
    ids=["accountable", "operational"],
)
def test_day_and_week_cases_differ_only_by_the_time_bucket(
    registry: Registry, run_date: datetime.date, day_case: str, week_case: str
) -> None:
    """A re-grained Case costs exactly its difference, and the SQL proves it.

    `accountable_by_week` is declared as `accountable_by_day.variant(grain=...)` - four
    lines. The claim is that nothing else moves. Substituting the week bucket expression for
    the day one, and the alias with it, must turn one statement into the other character for
    character; any surviving difference is something `variant()` changed that nobody asked
    it to.

    Two failures this catches that an equality snapshot on its own does not name. A
    `variant()` that started inheriting or dropping a Filter would change only the week
    statement, and the rewrite would no longer land. And the substitution itself pins the
    WEEK bucket expression - `NEXT_DAY(..., 'MO')` less seven days is what anchors an ISO
    week to its Monday, and an off-by-one there moves every weekly number by a day with no
    other visible symptom.
    """
    day_sql = _compiled_sql(registry, day_case, run_date)
    week_sql = _compiled_sql(registry, week_case, run_date)
    assert _WEEK_BUCKET in week_sql
    rewritten = week_sql.replace(_WEEK_BUCKET, _DAY_BUCKET).replace("`dt_week`", "`dt_day`")
    assert rewritten == day_sql


@pytest.mark.parametrize(
    ("accountable_case", "operational_case"),
    [
        ("accountable_by_day", "operational_by_day"),
        ("accountable_by_week", "operational_by_week"),
    ],
    ids=["by_day", "by_week"],
)
def test_tag_families_differ_only_in_the_projected_metrics(
    registry: Registry,
    run_date: datetime.date,
    accountable_case: str,
    operational_case: str,
) -> None:
    """Swapping the Tag family changes the SELECT list and nothing else.

    A Case names a family, never a list, so that a newly declared Metric joins every Case
    asking for that family with no Case edited. The observable consequence is that two Cases
    differing only by Tag must produce identical FROM, JOIN, WHERE and GROUP BY clauses -
    the Grain and the Filters came from the same parent.

    A Metric-scoped `when` that leaked into the WHERE clause would break this immediately,
    which is the failure worth catching: `failed_deliveries` is ACCOUNTABLE-only and
    `late_deliveries` is OPERATIONAL-only, so a leak would narrow one family's rows and not
    the other's, and both Cases would keep returning plausible numbers.
    """
    marker = " FROM `mart`.`deliveries` AS `deliveries`"
    accountable_sql = _compiled_sql(registry, accountable_case, run_date)
    operational_sql = _compiled_sql(registry, operational_case, run_date)
    assert accountable_sql[accountable_sql.index(marker) :] == (
        operational_sql[operational_sql.index(marker) :]
    )


@pytest.mark.parametrize("case_name", sorted(READ_GOLDENS), ids=sorted(READ_GOLDENS))
def test_partition_predicates_carry_bare_literals(
    registry: Registry, run_date: datetime.date, case_name: str
) -> None:
    """No CAST reaches a Partition predicate, in any Case.

    `exp.convert(date(2026, 9, 17))` renders `CAST('2026-09-17' AS DATE)`, and that CAST
    inside a predicate on a Partition column defeats Hive partition pruning: the query still
    returns the right rows and reads the whole table. It is a performance failure that no
    number will ever reveal, which is why `Column.literal` special-cases a Partition column.

    Every Case in the fixture is filtered to a seven-day window on its Source's Partition
    column, so both halves of the assertion apply everywhere: the window is present, and it
    is present as two bare string literals.

    Scoped to the WHERE clause rather than the whole statement so a future Case that casts
    something in a projection does not have to edit this test.
    """
    sql = _compiled_sql(registry, case_name, run_date)
    where_clause = sql[sql.index(" WHERE ") : sql.index(" GROUP BY ")]
    assert "CAST(" not in where_clause
    assert "'2026-09-11'" in where_clause
    assert "'2026-09-17'" in where_clause


def test_write_partition_value_is_a_bare_literal(
    registry: Registry, run_date: datetime.date
) -> None:
    """The same rule on the write side, where getting it wrong is more expensive.

    A CAST in a WHERE clause costs one query a full scan. A CAST in the PARTITION clause of
    the statement that writes the table is baked into how the partition is named, and every
    later read of `mart.delivery_health_daily` pays for it.
    """
    statement = write.insert_overwrite(
        registry, deliveries.ACCOUNTABLE_BY_DAY, run_date=run_date
    )
    partition_clause = statement.sql[: statement.sql.index(" SELECT ")]
    assert "CAST(" not in partition_clause
    assert partition_clause.endswith("PARTITION(dt = '2026-09-17')")


_DETERMINISM_PROBE = textwrap.dedent(
    """
    import datetime, sys
    from declarations import REGISTRY
    from sqlcomposer import compile as compiler

    run_date = datetime.date.fromisoformat(sys.argv[1])
    for case in REGISTRY.cases():
        print(case.name, compiler.compile_case(REGISTRY, case, run_date=run_date).sql, sep="\\t")
    """
)
"""The child process's whole job. The run date arrives as argv rather than being written
into the source, so it cannot drift away from `GOLDEN_RUN_DATE` and leave this test
comparing two identical-but-wrong outputs against goldens taken on another day."""


def test_goldens_are_stable_across_hash_seeds() -> None:
    """The same Declarations compile to the same bytes in two differently seeded processes.

    The static Lineage artifact is a git-tracked file regenerated by a command and diffed in
    review, and the goldens in this file are the same bargain in miniature. Both are worth
    nothing if the emitted text depends on iteration order. It plausibly could: Cases,
    Metrics and Filters all expose their columns and Sources as `frozenset`, and a set of
    strings iterates in an order that changes with `PYTHONHASHSEED` between processes - not
    within one. So compiling twice in this process would prove nothing, and two subprocesses
    with pinned, different seeds is the cheapest thing that can actually fail.

    Both runs are also compared against the goldens, so a drift that happens to be stable
    across seeds still reports here rather than only in the per-Case tests.
    """
    outputs = []
    for seed in ("0", "425886"):
        # A copy of the real environment, not a bare dict: on Windows a child interpreter
        # started without SYSTEMROOT fails before it reaches the probe, and the failure
        # looks like a determinism failure rather than a broken test.
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(REPO_ROOT))
        completed = subprocess.run(
            [sys.executable, "-c", _DETERMINISM_PROBE, GOLDEN_RUN_DATE.isoformat()],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        outputs.append(dict(line.split("\t", 1) for line in completed.stdout.splitlines() if line))

    first, second = outputs
    assert first == second
    assert first == READ_GOLDENS
