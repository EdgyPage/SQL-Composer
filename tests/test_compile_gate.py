"""The three nets between a plan and a statement, and the two refusals around the run date.

`tests/test_compile_golden.py` asserts what the compiler PRODUCES. This file asserts what it
REFUSES, which nothing did:

* the `qualify()` resolution gate. Both halves of it were unevidenced - swallowing
  `OptimizeError` and handing qualify an empty schema each left the whole suite green,
  because the goldens pin qualify's rewrite (backticks and aliases) and never its
  resolution. So the gate could degrade into a pretty-printer undetected.
* `errors.warnings_are_refusals`, which decision 10 requires so sqlglot's silent
  degradations surface. Making it a no-op left the suite green, although two modules and
  another test module's docstring lean on it.
* `UnboundRunDate`. Every fixture Case carries a `RunDate`, and all three of its raise sites
  could be disabled together: a deferred Case compiled without a date then emitted
  `WHERE dt BETWEEN NULL AND NULL`, which runs, returns nothing, and reports zero for every
  Metric.
* `ScopeCollision`, which is new here: a Case-level Filter that is also a Metric's scope.

`tests/test_escaping.py` owns the `ErrorLevel.RAISE` half of generation, because that is
where the sqlglot-behaviour tripwires live.
"""
from __future__ import annotations

import datetime
import logging

import pytest
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify

from declarations import REGISTRY
from declarations import deliveries as fixture
from sqlcomposer import compile as compiler
from sqlcomposer.declaration import Column, Registry, Source
from sqlcomposer.errors import (
    RenderError,
    ResolutionFailed,
    ScopeCollision,
    UnboundRunDate,
    warnings_are_refusals,
)
from sqlcomposer.model import Case, Grain, by_name, by_tag, count_rows

RUN_DATE = datetime.date(2026, 9, 17)


def _tree(column: str) -> exp.Select:
    """`SELECT deliveries.<column> FROM mart.deliveries`, built as nodes, never parsed."""
    return sqlglot.select(exp.column(column, table="deliveries")).from_(
        exp.table_("deliveries", db="mart")
    )


# ======================================================================================
# The qualify() resolution gate
# ======================================================================================


def test_the_gate_refuses_a_column_no_declaration_carries() -> None:
    """The second, independent net under attribute access.

    Attribute access refuses a misspelled column where it is written. This catches a column
    that reached the tree some other way - a hand-built node, a future code path - and it is
    independent precisely because it asks sqlglot rather than the Declarations directly.
    """
    with pytest.raises(ResolutionFailed) as refused:
        compiler.qualify_gate(REGISTRY, _tree("nope"), case="probe")

    error = refused.value
    assert error.case == "probe"
    assert "nope" in error.sqlglot_message

    # The adjacent build: a declared column passes the gate, and comes back qualified.
    qualified = compiler.qualify_gate(REGISTRY, _tree("fee_amount"), case="probe")
    assert qualified.sql(dialect=compiler.DIALECT) == (
        "SELECT `deliveries`.`fee_amount` AS `fee_amount` FROM `mart`.`deliveries` AS "
        "`deliveries`"
    )


def test_the_gates_teeth_come_from_the_schema_and_not_from_the_rewrite() -> None:
    """Why the schema must be the WHOLE declared schema, asserted rather than commented.

    qualify() backtick-quotes and aliases whatever it is given, so a gate handed an empty
    schema still produces exactly the SQL every golden in this suite pins - while resolving
    nothing at all. This test is the difference between those two, and it is the one that
    fails if `Registry.schema()` is ever narrowed to "the Sources this Case touches".
    """
    toothless = qualify(_tree("nope").copy(), schema=None, dialect=compiler.DIALECT)

    assert toothless.sql(dialect=compiler.DIALECT) == (
        "SELECT `deliveries`.`nope` AS `nope` FROM `mart`.`deliveries` AS `deliveries`"
    )
    with pytest.raises(ResolutionFailed):
        compiler.qualify_gate(REGISTRY, _tree("nope"))


def test_the_gate_does_not_mutate_the_tree_it_was_given() -> None:
    """qualify() rewrites in place and returns its argument, so the gate copies first.

    The semantic-diff tests hold the pre-gate tree; a gate that rewrote it would make those
    comparisons compare a tree against itself.
    """
    tree = _tree("fee_amount")
    before = tree.sql(dialect=compiler.DIALECT)

    compiler.qualify_gate(REGISTRY, tree)

    assert tree.sql(dialect=compiler.DIALECT) == before
    assert "`" not in before


def test_the_gate_answers_from_the_registry_it_was_given_and_catches_columns_not_tables() -> None:
    """The gate's answer is a function of the schema handed to it - and of columns only.

    The limit is worth knowing rather than discovering: qualify() raises on a column of a
    table it knows, and says NOTHING about a table the schema has never heard of - it
    quotes it and moves on. So the gate is a net under column references, not under table
    references, and what keeps a table honest is that every table node in this library comes
    from a `Source` the Registry holds.
    """
    lonely = Source(db="d", table="only", columns=(Column("k", "STRING"),))
    partial = Registry(name="partial").add(lonely).freeze()
    unknown_table = sqlglot.select(exp.column("k", table="elsewhere")).from_(
        exp.table_("elsewhere", db="d")
    )
    unknown_column = sqlglot.select(exp.column("zzz", table="only")).from_(
        exp.table_("only", db="d")
    )

    assert compiler.qualify_gate(partial, unknown_table, case="partial").sql(
        dialect=compiler.DIALECT
    ) == "SELECT `elsewhere`.`k` AS `k` FROM `d`.`elsewhere` AS `elsewhere`"

    with pytest.raises(ResolutionFailed) as refused:
        compiler.qualify_gate(partial, unknown_column, case="partial")
    assert "zzz" in refused.value.sqlglot_message


# ======================================================================================
# sqlglot's own silence
# ======================================================================================


def test_a_sqlglot_warning_is_a_refusal_inside_the_context_and_not_outside_it() -> None:
    """sqlglot degrades by LOGGING in several places, and a log line nobody reads is
    indistinguishable from success.

    "Unknown subquery scope" is the real message this defends against: it is how
    `sqlglot.lineage` reports that it could not resolve part of a query, and it comes back
    as a confident-looking graph with a hole in it.
    """
    logger = logging.getLogger("sqlglot")

    with pytest.raises(RenderError) as refused:
        with warnings_are_refusals():
            logger.warning("Unknown subquery scope: x")

    assert "Unknown subquery scope" in refused.value.problem

    # Outside it, sqlglot's own behaviour is untouched - the escalation is scoped, so a
    # caller who genuinely wants best-effort behaviour can step out of it.
    logger.warning("this one is only a log line")


def test_the_escalation_restores_the_logger_it_borrowed() -> None:
    """Test isolation is the reason this is a context manager rather than a global install.

    A handler left behind would turn every later sqlglot warning in the process into an
    exception raised from wherever it happened to be logged.
    """
    logger = logging.getLogger("sqlglot")
    handlers_before = list(logger.handlers)
    level_before = logger.level

    with warnings_are_refusals():
        assert len(logger.handlers) == len(handlers_before) + 1

    assert list(logger.handlers) == handlers_before
    assert logger.level == level_before


def test_escalate_sqlglot_logging_is_idempotent_and_installs_the_same_refusal() -> None:
    """The process-wide version, for an application entry point rather than a test.

    Asserted with an explicit teardown because it is deliberately a context that is entered
    and never exited: leaving it installed would escalate sqlglot warnings for every test
    that runs after this one.
    """
    logger = logging.getLogger("sqlglot")
    handlers_before = list(logger.handlers)
    try:
        compiler.escalate_sqlglot_logging()
        added = [handler for handler in logger.handlers if handler not in handlers_before]
        assert len(added) == 1

        compiler.escalate_sqlglot_logging()  # second call is a no-op
        assert [h for h in logger.handlers if h not in handlers_before] == added

        with pytest.raises(RenderError):
            logger.warning("Unknown subquery scope: y")
    finally:
        # Reaching into the module's own state: the install has no public uninstall, by
        # design, and a test that leaves it in place changes every test after it.
        stack = compiler._escalation
        compiler._escalation = None
        if stack is not None:
            stack.close()

    assert list(logger.handlers) == handlers_before


# ======================================================================================
# The run date
# ======================================================================================


def test_a_deferred_case_compiled_without_a_run_date_refuses() -> None:
    """Substituting today would build a statement for the wrong day, silently.

    The refusal names the Case and the Filter that needs the date rather than surfacing
    from inside a predicate builder half a tree later, because the Filter is the thing a
    contributor has to look at.
    """
    assert fixture.ACCOUNTABLE_BY_DAY.deferred is True

    with pytest.raises(UnboundRunDate) as refused:
        compiler.compile_case(REGISTRY, fixture.ACCOUNTABLE_BY_DAY)

    error = refused.value
    assert error.subject == "accountable_by_day.filters[last_7_delivery_days]"
    assert "run_date" in error.text

    # The adjacent build: supplying the date compiles, and the date is in the statement.
    compiled = compiler.compile_case(REGISTRY, fixture.ACCOUNTABLE_BY_DAY, run_date=RUN_DATE)
    assert "BETWEEN '2026-09-11' AND '2026-09-17'" in compiled.sql
    assert compiled.run_date == RUN_DATE


def test_an_undeferred_case_needs_no_run_date() -> None:
    """`Case.deferred` is a property of its Filters, so a Case without one is ordinary."""
    undeferred = Case(
        name="attempts_by_carrier",
        metrics=by_name(fixture.DELIVERY_ATTEMPTS),
        grain=Grain.of(fixture.BY_CARRIER),
        filters=(fixture.LIVE_CARRIERS,),
    )

    assert undeferred.deferred is False
    assert compiler.compile_case(REGISTRY, undeferred).run_date is None


def test_a_metric_scoped_run_date_refuses_too_although_the_case_cannot_see_it() -> None:
    """`Case.deferred` reads the Case's own Filters, and a Metric-scoped `when` is not one.

    That one refuses later - from `grain.aggregate_expression` - but still before any SQL
    exists, which is the property that matters.
    """
    recent = count_rows("recent_attempts", fixture.DELIVERIES, when=fixture.LAST_7_DAYS)

    with pytest.raises(UnboundRunDate):
        compiler.compile_metric_only(REGISTRY, recent)

    assert "BETWEEN '2026-09-11'" in compiler.compile_metric_only(
        REGISTRY, recent, run_date=RUN_DATE
    )


def test_render_predicate_names_the_whole_predicate_rather_than_one_offset() -> None:
    """A contributor reading the refusal needs the Filter, not the offset that happened to
    be reached first inside the builder closure."""
    with pytest.raises(UnboundRunDate) as refused:
        compiler.render_predicate(fixture.LAST_7_DAYS.predicate)

    assert refused.value.subject == fixture.LAST_7_DAYS.predicate.text
    assert "run_date-6" in refused.value.text


# ======================================================================================
# A Case-level Filter that is also a Metric's scope
# ======================================================================================


def test_a_case_filtered_by_a_metrics_own_scope_refuses() -> None:
    """Under a WHERE that already asserts the predicate, the conditional aggregate is a
    tautology - so `failed_deliveries` equals `delivery_attempts` and `failure_rate` reads
    1.0 on every row. Three columns whose names mean something they do not.

    It is the collision of two good ideas, which is why nobody writes it down: the Case
    narrows with a Filter, and asks for a Tag family that happens to contain a Metric scoped
    by that same Filter.
    """
    colliding = Case(
        name="failures_narrowed_twice",
        metrics=by_tag(fixture.ACCOUNTABLE),
        grain=Grain.of(fixture.BY_DAY),
        filters=(fixture.LAST_7_DAYS, fixture.FAILURE_TO_DELIVER),
    )

    with pytest.raises(ScopeCollision) as refused:
        compiler.compile_case(REGISTRY, colliding, run_date=RUN_DATE)

    error = refused.value
    assert error.case == "failures_narrowed_twice"
    assert error.filter == "failure_to_deliver"
    assert error.outputs == ("failed_deliveries", "failure_rate")

    # The adjacent build: the shipped Case asks the same question without the collision,
    # and its denominator still counts every attempt.
    sql = compiler.compile_case(
        REGISTRY, fixture.FAILURES_BY_SITE_AND_SEGMENT, run_date=RUN_DATE
    ).sql
    assert "COUNT(*) AS `delivery_attempts`" in sql
    assert "WHERE `deliveries`.`dt` BETWEEN '2026-09-11' AND '2026-09-17' GROUP BY" in sql


def test_a_case_filter_that_merely_shares_a_source_with_a_scope_is_fine() -> None:
    """The refusal is about ONE Filter used twice, not about filtering a Case at all."""
    ordinary = Case(
        name="failures_last_week",
        metrics=by_name(fixture.FAILED_DELIVERIES, fixture.DELIVERY_ATTEMPTS),
        grain=Grain.of(fixture.BY_DAY),
        filters=(fixture.LAST_7_DAYS, fixture.DELIVERED_LATE),
    )

    sql = compiler.compile_case(REGISTRY, ordinary, run_date=RUN_DATE).sql

    assert "`deliveries`.`late_flag` = 1" in sql
    assert "CASE WHEN NOT `deliveries`.`failure_reason` IS NULL" in sql
