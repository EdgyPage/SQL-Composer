"""The refusal hierarchy.

Every class in this module exists because the alternative to raising it is a plausible
WRONG NUMBER rather than an error. A re-grain a Re-aggregation rule cannot prove safe, a
Join path that fans out the Source a Metric measures, an ambiguous Join path, a column no
Declaration carries - each of those, left unrefused, produces SQL that runs, returns rows,
and is wrong. So there is deliberately no warning type anywhere in this module, and the
absence of one is how "a warning is never acceptable where a refusal is possible" is
enforced structurally rather than by review.

The second reason for the shape here: a refusal a contributor cannot act on decays into a
refusal they route around. `ComposerError` therefore cannot be constructed from a bare
message - it takes `subject` (the Metric, Source or column at fault), `problem` (what went
wrong) and `remedy` (the one declaration change that would make the build pass), and every
subclass declares typed attributes for the objects involved. `subject` is a stable,
greppable string, so tests assert on attributes rather than on prose.
"""
from __future__ import annotations

import contextlib
import logging
from typing import Any, Iterator, Mapping, Sequence

__all__ = [
    "ComposerError",
    "DeclarationError",
    "UndeclaredColumn",
    "UndeclaredSource",
    "UnknownMetric",
    "UnknownFilter",
    "UnknownCase",
    "UnknownJoin",
    "DuplicateDeclaration",
    "InvalidDeclaration",
    "LiteralTypeMismatch",
    "RegistryFrozen",
    "RegistryNotFrozen",
    "RefusalError",
    "EmptyTagFamily",
    "ScopeCollision",
    "JoinError",
    "NoJoinPath",
    "AmbiguousJoinPath",
    "FanOut",
    "ReAggregationError",
    "UnsafeReAggregation",
    "GrainTooFine",
    "GrainNotComparable",
    "UnboundRunDate",
    "PlanInvariantViolated",
    "RenderError",
    "ResolutionFailed",
    "UnsupportedConstruct",
    "DriftError",
    "BreakingDrift",
    "warnings_are_refusals",
]


class ComposerError(Exception):
    """Root of every refusal. Never raised directly.

    Three-part shape because the reader of a refusal is a contributor who has to edit a
    Declaration to make the build pass, and a message naming only the symptom sends them
    searching. `remedy` is required, not optional.

    `context` carries whatever else is worth printing (candidate join paths, near-miss
    column names). It is rendered sorted so two runs of the same failure produce
    byte-identical text, which matters when a refusal ends up in a CI log diff.
    """

    def __init__(
        self,
        *,
        subject: str,
        problem: str,
        remedy: str,
        **context: Any,
    ) -> None:
        self.subject = subject
        self.problem = problem
        self.remedy = remedy
        self.context: Mapping[str, Any] = dict(context)
        super().__init__(self.__str__())

    def __str__(self) -> str:
        lines = [
            f"{type(self).__name__}: {self.problem}",
            f"  at:  {self.subject}",
            f"  fix: {self.remedy}",
        ]
        for key in sorted(self.context):
            lines.append(f"  {key}: {self.context[key]}")
        return "\n".join(lines)


# --------------------------------------------------------------------------------------
# The Declarations themselves are wrong. Raised at import time wherever possible, so a bad
# Declaration cannot reach a Case.
# --------------------------------------------------------------------------------------


class DeclarationError(ComposerError):
    """A checked-in Declaration is malformed, incomplete or contradicts another one."""


class UndeclaredColumn(DeclarationError, AttributeError):
    """Attribute access named a column no Declaration carries.

    Refusal 4 of the four: the composer will not reference anything absent from a
    Declaration, and a misspelled column is otherwise a query against a column that
    happens to exist and means something else.

    Also an AttributeError, because `Source.__getattr__` raising anything else breaks
    `copy`, `pickle`, `dataclasses` and REPL completion in ways that are far harder to
    diagnose than the cost: `hasattr(src, "typo")` returns False and
    `getattr(src, "typo", default)` yields the default instead of refusing. Code that
    probes columns defensively therefore loses this refusal - use `Source.column(name)`,
    which refuses unconditionally, anywhere that matters.
    """

    def __init__(
        self,
        *,
        source: str,
        column: str,
        did_you_mean: Sequence[str] = (),
    ) -> None:
        self.source = source
        self.column = column
        self.did_you_mean = tuple(did_you_mean)
        suggestion = (
            f"did you mean {', '.join(self.did_you_mean)}?"
            if self.did_you_mean
            else f"add it to the Declaration of {source}"
        )
        super().__init__(
            subject=f"{source}.{column}",
            problem=f"{source} declares no column named {column!r}",
            remedy=suggestion,
            declared=", ".join(self.did_you_mean) or "(no near match)",
        )


class UndeclaredSource(DeclarationError):
    """A qualified name was looked up that no Declaration covers."""

    def __init__(self, *, qualified: str, known: Sequence[str] = ()) -> None:
        self.qualified = qualified
        self.known = tuple(known)
        super().__init__(
            subject=qualified,
            problem=f"no Source is declared as {qualified!r}",
            remedy="declare it in a module listed in declarations/__init__.py",
            known=", ".join(self.known) or "(none)",
        )


class UnknownMetric(DeclarationError):
    """A Metric was selected by name and the Registry holds nothing under it."""

    def __init__(self, *, metric: str, known: Sequence[str] = ()) -> None:
        self.metric = metric
        self.known = tuple(known)
        super().__init__(
            subject=metric,
            problem=f"no Metric named {metric!r} is declared",
            remedy="check the spelling, or declare the Metric at module level so the "
            "Registry's module scan finds it",
            known=", ".join(self.known) or "(none)",
        )


class UnknownFilter(DeclarationError):
    """A Filter was looked up by name and the Registry holds nothing under it."""

    def __init__(self, *, filter: str, known: Sequence[str] = ()) -> None:
        self.filter = filter
        self.known = tuple(known)
        super().__init__(
            subject=filter,
            problem=f"no Filter named {filter!r} is declared",
            remedy="declare it at module level in a declarations module",
            known=", ".join(self.known) or "(none)",
        )


class UnknownCase(DeclarationError):
    """A Case was looked up by name and the Registry holds nothing under it."""

    def __init__(self, *, case: str, known: Sequence[str] = ()) -> None:
        self.case = case
        self.known = tuple(known)
        super().__init__(
            subject=case,
            problem=f"no Case named {case!r} is declared",
            remedy="declare it at module level in a declarations module",
            known=", ".join(self.known) or "(none)",
        )


class UnknownJoin(DeclarationError):
    """A Case pinned `via=` a Join name that no Source declares.

    Join names, not Source names: two Sources can be joined two ways, so a Join path has to
    be stated as edges. A stale `via=` after a Join is renamed must refuse, because silently
    falling back to path inference would quietly change the row count.
    """

    def __init__(self, *, case: str, join: str, known: Sequence[str] = ()) -> None:
        self.case = case
        self.join = join
        self.known = tuple(known)
        super().__init__(
            subject=f"{case}.via",
            problem=f"Case {case!r} pins join {join!r}, which is not declared",
            remedy="use one of the declared join names, or drop `via=` and let the "
            "composer infer the path",
            known=", ".join(self.known) or "(none)",
        )


class DuplicateDeclaration(DeclarationError):
    """Two Declarations claim the same name.

    Names are the join key between the SQL, the git-tracked Lineage artifact and the
    review diff. A collision corrupts all three, and silently shadows one of the two.
    """

    def __init__(self, *, kind: str, name: str) -> None:
        self.kind = kind
        self.name = name
        super().__init__(
            subject=name,
            problem=f"two {kind}s are declared as {name!r}",
            remedy=f"rename one of them; {kind} names must be unique across all "
            "declaration modules",
        )


class InvalidDeclaration(DeclarationError):
    """A single Declaration contradicts itself.

    Covers a Hive type text sqlglot cannot parse, a Metric whose shape does not match its
    Aggregate, a Join with no keys or keys absent from either side, a ratio whose parts
    measure different Sources, a written Source whose declared Grain disagrees with the
    Case that writes it.
    """

    def __init__(self, *, subject: str, problem: str, remedy: str, **context: Any) -> None:
        super().__init__(subject=subject, problem=problem, remedy=remedy, **context)


class LiteralTypeMismatch(DeclarationError):
    """A Python value cannot inhabit the declared Hive type of the column compared to it.

    Hive does not error on a mistyped comparison: it returns NULL and the row quietly
    vanishes, so a filter that should match a million rows matches none and the Case
    reports zero. This check is coarse on purpose - it catches `dt.eq(20260917)` against a
    STRING partition column, but not `dt.eq("2026/09/17")` against a `yyyy-MM-dd` one.
    Partition literal formats live in `Column.note` and are checked by nothing.

    It also carries the two refusals that are about a value's CONTENT rather than its type,
    because both end in the same place - a value that cannot become a literal node for this
    column - and both want the same three typed attributes: a non-finite float or Decimal,
    and a number whose formatted text is not a numeric literal. `reason` replaces the
    problem line for those; the attributes do not move.
    """

    def __init__(
        self,
        *,
        column: str,
        declared_type: str,
        value: Any,
        reason: str | None = None,
    ) -> None:
        self.column = column
        self.declared_type = declared_type
        self.value = value
        self.reason = reason
        super().__init__(
            subject=column,
            problem=reason
            or f"{type(value).__name__} value {value!r} cannot inhabit declared type "
            f"{declared_type}",
            remedy=f"pass a value matching {declared_type}, or correct the declared type",
        )


class RegistryFrozen(DeclarationError):
    """Something was declared after `Registry.freeze()`.

    Late declaration is precisely how a Tag family comes to differ between two runs of the
    same Case: a Metric registered after the Case resolved its family joins the next run
    and not this one, and the number changes with no diff to point at.
    """

    def __init__(self, *, kind: str, name: str) -> None:
        self.kind = kind
        self.name = name
        super().__init__(
            subject=name,
            problem=f"the Registry is frozen; {kind} {name!r} was declared too late",
            remedy="import every declarations module before calling Registry.freeze()",
        )


class RegistryNotFrozen(DeclarationError):
    """Compilation was asked to run against a Registry that was never frozen.

    `freeze()` is where the cross-Declaration checks run - join targets resolve, join keys
    exist on both sides, a written Source's Grain agrees with its producer. Compiling
    without it would skip all of them.
    """

    def __init__(self, *, operation: str) -> None:
        self.operation = operation
        super().__init__(
            subject=operation,
            problem=f"{operation} requires a frozen Registry",
            remedy="call Registry.freeze() once every declarations module is imported",
        )


# --------------------------------------------------------------------------------------
# The Declarations are sound but this Case cannot be assembled from them without risking a
# wrong number. These are the refusals of decision 3.
# --------------------------------------------------------------------------------------


class RefusalError(ComposerError):
    """We could have emitted plausible SQL from sound Declarations, and refuse to."""


class EmptyTagFamily(RefusalError):
    """A Tag selected no Metrics.

    Checked per Tag, never over the union: a Case naming two Tags where one is misspelled
    would otherwise resolve to a non-empty family missing half its Metrics, report fewer
    columns than its author intended, and raise nothing. This refusal is what lets Tag be
    a plain `str` without a wrapper type.
    """

    def __init__(self, *, tag: str, known: Sequence[str] = (), case: str | None = None) -> None:
        self.tag = tag
        self.known = tuple(known)
        self.case = case
        super().__init__(
            subject=f"{case}.metrics" if case else f"tag:{tag}",
            problem=f"Tag {tag!r} is carried by no declared Metric",
            remedy="check the spelling, or tag a Metric with it",
            known_tags=", ".join(self.known) or "(none)",
        )


class ScopeCollision(RefusalError):
    """A Case is narrowed by the same Filter that scopes one of its Metrics.

    A Metric-scoped `when` compiles to `CASE WHEN <pred> THEN ... END` inside the
    aggregate. Under a WHERE clause that already asserts `<pred>`, that conditional is a
    tautology: the scoped Metric silently becomes its own unscoped form, and a ratio built
    on it is 1.0 on every row. `failed_deliveries` then equals `delivery_attempts` and
    `failure_rate` is constant - three columns whose names mean something they do not.

    It is the collision of two good ideas rather than a mistake in either: a Case narrows
    with a Filter (decision 3's "failure to deliver is a Filter, not a Metric"), and asks
    for a Tag family (decision 2) that happens to contain a Metric scoped by that same
    Filter. Nobody wrote the two down together, which is exactly why it is refused rather
    than left to review.
    """

    def __init__(self, *, case: str, filter: str, metric: str, outputs: Sequence[str] = ()) -> None:
        self.case = case
        self.filter = filter
        self.metric = metric
        self.outputs = tuple(outputs)
        super().__init__(
            subject=case,
            problem=f"Case {case!r} is narrowed by Filter {filter!r}, which is also the "
            f"scope of Metric {metric!r}; inside that WHERE clause the Metric's conditional "
            "aggregate is a tautology, so it reports the same number as its unscoped form",
            remedy=f"drop {filter!r} from the Case's `filters` and let {metric!r} carry the "
            f"scoping, or select a family that does not contain {metric!r}",
            affected=", ".join(self.outputs) or metric,
        )


class JoinError(RefusalError):
    """Base for every Join path refusal - one `except` for 'my join graph is wrong'."""


class NoJoinPath(JoinError):
    """No chain of declared Joins connects the Sources this Case needs."""

    def __init__(self, *, case: str, anchor: str, unreachable: Sequence[str]) -> None:
        self.case = case
        self.anchor = anchor
        self.unreachable = tuple(unreachable)
        super().__init__(
            subject=case,
            problem=f"no declared Join path reaches {', '.join(self.unreachable)} "
            f"from {anchor}",
            remedy="declare the missing Join on one of the Sources, with its keys and "
            "Cardinality",
        )


class AmbiguousJoinPath(JoinError):
    """More than one declared Join path - or more than one spine - connects the Sources this
    Case needs.

    The composer refuses rather than picking, because the choices differ in row count and
    picking one silently is a wrong number. `candidates` is load-bearing: each entry is a
    tuple of Join names, printed so a human can paste one straight into `Case(via=...)`.

    `anchors`, when present, runs parallel to `candidates`: entry i is the spine that
    candidate i is anchored at, and one Join path appears twice with two different spines
    because those are two different statements. A `kind="left"` edge preserves whichever
    end the FROM clause names, so the spine moves the numbers exactly as a different path
    would. The printed form is then the whole answer - `anchor=..., via=(...)` - because a
    refusal whose subject is the spine has to print the spine.

    The printed `via=` is valid Python for a one-edge Join path too: `via=('x',)`, with the
    trailing comma that makes it a tuple. Without it a pasted candidate is a str, `via`
    iterates character by character, and the build dies naming a join called 'x' - a
    refusal about the remedy rather than about the problem.
    """

    def __init__(
        self,
        *,
        case: str,
        anchor: str,
        candidates: Sequence[Sequence[str]],
        anchors: Sequence[str] = (),
    ) -> None:
        self.case = case
        self.anchor = anchor
        self.candidates = tuple(tuple(path) for path in candidates)
        self.anchors = tuple(anchors)
        if self.anchors and len(self.anchors) != len(self.candidates):  # pragma: no cover
            raise ValueError("anchors must run parallel to candidates")
        rendered = "; ".join(
            (f"anchor={spine!r}, " if spine else "") + _via_text(path)
            for spine, path in zip(
                self.anchors or (("",) * len(self.candidates)), self.candidates
            )
        )
        subject_of_choice = "spines and Join paths" if self.anchors else "Join paths"
        fields = "`anchor=` and `via=`" if self.anchors else "`via=`"
        super().__init__(
            subject=case,
            problem=f"{len(self.candidates)} declared {subject_of_choice} connect the "
            f"Sources {case!r} needs, anchored at {anchor}",
            remedy=f"state which one the Case means by copying one candidate into {fields}",
            candidates=rendered,
        )


def _via_text(path: Sequence[str]) -> str:
    """One candidate Join path as the literal a contributor pastes into `via=`.

    A one-element tuple keeps its trailing comma. That is the whole of this function, and it
    is a function because the alternative was a join() that silently produced a str."""
    names = tuple(path)
    inner = ", ".join(repr(name) for name in names)
    if len(names) == 1:
        inner += ","
    return f"via=({inner})"


class FanOut(JoinError):
    """A Join path would multiply the rows of the Source a Metric measures.

    Detected from declared Cardinality before any SQL exists, because the symptom
    otherwise is an inflated number that looks entirely reasonable. Note the ceiling on
    this check: it is only ever as good as the declared Cardinality. A Join hand-annotated
    MANY_TO_ONE that is really ONE_TO_MANY produces a silent inflated number with no
    refusal anywhere, and a warehouse DESCRIBE cannot catch it either.
    """

    def __init__(
        self,
        *,
        metric: str,
        measures: str,
        join: str,
        cardinality: str,
        path: Sequence[str] = (),
    ) -> None:
        self.metric = metric
        self.measures = measures
        self.join = join
        self.cardinality = cardinality
        self.path = tuple(path)
        super().__init__(
            subject=metric,
            problem=f"Join {join!r} ({cardinality}) multiplies the rows of {measures}, "
            f"which Metric {metric!r} measures",
            remedy="report this Metric in a Case that does not reach across that Join, "
            "or pre-aggregate the many side into a written Source first",
            path=" -> ".join(self.path) or "(direct)",
        )


class ReAggregationError(RefusalError):
    """Base for every refusal to recompute a Metric at a different Grain."""


class UnsafeReAggregation(ReAggregationError):
    """A Metric's Re-aggregation rule cannot prove the requested re-grain is safe.

    COUNT(DISTINCT) does not roll up. An average of averages is wrong. A ratio must be
    re-derived from re-aggregated numerator and denominator, never averaged. Each of those
    silently produces a number, which is why this is a refusal rather than a note in the
    docs.

    `stored_by` names the Metric that WROTE the column being read, for the second and
    nastier shape of this mistake: a Metric declared against a written Source with a rule
    that contradicts the one the numbers were produced under. `sum_of(DAILY.failure_rate)`
    is a well-formed SUM of a column of DOUBLEs and it is a wrong number, and the only
    thing that knows so is the producing Metric's own rule. When it is set, `rule` is the
    PRODUCING Metric's rule rather than the reading Metric's - the rule that actually
    governs the stored numbers.
    """

    def __init__(
        self,
        *,
        metric: str,
        rule: str,
        native: str,
        target: str,
        stored_by: str | None = None,
        **context: Any,
    ) -> None:
        self.metric = metric
        self.rule = rule
        self.native = native
        self.target = target
        self.stored_by = stored_by
        if stored_by is None:
            problem = (
                f"Metric {metric!r} has Re-aggregation rule {rule} and was stored at "
                f"{native}; it cannot be recomputed at {target}"
            )
            remedy = (
                "report this Metric at the Grain it was written at, or re-declare it "
                "against the atomic Source so it can be computed from rows"
            )
        else:
            problem = (
                f"Metric {metric!r} reads a column written by Metric {stored_by!r}, whose "
                f"Re-aggregation rule is {rule}; those numbers were stored at {native} and "
                f"cannot be recomputed at {target}"
            )
            remedy = (
                f"declare {metric!r} with the same rule {stored_by!r} carries and report "
                "it at the Grain it was written at, or build it from stored columns that "
                "do roll up - a rate is re-derived from a stored numerator and "
                "denominator, never summed or averaged"
            )
        super().__init__(subject=metric, problem=problem, remedy=remedy, **context)


class GrainTooFine(ReAggregationError):
    """The Case asks for detail the Metric's Source has already thrown away."""

    def __init__(
        self,
        *,
        metric: str,
        native: str,
        target: str,
        offending: Sequence[str] = (),
    ) -> None:
        self.metric = metric
        self.native = native
        self.target = target
        self.offending = tuple(offending)
        super().__init__(
            subject=metric,
            problem=f"Metric {metric!r} is stored at {native}, which does not carry "
            f"{', '.join(self.offending) or target}",
            remedy="drop those Dimensions from the Case's Grain, or read the atomic "
            "Source instead of the written one",
        )


class GrainNotComparable(ReAggregationError):
    """Neither Grain contains the other, so no re-aggregation is defined between them.

    The case that matters is WEEK against MONTH: ISO weeks straddle month boundaries, so
    rolling weeks into months is a wrong number, and the two buckets are deliberately
    incomparable rather than ordered. Refuse, never guess.
    """

    def __init__(self, *, metric: str, native: str, target: str) -> None:
        self.metric = metric
        self.native = native
        self.target = target
        super().__init__(
            subject=metric,
            problem=f"Grains {native} and {target} are not comparable, so Metric "
            f"{metric!r} has no defined re-aggregation between them",
            remedy="report at a Grain that contains the stored one - weeks roll up to "
            "years, never to months",
        )


class UnboundRunDate(RefusalError):
    """A Predicate holds a RunDate but compilation was called without `run_date`.

    RunDate is the only deferred value in the library, and the alternative to it is a date
    formatted into SQL text - which sqlglot cannot escape and this design forbids. So an
    unbound one refuses rather than rendering something arbitrary.
    """

    def __init__(self, *, subject: str, text: str) -> None:
        self.text = text
        super().__init__(
            subject=subject,
            problem=f"predicate {text!r} holds a RunDate and no run_date was supplied",
            remedy="pass run_date=date(...) to compile_case(), overwrite_partition() or "
            "the statement plan",
        )


class PlanInvariantViolated(RefusalError):
    """A hand-assembled CasePlan failed its own structural re-verification.

    Python cannot seal a constructor, so the plan token is made self-checking instead:
    `CasePlan.__post_init__` re-derives the cheap invariants (the path chains from the
    spine and visits each Source once, every MetricPlan targets the Case's Grain, no plan
    carries a rule of NONE at a coarser Grain) from its own fields. It deliberately does
    not re-run the ambiguous-path search, which is why a caller who hand-builds a plan with
    a valid but arbitrarily chosen Join path still gets SQL.
    """

    def __init__(self, *, case: str, invariant: str, detail: str) -> None:
        self.case = case
        self.invariant = invariant
        self.detail = detail
        super().__init__(
            subject=case,
            problem=f"CasePlan for {case!r} violates {invariant}: {detail}",
            remedy="build the plan through compile.plan() rather than assembling it by "
            "hand",
        )


# --------------------------------------------------------------------------------------
# The tree is assembled but will not render to trustworthy Hive.
# --------------------------------------------------------------------------------------


class RenderError(ComposerError):
    """Generation, or the qualify() resolution gate, refused the tree.

    Reaching this usually means the composer built something it should have refused
    earlier - it is the backstop, not the front door.
    """


class ResolutionFailed(RenderError):
    """The qualify() gate rejected the AST. Wraps sqlglot's OptimizeError.

    The gate runs against the whole declared schema, never a subset: qualify()'s star
    expansion silently no-ops on an incomplete schema rather than raising, so a partial
    schema turns the gate into a no-op without saying so.
    """

    def __init__(self, *, case: str, sqlglot_message: str) -> None:
        self.case = case
        self.sqlglot_message = sqlglot_message
        super().__init__(
            subject=case,
            problem=f"sqlglot could not resolve the query for {case!r}: {sqlglot_message}",
            remedy="the column exists in the query but not in a Declaration - add it, or "
            "correct the Declaration it should have come from",
        )


class UnsupportedConstruct(RenderError):
    """Generation under ErrorLevel.RAISE refused a construct. Wraps UnsupportedError.

    sqlglot's default is best-effort translation with a logged warning, which would hand
    back Hive that runs and means something else. Every generation call in this library
    passes `unsupported_level=ErrorLevel.RAISE`.
    """

    def __init__(self, *, case: str, sqlglot_message: str) -> None:
        self.case = case
        self.sqlglot_message = sqlglot_message
        super().__init__(
            subject=case,
            problem=f"Hive cannot express part of {case!r}: {sqlglot_message}",
            remedy="express it with a construct Hive supports - for Hive-only functions "
            "build exp.Anonymous rather than exp.func",
        )


# --------------------------------------------------------------------------------------
# Drift.
# --------------------------------------------------------------------------------------


class DriftError(ComposerError):
    """Base for Declaration/warehouse divergence."""


class BreakingDrift(DriftError):
    """A column some Case references was dropped or retyped in the warehouse.

    Only referenced columns break the build. An added column, or a change to a column no
    Case reads, is reported and never raised - otherwise every unrelated warehouse change
    blocks every build and the check gets switched off.
    """

    def __init__(
        self,
        *,
        source: str,
        dropped: Sequence[str] = (),
        retyped: Mapping[str, tuple[str, str]] | None = None,
        used_by: Sequence[str] = (),
    ) -> None:
        self.source = source
        self.dropped = tuple(dropped)
        self.retyped = dict(retyped or {})
        self.used_by = tuple(used_by)
        changes = list(self.dropped) + [
            f"{name}: {was} -> {now}" for name, (was, now) in sorted(self.retyped.items())
        ]
        super().__init__(
            subject=source,
            problem=f"{source} no longer matches its Declaration: {', '.join(changes)}",
            remedy="regenerate the Declaration with declaration.generate (or "
            "tools/generate_declarations.py) into a scratch file, merge the changed columns "
            "into the checked-in one so its hand annotations survive, then fix the Cases "
            "that read those columns",
            used_by=", ".join(self.used_by) or "(none)",
        )


# --------------------------------------------------------------------------------------
# Escalating sqlglot's own silence.
# --------------------------------------------------------------------------------------


class _RefuseOnWarning(logging.Handler):
    """A logging handler that turns a sqlglot warning into a RenderError."""

    def emit(self, record: logging.LogRecord) -> None:
        raise RenderError(
            subject=record.name,
            problem=f"sqlglot logged a warning: {record.getMessage()}",
            remedy="sqlglot degraded silently rather than refusing; inspect the construct "
            "it named and express it another way",
        )


@contextlib.contextmanager
def warnings_are_refusals(logger_name: str = "sqlglot") -> Iterator[None]:
    """Escalate sqlglot's logger so its silent warnings raise `RenderError`.

    sqlglot logs to `logging.getLogger("sqlglot")` and several of its degradations are
    warnings rather than errors - lineage resolving an unknown subquery scope, for one.
    A context manager rather than a global install, so test isolation survives and a
    caller who genuinely wants best-effort behaviour can step outside it.
    """
    logger = logging.getLogger(logger_name)
    handler = _RefuseOnWarning(level=logging.WARNING)
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        yield
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
