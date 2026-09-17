"""The builder-derived Lineage, and sqlglot's own lineage as a cross-check against it.

Two jobs, in that order.

The first is that the graph `lineage.build` derives from a `CasePlan` says something true:
node identity is the fully-qualified `db.table.column` a contributor typed into a
Declaration, every output column traces to the Source columns that actually feed it, the
chosen Join path is recorded (two Join paths give the same column-level graph and different
numbers, so the path is part of the answer), and a Case reading a written Source traces
THROUGH that table's Manifest to the real upstream Sources instead of stopping at it.

The second is the cross-check the design calls for: generate the SQL, run `sqlglot.lineage`
over it, and require the two graphs to agree on the source columns of every output column.
Builder-derived lineage is authoritative at runtime, so a disagreement here is a builder bug
- but sqlglot's lineage is only usable as a check if its silent degradations are treated as
failures. It disables qualify's validation internally, so an unresolvable column becomes an
`exp.Placeholder` leaf and an unexpanded star becomes a leaf literally named `"*"`, and
either one would otherwise shrink the comparison set until the two graphs "agree" about
nothing. `_sqlglot_source_columns` raises on both, `test_placeholder_leaf_is_a_failure_not_a_pass`
and `test_star_leaf_is_a_failure_not_a_pass` prove it raises, and every lineage call runs
inside `warnings_are_refusals()` so an "Unknown subquery scope" log line raises too.

What the two graphs can and cannot be compared on:

* sqlglot reads the SELECT projection. It cannot see a WHERE clause or an ON clause, so it
  never reports the columns a Case-level Filter narrows by or a Join path is joined on.
  The builder records those deliberately, with edge roles `filter` and `join_key`.
* So the comparable set on the builder's side is one output's `metric` and `dimension` edges
  plus the `filter` edges belonging to that Metric's own scoped `when` - a conditional
  aggregate IS in the projection. `_builder_projection_columns` assembles exactly that, and
  the test asserts set equality, not containment: a builder that attributed a column to the
  wrong Metric would pass a containment check in one direction.
* A `COUNT(*)` Metric measures rows rather than a column, so both sides report the empty set
  for it. That agreement is real, not vacuous - `test_sqlglot_cross_check_sees_real_columns`
  asserts the comparison is non-empty overall.
"""
from __future__ import annotations

import datetime
import json

import networkx
import pytest
import sqlglot
from sqlglot import exp
from sqlglot.lineage import Node as SqlglotNode
from sqlglot.lineage import lineage as sqlglot_lineage

from declarations import deliveries as fixture
from sqlcomposer import compile as compile_module
from sqlcomposer import lineage as lineage_module
from sqlcomposer import write
from sqlcomposer.compile import DIALECT
from sqlcomposer.declaration import Column, Registry, Source
from sqlcomposer.errors import InvalidDeclaration, warnings_are_refusals
from sqlcomposer.lineage import (
    ROLE_DIMENSION,
    ROLE_FILTER,
    ROLE_JOIN_KEY,
    ROLE_METRIC,
    Lineage,
    Manifest,
    output_id,
)
from sqlcomposer.model import (
    Case,
    CasePlan,
    Dimension,
    Grain,
    Metric,
    ReAggregation,
    by_name,
)

ALL_CASE_NAMES = (
    "accountable_by_day",
    "accountable_by_week",
    "failures_by_site_and_segment",
    "operational_by_day",
    "operational_by_week",
    "weekly_health_from_daily",
)
"""Every Case the fixture declares, named literally rather than read off the Registry.

A parametrisation derived from `registry.cases()` would silently shrink to nothing if the
scan that populates the Registry ever broke, and a suite that reports success because it
collected zero cases is the exact failure this library exists to refuse.
`test_every_declared_case_is_cross_checked` is the pin that keeps this list honest.
"""


# ======================================================================================
# Helpers
# ======================================================================================


def _plan(registry: Registry, case_name: str, run_date: datetime.date) -> CasePlan:
    return compile_module.plan(registry, registry.case(case_name), run_date=run_date)


def _lineage(registry: Registry, case_name: str, run_date: datetime.date) -> Lineage:
    return lineage_module.build(registry, _plan(registry, case_name, run_date))


def _scoped_filter_names(metric: Metric) -> frozenset[str]:
    """The names of every `when` Filter scoped to a Metric, its components included.

    Recomputed here rather than imported from `lineage._scoped_filters`: a cross-check that
    reuses the implementation's own helper stops being a check of it.
    """
    names: set[str] = set()
    if metric.when is not None:
        names.add(metric.when.name)
    for part in metric.components:
        names |= _scoped_filter_names(part)
    return frozenset(names)


def _builder_projection_columns(
    plan: CasePlan, built: Lineage
) -> dict[str, frozenset[str]]:
    """Per output, the Source columns the builder says appear in the SELECT projection.

    Read off the graph's edges, which is the point - this is what the cross-check compares,
    so it has to come from the artifact under test and not from the plan directly. Metric
    and Dimension edges are the number itself; a `filter` edge counts only when the Filter
    is that Metric's own scoped `when`, because that one renders as a conditional aggregate
    inside the projection while a Case-level Filter renders as a WHERE clause sqlglot's
    lineage cannot see. `join_key` edges are never in the projection.
    """
    scoped = {
        metric_plan.metric.name: _scoped_filter_names(metric_plan.metric)
        for metric_plan in plan.metrics
    }
    columns: dict[str, frozenset[str]] = {}
    for output in built.outputs():
        node = output_id(built.case, output)
        allowed = scoped.get(output, frozenset())
        found: set[str] = set()
        for source_node, _, data in built.graph.in_edges(node, data=True):
            role = data["role"]
            if role in (ROLE_METRIC, ROLE_DIMENSION):
                found.add(source_node)
            elif role == ROLE_FILTER and data.get("filter") in allowed:
                found.add(source_node)
        columns[output] = frozenset(found)
    return columns


def _qualified_leaf(node: SqlglotNode) -> str:
    """One sqlglot lineage leaf as `db.table.column`.

    The leaf's name is the column as sqlglot re-prints it (`"deliveries"."failure_reason"`),
    which carries the table ALIAS. The db comes from the leaf's `source`, which is the
    `exp.Table` the column was resolved against - so this is the only place the two halves
    of the node id meet, and it is reading sqlglot's answer rather than assuming ours.
    """
    column = sqlglot.parse_one(node.name)
    assert isinstance(column, exp.Column), (
        f"sqlglot lineage leaf {node.name!r} did not parse as a column reference"
    )
    table = node.source
    assert isinstance(table, exp.Table)
    assert table.db, f"sqlglot lineage leaf {node.name!r} resolved to an un-databased table"
    return f"{table.db}.{table.name}.{column.name}"


def _sqlglot_source_columns(sql: str, registry: Registry) -> dict[str, frozenset[str]]:
    """`{output column: {db.table.column}}` as sqlglot's own lineage reports it.

    The whole declared schema is supplied so a star would expand; the SQL this library emits
    never contains one, and the schema is here so that a future one does not silently become
    a leaf named `"*"`.

    Raises rather than returning a smaller set on either known silent degradation. That is
    the difference between a cross-check and a decoration: a placeholder leaf means sqlglot
    could not resolve a column, and a comparison that quietly drops it would agree with any
    builder at all.
    """
    with warnings_are_refusals():
        roots = sqlglot_lineage(None, sql, schema=registry.schema_dict(), dialect=DIALECT)

    columns: dict[str, frozenset[str]] = {}
    for output, root in roots.items():
        found: set[str] = set()
        for node in root.walk():
            if isinstance(node.source, exp.Placeholder) or isinstance(
                node.expression, exp.Placeholder
            ):
                raise AssertionError(
                    f"sqlglot lineage degraded to a placeholder leaf for output {output!r}: "
                    f"it could not resolve {node.name!r}. The cross-check is meaningless "
                    "against a placeholder - treat this as a failure, never as agreement."
                )
            if node.name == "*":
                raise AssertionError(
                    f"sqlglot lineage returned an unexpanded star leaf for output "
                    f"{output!r}; the schema did not cover the SELECT *."
                )
            if isinstance(node.expression, exp.Table) and isinstance(node.source, exp.Table):
                found.add(_qualified_leaf(node))
        columns[output] = frozenset(found)
    return columns


# ======================================================================================
# Node identity and output identity
# ======================================================================================


@pytest.mark.parametrize("case_name", ALL_CASE_NAMES)
def test_every_column_node_is_a_fully_qualified_declared_column(
    registry: Registry, run_date: datetime.date, case_name: str
) -> None:
    """Node identity is `db.table.column` and nothing re-derives it.

    Every column node must round-trip through `Registry.resolve_column` back to the
    `ColumnRef` whose `.qualified` it is. A node id that lost its db, carried a table alias
    instead of the table, or was spelled by some second code path would fail here - and a
    Lineage keyed by bare column names silently merges `deliveries.dt` with
    `delivery_health_daily.dt`, which is two different numbers under one name.
    """
    built = _lineage(registry, case_name, run_date)
    assert built.columns(), f"{case_name} has no column nodes at all"
    for node in built.columns():
        assert node.count(".") == 2, f"{node!r} is not db.table.column"
        ref = registry.resolve_column(node)
        assert ref.qualified == node
        assert built.graph.nodes[node]["kind"] == "column"
        assert built.graph.nodes[node]["type"] == ref.type
        assert built.graph.nodes[node]["partition"] == ref.partition


@pytest.mark.parametrize("case_name", ALL_CASE_NAMES)
def test_outputs_are_case_prefixed_and_in_the_cases_own_output_order(
    registry: Registry, run_date: datetime.date, case_name: str
) -> None:
    """`Lineage.outputs()` is `Case.output_names` - the same tuple, in the same order.

    That order is simultaneously the SELECT order and the INSERT column order, and Hive
    matches INSERT columns by position. A Lineage whose output order drifted from the Case's
    would describe a statement that writes the numbers into the wrong columns.
    """
    case = registry.case(case_name)
    built = _lineage(registry, case_name, run_date)
    assert built.outputs() == case.output_names(registry)
    for output in built.outputs():
        node = output_id(case_name, output)
        assert node == f"{case_name}:{output}"
        assert built.graph.nodes[node]["kind"] == "output"
        assert built.graph.nodes[node]["role"] in (ROLE_DIMENSION, ROLE_METRIC)


def test_output_id_refuses_a_case_name_containing_a_colon() -> None:
    """The no-collision argument for the node id scheme rests on this one rule."""
    with pytest.raises(InvalidDeclaration):
        output_id("weekly:health", "failure_rate")


# ======================================================================================
# Every output traces to its true Source columns
# ======================================================================================


DELIVERIES_SPINE_BASE = frozenset(
    {
        # Case-level Filters: the seven-day Partition window and the test-carrier exclusion.
        "mart.deliveries.dt",
        "mart.carriers.is_test",
        # The join keys of the one Join path between deliveries and carriers.
        "mart.deliveries.carrier_id",
        "mart.carriers.carrier_id",
    }
)
"""What every output of `accountable_by_day` depends on regardless of what it measures: the
two Filters that narrow the Case and the two columns the Join path is joined on. Spelled out
because these are exactly the dependencies a parser-derived lineage would miss, and missing
them is how a column that moves every number in a Case looks like it moves none."""


def test_accountable_by_day_traces_every_output_to_exactly_its_source_columns(
    registry: Registry, run_date: datetime.date
) -> None:
    """The full upstream set of every output of one Case, written out.

    Exact equality, not containment, in both directions at once: an extra column means the
    Lineage over-claims a dependency and a review of a warehouse change looks worse than it
    is; a missing one means a change to a column that really does move this number shows up
    in nobody's impact report.
    """
    built = _lineage(registry, "accountable_by_day", run_date)
    expected = {
        "dt_day": DELIVERIES_SPINE_BASE,
        "carrier": DELIVERIES_SPINE_BASE | {"mart.carriers.carrier_name"},
        "active_couriers": DELIVERIES_SPINE_BASE | {"mart.deliveries.courier_id"},
        "delivery_attempts": DELIVERIES_SPINE_BASE,
        "failed_deliveries": DELIVERIES_SPINE_BASE | {"mart.deliveries.failure_reason"},
        # A ratio inherits its components' columns, the scoped `when` of a component
        # included - which is the whole reason `failure_rate` is re-derived rather than
        # averaged.
        "failure_rate": DELIVERIES_SPINE_BASE | {"mart.deliveries.failure_reason"},
        "fees_charged": DELIVERIES_SPINE_BASE | {"mart.deliveries.fee_amount"},
    }
    assert set(built.outputs()) == set(expected)
    for output, columns in expected.items():
        assert built.upstream(output) == columns, output


def test_edge_roles_separate_measuring_from_narrowing_from_joining(
    registry: Registry, run_date: datetime.date
) -> None:
    """A column that IS a number, one that only narrowed it, and one that only joined on it
    are
    three different claims, and the graph has to keep them apart.

    Collapsed together, `mart.carriers.carrier_id` - a join key nobody reports - would read
    as a contributor to every number in the Case.
    """
    built = _lineage(registry, "accountable_by_day", run_date)

    def role(column: str, output: str) -> dict[str, object]:
        return dict(built.graph.edges[column, output_id("accountable_by_day", output)])

    assert role("mart.deliveries.fee_amount", "fees_charged") == {
        "role": ROLE_METRIC,
        "metric": "fees_charged",
    }
    assert role("mart.deliveries.courier_id", "active_couriers") == {
        "role": ROLE_METRIC,
        "metric": "active_couriers",
    }
    assert role("mart.carriers.carrier_name", "carrier") == {"role": ROLE_DIMENSION}
    # A Metric-scoped `when` narrows one Metric...
    assert role("mart.deliveries.failure_reason", "failed_deliveries") == {
        "role": ROLE_FILTER,
        "filter": "failure_to_deliver",
    }
    assert not built.graph.has_edge(
        "mart.deliveries.failure_reason", output_id("accountable_by_day", "fees_charged")
    ), "a Metric-scoped `when` must not reach another Metric's output"
    # ...while a Case-level Filter narrows all of them.
    for output in built.outputs():
        assert role("mart.carriers.is_test", output)["role"] == ROLE_FILTER
        assert role("mart.carriers.carrier_id", output) == {"role": ROLE_JOIN_KEY}


def test_a_column_that_both_measures_and_narrows_keeps_the_stronger_claim(
    registry: Registry, run_date: datetime.date
) -> None:
    """`mart.deliveries.dt` is the Grain of `accountable_by_day` AND the column its
    seven-day Filter narrows on. A DiGraph holds one edge per ordered pair, so the two
    claims collapse - and the surviving one has to be `dimension`.

    Collapsed the other way, the breakdown column of the Case would print as a filter and
    the day column would look as though it came from nowhere.
    """
    built = _lineage(registry, "accountable_by_day", run_date)
    dt_edge = built.graph.edges["mart.deliveries.dt", output_id("accountable_by_day", "dt_day")]
    assert dt_edge == {"role": ROLE_DIMENSION}
    # On an output it does not break down, the same column is still only a filter.
    other = built.graph.edges[
        "mart.deliveries.dt", output_id("accountable_by_day", "fees_charged")
    ]
    assert other == {"role": ROLE_FILTER, "filter": "last_7_delivery_days"}


def test_metric_outputs_carry_the_regrain_proof_they_were_planned_with(
    registry: Registry, run_date: datetime.date
) -> None:
    """A Metric output node records its Re-aggregation rule and the Grain it rolled up from.

    Those two facts are what separates a number computed from atomic rows from the same
    number summed out of a stored daily table, and they are not recoverable from the SQL:
    `SUM(delivery_attempts)` looks identical either way. They are the live objects, not
    strings, so a reader compares against `ReAggregation.SUM`.
    """
    atomic = _lineage(registry, "accountable_by_day", run_date)
    graph = atomic.graph
    assert graph.nodes[output_id("accountable_by_day", "fees_charged")]["rule"] is (
        ReAggregation.SUM
    )
    assert graph.nodes[output_id("accountable_by_day", "failure_rate")]["rule"] is (
        ReAggregation.REDERIVE
    )
    assert graph.nodes[output_id("accountable_by_day", "active_couriers")]["rule"] is (
        ReAggregation.NONE
    )
    for output in ("fees_charged", "failure_rate", "active_couriers"):
        assert graph.nodes[output_id("accountable_by_day", output)]["native"] is None, (
            "a Case reading atomic rows rolled up from nothing"
        )

    rolled = _lineage(registry, "weekly_health_from_daily", run_date)
    stored = rolled.graph.nodes[
        output_id("weekly_health_from_daily", "weekly_fees_charged")
    ]
    assert stored["rule"] is ReAggregation.SUM
    assert stored["native"] == registry.native_grain(fixture.DELIVERY_HEALTH_DAILY)
    assert stored["native"] is not None, (
        "a re-aggregation out of a written table records its Grain"
    )


def test_downstream_answers_the_impact_question(
    registry: Registry, run_date: datetime.date
) -> None:
    """Which numbers move if this warehouse column changes.

    A measured column moves one number; a Case-level Filter's column moves all of them. A
    column this Case never reads answers with the empty set rather than refusing, because
    "none of them" is the true answer when sweeping every column of a changed table.
    """
    built = _lineage(registry, "accountable_by_day", run_date)
    assert built.downstream("mart.deliveries.fee_amount") == {"fees_charged"}
    assert built.downstream("mart.carriers.is_test") == set(built.outputs())
    assert built.downstream("mart.deliveries.scan_count") == frozenset()


def test_upstream_refuses_an_output_the_case_does_not_publish(
    registry: Registry, run_date: datetime.date
) -> None:
    """An empty answer to "where did this number come from" is indistinguishable from a
    misspelled output name, and one of those is a wrong review."""
    built = _lineage(registry, "accountable_by_day", run_date)
    with pytest.raises(InvalidDeclaration):
        built.upstream("fees_charrged")


# ======================================================================================
# The Join path is recorded
# ======================================================================================


def test_the_chosen_join_path_is_recorded_on_the_lineage(
    registry: Registry, run_date: datetime.date
) -> None:
    """Two Join paths between the same Sources give the same column-level graph and
    different numbers, so the path is part of the answer rather than an implementation detail.

    Recorded as edge NAMES, which is what a Case's `via=` pins, and in traversal order.
    """
    plan = _plan(registry, "accountable_by_day", run_date)
    built = lineage_module.build(registry, plan)
    assert built.path == ("carrier_deliveries",)
    assert built.path == plan.join_names


def test_a_metric_named_after_a_dimension_refuses_where_the_graph_is_built(
    registry: Registry, run_date: datetime.date
) -> None:
    """`Grain` refuses two Dimensions publishing one name, but a Metric named after a
    Dimension is a collision between two different kinds of output and is caught only here.

    Both would become one node in the graph and one INSERT column downstream, so the Lineage
    would report a Dimension's Source column as feeding a Metric, and a write would send the
    Grain column's values into whichever column Hive matched by position.
    """
    collided = Case(
        name="metric_named_like_its_dimension",
        metrics=by_name(fixture.DELIVERY_ATTEMPTS),
        grain=Grain.of(Dimension(fixture.DELIVERIES.carrier_id, alias="delivery_attempts")),
    )
    plan = compile_module.plan(registry, collided, run_date=run_date)

    with pytest.raises(InvalidDeclaration) as refused:
        lineage_module.build(registry, plan)

    assert refused.value.subject == "case:metric_named_like_its_dimension"
    assert "delivery_attempts" in refused.value.problem


def test_asking_the_text_tree_for_an_output_the_case_does_not_publish_refuses(
    registry: Registry, run_date: datetime.date
) -> None:
    """`to_text(built, "typo")` printing an empty tree would read as "this column comes from
    nowhere", which is a claim about the Case rather than about the question asked."""
    built = _lineage(registry, "accountable_by_day", run_date)

    with pytest.raises(InvalidDeclaration) as refused:
        lineage_module.to_text(built, "delivery_attempt")

    assert refused.value.subject == "accountable_by_day:delivery_attempt"
    assert "delivery_attempts" in str(refused.value)  # the names it does publish

    # The adjacent build: the name it does publish prints its own block.
    assert "delivery_attempts" in lineage_module.to_text(built, "delivery_attempts")


def test_a_case_reading_one_source_records_an_empty_join_path(
    registry: Registry, run_date: datetime.date
) -> None:
    """`()` is a recorded fact, not a gap: this Case reaches its numbers without a join, so
    no Fan-out and no Join path choice is in play."""
    built = _lineage(registry, "weekly_health_from_daily", run_date)
    assert built.path == ()
    assert not any(
        data["role"] == ROLE_JOIN_KEY for _, _, data in built.graph.edges(data=True)
    )


def test_an_ambiguous_join_path_records_which_edges_were_actually_taken(
    registry: Registry, run_date: datetime.date
) -> None:
    """Two declared edges reach `mart.sites` - origin and destination - and the Case pins
    one with `via=`. The Lineage has to say which, and its join keys have to match.

    This is the case where a Lineage that recorded only columns would be actively
    misleading: both paths produce a `site_name` Dimension fed by `mart.sites.site_name`,
    and the numbers under it are different sites.
    """
    built = _lineage(registry, "failures_by_site_and_segment", run_date)
    assert built.path == ("delivery_customer", "delivery_destination_site")
    assert "delivery_origin_site" not in built.path

    columns = built.columns()
    assert "mart.deliveries.destination_site_id" in columns
    assert "mart.deliveries.origin_site_id" not in columns, (
        "the Join path not taken must not appear in the Lineage"
    )
    for output in built.outputs():
        edge = built.graph.edges[
            "mart.deliveries.destination_site_id", output_id(built.case, output)
        ]
        assert edge["role"] == ROLE_JOIN_KEY


# ======================================================================================
# Tracing through a written Source's Manifest
# ======================================================================================


@pytest.fixture()
def daily_manifest(registry: Registry, run_date: datetime.date) -> Manifest:
    """The Manifest `accountable_by_day` writes onto `mart.delivery_health_daily`."""
    plan = _plan(registry, "accountable_by_day", run_date)
    return lineage_module.manifest_for(registry, plan, fixture.DELIVERY_HEALTH_DAILY)


def test_without_a_manifest_the_trace_honestly_stops_at_the_written_table(
    registry: Registry, run_date: datetime.date
) -> None:
    """The baseline the next test is measured against. Without the Manifest, the weekly
    numbers trace to the written table and no further - which is true, and useless."""
    built = _lineage(registry, "weekly_health_from_daily", run_date)
    assert built.upstream("weekly_fees_charged") == {
        "mart.delivery_health_daily.fees_charged",
        "mart.delivery_health_daily.dt",
    }
    assert not any(node.startswith("mart.deliveries.") for node in built.columns())


def test_trace_through_reaches_the_true_upstream_sources(
    registry: Registry, run_date: datetime.date, daily_manifest: Manifest
) -> None:
    """A Case reading a written Source traces through the Manifest to the Sources the
    numbers actually came from.

    `weekly_fees_charged` is `SUM(fees_charged)` off a daily table; the fee itself lives on
    `mart.deliveries`, and it got there through a Case that excluded test carriers and
    joined on carrier id. All of that has to survive the splice, or the answer to "where did
    this number come from" stops one table short of the truth.
    """
    built = _lineage(registry, "weekly_health_from_daily", run_date)
    traced = lineage_module.trace_through(built, [daily_manifest])

    assert traced.upstream("weekly_fees_charged") == {
        # ...still through the written table,
        "mart.delivery_health_daily.fees_charged",
        "mart.delivery_health_daily.dt",
        # ...and on to the atomic Source and the producing Case's own dependencies.
        "mart.deliveries.fee_amount",
        "mart.deliveries.dt",
        "mart.deliveries.carrier_id",
        "mart.carriers.carrier_id",
        "mart.carriers.is_test",
    }
    assert traced.upstream("weekly_failure_rate") >= {
        "mart.deliveries.failure_reason",
        "mart.delivery_health_daily.delivery_attempts",
        "mart.delivery_health_daily.failed_deliveries",
    }
    # The written column keeps its own edge into the output, so the chain is traversable
    # rather than short-circuited.
    assert networkx.has_path(
        traced.graph,
        "mart.deliveries.fee_amount",
        output_id("weekly_health_from_daily", "weekly_fees_charged"),
    )
    assert traced.graph.has_edge(
        "mart.deliveries.fee_amount", "mart.delivery_health_daily.fees_charged"
    )


def test_trace_through_does_not_mutate_or_leak_the_producing_case(
    registry: Registry, run_date: datetime.date, daily_manifest: Manifest
) -> None:
    """The spliced graph is still ONE Case's Lineage.

    The Manifest's output nodes are the written table's columns, so they must be consumed by
    the graft rather than copied in beside it - two nodes for one number would make
    `outputs()` report a Case that is not being compiled, and `upstream()` walk into it.
    """
    built = _lineage(registry, "weekly_health_from_daily", run_date)
    before = built.graph.copy()
    traced = lineage_module.trace_through(built, [daily_manifest])

    assert traced.case == "weekly_health_from_daily"
    assert traced.outputs() == built.outputs()
    assert not [node for node in traced.graph if node.startswith("accountable_by_day:")]
    assert networkx.utils.graphs_equal(built.graph, before), (
        "trace_through must return a new Lineage, not edit the one it was given"
    )


def test_trace_through_leaves_a_column_the_producing_case_never_wrote_as_a_leaf(
    registry: Registry, run_date: datetime.date, daily_manifest: Manifest
) -> None:
    """`mart.delivery_health_daily.dt` is the write's Partition column, added by the write
    rather than published by `accountable_by_day`. No Manifest output matches it, so the
    trace stops there - honestly, rather than by inventing an upstream for it."""
    traced = lineage_module.trace_through(
        _lineage(registry, "weekly_health_from_daily", run_date), [daily_manifest]
    )
    assert "mart.delivery_health_daily.dt" not in daily_manifest.lineage.outputs()
    assert list(traced.graph.predecessors("mart.delivery_health_daily.dt")) == []


def test_an_unrelated_manifest_changes_nothing(
    registry: Registry, run_date: datetime.date, daily_manifest: Manifest
) -> None:
    """A Manifest for a table this Case does not read is ignored rather than grafted
    somewhere plausible. Without this, `trace_through` passing a manifest list from a whole
    write plan would contaminate every Case in it."""
    built = _lineage(registry, "accountable_by_day", run_date)
    traced = lineage_module.trace_through(built, [daily_manifest])
    assert traced.columns() == built.columns()
    assert networkx.utils.graphs_equal(traced.graph, built.graph)


def test_a_manifest_survives_the_json_round_trip_it_is_stored_as(
    registry: Registry, run_date: datetime.date, daily_manifest: Manifest
) -> None:
    """The Manifest is a checked-in artifact, so the trace a later Case gets is the one that
    came back off disk - not the one that was in memory when it was written.

    A round trip that dropped edge roles or the written Grain would still trace, and would
    trace to a slightly different set. That is the failure mode worth a test.
    """
    restored = Manifest.from_json(daily_manifest.to_json(), registry)
    assert restored.source == daily_manifest.source == "mart.delivery_health_daily"
    assert restored.written_by == "accountable_by_day"
    assert restored.written_at == daily_manifest.written_at
    assert networkx.utils.graphs_equal(
        restored.lineage.graph, daily_manifest.lineage.graph
    )

    built = _lineage(registry, "weekly_health_from_daily", run_date)
    assert lineage_module.trace_through(built, [restored]).upstream(
        "weekly_fees_charged"
    ) == lineage_module.trace_through(built, [daily_manifest]).upstream(
        "weekly_fees_charged"
    )


def test_a_manifest_for_a_target_missing_a_published_column_refuses(
    registry: Registry, run_date: datetime.date
) -> None:
    """A Manifest's output nodes are the written table's columns, and that is what a later
    Case traces THROUGH.

    A target that declares no column for one of the Case's outputs would get a Manifest
    describing a column the table does not have. Nothing fails at write time - Hive matches
    INSERT columns by position - and the mis-trace surfaces much later, as a reading Case
    whose Lineage attributes its numbers to the wrong upstream Source.
    """
    plan = _plan(registry, "accountable_by_day", run_date)
    short = Source(
        db="mart",
        table="health_daily_short",
        columns=(Column("dt_day", "STRING"), Column("carrier", "STRING")),
    )

    with pytest.raises(InvalidDeclaration) as refused:
        lineage_module.manifest_for(registry, plan, short)

    assert refused.value.subject == "source:mart.health_daily_short"
    assert "delivery_attempts" in refused.value.problem

    # The adjacent build: the target the fixture actually writes carries every output name.
    written = registry.source("mart.delivery_health_daily")
    assert lineage_module.manifest_for(registry, plan, written).source == written.qualified


def test_a_manifest_written_by_another_format_version_refuses(
    registry: Registry, daily_manifest: Manifest
) -> None:
    """A Manifest is read back out of a file some other version of this library wrote, so
    the version field is the one fact that must be checked before anything else in it is
    believed.

    Read anyway, a v2 document's missing or moved keys surface as a `KeyError` inside
    `from_json`, or - worse - as a trace that silently omits whatever the older format
    spelled differently. Either way the numbers a reader attributes to a Source come from a
    file this library cannot actually read.
    """
    forward = json.loads(daily_manifest.to_json())
    forward["version"] = 99

    with pytest.raises(InvalidDeclaration) as refused:
        Manifest.from_json(json.dumps(forward), registry)

    assert refused.value.subject == "manifest:mart.delivery_health_daily"
    assert "99" in refused.value.problem

    # The adjacent build: the version this library writes reads back.
    assert Manifest.from_json(daily_manifest.to_json(), registry).source == (
        "mart.delivery_health_daily"
    )


def test_the_write_plans_manifests_are_the_ones_that_trace(
    registry: Registry, run_date: datetime.date
) -> None:
    """The Manifests a write plan emits are what an execution script actually has in hand,
    so they are what the trace has to work from - not a Manifest a test built by itself."""
    statement_plan = write.plan(
        registry, [registry.case("accountable_by_day")], run_date=run_date
    )
    assert [manifest.source for manifest in statement_plan.manifests] == [
        "mart.delivery_health_daily"
    ]
    traced = lineage_module.trace_through(
        _lineage(registry, "weekly_health_from_daily", run_date),
        statement_plan.manifests,
    )
    assert "mart.deliveries.fee_amount" in traced.upstream("weekly_fees_charged")


# ======================================================================================
# The cross-check: sqlglot's own lineage over the emitted SQL
# ======================================================================================


def test_every_declared_case_is_cross_checked(registry: Registry) -> None:
    """`ALL_CASE_NAMES` is written out, so this is the pin that keeps it complete. A Case
    added to the fixture and not to that tuple would otherwise be parametrised over by
    nothing and reported as a pass."""
    assert tuple(case.name for case in registry.cases()) == ALL_CASE_NAMES


@pytest.mark.parametrize("case_name", ALL_CASE_NAMES)
def test_sqlglot_lineage_agrees_with_the_builder_on_every_outputs_source_columns(
    registry: Registry, run_date: datetime.date, case_name: str
) -> None:
    """The cross-check the design asks for. Disagreement is a builder bug.

    Two assertions per output, and they close from opposite sides:

    * the projection columns the builder claims equal the ones sqlglot reads out of the
      generated SQL - so the builder cannot attribute a column to the wrong Metric, and
      cannot claim one the statement does not read;
    * everything sqlglot found is somewhere in the builder's full upstream set - so a column
      that reaches a number through a Join path the builder models differently is still
      accounted for rather than dropped.
    """
    case: Case = registry.case(case_name)
    compiled = compile_module.compile_case(registry, case, run_date=run_date)
    built = compiled.lineage
    theirs = _sqlglot_source_columns(compiled.sql, registry)
    ours = _builder_projection_columns(compiled.plan, built)

    assert tuple(theirs) == built.outputs(), (
        "the emitted SQL publishes different output columns, or a different order, than the "
        "Lineage claims"
    )
    for output in built.outputs():
        assert ours[output] == theirs[output], (
            f"{case_name}:{output} - builder says {sorted(ours[output])}, "
            f"sqlglot reads {sorted(theirs[output])}"
        )
        assert theirs[output] <= built.upstream(output), (
            f"{case_name}:{output} - the SQL reads columns the Lineage does not record"
        )
        for column in theirs[output]:
            registry.resolve_column(column)  # refuses anything absent from a Declaration


def test_sqlglot_cross_check_sees_real_columns(
    registry: Registry, run_date: datetime.date
) -> None:
    """The comparison above is set equality, and two empty sets are equal. This is the guard
    that it is not comparing nothing: a `COUNT(*)` Metric genuinely has no source column, but
    most outputs do."""
    compiled = compile_module.compile_case(
        registry, registry.case("accountable_by_day"), run_date=run_date
    )
    theirs = _sqlglot_source_columns(compiled.sql, registry)
    assert theirs["fees_charged"] == {"mart.deliveries.fee_amount"}
    assert theirs["carrier"] == {"mart.carriers.carrier_name"}
    non_empty = [output for output, columns in theirs.items() if columns]
    assert len(non_empty) >= 5, theirs
    # COUNT(*) measures rows, not a column. Both sides say so, and that agreement is real.
    assert theirs["delivery_attempts"] == frozenset()
    built = _builder_projection_columns(compiled.plan, compiled.lineage)
    assert built["delivery_attempts"] == frozenset()


def test_placeholder_leaf_is_a_failure_not_a_pass(registry: Registry) -> None:
    """The degradation guard, exercised. sqlglot's lineage disables qualify's validation, so
    a column qualified by a table that is not in the FROM becomes an `exp.Placeholder` leaf
    instead of an error - and a cross-check that skipped it would compare a builder's claim
    against an empty set and call it agreement."""
    sql = "SELECT `y`.`fee_amount` AS `fees` FROM `mart`.`deliveries` AS `deliveries`"
    with pytest.raises(AssertionError, match="placeholder"):
        _sqlglot_source_columns(sql, registry)


def test_star_leaf_is_a_failure_not_a_pass(registry: Registry) -> None:
    """The other degradation: a star sqlglot cannot expand becomes a leaf named `"*"`. The
    schema this library supplies is always the whole declared one, so this should never
    happen - which is exactly why it has to fail loudly if it ever does."""
    sql = "SELECT * FROM `mart`.`undeclared_table` AS `undeclared_table`"
    with pytest.raises(AssertionError, match="star"):
        _sqlglot_source_columns(sql, registry)


# ======================================================================================
# The git-tracked artifacts: the static Lineage text and the Manifests beside it
# ======================================================================================


def test_the_static_artifact_traces_through_a_written_source_to_the_real_upstream(
    registry: Registry,
) -> None:
    """Decision 7's two halves, wired to each other.

    The artifact used to stop at `mart.delivery_health_daily`, which is the exact stop the
    Manifest exists to prevent: the committed record for the one Case that reads a written
    table said its numbers came from a TABLE rather than from Sources. The traced tree is
    derivable with nothing running and no `run_date` - a plan needs neither - so there was
    never a reason for it to be reachable only in-process.

    Both trees are asserted, because both are wanted: the first is what the statement
    literally reads, and it is the one under review as SQL.
    """
    artifact = lineage_module.static_lineage(registry, fixture.WEEKLY_HEALTH_FROM_DAILY)

    assert "as read:" in artifact and "traced to source:" in artifact
    assert "traces through: mart.delivery_health_daily (written by accountable_by_day)" in artifact
    assert "mart.deliveries.failure_reason" in artifact
    assert "mart.deliveries.fee_amount" in artifact
    assert "mart.carriers.carrier_name" in artifact

    as_read, traced = artifact.split("traced to source:")
    assert "mart.deliveries" not in as_read, (
        "the first tree must describe the statement, which reads only the written table"
    )
    assert "mart.deliveries" in traced


def test_a_case_that_reads_no_written_source_has_one_tree(registry: Registry) -> None:
    """The adjacent build: nothing to trace through means nothing traced, and no heading
    for a section that would be a copy of the one above it."""
    artifact = lineage_module.static_lineage(registry, fixture.ACCOUNTABLE_BY_DAY)

    assert "traced to source:" not in artifact
    assert "traces through:" not in artifact
    assert "writes: mart.delivery_health_daily" in artifact


def test_editing_the_producing_case_moves_the_reading_cases_artifact(
    registry: Registry,
) -> None:
    """The action at a distance this artifact exists to make reviewable.

    `weekly_health_from_daily` does not mention `accountable_by_day`'s Filters anywhere, and
    its SQL does not change when they do - the change is inside a table it reads. Before the
    trace was wired in, editing the producing Case left this file byte-identical, so the one
    artifact meant to catch action at a distance was blind to the only action at a distance
    the fixture has.
    """
    before = lineage_module.static_lineage(registry, fixture.WEEKLY_HEALTH_FROM_DAILY)

    narrowed = fixture.ACCOUNTABLE_BY_DAY.variant(
        "accountable_by_day",
        also_filtered_by=(fixture.DELIVERED_LATE,),
        writes_to=fixture.DELIVERY_HEALTH_DAILY,
    )
    edited = Registry(name="edited-producer")
    for declared in (
        *registry.sources(),
        *registry.metrics(),
        *registry.filters(),
        *(case for case in registry.cases() if case.name != "accountable_by_day"),
    ):
        edited.add(declared)
    edited.add(narrowed).freeze()

    after = lineage_module.static_lineage(edited, fixture.WEEKLY_HEALTH_FROM_DAILY)

    assert after != before
    assert "mart.deliveries.late_flag" in after
    assert "mart.deliveries.late_flag" not in before
    # ...while the SQL the reading Case emits is identical either way, which is why the
    # artifact is the only place this shows up at all.
    assert compile_module.compile_case(
        edited, fixture.WEEKLY_HEALTH_FROM_DAILY, run_date=datetime.date(2026, 9, 17)
    ).sql == compile_module.compile_case(
        registry, fixture.WEEKLY_HEALTH_FROM_DAILY, run_date=datetime.date(2026, 9, 17)
    ).sql


def test_manifests_are_written_where_from_json_can_read_them_back(
    registry: Registry, tmp_path
) -> None:
    """`Manifest.from_json` had no writer anywhere in the library.

    A Manifest round-trips through JSON precisely so a reader in another process can trace
    through a written table without re-deriving it - and until something wrote one, that
    reader had no file to open. The round trip is asserted by USING the file: the Manifest
    read back off disk traces a Case to the same upstream columns the in-memory one does.
    """
    written = lineage_module.write_manifests(registry, tmp_path)

    assert [path.name for path in written] == ["mart.delivery_health_daily.json"]

    restored = Manifest.from_json(written[0].read_text(encoding="utf-8"), registry)
    assert restored.source == "mart.delivery_health_daily"
    assert restored.written_by == "accountable_by_day"

    reading = _lineage(registry, "weekly_health_from_daily", datetime.date(2026, 9, 17))
    from_disk = lineage_module.trace_through(reading, [restored])
    in_memory = lineage_module.trace_through(
        reading, lineage_module.manifests_for_reads(registry, fixture.WEEKLY_HEALTH_FROM_DAILY)
    )

    assert from_disk.upstream("weekly_failure_rate") == in_memory.upstream(
        "weekly_failure_rate"
    )
    assert "mart.deliveries.failure_reason" in from_disk.upstream("weekly_failure_rate")


def test_rewriting_the_artifacts_is_a_no_op(registry: Registry, tmp_path) -> None:
    """Both artifacts are regenerated output that CI diffs, so a second run that changed
    them would make every review diff meaningless. Nothing in either carries a timestamp or
    a host name for the same reason."""
    first_lineage = lineage_module.write_static_lineage(registry, tmp_path / "lineage")
    first_manifests = lineage_module.write_manifests(registry, tmp_path / "manifests")
    contents = {path: path.read_bytes() for path in first_lineage + first_manifests}

    lineage_module.write_static_lineage(registry, tmp_path / "lineage")
    lineage_module.write_manifests(registry, tmp_path / "manifests")

    assert {path: path.read_bytes() for path in contents} == contents
    assert [path.name for path in first_lineage] == [
        f"{name}.txt" for name in ALL_CASE_NAMES
    ]
