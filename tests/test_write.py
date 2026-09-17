"""The write path: an ordered plan whose statements a retry can safely repeat.

What this module is defending, in the order the tests appear:

* ORDER. `plan()` emits a list an execution script runs top to bottom. A Case that reads a
  Source another Case in the same plan writes MUST come after it, or the reader computes
  its numbers from yesterday's partition and nothing anywhere reports a problem. The
  fixture below is built so that the correct order is neither the input order nor the
  alphabetical order - both of those are wrong here, so a test that passes is evidence of
  a real topological sort rather than of an accident.

* IDEMPOTENCE. Write mode is INSERT OVERWRITE into a dated Partition. That is the whole
  reason a scheduler retry converges instead of double-counting, and it only holds if the
  second emission of the same plan targets the same Partition with the same statements. So
  the identity is asserted twice: within one process, and across two processes started
  with different PYTHONHASHSEED values - the cheap way to catch a plan whose order comes
  from set iteration and would therefore differ between two runs of the same scheduler.

* EXACT TEXT. One golden INSERT OVERWRITE, asserted whole. The partition literal is a bare
  `'2026-01-02'` and not a `CAST(... AS DATE)`, because a CAST in a Hive PARTITION clause
  defeats partition pruning on every subsequent read of the table. That is the kind of
  regression that costs money without ever failing.

* REFUSALS. A Partition column left without a value, one whose declared type cannot hold
  the run date, two Cases writing one Source, one Case listed twice, and a dependency cycle
  each raise. Every one of them otherwise produces a plausible wrong number rather than an
  error. The duplicate-Case refusal is asserted on its SUBJECT, because the two-writers
  check refuses the same list one line later and either raise could otherwise be deleted
  unnoticed.

The Sources declared here are a second INVENTED FIXTURE, deliberately smaller than
`declarations/` so the golden SQL fits on a line and so the Case names can be chosen to
make the ordering test discriminating. They describe no real warehouse.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from sqlcomposer.declaration import Column, Registry, RunDate, Source
from sqlcomposer.errors import (
    InvalidDeclaration,
    LiteralTypeMismatch,
    RegistryNotFrozen,
)
from sqlcomposer.model import Case, Grain, by_name, count_rows, sum_of
from sqlcomposer.write import (
    Statement,
    StatementKind,
    create_table_as,
    insert_overwrite,
    partition_values,
    plan,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

RUN_DATE = date(2026, 1, 2)
"""Fixed, because the golden SQL names it. A test that took `date.today()` would render a
different Partition every day and could only ever assert its own arithmetic back."""


# ======================================================================================
# INVENTED FIXTURE. No warehouse anywhere looks like this.
# ======================================================================================

SALES = Source(
    db="raw",
    table="sales",
    one_row_per="order line",
    columns=(
        Column("region", "STRING", nullable=False),
        Column("amount", "DECIMAL(18,2)", nullable=False),
        Column("dt", "STRING", partition=True, nullable=False, note="yyyy-MM-dd"),
    ),
)

SALES_DAILY = Source(
    db="mart",
    table="sales_daily",
    written_by="z_write_sales_daily",
    columns=(
        # These non-Partition columns, in this order, ARE the writing Case's output names:
        # Grain first, then Metrics sorted by name. Hive matches INSERT columns by
        # position, so the order is the contract `insert_overwrite` checks.
        Column("region", "STRING", nullable=False),
        Column("amount_total", "DECIMAL(18,2)"),
        Column("orders", "BIGINT"),
        Column("dt", "STRING", partition=True, nullable=False),
    ),
)

AMOUNT_TOTAL = sum_of("amount_total", SALES.amount)
ORDERS = count_rows("orders", SALES)
ROLLED_AMOUNT = sum_of("rolled_amount", SALES_DAILY.amount_total)

WRITE_CASE = Case(
    name="z_write_sales_daily",
    metrics=by_name(AMOUNT_TOTAL, ORDERS),
    grain=Grain.of(SALES.region),
    writes_to=SALES_DAILY,
)
"""Named to sort LAST. It has to run FIRST, because `a_read_sales_daily` reads the table it
writes - which is what makes the ordering test able to fail."""

READ_CASE = Case(
    name="a_read_sales_daily",
    metrics=by_name(ROLLED_AMOUNT),
    grain=Grain.of(SALES_DAILY.region),
)
"""Named to sort FIRST, and depends on the write. Must come out of `plan()` last."""

STANDALONE_CASE = Case(
    name="m_standalone",
    metrics=by_name(AMOUNT_TOTAL),
    grain=Grain.of(SALES.region),
)
"""Depends on nothing and writes nothing: the free statement whose position pins the
tie-break rule. Sorting between the other two by name, it must come out first."""

SECOND_WRITER = Case(
    name="b_also_writes_sales_daily",
    metrics=by_name(AMOUNT_TOTAL, ORDERS),
    grain=Grain.of(SALES.region),
    writes_to=SALES_DAILY,
)
"""A second Case pointed at the same target, deliberately NOT added to the Registry.

`freeze()` checks the write->read link in both directions, so registering this beside
`WRITE_CASE` is refused there - `mart.sales_daily` names only one producer and a Source
cannot name two. That refusal is asserted in tests/test_registry.py. What is left for
`write.plan` to catch is the same mistake arriving from outside the Registry, which it can,
because `plan()` takes a list of Cases and never requires them to be registered."""

SALES_REGISTRY = (
    Registry(name="test_write-fixture")
    .add(
        SALES,
        SALES_DAILY,
        AMOUNT_TOTAL,
        ORDERS,
        ROLLED_AMOUNT,
        WRITE_CASE,
        READ_CASE,
        STANDALONE_CASE,
    )
    .freeze()
)

GOLDEN_INSERT = (
    "INSERT OVERWRITE TABLE mart.sales_daily PARTITION(dt = '2026-01-02') "
    "SELECT `sales`.`region` AS `region`, SUM(`sales`.`amount`) AS `amount_total`, "
    "COUNT(*) AS `orders` FROM `raw`.`sales` AS `sales` GROUP BY `sales`.`region`"
)
"""The whole statement, asserted whole. The asymmetry - a bare `mart.sales_daily` target
next to a backtick-quoted SELECT - is real and documented: `qualify()` runs on the SELECT
only."""


# ======================================================================================
# The plan is ordered
# ======================================================================================


def test_plan_runs_a_writer_before_the_case_that_reads_what_it_wrote() -> None:
    """The dependency order, against a fixture where no simpler rule gives the same answer.

    Alphabetical would be (a_read, b/m_standalone, z_write) and input order is whatever the
    caller passed. Only a topological sort puts z_write_sales_daily before
    a_read_sales_daily, and only that order gives the reader today's numbers.
    """
    statements = plan(
        SALES_REGISTRY, [READ_CASE, WRITE_CASE, STANDALONE_CASE], run_date=RUN_DATE
    ).statements
    purposes = [statement.purpose for statement in statements]

    assert [statement.target for statement in statements] == [
        None,
        "mart.sales_daily",
        None,
    ], purposes
    assert "m_standalone" in purposes[0]
    assert "z_write_sales_daily" in purposes[1]
    assert "a_read_sales_daily" in purposes[2]


def test_plan_order_does_not_depend_on_the_order_the_cases_were_passed() -> None:
    """Two contributors listing the same Cases differently must get the same script.

    The list a caller passes is a set of questions, not a schedule; if it were load-bearing
    then the correctness of the numbers would depend on the order somebody typed.
    """
    forwards = plan(
        SALES_REGISTRY, [READ_CASE, WRITE_CASE, STANDALONE_CASE], run_date=RUN_DATE
    )
    backwards = plan(
        SALES_REGISTRY, [STANDALONE_CASE, WRITE_CASE, READ_CASE], run_date=RUN_DATE
    )

    assert [statement.sql for statement in forwards] == [
        statement.sql for statement in backwards
    ]


def test_plan_iterates_and_counts_as_the_ordered_list_it_is() -> None:
    """`for statement in plan` is the documented way to run one, so it must yield the
    statements in plan order and `len()` must agree with what iteration produces."""
    built = plan(SALES_REGISTRY, [READ_CASE, WRITE_CASE, STANDALONE_CASE], run_date=RUN_DATE)

    assert tuple(built) == built.statements
    assert len(built) == 3
    assert all(isinstance(statement, Statement) for statement in built)


def test_to_script_keeps_plan_order_and_comments_every_statement() -> None:
    """The script is what gets pasted into a scheduler, so a reordering there would undo
    the ordering guarantee even with the plan itself correct."""
    built = plan(SALES_REGISTRY, [READ_CASE, WRITE_CASE, STANDALONE_CASE], run_date=RUN_DATE)
    script = built.to_script()

    positions = [script.index(statement.sql) for statement in built]
    assert positions == sorted(positions)
    assert script.count(";") >= len(built)
    for statement in built:
        assert f"-- {statement.purpose}" in script


def test_an_empty_plan_renders_as_an_empty_script() -> None:
    """Written to a file, a lone newline looks like a script that contains something."""
    assert plan(SALES_REGISTRY, [], run_date=RUN_DATE).to_script() == ""


def test_a_case_that_writes_nothing_is_a_plain_select() -> None:
    """A plan can end with the query whose numbers a human actually wants."""
    (statement,) = plan(SALES_REGISTRY, [STANDALONE_CASE], run_date=RUN_DATE).statements

    assert statement.kind is StatementKind.SELECT
    assert statement.target is None
    assert statement.partition == ()
    assert statement.sql.startswith("SELECT ")


# ======================================================================================
# The default write mode, and the exact text of it
# ======================================================================================


def test_default_write_mode_is_insert_overwrite_into_a_dated_partition() -> None:
    """The default with no `partition=` argument: OVERWRITE, of the run date's Partition.

    `INSERT INTO` here would double-count on every retry and look identical in every log.
    """
    (statement,) = plan(SALES_REGISTRY, [WRITE_CASE], run_date=RUN_DATE).statements

    assert statement.kind is StatementKind.INSERT_OVERWRITE
    assert statement.target == "mart.sales_daily"
    assert statement.partition == (("dt", "'2026-01-02'"),)
    assert statement.sql.startswith(
        "INSERT OVERWRITE TABLE mart.sales_daily PARTITION(dt = '2026-01-02') SELECT "
    )
    assert "INSERT INTO" not in statement.sql


def test_insert_overwrite_renders_exactly_this_hive_text() -> None:
    """The golden statement. Any change to quoting, column order or the PARTITION clause
    lands here first, where it is a diff a reviewer reads rather than a number that moved."""
    assert insert_overwrite(SALES_REGISTRY, WRITE_CASE, run_date=RUN_DATE).sql == GOLDEN_INSERT


def test_the_partition_literal_is_bare_and_never_a_cast() -> None:
    """A `CAST('2026-01-02' AS DATE)` in a PARTITION clause defeats pruning on every later
    read of the table - the query still returns the right answer, at full-table cost.

    The second assertion is what stops this test being a tautology: the obvious way to
    render a `date` DOES produce a CAST, so the composer is actively avoiding it.
    """
    from sqlglot import exp

    statement = insert_overwrite(SALES_REGISTRY, WRITE_CASE, run_date=RUN_DATE)
    partition_clause = statement.sql[: statement.sql.index(" SELECT ")]

    assert "CAST" not in partition_clause
    assert partition_clause.endswith("PARTITION(dt = '2026-01-02')")
    assert "CAST" in exp.convert(RUN_DATE).sql(dialect="hive")


def test_partition_values_report_what_a_retry_would_replace() -> None:
    """An operator's question is "what does re-running this destroy", and the answer has to
    be available without parsing the SQL back."""
    assert partition_values(SALES_REGISTRY, WRITE_CASE, run_date=RUN_DATE) == (
        ("dt", RUN_DATE),
    )


def test_an_override_moves_the_partition_in_both_the_spec_and_the_sql() -> None:
    """`partition=` and the emitted statement cannot be allowed to disagree about which
    Partition is being overwritten - a backfill would report replacing one day and replace
    another."""
    statement = insert_overwrite(
        SALES_REGISTRY, WRITE_CASE, run_date=RUN_DATE, partition={"dt": RunDate() - 1}
    )

    assert statement.partition == (("dt", "'2026-01-01'"),)
    assert "PARTITION(dt = '2026-01-01')" in statement.sql
    assert "'2026-01-02'" not in statement.sql


def test_a_partition_value_that_cannot_inhabit_its_column_refuses() -> None:
    """`dt` is declared STRING holding yyyy-MM-dd. An int compared to it is NULL in Hive
    and the write silently lands in a Partition nobody asked for."""
    with pytest.raises(LiteralTypeMismatch):
        insert_overwrite(
            SALES_REGISTRY, WRITE_CASE, run_date=RUN_DATE, partition={"dt": 20260102}
        )


def test_create_table_as_is_not_the_write_path() -> None:
    """CTAS exists for creating an intermediate Source the first time. It is not idempotent
    - a retry fails on the existing table - so it must never carry a PARTITION clause that
    would make it look like the repeatable write."""
    statement = create_table_as(SALES_REGISTRY, WRITE_CASE, run_date=RUN_DATE)

    assert statement.kind is StatementKind.CTAS
    assert statement.sql.startswith("CREATE TABLE mart.sales_daily AS SELECT ")
    assert "PARTITION" not in statement.sql
    assert statement.partition == ()


# ======================================================================================
# Idempotence: the property that makes a scheduler retry converge
# ======================================================================================


def test_emitting_the_same_plan_twice_produces_identical_statements() -> None:
    """The property the whole write mode rests on.

    A retry converges only because the second emission overwrites exactly the Partition the
    first one wrote. If two emissions of one plan could differ - in statement order, in
    column order, in the Partition targeted - then a retry would be a different write, and
    INSERT OVERWRITE would stop being a safety property and become a way to lose data.
    """
    cases = [READ_CASE, WRITE_CASE, STANDALONE_CASE]
    first = plan(SALES_REGISTRY, cases, run_date=RUN_DATE)
    second = plan(SALES_REGISTRY, cases, run_date=RUN_DATE)

    assert first.statements == second.statements
    assert first.to_script() == second.to_script()
    assert [manifest.source for manifest in first.manifests] == [
        manifest.source for manifest in second.manifests
    ]


def test_a_retry_targets_the_same_partition_and_a_new_run_date_does_not() -> None:
    """Same run date, same Partition: the retry replaces its own rows. Different run date,
    different Partition: yesterday's numbers survive.

    The second half is what makes the first half meaningful - a `partition` field that was
    simply constant would satisfy the first assertion and be useless.
    """
    today = insert_overwrite(SALES_REGISTRY, WRITE_CASE, run_date=RUN_DATE)
    retry = insert_overwrite(SALES_REGISTRY, WRITE_CASE, run_date=RUN_DATE)
    tomorrow = insert_overwrite(SALES_REGISTRY, WRITE_CASE, run_date=date(2026, 1, 3))

    assert retry == today
    assert tomorrow.partition == (("dt", "'2026-01-03'"),)
    assert tomorrow.sql != today.sql


def test_the_plan_is_identical_across_processes_with_different_hash_seeds() -> None:
    """Two runs of one scheduler must emit the same script, not merely two calls in one
    process.

    The library resolves Tag families, Join paths and `Case.sources()` through sets, and a
    set of strings iterates in an order that depends on PYTHONHASHSEED. An ordering that
    leaked from one would be invisible to every in-process assertion above and would show
    up as a plan that differs between runs - which for INSERT OVERWRITE means a retry that
    overwrites a different Partition than the attempt it is retrying.

    Run against `declarations/`, not this module's fixture, because the fixture has one Tag
    family of one Metric and no Join path: the real Declarations are where the set
    iteration actually happens.
    """
    program = (
        "import sys\n"
        "from datetime import date\n"
        "from declarations import REGISTRY, deliveries\n"
        "from sqlcomposer import write\n"
        "built = write.plan(REGISTRY, [deliveries.WEEKLY_HEALTH_FROM_DAILY, "
        "deliveries.ACCOUNTABLE_BY_DAY], run_date=date(2026, 1, 2))\n"
        "sys.stdout.write(built.to_script())\n"
    )

    def emit(seed: str) -> str:
        environment = dict(os.environ, PYTHONHASHSEED=seed)
        finished = subprocess.run(
            [sys.executable, "-c", program],
            cwd=str(REPO_ROOT),
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert finished.returncode == 0, finished.stderr
        return finished.stdout

    first = emit("0")
    second = emit("987654321")

    assert "INSERT OVERWRITE TABLE mart.delivery_health_daily" in first
    assert first == second


# ======================================================================================
# Refusals. Each of these otherwise writes plausible wrong numbers.
# ======================================================================================


def test_a_partition_column_left_without_a_value_refuses() -> None:
    """A dynamic Partition overwrites whatever the SELECT happened to produce, which on a
    bad day is every Partition in the table."""
    with pytest.raises(InvalidDeclaration) as refusal:
        insert_overwrite(
            SALES_REGISTRY, WRITE_CASE, run_date=RUN_DATE, partition={"dt": None}
        )

    assert "dt" in str(refusal.value)


def test_a_partition_key_that_matches_no_column_refuses() -> None:
    """Swallowing the typo would leave the Partition defaulted to the run date in silence,
    and a backfill would quietly overwrite today instead of the day requested."""
    with pytest.raises(InvalidDeclaration):
        insert_overwrite(
            SALES_REGISTRY, WRITE_CASE, run_date=RUN_DATE, partition={"dt_day": "2026-01-01"}
        )
    with pytest.raises(InvalidDeclaration):
        plan(SALES_REGISTRY, [WRITE_CASE], run_date=RUN_DATE, partition={"dt_day": "x"})


def test_two_cases_writing_one_source_refuse_rather_than_racing() -> None:
    """They would overwrite each other's Partition on every run, and which numbers survived
    would depend on the order of the list."""
    with pytest.raises(InvalidDeclaration) as refusal:
        plan(SALES_REGISTRY, [WRITE_CASE, SECOND_WRITER], run_date=RUN_DATE)

    assert "mart.sales_daily" in str(refusal.value)


def test_the_same_case_twice_in_one_plan_refuses() -> None:
    """Its write would run twice in one pass - harmless for INSERT OVERWRITE, and a sign
    the caller believes something about the plan that is not true.

    Asserted on the SUBJECT, which is what separates this refusal from the one below it: a
    Case listed twice is refused as `case:<name>` before the two-writers check can refuse
    the same list as `source:mart.sales_daily`. Without that, one raise stands in for two
    and either could be deleted unnoticed.
    """
    with pytest.raises(InvalidDeclaration) as refusal:
        plan(SALES_REGISTRY, [WRITE_CASE, WRITE_CASE], run_date=RUN_DATE)

    assert refusal.value.subject == "case:z_write_sales_daily"

    # A Case that writes nothing is refused the same way, so the refusal is about the
    # duplicate entry rather than about the write.
    with pytest.raises(InvalidDeclaration) as read_twice:
        plan(SALES_REGISTRY, [READ_CASE, READ_CASE], run_date=RUN_DATE)

    assert read_twice.value.subject == "case:a_read_sales_daily"

    # The adjacent build: the two distinct Cases plan in one pass.
    assert len(plan(SALES_REGISTRY, [WRITE_CASE, READ_CASE], run_date=RUN_DATE)) == 2


def test_a_partition_column_that_cannot_hold_the_run_date_refuses_naming_its_type() -> None:
    """A Partition column left to its default takes the run date, and a column no date can
    inhabit is the one shape where that default cannot be honoured.

    The refusal has to say so in those terms. `LiteralTypeMismatch` alone would report that
    a date does not fit a BIGINT, which is true and useless: the contributor never wrote a
    date anywhere, the library supplied it, and the fix is a `partition={...}` value rather
    than anything about the value in the message.
    """
    epoch_target = Source(
        db="mart",
        table="sales_epoch",
        written_by="write_sales_epoch",
        columns=(
            Column("region", "STRING", nullable=False),
            Column("amount_total", "DECIMAL(18,2)"),
            Column("dt_epoch", "BIGINT", partition=True, nullable=False),
        ),
    )
    epoch_case = Case(
        name="write_sales_epoch",
        metrics=by_name(AMOUNT_TOTAL),
        grain=Grain.of(SALES.region),
        writes_to=epoch_target,
    )
    registry = (
        Registry(name="test_write-epoch")
        .add(SALES, epoch_target, AMOUNT_TOTAL, epoch_case)
        .freeze()
    )

    with pytest.raises(InvalidDeclaration) as refusal:
        insert_overwrite(registry, epoch_case, run_date=RUN_DATE)

    assert refusal.value.subject == "mart.sales_epoch.dt_epoch"
    assert "BIGINT" in refusal.value.problem

    # The adjacent build: supplying a value the column CAN hold writes the Partition.
    supplied = insert_overwrite(
        registry, epoch_case, run_date=RUN_DATE, partition={"dt_epoch": 20260102}
    )
    assert supplied.partition == (("dt_epoch", "20260102"),)


def test_a_case_with_no_target_cannot_be_written() -> None:
    """Guessing a table name from the Case would invent a Source no Declaration carries."""
    with pytest.raises(InvalidDeclaration):
        insert_overwrite(SALES_REGISTRY, READ_CASE, run_date=RUN_DATE)
    with pytest.raises(InvalidDeclaration):
        create_table_as(SALES_REGISTRY, READ_CASE, run_date=RUN_DATE)


def test_a_target_whose_columns_are_out_of_order_refuses() -> None:
    """Hive matches INSERT columns by position and checks nothing else, so a target
    declaring (amount_total, region) against a Case producing (region, amount_total) writes
    every number into the wrong column and reports them without complaint."""
    misordered_target = Source(
        db="mart",
        table="sales_daily_misordered",
        written_by="misordered_case",
        columns=(
            Column("amount_total", "DECIMAL(18,2)"),
            Column("region", "STRING", nullable=False),
            Column("dt", "STRING", partition=True, nullable=False),
        ),
    )
    misordered_case = Case(
        name="misordered_case",
        metrics=by_name(AMOUNT_TOTAL),
        grain=Grain.of(SALES.region),
        writes_to=misordered_target,
    )
    registry = (
        Registry(name="misordered")
        .add(SALES, misordered_target, AMOUNT_TOTAL, misordered_case)
        .freeze()
    )

    with pytest.raises(InvalidDeclaration) as refusal:
        insert_overwrite(registry, misordered_case, run_date=RUN_DATE)

    assert "amount_total" in str(refusal.value)


def test_a_cycle_between_two_writes_refuses_instead_of_picking_an_order() -> None:
    """Two Cases each reading a Source the other writes: no order of statements gives both
    of them today's numbers, and any order the library invented would give one of them
    yesterday's without saying so."""
    left = Source(
        db="mart",
        table="left",
        written_by="case_left",
        columns=(
            Column("k", "STRING", nullable=False),
            Column("n", "BIGINT"),
            Column("dt", "STRING", partition=True, nullable=False),
        ),
    )
    right = Source(
        db="mart",
        table="right",
        written_by="case_right",
        columns=(
            Column("k", "STRING", nullable=False),
            Column("n", "BIGINT"),
            Column("dt", "STRING", partition=True, nullable=False),
        ),
    )
    n_from_right = sum_of("n", right.n)
    n_from_left = sum_of("n_left", left.n)
    case_left = Case(
        name="case_left",
        metrics=by_name(n_from_right),
        grain=Grain.of(right.k),
        writes_to=left,
    )
    case_right = Case(
        name="case_right",
        metrics=by_name(n_from_left),
        grain=Grain.of(left.k),
        writes_to=right,
    )
    registry = (
        Registry(name="cycle")
        .add(left, right, n_from_right, n_from_left, case_left, case_right)
        .freeze()
    )

    with pytest.raises(InvalidDeclaration) as refusal:
        plan(registry, [case_left, case_right], run_date=RUN_DATE)

    assert "case_left" in str(refusal.value)
    assert "case_right" in str(refusal.value)


def test_an_unfrozen_registry_cannot_be_planned_against() -> None:
    """freeze() is where Join targets, Join keys and written-Source agreement are checked.
    Emitting writes against an unchecked Registry would skip all of it."""
    unfrozen = Registry(name="unfrozen").add(SALES, AMOUNT_TOTAL, STANDALONE_CASE)

    with pytest.raises(RegistryNotFrozen):
        plan(unfrozen, [STANDALONE_CASE], run_date=RUN_DATE)
    with pytest.raises(RegistryNotFrozen):
        partition_values(unfrozen, STANDALONE_CASE, run_date=RUN_DATE)


# ======================================================================================
# Manifests: what a write leaves behind for the next Case to trace through
# ======================================================================================


def test_each_write_contributes_one_manifest_in_statement_order() -> None:
    """A Manifest is what lets a later Case trace through the written table to the true
    upstream Sources. One per write, positionally matched to the writes, or the trace lands
    on the wrong table."""
    built = plan(SALES_REGISTRY, [READ_CASE, WRITE_CASE, STANDALONE_CASE], run_date=RUN_DATE)
    writes = [
        statement
        for statement in built
        if statement.kind is StatementKind.INSERT_OVERWRITE
    ]

    assert len(built.manifests) == len(writes) == 1
    assert built.manifests[0].source == writes[0].target == "mart.sales_daily"
    assert built.manifests[0].written_by == "z_write_sales_daily"


def test_a_plan_of_only_selects_carries_no_manifests() -> None:
    """Nothing was written, so there is nothing for a later Case to trace through."""
    assert plan(SALES_REGISTRY, [STANDALONE_CASE], run_date=RUN_DATE).manifests == ()
