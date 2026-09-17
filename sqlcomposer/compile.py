"""Case -> CasePlan -> sqlglot AST -> Hive SQL, with the resolution gate in the middle.

This module never executes anything. It returns a statement and its Lineage, and the caller
decides what to do with them.

`render()` does not accept a `Case`. It accepts a `CasePlan`, whose fields are the proofs
joins.py and grain.py searched for - so there is no way from a Case to SQL that skips the
refusals. Assembling a plan by hand is possible (Python cannot seal a constructor) and
`CasePlan.__post_init__` re-checks what it cheaply can, but the supported entry point is
`plan()`.

Three rendering disciplines are absolute here:

* Values enter the AST only through `ColumnRef.literal` / `Column.literal`. Never an
  f-string, never `.format`, never `maybe_parse` of an interpolated string. sqlglot escapes
  string-literal nodes and nothing else.
* Every generation call passes `unsupported_level=ErrorLevel.RAISE`. The default is WARN,
  which best-effort translates an unsupported construct into Hive that runs and means
  something else.
* `qualify()` runs as a gate before generation, against the WHOLE declared schema. It
  raises `OptimizeError` on an unknown column - a second, independent net under attribute
  access. Against an incomplete schema its star expansion silently no-ops, which is why the
  schema is never a subset.

Both of the sqlglot calls in this module - the gate and the one generation call - run inside
`errors.warnings_are_refusals()`. sqlglot degrades by logging rather than by raising in
several places, and a degradation nobody reads is indistinguishable from success.

This module holds no rendering knowledge of its own beyond assembly order. A value's literal
form belongs to the Column that declares it, a bucket's expression and a Metric's aggregate
belong to grain.py, and a JOIN clause belongs to joins.py; compile.py decides only what goes
where in the SELECT, and in which order the refusals run.
"""
from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import date
from typing import Final, Sequence

import sqlglot
from sqlglot import exp
from sqlglot.errors import OptimizeError, UnsupportedError
from sqlglot.optimizer.qualify import qualify as _qualify

from sqlcomposer import grain, joins, lineage
from sqlcomposer.declaration import ColumnRef, Predicate, Registry, Value
from sqlcomposer.errors import (
    ResolutionFailed,
    ScopeCollision,
    UnboundRunDate,
    UnsupportedConstruct,
    warnings_are_refusals,
)
from sqlcomposer.lineage import Lineage
from sqlcomposer.model import Case, CasePlan, Filter, Grain, Metric, MetricPlan

__all__ = [
    "DIALECT",
    "ERROR_LEVEL",
    "Compiled",
    "escalate_sqlglot_logging",
    "literal",
    "render_predicate",
    "render_metric",
    "plan",
    "build",
    "qualify_gate",
    "render",
    "compile_case",
    "compile_metric_only",
]

DIALECT: Final[str] = "hive"
"""The only dialect this library targets. A constant rather than a default argument in ten
places, so a later move to Spark is one edit - which is half the reason the ADR chose
sqlglot."""

ERROR_LEVEL: Final = sqlglot.ErrorLevel.RAISE
"""Passed to every `.sql()` call. sqlglot's default is WARN: an unsupported construct is
best-effort translated and merely logged, which is indistinguishable from success."""


@dataclass(frozen=True)
class Compiled:
    """One finished statement and everything known about it.

    Reads and writes share this type, so write.py adds no result type of its own. `ast` is
    kept alongside `sql` because the semantic-diff tests compare trees rather than text -
    `sqlglot.diff` returns edits in a non-deterministic order, so nothing may assert on
    edit order, but the trees themselves are stable.

    `ast` is the QUALIFIED tree, the one `sql` was generated from: backtick-quoted, with
    every table aliased by its bare name. `ast.sql(dialect=DIALECT)` reproduces `sql`
    exactly, which is the property the diff tests rely on; the pre-gate tree is not kept,
    because a tree that does not correspond to the emitted text is a trap.

    `run_date` records what a deferred Predicate was bound to, so a stored statement can be
    read back and understood without the caller remembering.
    """

    name: str
    sql: str
    ast: exp.Expr
    plan: CasePlan
    lineage: Lineage
    run_date: date | None = None


_escalation: contextlib.ExitStack | None = None
"""The open `warnings_are_refusals()` context installed by `escalate_sqlglot_logging()`.
Module state exists here only so the install is idempotent; nothing else reads it."""


def escalate_sqlglot_logging() -> None:
    """Install a permanent handler that turns sqlglot's warnings into refusals.

    Call once at process start. `errors.warnings_are_refusals()` is the scoped equivalent
    and is what the test suite uses; this is for an application entry point that wants the
    escalation for its whole life. Idempotent.

    Implemented as the scoped context manager entered and never exited, rather than as a
    second handler class: one definition of "a sqlglot warning is a refusal" is worth more
    than a few saved lines, and an ExitStack makes "already installed" a value to check
    rather than a handler list to scan.
    """
    global _escalation
    if _escalation is not None:
        return
    stack = contextlib.ExitStack()
    stack.enter_context(warnings_are_refusals())
    _escalation = stack


def literal(ref: ColumnRef, value: Value, *, run_date: date | None = None) -> exp.Expr:
    """A Python value as an AST node, rendered for this column.

    A pass-through to `ColumnRef.literal`, re-exported so that everything the rendering
    discipline needs is reachable from this module. Bare literal on a Partition column
    (`exp.convert`'s CAST defeats pruning), `exp.convert` otherwise, and the declared-type
    check on the way through.

    It stays a one-line delegation on purpose: two implementations of "a value becomes a
    node" is exactly one more than the discipline can survive.
    """
    return ref.literal(value, run_date=run_date)


def render_predicate(predicate: Predicate, *, run_date: date | None = None) -> exp.Condition:
    """Build a Predicate's condition, raising `UnboundRunDate` if it is deferred and
    `run_date` is None.

    The refusal is raised here, up front, rather than being left to the `RunDate` deep
    inside the builder closure: both refuse, but this one can name the whole predicate
    (`mart.deliveries.dt BETWEEN run_date-6 AND run_date`) instead of the single offset that
    happened to be reached first, and a contributor reading the message needs the Filter,
    not the offset.
    """
    if predicate.deferred and run_date is None:
        raise UnboundRunDate(subject=predicate.text, text=predicate.text)
    return predicate.to_sqlglot(run_date=run_date)


def render_metric(plan: MetricPlan, *, run_date: date | None = None) -> exp.Alias:
    """A planned Metric's SELECT entry. Delegates to `grain.render_metric`.

    The aggregate, the re-aggregation and the ratio re-derivation are grain.py's, because
    they are the same knowledge the re-grain proof is made of, and splitting it across two
    modules is how the proof and the SQL come to disagree.
    """
    return grain.render_metric(plan, run_date=run_date)


def plan(registry: Registry, case: Case, *, run_date: date | None = None) -> CasePlan:
    """Resolve a Case into a plan, running every build-time refusal.

    In order: `registry.require_frozen`, resolve the Tag family, `joins.resolve` for the
    spine and path (`NoJoinPath` / `AmbiguousJoinPath`), `joins.check_fan_out` (`FanOut`),
    `grain.plan_metrics` (`UnsafeReAggregation` / `GrainTooFine` / `GrainNotComparable`).

    The order is part of the contract, not an implementation detail: a Case with both an
    ambiguous Join path and an unsafe re-grain must report the path first, because the path
    determines which Sources the Metrics are measured over and so can change the re-grain
    answer. Fan-out is checked before the Metrics are planned for the same reason.

    `run_date` is carried on the plan rather than used here: nothing in planning depends on
    the date, but `build()` needs it and a plan that quietly loses it would render a
    different statement than the one that was checked.

    One refusal runs before the Join path, because it needs neither: a Case-level Filter that
    is also a resolved Metric's scoped `when` (`ScopeCollision`). It is checked first because
    it is a fact about the Case's own declaration rather than about the Join graph, and
    because the Metric it names is wrong at every Grain and over every Join path.
    """
    registry.require_frozen("compile.plan")
    metrics = case.resolved_metrics(registry)
    _check_scopes(case, metrics)
    spine, path = joins.resolve(registry, case)
    joins.check_fan_out(spine, path, metrics)
    metric_plans = grain.plan_metrics(
        registry, metrics, case.grain, spine=spine, path=path
    )
    return CasePlan(
        case=case,
        spine=spine,
        path=path,
        metrics=metric_plans,
        dimensions=case.grain.dimensions,
        filters=case.filters,
        run_date=run_date,
    )


def _scoped_filters(metric: Metric) -> tuple[Filter, ...]:
    """Every `when` Filter attached to this Metric or to a ratio's components."""
    found: list[Filter] = []
    if metric.when is not None:
        found.append(metric.when)
    for part in metric.components:
        found.extend(_scoped_filters(part))
    return tuple(found)


def _check_scopes(case: Case, metrics: Sequence[Metric]) -> None:
    """Refuse a Case-level Filter that is also a Metric's scope.

    Matched by identity OR by name. Identity is the common shape - one module-level Filter
    object referenced twice - and the name catches the same predicate declared twice, which
    compiles to exactly the same tautology.

    The affected outputs include any ratio whose component is the scoped Metric, because
    that is the column whose wrongness is hardest to see: `failed_deliveries` merely
    duplicates another column, while `failure_rate` reads 1.0 and looks like a catastrophe
    rather than a bug.
    """
    scoped_by: dict[str, list[str]] = {}
    for metric in metrics:
        for filter_ in _scoped_filters(metric):
            scoped_by.setdefault(filter_.name, []).append(metric.name)
    for case_filter in case.filters:
        affected = scoped_by.get(case_filter.name)
        if affected:
            raise ScopeCollision(
                case=case.name,
                filter=case_filter.name,
                metric=affected[0],
                outputs=tuple(sorted(set(affected))),
            )


def build(registry: Registry, case_plan: CasePlan) -> exp.Select:
    """Assemble the SELECT for a planned Case. No gate, no generation - just the tree.

    `SELECT <dimensions in Grain order>, <metrics in plan order> FROM <spine>
    <joins from the path> WHERE <Case filters ANDed> GROUP BY <dimension expressions>`.

    No ORDER BY and no LIMIT: neither is settled scope, and a Case that wants either has no
    way through this API. If that turns out to be common the honest fix is a field on
    Case, not string manipulation on the result - which is exactly the habit the rendering
    discipline exists to prevent.

    Metric-scoped `when` Filters become conditional aggregates and never reach the WHERE
    clause; moving one there would silently narrow every other Metric in the Case.

    Everything is read off the plan, never off `case_plan.case`: the plan's `dimensions`,
    `filters` and `run_date` are what was proved, and a plan whose fields have been narrowed
    relative to its Case must render what it proved. `registry` is used for one thing only -
    refusing an unfrozen Registry, because building a tree from Declarations whose
    cross-checks never ran is compiling against an unchecked warehouse.

    A Grain with no Dimensions is ordinary and renders with no GROUP BY: one row, every
    Metric over the whole filtered Source.
    """
    registry.require_frozen("compile.build")

    projections: list[exp.Expr] = [
        grain.projection(dimension) for dimension in case_plan.dimensions
    ]
    projections += [
        render_metric(metric_plan, run_date=case_plan.run_date)
        for metric_plan in case_plan.metrics
    ]

    select = sqlglot.select(*projections).from_(case_plan.spine.to_sqlglot())
    select = joins.apply(select, case_plan.path)

    predicate = _filters_predicate(case_plan)
    if predicate is not None:
        select = select.where(render_predicate(predicate, run_date=case_plan.run_date))

    grouping = grain.group_by(Grain(dimensions=case_plan.dimensions))
    if grouping:
        select = select.group_by(*grouping)
    return select


def _filters_predicate(case_plan: CasePlan) -> Predicate | None:
    """The plan's Case-level Filters ANDed, or None when there are none.

    `Case.predicate()` answers the same question for a Case; this asks it of the plan,
    because the plan is what was proved and a hand-built plan may carry fewer Filters than
    its Case does. Metric-scoped `when` Filters are not here and must never be: they are
    conditional aggregates, and one of them in the WHERE clause silently narrows every other
    Metric in the same SELECT.
    """
    if not case_plan.filters:
        return None
    combined = case_plan.filters[0].predicate
    for filter_ in case_plan.filters[1:]:
        combined = combined & filter_.predicate
    return combined


def qualify_gate(registry: Registry, ast: exp.Expr, *, case: str = "") -> exp.Expr:
    """Run `qualify()` as a resolution gate, wrapping its failure as `ResolutionFailed`.

    `qualify(ast, schema=registry.schema(), dialect=DIALECT)` raises `OptimizeError` on a
    column no Declaration carries, and also backtick-quotes and aliases everything - so the
    tree that comes back is the tree that gets rendered, and golden SQL must be written
    against the qualified form.

    Always against `registry.schema()` entire. A partial schema turns qualify's star
    expansion into a silent no-op, which converts this gate into decoration.

    Returns the qualified tree; does not mutate the one passed in.

    Two details learned while implementing. qualify() rewrites its argument in place and
    returns it, so the copy is what keeps that promise - callers that keep the pre-gate tree
    for a diff depend on it. And the gate runs inside `warnings_are_refusals()`: qualify
    reports some of its own degradations through sqlglot's logger rather than by raising,
    and an unread log line here is a resolution failure that reaches production as SQL.
    """
    try:
        with warnings_are_refusals():
            return _qualify(ast.copy(), schema=registry.schema(), dialect=DIALECT)
    except OptimizeError as err:
        raise ResolutionFailed(case=case or "(unnamed)", sqlglot_message=str(err)) from err


def render(ast: exp.Expr, *, dialect: str = DIALECT) -> str:
    """Generate SQL. The only `.sql()` call in the library.

    Runs inside `errors.warnings_are_refusals()` and passes
    `unsupported_level=ErrorLevel.RAISE`, so a construct Hive cannot express raises
    `UnsupportedConstruct` instead of being best-effort translated with a log line nobody
    reads.

    The refusal it raises names the tree rather than a Case, because a tree does not know
    which Case it came from; `compile_case` re-raises it naming the Case, which is the
    version a contributor sees.
    """
    try:
        with warnings_are_refusals():
            return ast.sql(dialect=dialect, unsupported_level=ERROR_LEVEL)
    except UnsupportedError as err:
        raise UnsupportedConstruct(
            case=f"render:{type(ast).__name__.lower()}", sqlglot_message=str(err)
        ) from err


def compile_case(
    registry: Registry,
    case: Case,
    *,
    run_date: date | None = None,
) -> Compiled:
    """The whole read path: plan, build, gate, render, and derive the Lineage.

    `run_date` is required when any of the Case's Filters holds a `RunDate`
    (`Case.deferred`); omitting it raises `UnboundRunDate` rather than substituting today,
    because a statement silently built for the wrong day is a wrong number with a plausible
    shape. The check is made here, before any planning, so the refusal costs nothing and
    names the Case and the Filter that needs the date rather than surfacing from inside a
    predicate builder half a tree later.

    A Metric-scoped `when` Filter can be deferred too, and `Case.deferred` does not see it -
    that one refuses later, from `grain.aggregate_expression`, still before any SQL exists.

    Returns a `Compiled` whose `lineage` is builder-derived from the plan, never from the
    SQL - sqlglot's own lineage disables qualify's validation internally and degrades to
    placeholder leaves, so it is a test-suite cross-check and never a runtime source.
    """
    _require_run_date(case, run_date)
    case_plan = plan(registry, case, run_date=run_date)
    tree = build(registry, case_plan)
    qualified = qualify_gate(registry, tree, case=case.name)
    try:
        sql = render(qualified)
    except UnsupportedConstruct as err:
        raise UnsupportedConstruct(
            case=case.name, sqlglot_message=err.sqlglot_message
        ) from err
    return Compiled(
        name=case.name,
        sql=sql,
        ast=qualified,
        plan=case_plan,
        lineage=lineage.build(registry, case_plan),
        run_date=run_date,
    )


def _require_run_date(case: Case, run_date: date | None) -> None:
    """Refuse a deferred Case compiled without the date it was deferred for."""
    if run_date is not None or not case.deferred:
        return
    deferred = next(filter_ for filter_ in case.filters if filter_.deferred)
    raise UnboundRunDate(
        subject=f"{case.name}.filters[{deferred.name}]", text=deferred.predicate.text
    )


def compile_metric_only(
    registry: Registry,
    metric: Metric,
    *,
    run_date: date | None = None,
) -> str:
    """One Metric's aggregate expression as Hive text, for error messages and tests.

    Not a statement and not part of the read path. It exists because a refusal that names a
    Metric is much easier to act on when a contributor can see what that Metric actually
    compiles to.

    What comes back is the aggregate over ATOMIC rows - `COUNT(CASE WHEN ... THEN 1 END)`,
    `SUM(fee_amount)` - with no FROM, no Grain and therefore no re-aggregation. That is
    deliberate:
    the question it answers is "what does this Metric mean", and a Metric read from a
    pre-aggregated Source renders differently in a real Case depending on the Grain asked
    for, which is precisely the thing this function must not pretend to know.

    Unqualified, too: there is no schema to resolve a bare expression against, so the gate
    does not run and identifiers appear as the Declaration spells them. `registry` is taken
    for the registry-first convention and to keep the signature stable if that ever changes;
    a Metric already carries the Source it measures, so nothing here needs to look anything
    up. It is not consulted, which also means a ratio's unregistered components render fine.
    """
    return render(grain.aggregate_expression(metric, run_date=run_date))
