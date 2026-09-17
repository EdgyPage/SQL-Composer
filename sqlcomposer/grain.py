"""Re-aggregation safety and time bucketing.

The refusal that lives here is the subtlest of the four, because the SQL it prevents is
perfectly valid SQL that returns a perfectly reasonable number. SUM rolls up. COUNT rolls up
by SUM, not by COUNT. COUNT(DISTINCT) does not roll up at all. An average of averages is
wrong, and a ratio must be re-derived from re-aggregated numerator and denominator rather
than averaged. None of those produce an error in Hive; all of them produce a number.

The check is total, which is what makes it trustworthy. A Metric's native Grain comes from
the Source it measures, not from the Metric: `Registry.native_grain` returns None for atomic
rows, where computing from scratch is always safe, and a Grain for a pre-aggregated or
written Source. Then: equal Grains are identity; a target this Grain coarsens into consults
the Re-aggregation rule; a strictly finer target is `GrainTooFine`; and one that does not
nest in either direction is `GrainNotComparable`. The last case is not an edge case - WEEK
and MONTH are deliberately incomparable because ISO weeks straddle month boundaries.

Time bucketing renders through DATE_FORMAT masks and `exp.Anonymous`, never `exp.func`.
Verified against sqlglot 30.18.0: `exp.func("trunc", col, "MM")` builds a generic `Trunc`
node that RAISES `UnsupportedError` when targeting Hive under `ErrorLevel.RAISE`.

Two things learned while implementing, both worth carrying:

* Every bucket except HOUR renders as a `yyyy-MM-dd` date string - the first day of the
  week, month, quarter or year - rather than as a period number. A week number collides
  across years, `2026-Q1` does not join to anything, and a written Source's bucket column
  has to keep one stable type whichever bucket produced it.
* Bucketing a Partition column in the GROUP BY does NOT narrow the scan, and nothing here
  can make it. Partition pruning comes from a Filter comparing the RAW partition column to
  a bare literal (`Column.literal` on a Partition column exists for that). A bucket
  expression must therefore never migrate into a predicate: `DATE_FORMAT(dt, 'yyyy-MM-01')
  = '2026-01-01'` reads every Partition of the Source. Grouping by it is free; filtering by
  it is a full scan.
"""
from __future__ import annotations

from datetime import date
from typing import Sequence

from sqlglot import exp

from sqlcomposer.declaration import (
    ColumnRef,
    JoinPath,
    JoinStep,
    Registry,
    Source,
    TimeBucket,
    hive_type,
)
from sqlcomposer.errors import (
    GrainNotComparable,
    GrainTooFine,
    InvalidDeclaration,
    UnsafeReAggregation,
)
from sqlcomposer.model import (
    Aggregate,
    Dimension,
    Grain,
    Metric,
    MetricPlan,
    ReAggregation,
)

__all__ = [
    "bucket_expression",
    "group_by",
    "projection",
    "native_grain",
    "determines",
    "check_regrain",
    "plan_metric",
    "plan_metrics",
    "aggregate_expression",
    "reaggregate",
    "rederive",
    "render_metric",
]

# --------------------------------------------------------------------------------------
# Time bucketing
# --------------------------------------------------------------------------------------

_DAY_MASK = "yyyy-MM-dd"
_YEAR_MASK = "yyyy-01-01"

_MASKS: dict[TimeBucket, str] = {
    TimeBucket.HOUR: "yyyy-MM-dd HH:00:00",
    TimeBucket.DAY: _DAY_MASK,
    TimeBucket.MONTH: "yyyy-MM-01",
    TimeBucket.YEAR: _YEAR_MASK,
}
"""Java SimpleDateFormat masks, which is what Hive's DATE_FORMAT takes. The digits in
`yyyy-MM-01` are literal - only letters are pattern characters - so the mask truncates and
formats in one call, and the result is still a date."""

_BUCKETABLE = exp.DataType.TEXT_TYPES | exp.DataType.TEMPORAL_TYPES
"""Declared types DATE_FORMAT can read. A BIGINT `20260102` is not one of them: Hive
returns NULL for it rather than failing, which would publish a Grain column of NULLs."""

_DATE_ONLY = {exp.DataType.Type.DATE, exp.DataType.Type.DATE32}
"""Types that carry no time of day. An HOUR bucket over one of these is every row at
midnight - a daily number wearing an hourly label."""


def _anonymous(name: str, *arguments: exp.Expr) -> exp.Anonymous:
    """A Hive-only function call sqlglot will not try to translate.

    `exp.func(name, ...)` resolves to a typed node where one exists (`Trunc`, `DateAdd`),
    and those RAISE for Hive under `ErrorLevel.RAISE`. `Anonymous` is passed through
    verbatim, which is the whole point when the target dialect is the only dialect.
    """
    return exp.Anonymous(this=name, expressions=list(arguments))


def bucket_expression(column: ColumnRef, bucket: TimeBucket) -> exp.Expr:
    """The Hive expression that truncates a column to a time bucket.

    Built as `exp.Anonymous(this="date_format", expressions=[...])` with an explicit mask,
    or as `exp.Anonymous(this="next_day"/"date_sub", ...)` for WEEK - never through
    `exp.func`, which builds a generic node sqlglot refuses to render for Hive under
    `ErrorLevel.RAISE`.

    The column may be declared STRING (the standard shape for a `yyyy-MM-dd` Hive partition
    column), DATE or TIMESTAMP. WEEK means the ISO week, anchored to Monday, and is rendered
    as the date of that Monday so the bucket sorts and joins as a date rather than as a week
    number - a week number collides across years. QUARTER is likewise the quarter's first
    day, built from ADD_MONTHS and QUARTER because no single mask can express it.

    The returned node is the GROUP BY expression and the SELECT expression both; it must be
    deterministic so the two are textually identical. Nothing here is cached or shared:
    every call builds fresh nodes, because sqlglot nodes carry a parent pointer and reusing
    one in two trees corrupts both.

    Two findings the frozen docstring anticipated differently:

    * No CAST is needed anywhere. Hive's DATE_FORMAT, NEXT_DAY and QUARTER all accept a
      string, a date or a timestamp, and the WEEK path normalises through
      `DATE_FORMAT(x, 'yyyy-MM-dd')` first, so all three declared shapes land on the same
      `yyyy-MM-dd` text. A CAST would only add a node for Hive to undo.
    * Two declared types are refused rather than bucketed, because Hive answers both with a
      silent NULL rather than an error: a non-temporal, non-text column (an epoch BIGINT,
      say), and an HOUR bucket over a DATE column, whose time of day does not exist.
    """
    kind = hive_type(column.type).this
    if kind not in _BUCKETABLE:
        raise InvalidDeclaration(
            subject=column.qualified,
            problem=f"{column.qualified} is declared {column.type}, which Hive's "
            f"DATE_FORMAT cannot read, so bucketing it by {bucket.value} would publish a "
            "Grain column of NULLs",
            remedy="bucket a STRING, DATE or TIMESTAMP column; an epoch or yyyyMMdd "
            "integer needs a declared view column of a date type first",
        )
    if bucket is TimeBucket.HOUR and kind in _DATE_ONLY:
        raise InvalidDeclaration(
            subject=column.qualified,
            problem=f"{column.qualified} is declared {column.type} and carries no time of "
            "day, so an HOUR bucket is a daily number labelled hourly",
            remedy="report this column at DAY or coarser, or bucket a TIMESTAMP column",
        )
    if bucket is TimeBucket.WEEK:
        # NEXT_DAY(d, 'MO') is the first Monday strictly after d, so backing up seven days
        # is the Monday of d's own week - for a Monday and for a Sunday alike.
        return _anonymous(
            "date_sub",
            _anonymous(
                "next_day",
                _anonymous("date_format", column.to_sqlglot(), exp.Literal.string(_DAY_MASK)),
                exp.Literal.string("MO"),
            ),
            exp.Literal.number(7),
        )
    if bucket is TimeBucket.QUARTER:
        # First day of the year, then (quarter - 1) * 3 months on. ADD_MONTHS returns
        # yyyy-MM-dd text, so a quarter bucket has the same type as every other bucket.
        months = exp.Mul(
            this=exp.Paren(
                this=exp.Sub(
                    this=_anonymous("quarter", column.to_sqlglot()),
                    expression=exp.Literal.number(1),
                )
            ),
            expression=exp.Literal.number(3),
        )
        return _anonymous(
            "add_months",
            _anonymous("date_format", column.to_sqlglot(), exp.Literal.string(_YEAR_MASK)),
            months,
        )
    mask = _MASKS.get(bucket)
    if mask is None:  # a TimeBucket member added without a rendering
        raise InvalidDeclaration(
            subject=column.qualified,
            problem=f"TimeBucket.{bucket.name} has no Hive rendering in grain.py",
            remedy="add its DATE_FORMAT mask to grain._MASKS, or its own branch where no "
            "single mask expresses it",
        )
    return _anonymous("date_format", column.to_sqlglot(), exp.Literal.string(mask))


def _dimension_expression(dimension: Dimension) -> exp.Expr:
    """A Dimension as one expression: bucketed when it carries a bucket, bare otherwise."""
    if dimension.bucket is None:
        return dimension.column.to_sqlglot()
    return bucket_expression(dimension.column, dimension.bucket)


def group_by(grain: Grain) -> tuple[exp.Expr, ...]:
    """The GROUP BY expressions for a Grain, in Grain order.

    Grouping by the expression rather than by output position or alias: Hive resolves an
    alias in GROUP BY inconsistently across versions, and positional grouping silently
    re-points when a column is inserted.
    """
    return tuple(_dimension_expression(dimension) for dimension in grain.dimensions)


def projection(dimension: Dimension) -> exp.Alias:
    """A Dimension's SELECT entry: its expression aliased to `Dimension.name`.

    Bucketed through `bucket_expression` when `dimension.bucket` is set, a bare column node
    otherwise. Unquoted here on purpose - `compile.qualify_gate` backtick-quotes the whole
    tree, and quoting twice is how a golden-SQL file starts disagreeing with itself.
    """
    return exp.alias_(_dimension_expression(dimension), dimension.name)


# --------------------------------------------------------------------------------------
# Native Grain, and the Dimensions that do not count as a re-grain
# --------------------------------------------------------------------------------------


def native_grain(registry: Registry, source: Source) -> Grain | None:
    """The Grain `source`'s rows are already collapsed to, or None for atomic rows.

    A thin pass-through to `Registry.native_grain`, re-exported here so that everything a
    re-grain check needs is reachable from one module. None is the permissive answer and it
    is the default: a Source with neither `written_by` nor a declared `grain` is treated as
    atomic, which silently disables this whole check for it. That is the one place in the
    design where the default is permissive rather than refusing, and it is why declaring
    `grain` on a Source another pipeline has already coarsened matters.
    """
    return registry.native_grain(source)


def _walk_between(frm: Source, to: Source, path: JoinPath) -> tuple[JoinStep, ...] | None:
    """The oriented steps leading from `frm` to `to` along `path`, or None if unreachable.

    `path` is oriented from the spine, but a Metric's Source is not always the spine, so a
    stretch of it may have to be walked backwards - `JoinStep.inverted()` flips the declared
    Cardinality with it, which is exactly the fact `determines` needs. A CasePlan's path
    visits each Source once, so it is a tree and the stretch between two of its Sources is
    unique; a breadth-first walk finds it without any choice to make.
    """
    if frm.qualified == to.qualified:
        return ()
    adjacency: dict[str, list[JoinStep]] = {}
    for step in path:
        for oriented in (step, step.inverted()):
            adjacency.setdefault(oriented.frm.qualified, []).append(oriented)
    seen = {frm.qualified}
    queue: list[tuple[str, tuple[JoinStep, ...]]] = [(frm.qualified, ())]
    while queue:
        node, so_far = queue.pop(0)
        for step in adjacency.get(node, ()):
            if step.to.qualified in seen:
                continue
            walked = so_far + (step,)
            if step.to.qualified == to.qualified:
                return walked
            seen.add(step.to.qualified)
            queue.append((step.to.qualified, walked))
    return None


def determines(
    dimension: Dimension,
    metric: Metric,
    spine: Source,
    path: JoinPath,
) -> bool:
    """True when grouping by `dimension` only relabels `metric`'s rows rather than splitting
    them.

    A Dimension on the Metric's own Source always refines. A Dimension on another Source
    reached over edges that each determine their right-hand side (MANY_TO_ONE or ONE_TO_ONE
    from the Metric's Source outward) attaches at most one value per row, so grouping by it
    is a relabelling - which is what lets a Case report a delivery Metric by the courier's
    city without that counting as a re-grain the Metric has to survive.

    The same declared Cardinality that detects Fan-out buys this back; that symmetry is
    deliberate.

    Every uncertain answer is False, because False is the answer that makes the caller
    check: a Dimension on a Source this path never reaches, or one reached over a
    ONE_TO_MANY or MANY_TO_MANY edge, is treated as refining and therefore has to be
    survivable by the Metric's Re-aggregation rule. `spine` is what makes "never reaches"
    decidable when `path` is empty and the Case reads one Source.
    """
    if dimension.source.qualified == metric.source.qualified:
        return False
    reached = {spine.qualified} | {step.to.qualified for step in path}
    if metric.source.qualified not in reached or dimension.source.qualified not in reached:
        return False
    walked = _walk_between(metric.source, dimension.source, path)
    if walked is None:
        return False
    return all(step.cardinality.determines_right for step in walked)


def _relabelling_removed(
    target: Grain,
    metric: Metric,
    spine: Source,
    path: JoinPath,
) -> Grain:
    """`target` minus the Dimensions that merely relabel `metric`'s rows.

    What is left is the Grain the Metric genuinely has to be reported at, and it is what
    `check_regrain` is asked about. The full `target` still reaches the MetricPlan, because
    the SELECT and the GROUP BY are built from the Case's Grain and not from this.
    """
    kept = tuple(
        dimension
        for dimension in target.dimensions
        if not determines(dimension, metric, spine, path)
    )
    if len(kept) == len(target.dimensions):
        return target
    return Grain(dimensions=kept)


# --------------------------------------------------------------------------------------
# The re-grain proof
# --------------------------------------------------------------------------------------


def _same_grain(left: Grain, right: Grain) -> bool:
    """Mutual coarsening rather than `==`.

    Two Grains that roll up into each other are the same Grain even when their Dimensions
    differ in alias or declaration order, and `MetricPlan.__post_init__` asks the question
    this way too. Structural equality here would refuse a Case for renaming a column in its
    output.
    """
    return left.coarsens(right) and right.coarsens(left)


def _missing_from(native: Grain, target: Grain) -> tuple[str, ...]:
    """The output names `target` asks for that `native` cannot supply - a GrainTooFine list."""
    return tuple(
        dimension.name
        for dimension in target.dimensions
        if not any(stored.coarsens_to(dimension) for stored in native.dimensions)
    )


def check_regrain(metric: Metric, *, native: Grain | None, target: Grain) -> ReAggregation:
    """Decide how `metric` is computed at `target`, or refuse.

    Returns the `ReAggregation` that applies for this particular re-grain:

    * `native is None` (atomic rows) - the Metric is computed from scratch, and the rule
      returned is the one that would apply to its partials, so a caller can record it.
    * `native == target` - identity; the stored values are read as they are.
    * `target` coarsens `native` - consults `metric.reaggregation`, and raises
      `UnsafeReAggregation` when it is `ReAggregation.NONE`.
    * `native` strictly coarsens `target` - `GrainTooFine`, naming the Dimensions the stored
      Source does not carry.
    * neither coarsens the other - `GrainNotComparable`.

    A ratio is never refused for being a ratio: `REDERIVE` is returned and the caller plans
    its components, each of which is checked on its own.

    "Equal" is mutual coarsening, not `==`. Note what that makes of a bucket: an unbucketed
    Dimension and a DAY-bucketed one over the same column do not coarsen each other in
    either direction (`Dimension.coarsens_to` refuses to guess), so a Case reading a written
    Source has to carry the same bucket the writing Case did. Dropping the bucket there is
    `GrainNotComparable`, which is the loud version of a mistake whose quiet version is a
    column of NULLs.
    """
    if native is None:
        return metric.reaggregation
    if _same_grain(native, target):
        return metric.reaggregation
    if target.coarsens(native):
        rule = metric.reaggregation
        if not rule.is_provable:
            raise UnsafeReAggregation(
                metric=metric.name,
                rule=rule.value,
                native=str(native),
                target=str(target),
            )
        return rule
    if native.coarsens(target):
        raise GrainTooFine(
            metric=metric.name,
            native=str(native),
            target=str(target),
            offending=_missing_from(native, target),
        )
    raise GrainNotComparable(metric=metric.name, native=str(native), target=str(target))


def _check_stored_rule(
    registry: Registry,
    metric: Metric,
    rule: ReAggregation,
    *,
    native: Grain,
    target: Grain,
) -> None:
    """Refuse a re-aggregation whose rule contradicts the rule the stored numbers were
    written by.

    `check_regrain` asks the READING Metric whether it may be recomputed, which is the
    whole question when the Metric measures atomic rows. Against a written Source it is
    only half of one: the reading Metric is a fresh Declaration, so nothing stops a
    contributor writing `sum_of("weekly_couriers", DAILY.active_couriers)` over a column
    that holds a COUNT(DISTINCT), or `sum_of("weekly_rate", DAILY.failure_rate)` over a
    column that holds a ratio. Both are well-formed SUMs of well-typed columns, both run,
    and both are wrong - the same two wrong numbers decision 3 exists to refuse, arriving
    by a different door.

    `Registry.metric_behind` is the hop that closes it: given a column of a written Source
    it recovers the Metric that put the numbers there, and therefore the Re-aggregation
    rule that actually governs them. The reading Metric must claim that same rule or the
    build fails.

    Two deliberate limits. The check only runs when a re-aggregation is genuinely happening -
    at the stored Grain each group holds one row, so any rule reads the stored value back
    unchanged and refusing there would be a refusal of something provably safe. And it is
    silent for a Source this library does not write: `metric_behind` returns None for a
    pre-aggregated Source produced elsewhere, so its stored rules live in `Column.note` and
    are checked by nothing. That is the same ceiling Fan-out detection has against a
    mis-annotated Cardinality.
    """
    if metric.column is None:
        # A ratio, or a COUNT of the stored rows. Neither reads a stored partial: the
        # ratio's components are planned separately and checked on their own terms, and
        # counting rows at a coarser Grain equals summing the partial counts.
        return
    produced = registry.metric_behind(metric.column)
    if produced is None or produced.reaggregation is rule:
        return
    raise UnsafeReAggregation(
        metric=metric.name,
        rule=produced.reaggregation.value,
        native=str(native),
        target=str(target),
        stored_by=produced.name,
        reading=metric.column.qualified,
        declared_rule=rule.value,
    )


def plan_metric(
    registry: Registry,
    metric: Metric,
    target: Grain,
    *,
    spine: Source,
    path: JoinPath,
) -> MetricPlan:
    """Prove that one Metric can be reported at one Grain, or refuse.

    Resolves the Metric's native Grain from the Source it measures, drops the Dimensions of
    `target` that merely relabel it (see `determines`), runs `check_regrain` on what is
    left, and recurses into a ratio's components so that each is proven on its own terms.

    The returned `MetricPlan` always carries `target=target` - `CasePlan.__post_init__`
    re-checks that - and carries the Metric's native Grain so lineage.py can record what the
    numbers were rolled up from.

    A ratio is planned before its components, so a Grain refusal names the ratio a
    contributor put in the Case rather than a component they may never have written down.

    When the Metric measures a Source this library WRITES, one more refusal runs after
    `check_regrain`: the reading Metric's rule has to match the rule of the Metric that
    produced the stored column (`_check_stored_rule`). `check_regrain` only ever asks the
    reading Metric, and against a written Source that is half a question - the reading
    Metric is a fresh Declaration and can claim any rule it likes about numbers it did not
    produce.

    One conservative extra refusal, forced by `MetricPlan.__post_init__`: a `NONE` rule is
    only representable when `native` is None or equals the FULL target, so a stored
    COUNT(DISTINCT) read at exactly its own Grain but reported alongside a relabelling
    Dimension is refused here as `UnsafeReAggregation`, even though the relabelling cannot
    change its value. Refusing a provably-safe read is the wrong-way error, but it is the
    one the frozen plan type can express, and `UnsafeReAggregation` is the refusal that type
    says should have been raised.
    """
    native = native_grain(registry, metric.source)
    reported_at = _relabelling_removed(target, metric, spine, path)
    rule = check_regrain(metric, native=native, target=reported_at)
    if native is not None and not _same_grain(native, reported_at):
        # A genuine re-aggregation, so the rule the stored numbers were WRITTEN under has to
        # agree
        # with the one this Metric claims. check_regrain only asked the reading Metric.
        _check_stored_rule(registry, metric, rule, native=native, target=target)
    if rule is ReAggregation.NONE and native is not None and not _same_grain(native, target):
        raise UnsafeReAggregation(
            metric=metric.name,
            rule=rule.value,
            native=str(native),
            target=str(target),
        )
    parts: tuple[MetricPlan, MetricPlan] | None = None
    if metric.is_ratio:
        numerator, denominator = metric.components
        parts = (
            plan_metric(registry, numerator, target, spine=spine, path=path),
            plan_metric(registry, denominator, target, spine=spine, path=path),
        )
    return MetricPlan(metric=metric, target=target, rule=rule, native=native, parts=parts)


def plan_metrics(
    registry: Registry,
    metrics: Sequence[Metric],
    target: Grain,
    *,
    spine: Source,
    path: JoinPath,
) -> tuple[MetricPlan, ...]:
    """`plan_metric` for each Metric, in the order given.

    Callers pass Metrics already sorted by name (`Case.resolved_metrics` does), and this
    preserves that order, so the SELECT list, the golden SQL and the Lineage artifact all
    agree. Raises on the first Metric that cannot be planned rather than collecting
    failures: the first refusal is the one a contributor acts on.
    """
    return tuple(
        plan_metric(registry, metric, target, spine=spine, path=path) for metric in metrics
    )


# --------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------


def _measured_column(metric: Metric) -> exp.Column:
    """The column this aggregate reads, as a fresh node.

    `Metric.__post_init__` already refuses an aggregate that needs a column without one, so
    this refusal is unreachable through the declared API. It is a refusal rather than an
    `assert` because `assert` disappears under `python -O`, and what it would leave behind
    is `SUM()` - a syntax error at best and an argument with the warehouse at worst.
    """
    if metric.column is None:
        raise InvalidDeclaration(
            subject=f"metric:{metric.name}",
            problem=f"{metric.aggregate.value} needs a column to aggregate and this Metric "
            "carries none",
            remedy="build it with sum_of, min_of, max_of, count_of or count_distinct, each "
            "of which requires the column",
        )
    return metric.column.to_sqlglot()


def _scoped(value: exp.Expr, metric: Metric, *, run_date: date | None, else_zero: bool) -> exp.Expr:
    """`value`, or `CASE WHEN <scoped Filter> THEN value [ELSE 0] END`.

    The conditional is built around the VALUE rather than around the aggregate, which is
    what keeps a Metric-scoped `when` out of the WHERE clause - a WHERE would narrow every
    other Metric in the same Case, quietly and in the right direction to look plausible.

    `ELSE 0` for the summing forms so a group with no matching row reads 0 rather than NULL;
    no default for the counting, MIN and MAX forms, which all ignore NULL already and whose
    zero is not 0.
    """
    if metric.when is None:
        return value
    condition = metric.when.predicate.to_sqlglot(run_date=run_date)
    branch = [exp.If(this=condition, true=value)]
    if else_zero:
        return exp.Case(ifs=branch, default=exp.Literal.number(0))
    return exp.Case(ifs=branch)


def aggregate_expression(metric: Metric, *, run_date: date | None = None) -> exp.Expr:
    """The aggregate a Metric computes from ATOMIC rows, unaliased.

    `SUM(col)`, `COUNT(*)`, `COUNT(col)`, `COUNT(DISTINCT col)` built as
    `exp.Count(this=exp.Distinct(expressions=[col]))` - verified: passing `distinct=True` to
    `exp.Count` does NOT emit DISTINCT in 30.18.0 - `MIN(col)`, `MAX(col)`, and for a ratio
    the numerator over the denominator.

    A Metric with a scoped `when` Filter becomes a conditional aggregate,
    `SUM(CASE WHEN <pred> THEN col ELSE 0 END)` for SUM and COUNT and
    `COUNT(CASE WHEN <pred> THEN col END)` for the counting forms - never a WHERE clause,
    which would silently narrow every other Metric in the same Case.

    Reading that split precisely, since it decides what golden SQL looks like: a scoped
    COUNT of ROWS (`count_rows`, which has no column) becomes
    `SUM(CASE WHEN <pred> THEN 1 ELSE 0 END)`, because there is no column to count and the
    summing form is the one the sentence above names for COUNT. A scoped COUNT of a COLUMN
    (`count_of`, `count_distinct`) keeps its COUNT and moves the condition inside:
    `COUNT(CASE WHEN <pred> THEN col END)`. Both roll up by SUM, as COUNT always does.

    `run_date` is a `datetime.date` or None, passed through to the scoped Filter's
    Predicate; an unbound deferred Predicate raises `UnboundRunDate`.
    """
    aggregate = metric.aggregate
    if aggregate is Aggregate.RATIO:
        numerator, denominator = metric.components
        return rederive(
            aggregate_expression(numerator, run_date=run_date),
            aggregate_expression(denominator, run_date=run_date),
        )
    if aggregate is Aggregate.SUM:
        summed = _scoped(_measured_column(metric), metric, run_date=run_date, else_zero=True)
        return exp.Sum(this=summed)
    if aggregate is Aggregate.COUNT:
        if metric.column is None:  # count_rows: COUNT(*) over the Source's rows
            if metric.when is None:
                return exp.Count(this=exp.Star())
            one = exp.Literal.number(1)
            return exp.Sum(this=_scoped(one, metric, run_date=run_date, else_zero=True))
        counted = _scoped(_measured_column(metric), metric, run_date=run_date, else_zero=False)
        return exp.Count(this=counted)
    if aggregate is Aggregate.COUNT_DISTINCT:
        counted = _scoped(_measured_column(metric), metric, run_date=run_date, else_zero=False)
        return exp.Count(this=exp.Distinct(expressions=[counted]))
    if aggregate is Aggregate.MIN:
        lowest = _scoped(_measured_column(metric), metric, run_date=run_date, else_zero=False)
        return exp.Min(this=lowest)
    if aggregate is Aggregate.MAX:
        highest = _scoped(_measured_column(metric), metric, run_date=run_date, else_zero=False)
        return exp.Max(this=highest)
    raise InvalidDeclaration(  # an Aggregate member added without a rendering
        subject=f"metric:{metric.name}",
        problem=f"Aggregate.{aggregate.name} has no rendering in grain.py",
        remedy="add its branch to grain.aggregate_expression together with the "
        "Re-aggregation rule that is provably correct for it",
    )


def reaggregate(rule: ReAggregation, partial: exp.Expr) -> exp.Expr:
    """Wrap an already-aggregated column in the outer aggregate that composes partials.

    SUM -> `SUM(partial)`, MIN -> `MIN(partial)`, MAX -> `MAX(partial)`. `REDERIVE` raises
    `UnsafeReAggregation` here rather than returning anything: a ratio is never wrapped, it
    is rebuilt by `rederive`, and reaching this with a REDERIVE rule means a caller took a
    shortcut. `NONE` raises `UnsafeReAggregation` too.

    The refusal cannot name the Metric - this function is handed a rule and an expression,
    and rendering the expression to text to name it would be a second `.sql()` call in a
    library that allows exactly one. The rule it carries is the actionable half anyway.
    """
    if rule is ReAggregation.SUM:
        return exp.Sum(this=partial)
    if rule is ReAggregation.MIN:
        return exp.Min(this=partial)
    if rule is ReAggregation.MAX:
        return exp.Max(this=partial)
    raise UnsafeReAggregation(
        metric="(the partial passed to grain.reaggregate)",
        rule=rule.value,
        native="its native Grain",
        target="a coarser Grain",
    )


def rederive(numerator: exp.Expr, denominator: exp.Expr) -> exp.Expr:
    """A ratio at a coarser Grain: re-aggregated parts divided, never averaged.

    Both arguments are already the rolled-up parts. Emits `numerator / denominator` as
    `exp.Div`. Division by zero is Hive's problem and yields NULL, which is the honest
    answer for a rate with no denominator.

    A part that is itself a binary expression - a ratio of ratios - is parenthesised.
    sqlglot's generator does not insert parentheses by precedence, so `a / (b / c)` would
    otherwise render as `a / b / c`, which is a different and entirely plausible number.
    """
    return exp.Div(this=_parenthesised(numerator), expression=_parenthesised(denominator))


def _parenthesised(node: exp.Expr) -> exp.Expr:
    return exp.Paren(this=node) if isinstance(node, exp.Binary) else node


def _stored_expression(
    metric: Metric,
    rule: ReAggregation,
    *,
    run_date: date | None,
) -> exp.Expr | None:
    """The row-level expression `reaggregate` wraps, or None when there is nothing stored.

    The stored column, wrapped in the Metric's scoped `when` when it has one - dropping that
    Filter on the way into `reaggregate` would silently widen the Metric, which is the failure
    this module exists to prevent.

    None means the Metric has no column to roll up: `count_rows` over a pre-aggregated
    Source counts stored rows rather than reading a stored partial, and `SUM(COUNT(*))` is
    not valid SQL anyway. Counting those rows directly at the coarser Grain gives the same
    number as summing partial counts would, so the caller computes it instead.
    """
    if metric.column is None:
        return None
    return _scoped(
        metric.column.to_sqlglot(),
        metric,
        run_date=run_date,
        else_zero=rule is ReAggregation.SUM,
    )


def _metric_expression(plan: MetricPlan, *, run_date: date | None) -> exp.Expr:
    """The unaliased expression for a planned Metric. See `render_metric` for the dispatch."""
    metric = plan.metric
    if plan.native is None:
        return aggregate_expression(metric, run_date=run_date)
    if plan.rule is ReAggregation.REDERIVE and plan.parts is not None:
        numerator, denominator = plan.parts
        return rederive(
            _metric_expression(numerator, run_date=run_date),
            _metric_expression(denominator, run_date=run_date),
        )
    # A REDERIVE rule with no component plans cannot be built through MetricPlan. Should one
    # ever arrive, it falls through: a ratio carries no column of its own, so the fallback
    # re-derives it from its own components rather than averaging anything, and a non-ratio
    # carrying REDERIVE is refused by `reaggregate`.
    stored = _stored_expression(metric, plan.rule, run_date=run_date)
    if stored is None:
        return aggregate_expression(metric, run_date=run_date)
    if plan.rule is ReAggregation.NONE:
        # Identity: plan_metric only allows NONE here when the target IS the stored Grain,
        # so each group holds exactly one stored row and MIN reads it back unchanged. Hive
        # still requires an aggregate around a column that is not in the GROUP BY, and MIN
        # is the one that is defined for every type a Metric column can have.
        return exp.Min(this=stored)
    return reaggregate(plan.rule, stored)


def render_metric(plan: MetricPlan, *, run_date: date | None = None) -> exp.Alias:
    """A planned Metric's SELECT entry, aliased to `plan.metric.name`.

    Dispatches on `plan.native`: computed from atomic rows with `aggregate_expression` when
    it is None, rolled up with `reaggregate` over the stored column when the Metric is read from
    a pre-aggregated Source, and rebuilt with `rederive` over its planned components when
    the rule is `REDERIVE`.

    The alias is the Metric's name and nothing else - it is simultaneously the Lineage node,
    the INSERT column and the golden-SQL column, and re-deriving it anywhere would let the
    three drift.

    Two dispatch cases the three-way description above does not name, both reachable only
    off a pre-aggregated Source: a Metric with no column to roll up (`count_rows`) is
    computed directly, because counting stored rows at the coarser Grain equals summing the
    partial counts; and a `NONE` rule at its own stored Grain reads the value back through
    `MIN`, since one group holds one stored row and Hive still wants an aggregate.
    """
    return exp.alias_(_metric_expression(plan, run_date=run_date), plan.metric.name)
