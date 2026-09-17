"""The parts a business question is built from.

Two shapes here do the heavy lifting, and both are omissions rather than checks.

There is no AVG. `Aggregate` has SUM, COUNT, COUNT_DISTINCT, MIN, MAX and RATIO, and there
is no `average_of()` constructor. A contributor who wants a mean finds only `ratio()`,
which forces them to name a denominator Metric - and naming the denominator is exactly the
fact that makes the quantity re-derivable at any coarser Grain. The classic silent wrong
number, an average of averages, is not caught here; it is unspellable.

There is no way to type a Re-aggregation rule by accident. `Aggregate.default_rule()` maps
each aggregate to the re-aggregation that is provably correct for it - including the
COUNT -> SUM - and every constructor uses it. `rule=` is an override a contributor has to
mean, not a defaultable argument they can get wrong.

The module imports no sqlglot beyond what a type annotation needs, because a Metric is a
declared fact and compile.py is the only translator. That is also why `Filter` holds a
`Predicate` rather than an `exp.Condition`: a Predicate carries the ColumnRefs it reads, so
a Filter's Lineage edges and its Drift scope are known without walking an AST, and it can
hold a `RunDate` that binds per run instead of being formatted into SQL text.

`Cardinality` and `TimeBucket` are re-exported from declaration.py, where they live because
they are declared facts about a Source. Import them from either module.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from enum import Enum
from typing import Any, Final, Iterator, Sequence

from sqlcomposer.declaration import (
    Cardinality,
    ColumnRef,
    JoinPath,
    Predicate,
    Registry,
    Source,
    TimeBucket,
)
from sqlcomposer.errors import (
    EmptyTagFamily,
    InvalidDeclaration,
    PlanInvariantViolated,
    UnknownMetric,
)

__all__ = [
    "Tag",
    "Aggregate",
    "ReAggregation",
    "TimeBucket",
    "Cardinality",
    "Dimension",
    "Grain",
    "Filter",
    "Metric",
    "sum_of",
    "count_rows",
    "count_of",
    "count_distinct",
    "min_of",
    "max_of",
    "ratio",
    "MetricSelection",
    "by_tag",
    "by_name",
    "Case",
    "KEEP",
    "MetricPlan",
    "CasePlan",
]

Tag = str
"""A label on a Metric that selects a family of Metrics as a group.

A plain `str`. It has no fields and no behaviour, and the only argument for a wrapper type
is typo safety - which `Registry.tagged()` buys instead, and more completely: it refuses
each Tag that matches no Metric individually, so a misspelled Tag fails the build rather
than quietly narrowing a Case. Declare Tags as module-level string constants in a
declarations module if you want them greppable."""


# ======================================================================================
# Aggregates and the Re-aggregation rule
# ======================================================================================


class Aggregate(Enum):
    """How a Metric is computed from the rows of the Source it measures.

    Closed on purpose, and AVG IS ABSENT. An arbitrary SQL aggregate makes the re-grain
    question undecidable - there is no general rule for recomputing an unknown function at
    a coarser Grain - so exotic aggregates are simply not expressible. The price is real:
    percentiles, stddev, collect_set, approx_count_distinct and every window function have
    no member here, and the first Case needing a median forces a new member plus its
    provably-correct rule, not a workaround.
    """

    SUM = "SUM"
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    MIN = "MIN"
    MAX = "MAX"
    RATIO = "RATIO"

    def default_rule(self) -> ReAggregation:
        """The Re-aggregation rule that is provably correct for this aggregate.

        COUNT -> SUM is the one worth staring at: partial counts compose by summing, not by
        counting. Conflating those is one of the two ways this library would otherwise emit
        a plausible wrong number.
        """
        return _DEFAULT_RULE[self]

    @property
    def needs_column(self) -> bool:
        """True when the aggregate is computed over a column rather than over rows."""
        return self in (
            Aggregate.SUM,
            Aggregate.COUNT_DISTINCT,
            Aggregate.MIN,
            Aggregate.MAX,
        )


class ReAggregation(Enum):
    """A Metric's declaration of whether, and how, it can be recomputed at a coarser Grain.

    The member names the function applied to PARTIALS, which is not the Metric's own
    function. `NONE` is the honest answer for COUNT(DISTINCT) and percentiles: partials
    carry no information that composes, and no amount of SQL recovers it.
    """

    SUM = "SUM"
    MIN = "MIN"
    MAX = "MAX"
    REDERIVE = "REDERIVE"
    """Recompute from re-aggregated numerator and denominator - never average a ratio."""
    NONE = "NONE"
    """Cannot roll up at all: COUNT(DISTINCT), percentiles, a stored rate."""

    @property
    def is_provable(self) -> bool:
        """True when a coarser Grain can be computed from partials. False only for NONE."""
        return self is not ReAggregation.NONE


_DEFAULT_RULE: dict[Aggregate, ReAggregation] = {
    Aggregate.SUM: ReAggregation.SUM,
    Aggregate.COUNT: ReAggregation.SUM,
    Aggregate.COUNT_DISTINCT: ReAggregation.NONE,
    Aggregate.MIN: ReAggregation.MIN,
    Aggregate.MAX: ReAggregation.MAX,
    Aggregate.RATIO: ReAggregation.REDERIVE,
}


# ======================================================================================
# Dimension and Grain
# ======================================================================================


@dataclass(frozen=True)
class Dimension:
    """A column a Case reports its Metrics across, optionally time-bucketed.

    Absorbing the bucket here is what keeps Grain simple: a day-grain and a month-grain of
    the same column are two Dimensions over one ColumnRef, so "coarser" is a comparison
    between Dimensions rather than a property Grain has to model separately.

    `alias` names the output column. Left unset, a bucketed Dimension publishes as
    `column_bucket` (`dt_week`) and an unbucketed one as the column's own name - so the
    common case is `Dimension(COURIERS.city)` with no ceremony, and the output name still
    appears in exactly one place.
    """

    column: ColumnRef
    bucket: TimeBucket | None = None
    alias: str | None = None
    note: str = ""

    @property
    def name(self) -> str:
        """The output column name. Stable: it is a Lineage node id and an INSERT column."""
        if self.alias:
            return self.alias
        if self.bucket is not None:
            return f"{self.column.name}_{self.bucket.value.lower()}"
        return self.column.name

    @property
    def source(self) -> Source:
        return self.column.source

    @property
    def columns(self) -> frozenset[ColumnRef]:
        """Every declared column this Dimension reads - one, always, for now."""
        return frozenset({self.column})

    def coarsens_to(self, other: Dimension) -> bool:
        """True when `other` is this same column at an equal-or-coarser bucket.

        Compared by the column's qualified name, so a Dimension on a written Source never
        accidentally matches the upstream column it was derived from - those are different
        node ids and re-graining between them has to go through the Manifest.
        """
        if self.column.qualified != other.column.qualified:
            return False
        if self.bucket is None and other.bucket is None:
            return True
        if self.bucket is None or other.bucket is None:
            return False
        return other.bucket.coarsens(self.bucket)

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Grain:
    """The level a Case's rows are reported at - its Dimensions, time bucketing included.

    A type rather than a bare tuple because it is a glossary noun that carries invariants:
    two Dimensions must not publish the same output name, and "coarser than" is a question
    asked about a whole Grain rather than about one Dimension. Its answers are deliberately
    conservative - anything it cannot prove, it denies, so the re-grain check refuses
    rather than permits.
    """

    dimensions: tuple[Dimension, ...] = ()

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for dimension in self.dimensions:
            if dimension.name in seen:
                raise InvalidDeclaration(
                    subject=f"grain:{self}",
                    problem=f"two Dimensions both publish as {dimension.name!r}",
                    remedy="give one of them an explicit `alias=`; output names are "
                    "Lineage node ids and INSERT columns, so they must be unique",
                )
            seen.add(dimension.name)

    @classmethod
    def of(cls, *dimensions: Dimension | ColumnRef) -> Grain:
        """Build a Grain, accepting a bare ColumnRef where an unbucketed Dimension is meant.

        A ColumnRef is the same concept minus optional bucketing, and requiring the wrapper
        for the common case is ceremony with no guarantee attached.
        """
        return cls(dimensions=tuple(_as_dimension(item) for item in dimensions))

    @property
    def names(self) -> tuple[str, ...]:
        """Output column names, in declared order. The order a GROUP BY and an INSERT use."""
        return tuple(dimension.name for dimension in self.dimensions)

    @property
    def columns(self) -> frozenset[ColumnRef]:
        return frozenset(ref for dim in self.dimensions for ref in dim.columns)

    @property
    def sources(self) -> frozenset[Source]:
        return frozenset(dimension.source for dimension in self.dimensions)

    @property
    def time_bucket(self) -> TimeBucket | None:
        """The bucket of the single time Dimension, or None when there is none.

        Raises when two Dimensions are bucketed: a Grain with two independent time
        bucketings has no single answer to "is this coarser", and guessing one is how a
        re-grain check quietly starts permitting things.
        """
        buckets = [dim.bucket for dim in self.dimensions if dim.bucket is not None]
        if not buckets:
            return None
        if len(buckets) > 1:
            raise InvalidDeclaration(
                subject=f"grain:{self}",
                problem="more than one Dimension is time-bucketed",
                remedy="bucket one time column per Grain; two independent bucketings have "
                "no defined coarsening order",
            )
        return buckets[0]

    def coarsens(self, other: Grain) -> bool:
        """True when this Grain is `other` or a Grain `other` rolls up into.

        Read it as "self is at-or-coarser than other": every Dimension of self must be
        implied by some Dimension of other - the same column at an equal-or-finer bucket.
        Conservative by construction: a Dimension self carries that other does not is an
        immediate False, so an unprovable re-grain refuses.
        """
        for mine in self.dimensions:
            if not any(theirs.coarsens_to(mine) for theirs in other.dimensions):
                return False
        return True

    def comparable(self, other: Grain) -> bool:
        """True when one of the two Grains rolls up into the other, in either direction.

        The distinction that lets grain.py tell "you asked for detail that is gone"
        (GrainTooFine) apart from "these two do not nest at all" (GrainNotComparable) -
        WEEK against MONTH being the case that matters.
        """
        return self.coarsens(other) or other.coarsens(self)

    def __len__(self) -> int:
        return len(self.dimensions)

    def __iter__(self) -> Iterator[Dimension]:
        return iter(self.dimensions)

    def __str__(self) -> str:
        return "(" + ", ".join(self.names) + ")" if self.dimensions else "(ungrouped)"


def _as_dimension(item: Dimension | ColumnRef) -> Dimension:
    if isinstance(item, Dimension):
        return item
    if isinstance(item, ColumnRef):
        return Dimension(column=item)
    raise TypeError(f"a Grain takes Dimensions or ColumnRefs, not {type(item).__name__}")


# ======================================================================================
# Filter
# ======================================================================================


@dataclass(frozen=True)
class Filter:
    """A named predicate that narrows a Case.

    Named because it appears by name in the Lineage, in every refusal that mentions it and
    in every Case that reuses it - "failure to deliver" reads as a Filter over the shared
    delivery Source in three Cases, and is written once.

    One type serves both uses: a Case-level narrowing, and a Metric-scoped `when` that
    compiles to a conditional aggregate rather than a WHERE clause. The difference is where
    it is attached, not what it is.
    """

    name: str
    predicate: Predicate
    note: str = ""

    @property
    def columns(self) -> frozenset[ColumnRef]:
        """The declared columns this Filter reads - Lineage edges and Drift scope."""
        return self.predicate.columns

    @property
    def sources(self) -> frozenset[Source]:
        """The Sources this Filter drags into a Case's Join path."""
        return self.predicate.sources

    @property
    def deferred(self) -> bool:
        """True when the predicate holds a RunDate and needs `run_date` at compile time."""
        return self.predicate.deferred

    def __and__(self, other: Filter | Predicate) -> Predicate:
        return self.predicate & other

    def __or__(self, other: Filter | Predicate) -> Predicate:
        return self.predicate | other

    def __invert__(self) -> Predicate:
        return ~self.predicate

    def __str__(self) -> str:
        return self.name


# ======================================================================================
# Metric
# ======================================================================================


@dataclass(frozen=True)
class Metric:
    """A named aggregate quantity, declared against the one Source it measures.

    `source` is DERIVED, never declared, from the column, the scoped Filter and any ratio
    components - so it cannot disagree with them. A Metric whose parts straddle two Sources
    is refused: one side of such a quantity is always inflated by the Join that brings the
    other in, and the honest fix is to pre-aggregate into a written Source first. That is a
    multi-step detour for something a contributor expects to write in one line, and it is
    the refusal most likely to be argued with; it is still correct.

    The Metric carries no native Grain. That is read off the Source it measures - a
    pre-aggregated table states once what its rows are unique by, and every Metric on it
    inherits that. See `Registry.native_grain`.

    Prefer the module-level constructors (`sum_of`, `count_rows`, `ratio`, ...) over the
    initialiser: each one fixes the provably-correct Re-aggregation rule, so there is no
    defaultable path to a wrong one.
    """

    name: str
    aggregate: Aggregate
    column: ColumnRef | None = None
    of_source: Source | None = None
    when: Filter | None = None
    parts: tuple[Metric, Metric] | None = None
    tags: tuple[Tag, ...] = ()
    rule: ReAggregation | None = None
    note: str = ""

    def __post_init__(self) -> None:
        subject = f"metric:{self.name}"
        if not self.name:
            raise InvalidDeclaration(
                subject=subject,
                problem="a Metric was declared with an empty name",
                remedy="name it; the name is its output column and its Lineage node",
            )
        if self.aggregate is Aggregate.RATIO:
            if self.parts is None or len(self.parts) != 2:
                raise InvalidDeclaration(
                    subject=subject,
                    problem="a RATIO Metric needs exactly two component Metrics",
                    remedy="build it with ratio(name, numerator=..., denominator=...)",
                )
            if self.column is not None:
                raise InvalidDeclaration(
                    subject=subject,
                    problem="a RATIO Metric measures its components, not a column",
                    remedy="drop `column=`; the components carry the columns",
                )
            if self.when is not None:
                # `grain.aggregate_expression`'s RATIO branch renders the two components and
                # divides them; there is no expression of the ratio itself for a condition
                # to wrap. A `when` here would therefore be dropped from the SQL while
                # `Metric.columns` still reported its columns - the builder-derived Lineage,
                # which decision 6 makes authoritative and decision 7 makes a reviewable
                # artifact, would claim an edge the statement does not have.
                raise InvalidDeclaration(
                    subject=subject,
                    problem=f"a RATIO Metric carries a scoped Filter {self.when.name!r}, "
                    "but a ratio scopes its components rather than itself",
                    remedy="put `when=` on the numerator, the denominator, or both, and "
                    "build the ratio from those; scoping only the numerator is a rate "
                    "within the whole denominator, scoping both is a rate within the "
                    "subset",
                )
            numerator, denominator = self.parts
            if numerator.source.qualified != denominator.source.qualified:
                raise InvalidDeclaration(
                    subject=subject,
                    problem=f"numerator {numerator.name!r} measures "
                    f"{numerator.source.qualified} but denominator {denominator.name!r} "
                    f"measures {denominator.source.qualified}",
                    remedy="a cross-Source ratio is inflated by the Join that brings the "
                    "second Source in; pre-aggregate both sides into a written Source and "
                    "declare the ratio against that",
                )
            for part in self.parts:
                if not part.reaggregation.is_provable:
                    raise InvalidDeclaration(
                        subject=subject,
                        problem=f"component {part.name!r} has Re-aggregation rule NONE, so "
                        "the ratio cannot be re-derived at any coarser Grain",
                        remedy="use components that roll up - a COUNT(DISTINCT) "
                        "denominator makes the ratio unusable above its native Grain",
                    )
        else:
            if self.parts is not None:
                raise InvalidDeclaration(
                    subject=subject,
                    problem=f"a {self.aggregate.value} Metric carries component Metrics",
                    remedy="drop `parts=`; only a RATIO has components",
                )
            if self.aggregate.needs_column and self.column is None:
                raise InvalidDeclaration(
                    subject=subject,
                    problem=f"{self.aggregate.value} needs a column to aggregate",
                    remedy="pass `column=SOURCE.column_name`",
                )
            if self.aggregate is Aggregate.COUNT and self.column is None and self.of_source is None:
                raise InvalidDeclaration(
                    subject=subject,
                    problem="COUNT of rows needs to know which Source's rows",
                    remedy="pass `of_source=SOURCE`, or build it with count_rows(name, "
                    "SOURCE)",
                )
        measured = {ref.source.qualified for ref in self.columns}
        if self.of_source is not None:
            measured.add(self.of_source.qualified)
        if len(measured) > 1:
            raise InvalidDeclaration(
                subject=subject,
                problem=f"this Metric reads {', '.join(sorted(measured))}, but a Metric is "
                "declared against the one Source it measures",
                remedy="scope it to one Source; a Metric-scoped `when` must filter the "
                "same Source the Metric measures, and a Case-level Filter is where a "
                "predicate on another Source belongs",
            )
        if not measured:
            raise InvalidDeclaration(
                subject=subject,
                problem="this Metric names no Source at all",
                remedy="pass `column=` or `of_source=`",
            )

    # -- derived facts -----------------------------------------------------------------

    @property
    def source(self) -> Source:
        """The one Source this Metric measures, derived from its own parts."""
        if self.column is not None:
            return self.column.source
        if self.of_source is not None:
            return self.of_source
        assert self.parts is not None  # guaranteed by __post_init__
        return self.parts[0].source

    @property
    def reaggregation(self) -> ReAggregation:
        """The Re-aggregation rule: the explicit override, else the aggregate's default."""
        return self.rule if self.rule is not None else self.aggregate.default_rule()

    @property
    def is_ratio(self) -> bool:
        return self.aggregate is Aggregate.RATIO

    @property
    def components(self) -> tuple[Metric, ...]:
        """(numerator, denominator) for a ratio, an empty tuple otherwise."""
        return self.parts if self.parts is not None else ()

    @property
    def columns(self) -> frozenset[ColumnRef]:
        """Every declared column this Metric reads: measured, scoped-filter, component."""
        refs: set[ColumnRef] = set()
        if self.column is not None:
            refs.add(self.column)
        if self.when is not None:
            refs |= self.when.columns
        for part in self.components:
            refs |= part.columns
        return frozenset(refs)

    def tagged(self, tag: Tag) -> bool:
        return tag in self.tags

    def rename(self, name: str) -> Metric:
        """The same Metric published under a different output name.

        For a Case that reports one quantity twice under different Filters, and for reading
        a written Source whose column names differ from the Metric names that produced it.
        """
        return replace(self, name=name)

    def __str__(self) -> str:
        return self.name


# -- constructors ----------------------------------------------------------------------
#
# There is deliberately no average_of(). A mean is ratio(name, sum_of(...), count_of(...)),
# which re-grains correctly by construction because both parts roll up by SUM.


def sum_of(
    name: str,
    column: ColumnRef,
    *,
    when: Filter | None = None,
    tags: Sequence[Tag] = (),
    rule: ReAggregation | None = None,
    note: str = "",
) -> Metric:
    """`SUM(column)`, or `SUM(CASE WHEN when THEN column END)` when scoped. Rolls up by SUM."""
    return Metric(
        name=name,
        aggregate=Aggregate.SUM,
        column=column,
        when=when,
        tags=tuple(tags),
        rule=rule,
        note=note,
    )


def count_rows(
    name: str,
    source: Source,
    *,
    when: Filter | None = None,
    tags: Sequence[Tag] = (),
    note: str = "",
) -> Metric:
    """`COUNT(*)` over a Source's rows, or a conditional count when scoped.

    Rolls up by SUM, not by COUNT: partial counts compose by summing.
    """
    return Metric(
        name=name,
        aggregate=Aggregate.COUNT,
        of_source=source,
        when=when,
        tags=tuple(tags),
        note=note,
    )


def count_of(
    name: str,
    column: ColumnRef,
    *,
    when: Filter | None = None,
    tags: Sequence[Tag] = (),
    note: str = "",
) -> Metric:
    """`COUNT(column)` - rows where the column is not NULL. Rolls up by SUM."""
    return Metric(
        name=name,
        aggregate=Aggregate.COUNT,
        column=column,
        when=when,
        tags=tuple(tags),
        note=note,
    )


def count_distinct(
    name: str,
    column: ColumnRef,
    *,
    when: Filter | None = None,
    tags: Sequence[Tag] = (),
    note: str = "",
) -> Metric:
    """`COUNT(DISTINCT column)`. Re-aggregation rule NONE, and there is no override.

    Distinct counts of parts do not compose into a distinct count of the whole - the same
    courier appearing on two days counts once a week and twice as a sum of days. Reporting
    this Metric above the Grain it was computed at raises `UnsafeReAggregation`.
    """
    return Metric(
        name=name,
        aggregate=Aggregate.COUNT_DISTINCT,
        column=column,
        when=when,
        tags=tuple(tags),
        note=note,
    )


def min_of(
    name: str,
    column: ColumnRef,
    *,
    when: Filter | None = None,
    tags: Sequence[Tag] = (),
    note: str = "",
) -> Metric:
    """`MIN(column)`. Rolls up by MIN."""
    return Metric(
        name=name,
        aggregate=Aggregate.MIN,
        column=column,
        when=when,
        tags=tuple(tags),
        note=note,
    )


def max_of(
    name: str,
    column: ColumnRef,
    *,
    when: Filter | None = None,
    tags: Sequence[Tag] = (),
    note: str = "",
) -> Metric:
    """`MAX(column)`. Rolls up by MAX."""
    return Metric(
        name=name,
        aggregate=Aggregate.MAX,
        column=column,
        when=when,
        tags=tuple(tags),
        note=note,
    )


def ratio(
    name: str,
    numerator: Metric,
    denominator: Metric,
    *,
    tags: Sequence[Tag] = (),
    note: str = "",
) -> Metric:
    """A quantity derived from two other Metrics, re-derived at every Grain.

    The only way to express a mean or a rate, and the reason there is no AVG anywhere in
    this library. At a coarser Grain the numerator and denominator are re-aggregated by
    their own rules and then divided - an average of averages is not merely discouraged,
    it has no spelling.

    Both components must measure the same Source and both must roll up; a cross-Source
    ratio and a COUNT(DISTINCT) denominator are both refused here, at import time.
    Components need not themselves be registered - declare them at module level only if a
    Case should be able to report them on their own.
    """
    return Metric(
        name=name,
        aggregate=Aggregate.RATIO,
        parts=(numerator, denominator),
        tags=tuple(tags),
        note=note,
    )


# ======================================================================================
# Tag selection
# ======================================================================================


@dataclass(frozen=True)
class MetricSelection:
    """Which Metrics a Case reports - held unresolved until compile time.

    Late binding is the whole point of Tags. If a Case resolved its family at construction,
    a Metric declared in a module imported later would silently not join it, which is
    precisely the silent wrong number this library exists to refuse. `resolve()` runs
    against a frozen Registry and sorts by Metric name, so the SQL, the golden tests and
    the git-tracked Lineage artifact are stable and diffable.

    The consequence to know before it bites: declaring a new tagged Metric changes the SQL
    of every Case asking for that family, so a PR that edits no Case can still move golden
    output. That break is the intended review signal, not flakiness.

    Exclusions carry a mandatory reason, so the diff says why a Metric was cut out of a
    family it otherwise belongs to - and an exclusion that matches nothing is refused,
    because a stale exclusion that has quietly stopped excluding is a family that grew back
    without anyone noticing.
    """

    tags: tuple[Tag, ...] = ()
    names: tuple[str, ...] = ()
    excluded: tuple[tuple[str, str], ...] = ()

    def without(self, *names: str, because: str) -> MetricSelection:
        """Cut named Metrics out of the selection, recording why.

        `because` is required. It decays if nobody reads it in review, and it is still
        cheaper than the alternative, which is a family that quietly differs from its Tag
        with nothing in the file to say so.
        """
        if not because:
            raise InvalidDeclaration(
                subject="metric selection",
                problem="an exclusion was declared with no reason",
                remedy="pass because='...'; an unexplained exclusion is indistinguishable "
                "from a mistake in six months",
            )
        return MetricSelection(
            tags=self.tags,
            names=self.names,
            excluded=self.excluded + tuple((name, because) for name in names),
        )

    def __or__(self, other: MetricSelection) -> MetricSelection:
        """Union two selections; exclusions from both sides are kept."""
        return MetricSelection(
            tags=self.tags + tuple(t for t in other.tags if t not in self.tags),
            names=self.names + tuple(n for n in other.names if n not in self.names),
            excluded=self.excluded + other.excluded,
        )

    def resolve(self, registry: Registry, *, case: str | None = None) -> tuple[Metric, ...]:
        """The Metrics this selection names, sorted by name.

        Every Tag is checked individually (`EmptyTagFamily`), every explicit name must
        exist (`UnknownMetric`), every exclusion must match something it would otherwise
        have selected (`UnknownMetric`), and an empty result is `EmptyTagFamily` rather
        than a Case with no numbers.
        """
        selected: dict[str, Metric] = {}
        for metric in registry.tagged(*self.tags, case=case) if self.tags else ():
            selected[metric.name] = metric
        for name in self.names:
            metric = registry.metric(name)
            selected[metric.name] = metric
        for name, _reason in self.excluded:
            if name not in selected:
                raise UnknownMetric(metric=name, known=sorted(selected))
            del selected[name]
        if not selected:
            raise EmptyTagFamily(
                tag=", ".join(self.tags) or "(no tags)",
                known=sorted(registry.tags()),
                case=case,
            )
        return tuple(selected[key] for key in sorted(selected))

    def __str__(self) -> str:
        parts = []
        if self.tags:
            parts.append("tagged " + "+".join(self.tags))
        if self.names:
            parts.append("named " + ",".join(self.names))
        if self.excluded:
            parts.append("without " + ",".join(name for name, _ in self.excluded))
        return "; ".join(parts) or "(empty)"


def by_tag(*tags: Tag) -> MetricSelection:
    """Select every Metric carrying any of these Tags. The horizontal-scaling lever:
    declaring a Metric with one of these Tags joins it to every Case asking for the family,
    with no Case edited."""
    return MetricSelection(tags=tuple(tags))


def by_name(*metrics: Metric | str) -> MetricSelection:
    """Select Metrics explicitly.

    An escape hatch. A Case built this way does not scale horizontally - a newly declared
    Metric will not join it - so prefer `by_tag()` and use this only where the list really
    is the point. Accepts Metric objects (typo-proof) or names.
    """
    return MetricSelection(
        names=tuple(m.name if isinstance(m, Metric) else m for m in metrics)
    )


# ======================================================================================
# Case
# ======================================================================================


class _Keep:
    """Sentinel meaning 'inherit this field from the parent Case'."""

    _instance: _Keep | None = None

    def __new__(cls) -> _Keep:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "KEEP"


KEEP: Final[Any] = _Keep()
"""Sentinel for `Case.variant`: this field is unchanged from the parent Case. `None` is a
real value for `via` and `writes_to`, so the sentinel cannot be None."""


@dataclass(frozen=True)
class Case:
    """A named business question - the unit added when a new question arrives.

    `metrics` is a MetricSelection, never a resolved list, so a Metric declared later joins
    every Case asking for its Tag family with no Case edited.

    `via` pins Join NAMES, not Source names, and is supplied only after the composer has
    refused an ambiguous Join path. Two Sources can be joined two ways, so a path has to be
    stated as edges; the refusal prints candidates in exactly the form this field takes.
    It is matched as a SET - the order inside it carries no information.

    `anchor` pins the SPINE, as the `db.table` of the Source the FROM clause names. It is a
    second field rather than a convention on `via` precisely because `via` is a set: when
    the resolved Metrics measure more than one Source, which end of the Join path the FROM
    clause names decides which side a `kind="left"` edge preserves - and an edge set has no
    ends. Supplied only after `AmbiguousJoinPath` prints it, and refused for anything but
    one of the Sources the Case's own Metrics measure.

    `writes_to` makes this Case the producer of an intermediate Source, which is what lets
    a later Case re-grain its Metrics safely and trace Lineage through it. That Source must
    declare `written_by=<this Case>`; `Registry.freeze()` checks both directions, because
    everything downstream reads only the Source's half.
    """

    name: str
    metrics: MetricSelection
    grain: Grain
    filters: tuple[Filter, ...] = ()
    via: tuple[str, ...] = ()
    anchor: str | None = None
    writes_to: Source | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise InvalidDeclaration(
                subject="case:<unnamed>",
                problem="a Case was declared with an empty name",
                remedy="name it; the name keys its Lineage artifact and its statements",
            )
        if isinstance(self.via, str):
            # `via=('one_edge')` is a str, not a tuple, and every character of it would be
            # read as a Join name - the build then refuses, naming a join called 'd'. A
            # refusal about the remedy instead of about the problem is worse than no help,
            # so a bare str is refused here where the Case is still the subject.
            raise InvalidDeclaration(
                subject=f"case:{self.name}",
                problem=f"via={self.via!r} is a string, so each of its characters would be "
                "read as a Join name",
                remedy=f"write it as a tuple: via=({self.via!r},) - the trailing comma is "
                "what makes a one-edge Join path a tuple rather than a string",
            )
        object.__setattr__(self, "via", tuple(self.via))
        if isinstance(self.grain, (tuple, list)):
            object.__setattr__(self, "grain", Grain.of(*self.grain))
        if not isinstance(self.grain, Grain):
            raise InvalidDeclaration(
                subject=f"case:{self.name}",
                problem=f"grain must be a Grain, not {type(self.grain).__name__}",
                remedy="use Grain.of(BY_DAY, BY_COURIER), or pass a tuple of Dimensions",
            )
        if not isinstance(self.metrics, MetricSelection):
            raise InvalidDeclaration(
                subject=f"case:{self.name}",
                problem=f"metrics must be a MetricSelection, not "
                f"{type(self.metrics).__name__}",
                remedy="use by_tag('delivery_health') or by_name(SOME_METRIC)",
            )

    def variant(
        self,
        name: str,
        *,
        grain: Grain | Any = KEEP,
        metrics: MetricSelection | Any = KEEP,
        filters: tuple[Filter, ...] | Any = KEEP,
        also_filtered_by: Sequence[Filter] = (),
        via: tuple[str, ...] | Any = KEEP,
        anchor: str | None | Any = KEEP,
        writes_to: Source | None = None,
        note: str = "",
    ) -> Case:
        """The next Case, written as its difference from this one.

        The second Case is almost never a new question - it is the first question cut a
        different way. Same numbers, coarser Grain; same numbers, one more Filter; same
        numbers, by city instead of by courier. Everything not named here is inherited, so
        the diff in review is the business difference and nothing else.

        Note the consequence, which is the point: coarsening `grain` is exactly what trips
        the Re-aggregation check across the whole resolved family, so the cheapest edit is
        also the checked one.

        And note the cost, which is real: the parent Case becomes load-bearing for every
        variant, so editing it silently changes their SQL. The git-tracked static Lineage
        artifact is the only defence, and regenerating it belongs in CI.

        `writes_to` is NOT inherited - it defaults to None rather than KEEP. Two Cases
        writing the same Partition would overwrite each other on every run, and that is too
        expensive a mistake to make available by omission. `Registry.freeze()` now refuses
        that outright, and this default is what keeps a variant from tripping it by silence.

        `via` and `anchor` ARE inherited, because both are answers about the same declared
        Join graph and a variant that changed Grain has not changed the graph. A variant
        whose `metrics=` selects a different family may need a different answer, and the
        refusal says so at compile time rather than here.
        """
        inherited_filters = self.filters if filters is KEEP else tuple(filters)
        return Case(
            name=name,
            metrics=self.metrics if metrics is KEEP else metrics,
            grain=self.grain if grain is KEEP else grain,
            filters=inherited_filters + tuple(also_filtered_by),
            via=self.via if via is KEEP else tuple(via),
            anchor=self.anchor if anchor is KEEP else anchor,
            writes_to=writes_to,
            note=note or self.note,
        )

    # -- resolution --------------------------------------------------------------------

    def resolved_metrics(self, registry: Registry) -> tuple[Metric, ...]:
        """The Metrics this Case reports, sorted by name. Resolves the Tag family."""
        return self.metrics.resolve(registry, case=self.name)

    def sources(self, registry: Registry) -> frozenset[Source]:
        """Every Source this Case touches, across Metrics, Grain and Filters.

        The input to Join path resolution. A Source appearing only in a Filter still has to
        be reached, and reaching it can fan out - which is why Filters count here.
        """
        found = {metric.source for metric in self.resolved_metrics(registry)}
        found |= self.grain.sources
        for filter_ in self.filters:
            found |= filter_.sources
        return frozenset(found)

    def referenced_columns(self, registry: Registry) -> frozenset[ColumnRef]:
        """Every declared column this Case reaches. The scope of the Drift check."""
        refs: set[ColumnRef] = set()
        for metric in self.resolved_metrics(registry):
            refs |= metric.columns
        refs |= self.grain.columns
        for filter_ in self.filters:
            refs |= filter_.columns
        return frozenset(refs)

    def output_names(self, registry: Registry) -> tuple[str, ...]:
        """Dimension names in Grain order, then Metric names sorted.

        Stable by construction, because it is simultaneously the Lineage node set, the
        column order of an INSERT OVERWRITE and the column order of the golden SQL.
        """
        return self.grain.names + tuple(
            metric.name for metric in self.resolved_metrics(registry)
        )

    @property
    def deferred(self) -> bool:
        """True when any Filter holds a RunDate, so compiling needs `run_date`."""
        return any(filter_.deferred for filter_ in self.filters)

    def predicate(self) -> Predicate | None:
        """Every Filter ANDed together, or None when the Case is unfiltered.

        Metric-scoped `when` Filters are NOT included: those compile to conditional
        aggregates, and moving them into the WHERE clause would silently change every other
        Metric in the Case.
        """
        if not self.filters:
            return None
        combined = self.filters[0].predicate
        for filter_ in self.filters[1:]:
            combined = combined & filter_.predicate
        return combined

    def __str__(self) -> str:
        return self.name


# ======================================================================================
# The plan token
# ======================================================================================


@dataclass(frozen=True)
class MetricPlan:
    """grain.py's proof that one Metric can be reported at one Grain.

    `native` is the Grain the Metric's Source is already collapsed to, or None for atomic
    rows where computing from scratch is always safe. `rule` is the Re-aggregation rule
    that applies for this particular re-grain, which is `ReAggregation.SUM` for a plain
    SUM over atomic rows and `REDERIVE` for a ratio at any Grain.
    """

    metric: Metric
    target: Grain
    rule: ReAggregation
    native: Grain | None = None
    parts: tuple[MetricPlan, MetricPlan] | None = None

    def __post_init__(self) -> None:
        subject = f"metricplan:{self.metric.name}"
        if (self.rule is ReAggregation.REDERIVE) != (self.parts is not None):
            raise InvalidDeclaration(
                subject=subject,
                problem="REDERIVE and component plans must appear together",
                remedy="plan a ratio's numerator and denominator and pass both as `parts`",
            )
        if self.rule is ReAggregation.NONE and self.native is not None:
            if not (self.native.coarsens(self.target) and self.target.coarsens(self.native)):
                raise InvalidDeclaration(
                    subject=subject,
                    problem="a Metric with Re-aggregation rule NONE was planned at a Grain "
                    "other than the one it is stored at",
                    remedy="grain.plan_metric should have raised UnsafeReAggregation; do "
                    "not construct this plan by hand",
                )


@dataclass(frozen=True)
class CasePlan:
    """The token `compile.render()` requires. Its fields ARE the refusals of decision 3.

    `compile.render()` does not accept a `Case`. It accepts this, whose `path` is the proof
    joins.py searched for and whose `metrics` are the proofs grain.py searched for. A caller
    cannot skip the checks by taking a different way through the API, because there is no
    way to SQL that does not pass through a plan.

    `__post_init__` re-verifies what it can re-verify cheaply from its own fields: that the
    path chains from the spine and visits each Source once, and that every MetricPlan
    targets the Case's Grain. It deliberately does NOT re-run the ambiguous-path search or
    the Fan-out walk - both need the Registry and a graph search, and doubling that on every
    plan would buy a guarantee against a caller who is already assembling plans by hand.
    So this is a net, not a seal: a hand-built plan naming a valid but arbitrarily chosen
    Join path still renders. Build plans with `compile.plan()`.
    """

    case: Case
    spine: Source
    path: JoinPath
    metrics: tuple[MetricPlan, ...]
    dimensions: tuple[Dimension, ...]
    filters: tuple[Filter, ...] = ()
    run_date: date | None = None

    def __post_init__(self) -> None:
        name = self.case.name
        reached = {self.spine.qualified}
        for step in self.path:
            if step.frm.qualified not in reached:
                raise PlanInvariantViolated(
                    case=name,
                    invariant="path chains from the spine",
                    detail=f"step {step.name!r} leaves {step.frm.qualified}, which the path "
                    f"has not reached yet (reached: {', '.join(sorted(reached))})",
                )
            if step.to.qualified in reached:
                raise PlanInvariantViolated(
                    case=name,
                    invariant="path visits each Source once",
                    detail=f"step {step.name!r} re-enters {step.to.qualified}; a repeated "
                    "Source needs a self-join alias, which this library does not emit",
                )
            reached.add(step.to.qualified)
        for plan in self.metrics:
            if plan.target != self.case.grain:
                raise PlanInvariantViolated(
                    case=name,
                    invariant="every MetricPlan targets the Case's Grain",
                    detail=f"{plan.metric.name!r} is planned at {plan.target} but the Case "
                    f"reports at {self.case.grain}",
                )

    @property
    def sources(self) -> tuple[Source, ...]:
        """The spine, then each Source the path reaches, in the order the path walks them.

        This is FROM-then-JOIN order, so compile.py can walk it directly.
        """
        return (self.spine,) + tuple(step.to for step in self.path)

    @property
    def join_names(self) -> tuple[str, ...]:
        """The Join path as edge names - what a refusal prints and the Lineage records."""
        return tuple(step.name for step in self.path)

    @property
    def output_names(self) -> tuple[str, ...]:
        """Dimension names in order, then Metric names in plan order (already name-sorted)."""
        return tuple(dim.name for dim in self.dimensions) + tuple(
            plan.metric.name for plan in self.metrics
        )

    def __str__(self) -> str:
        walked = " -> ".join((self.spine.qualified,) + tuple(s.to.qualified for s in self.path))
        return f"{self.case.name} @ {self.case.grain} over {walked}"
