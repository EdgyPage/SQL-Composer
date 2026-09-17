"""Join path resolution, ambiguity refusal and Fan-out detection.

Two of the four refusals of decision 3 live here, and both are refusals rather than
choices. When more than one chain of declared Joins connects the Sources a Case needs, the
paths differ in row count, so picking one silently is a wrong number - this module refuses
and prints the candidates in the exact form `Case(via=...)` takes. When a path would
multiply the rows of the Source a Metric measures, the symptom is an inflated number that
looks entirely reasonable, so that is refused from declared Cardinality before any SQL
exists.

Paths are inferred but only ever along declared edges. `via=` selects among candidate
paths; it never invents one, and a `via=` naming an edge that does not exist is
`UnknownJoin` rather than a fallback to inference.

Two things learned while implementing, both of which shape the code below:

*Fan-out is a property of the edge set, not of the direction it is walked.* A Join declared
MANY_TO_ONE multiplies the rows of its RIGHT side, and a Metric measured over there is
inflated exactly as badly as a Metric on the spine under a ONE_TO_MANY. So `check_fan_out`
does not ask "does this step fan out" - it carries, per Source, whether that Source's rows
can still appear more than once in the joined rows, propagating the answer across every
step in path order. That also makes the refusal independent of which end of an edge the
Case happened to anchor at, which is what lets `resolve` refuse an ambiguous spine without
that refusal changing any Fan-out answer.

*The two "does this multiply" questions face opposite ways, on purpose.* `fans_out_between`
answers the SPINE's question - does reaching this Source hand the spine several rows where
it had one. `check_fan_out` answers the METRIC's question - can this Source's own rows
repeat. A MANY_TO_ONE lookup hop answers no to the first and yes to the second, and both
answers are right.

`grain.determines` asks a third question that looks like the first and is not, which is why
it does its own walk rather than calling anything here: it needs the Join path from the
METRIC's Source to the DIMENSION's Source, and that stretch is not in general a prefix of
the path from the spine - for a branching one it may have to be walked partly backwards.
`steps_between` and `fans_out_between` only ever read forward from the spine. Do not
"simplify" grain.py into calling them; the two agree on a chain and differ on a tree.
"""
from __future__ import annotations

from typing import Iterable, Mapping, Sequence

import networkx
from sqlglot import exp

from sqlcomposer.declaration import JoinPath, JoinStep, Registry, Source
from sqlcomposer.errors import (
    AmbiguousJoinPath,
    FanOut,
    InvalidDeclaration,
    NoJoinPath,
    UndeclaredSource,
    UnknownJoin,
)
from sqlcomposer.model import Case, Metric

__all__ = [
    "graph",
    "candidates",
    "spine",
    "resolve",
    "check_fan_out",
    "steps_between",
    "fans_out_between",
    "apply",
    "describe",
]


def graph(registry: Registry) -> networkx.MultiGraph:
    """The declared Joins as a graph: Sources as nodes, declared Joins as edges.

    A MultiGraph, not a Graph, because two Sources can be joined two ways and collapsing
    parallel edges would hide exactly the ambiguity this module exists to refuse.

    Nodes are `Source.qualified` strings. Each edge carries `step` (the `JoinStep` oriented
    as declared) and is keyed by `JoinStep.name`, so a path recovered from the graph can be
    turned back into named edges without a second lookup.

    Every declared Source is a node even when nothing joins it, so a Source that is declared
    but unreachable is reported as unreachable rather than as undeclared - two different
    mistakes with two different fixes. The graph is undirected because a declared edge is
    walkable both ways; the orientation is recovered per path by `JoinStep.inverted()`.

    Requires a frozen Registry.
    """
    registry.require_frozen("joins.graph")
    built = networkx.MultiGraph()
    for source in registry.sources():
        built.add_node(source.qualified, source=source)
    for step in registry.joins():
        built.add_edge(step.frm.qualified, step.to.qualified, key=step.name, step=step)
    return built


def candidates(
    registry: Registry,
    needed: frozenset[Source],
    *,
    anchor: Source,
) -> tuple[JoinPath, ...]:
    """Every minimal path from `anchor` that reaches all of `needed`.

    "Minimal" means no Source is visited twice and no step is present that could be dropped
    while still reaching every needed Source - a path padded with irrelevant hops is not a
    distinct business answer, it is the same answer with extra chances to fan out.

    Each returned path is oriented: `steps[0].frm` is `anchor`, and each later step leaves a
    Source an earlier step has already reached. Returned sorted by `JoinPath` join names, so
    the candidate list a refusal prints is stable between runs.

    Returns `()` when nothing connects them; returns a single empty tuple `((),)` when
    `needed` is just `{anchor}` and no join is required at all.

    A path is a tree rooted at `anchor`, not necessarily a chain: a Case needing three
    Sources that both hang off the spine has one candidate with two steps and no ordering
    between them. Minimality is then exactly "every leaf of that tree is a needed Source",
    which is how it is checked. Within a path the steps are ordered greedily by Join name
    among those whose `frm` has already been reached, so a branching path still has one
    canonical spelling and a golden test does not move when the Declarations are re-sorted.

    A Source in `needed` that no Declaration carries raises `UndeclaredSource` rather than
    being reported as disconnected - it is a Declaration mistake, not a missing edge.
    """
    registry.require_frozen("joins.candidates")
    built = graph(registry)
    _require_declared(built, (anchor, *needed))

    targets = frozenset(source.qualified for source in needed) | {anchor.qualified}
    if targets == {anchor.qualified}:
        return ((),)

    declared = _declared_steps(registry)
    reached_targets: list[frozenset[str]] = []
    seen: set[frozenset[str]] = set()
    stack: list[tuple[frozenset[str], frozenset[str]]] = [
        (frozenset({anchor.qualified}), frozenset())
    ]
    while stack:
        reached, used = stack.pop()
        if used in seen:
            continue
        seen.add(used)
        if targets <= reached:
            # Growing further can only add a Source nothing needs, so every extension of a
            # covering path is non-minimal by construction and is never pushed.
            reached_targets.append(used)
            continue
        for node in sorted(reached):
            for _left, right, name, _data in built.edges(node, keys=True, data=True):
                if right in reached:
                    continue
                stack.append((reached | {right}, used | {name}))

    paths: list[JoinPath] = []
    for used in reached_targets:
        path = _orient(declared, anchor, used)
        if path is None:  # pragma: no cover - the search only ever grows valid trees
            continue
        parents = {step.frm.qualified for step in path}
        leaves = ({anchor.qualified} | {step.to.qualified for step in path}) - parents
        if leaves <= targets:
            paths.append(path)
    return tuple(sorted(paths, key=describe))


def spine(registry: Registry, case: Case) -> Source:
    """The Source the FROM clause names - the one every Metric is measured relative to.

    If every resolved Metric measures the same Source, that is the spine. If they measure
    several, `case.anchor` states which one, and anything else raises `AmbiguousJoinPath`
    listing every (spine, path) pair. Never guessed: for a `kind="left"` edge the two ends
    of one path are different SQL, and choosing the wrong one silently deflates or inflates
    half the Metrics.

    The spine is its own field rather than a reading of `via[0]`, and that is load-bearing.
    `resolve` matches `via` as a SET, so the order inside it carries no information - which
    means a spine derived from `via[0]` would be decided by something the library documents
    as meaningless, and reordering two pinned edges would quietly move the numbers. The
    refusal therefore enumerates one candidate per (spine, path) pair, including the same
    edge set twice under two spines, because those are two different statements.

    `anchor` must name one of the Sources the Case's own Metrics measure. Anchoring on a
    Source that carries no Metric is refused rather than honoured: the spine is defined as
    the Source every Metric is measured relative to, and a lookup table in the FROM clause
    is a different statement wearing the same Declarations.
    """
    registry.require_frozen("joins.spine")
    homes = sorted(
        {metric.source.qualified: metric.source for metric in case.resolved_metrics(registry)}.values(),
        key=lambda source: source.qualified,
    )
    if not homes:  # pragma: no cover - MetricSelection.resolve refuses an empty family
        raise InvalidDeclaration(
            subject=f"case:{case.name}",
            problem="the Case resolves to no Metrics, so there is no Source to anchor on",
            remedy="select at least one Metric with by_tag(...) or by_name(...)",
        )
    if case.anchor is not None:
        for home in homes:
            if home.qualified == case.anchor:
                return home
        raise InvalidDeclaration(
            subject=f"case:{case.name}",
            problem=f"anchor={case.anchor!r} is not a Source any Metric of this Case "
            "measures",
            remedy="anchor on one of "
            f"{', '.join(home.qualified for home in homes)}, or drop `anchor=` when the "
            "Metrics measure one Source",
        )
    if len(homes) == 1:
        return homes[0]

    needed = case.sources(registry)
    printed: list[tuple[str, tuple[str, ...]]] = []
    for home in homes:
        for path in candidates(registry, needed, anchor=home):
            printed.append((home.qualified, describe(path)))
    if not printed:
        raise NoJoinPath(
            case=case.name,
            anchor=homes[0].qualified,
            unreachable=_unreachable(graph(registry), homes[0], needed),
        )
    printed.sort()
    raise AmbiguousJoinPath(
        case=case.name,
        anchor=", ".join(home.qualified for home in homes),
        candidates=tuple(names for _home, names in printed),
        anchors=tuple(home for home, _names in printed),
    )


def resolve(registry: Registry, case: Case) -> tuple[Source, JoinPath]:
    """The spine and the one Join path this Case is built over.

    Exactly one candidate path -> use it. None -> `NoJoinPath` naming the Sources it could
    not reach. More than one -> `AmbiguousJoinPath` carrying every candidate as a tuple of
    Join names, unless `case.via` names one of them, in which case that one is returned.

    A `case.via` that names edges forming no valid path (a gap, a repeat, an edge that does
    not touch the needed Sources) is `NoJoinPath`, not a silent fallback - a stale `via=`
    left behind after a Declaration changed must fail loudly.

    `via` is matched as a SET of Join names, not as an ordered list: an edge is one edge
    whichever way it is walked and whatever order a branching path lists it in, so the
    order inside `via=` carries no information and is not made to. A name repeated inside
    `via=` is still refused rather than quietly deduplicated - the second traversal would
    re-enter a Source the first already reached.

    Which end of the path the FROM clause names is `case.anchor`, never a reading of
    `via[0]`: a set has no first element, and deriving the spine from one would make the
    numbers depend on an order this contract says is meaningless. See `spine`.

    The refusal that follows a mismatch reports, in `NoJoinPath.unreachable`, the needed
    Sources the pinned edges fail to reach; failing that - because the edges reach every
    needed Source and are still not a path for this Case - the un-needed Sources they
    detour through, or the pinned names that could not be walked at all. Detours are refused
    rather than trimmed: an extra inner join drops rows on both sides and deflates every
    Metric in the Case. Read the typed attribute rather than the prose, which is phrased for
    the common case of a Source that nothing reaches.

    Does NOT check Fan-out; call `check_fan_out` with the resolved path. The two are
    separate because grain.py needs the path before the Metrics are planned.
    """
    registry.require_frozen("joins.resolve")
    anchor = spine(registry, case)
    needed = case.sources(registry)
    paths = candidates(registry, needed, anchor=anchor)

    if case.via:
        return anchor, _path_from_via(registry, case, anchor=anchor, needed=needed, paths=paths)
    if not paths:
        raise NoJoinPath(
            case=case.name,
            anchor=anchor.qualified,
            unreachable=_unreachable(graph(registry), anchor, needed),
        )
    if len(paths) > 1:
        raise AmbiguousJoinPath(
            case=case.name,
            anchor=anchor.qualified,
            candidates=tuple(describe(path) for path in paths),
        )
    return anchor, paths[0]


def check_fan_out(
    spine_source: Source,
    path: JoinPath,
    metrics: Sequence[Metric],
) -> None:
    """Refuse when the path multiplies the rows of a Source some Metric measures.

    For each Metric, walk the steps between `spine_source` and the Metric's own Source: if
    any step traversed on that stretch fans out relative to the Metric's Source, the Metric
    is measured over multiplied rows and raises `FanOut` naming the Metric, the Source it
    measures, the offending edge and its declared Cardinality.

    Steps BEYOND a Metric's Source still matter when they fan out the spine itself, because
    the spine's rows carry every Metric measured on it. A MANY_TO_ONE hop to a lookup table
    never fans out and is always allowed.

    Both of those are special cases of the one rule this implements, which is carried
    forward step by step in path order: a Source's rows can repeat if the step that brought
    it in has many rows on the left per row on the right (MANY_TO_ONE or MANY_TO_MANY read
    left-to-right), or if the Source it was joined from could already repeat; and any step
    that fans out multiplies every Source reached before it. So three refusals fall out that
    a reading of the first paragraph alone would miss:

    * a Metric measured on the RIGHT side of a MANY_TO_ONE lookup hop - the classic
      "sum the courier's fee once per delivery" - is refused, because "fans out relative to
      the Metric's Source" is the inverted edge;
    * a fan-out anywhere on the path inflates a Metric on a Source reached earlier, even
      when the fan-out is down an unrelated branch;
    * a fan-out inherited through an otherwise innocent ONE_TO_ONE hop is refused, and the
      refusal names the edge that actually caused it rather than the innocent one.

    The reported Cardinality is the edge as the PATH walks it, which for a path that walks
    an edge backwards is the inverse of the declared text. `FanOut.path` carries the whole
    path, so the edge is always locatable.

    Raises on the first offending Metric in the order given; callers pass Metrics sorted by
    name so the refusal is deterministic. That every Metric's Source is ON the path is an
    invariant of the caller rather than a refusal - see the assertion below.
    """
    blame = _duplicating_step(spine_source, path)
    for metric in metrics:
        home = metric.source
        # An invariant, deliberately not a refusal. `path` came from `resolve()`, which
        # only ever returns a candidate covering every Source in `case.sources()` - and
        # that set is built from these same Metrics' homes, so no Declaration and no Case
        # can leave a Metric's Source off the path. Only a caller pairing a hand-built path
        # with unrelated Metrics can, and a `NoJoinPath` for that would blame the
        # Declarations for a bug in the calling code, under a Case name no Case has.
        assert home.qualified in blame, (
            f"{metric.name} measures {home.qualified}, which the path from "
            f"{spine_source.qualified} never reaches: {describe(path)}"
        )
        offender = blame[home.qualified]
        if offender is not None:
            raise FanOut(
                metric=metric.name,
                measures=home.qualified,
                join=offender.name,
                cardinality=offender.cardinality.value,
                path=describe(path),
            )


def steps_between(spine_source: Source, target: Source, path: JoinPath) -> JoinPath:
    """The contiguous stretch of `path` from `spine_source` up to and including the step
    that first reaches `target`.

    Empty when `target` is `spine_source`. That `path` reaches `target` at all is an
    invariant of the caller rather than a refusal - see the assertion below.

    Contiguous means what it says: this is a prefix of `path`, so for a branching Join path
    it also carries the steps of any sibling branch that was walked first. That is deliberate -
    the callers ask whether anything on the way to `target` multiplied rows, and a sibling
    branch that fanned out multiplied them just as thoroughly. The distinction only exists
    for a branching path that fans out, which `check_fan_out` refuses anyway for every
    Metric on the spine.
    """
    if target.qualified == spine_source.qualified:
        return ()
    reached = [step.to.qualified for step in path]
    # An invariant, deliberately not a refusal, for the same reason as in `check_fan_out`:
    # every `path` in the library comes from `resolve()` and covers every Source the Case
    # names, so no Declaration and no Case can ask for a `target` that is not on it. Only a
    # caller holding a hand-built path can, and `NoJoinPath(case="joins.steps_between")`
    # would be a refusal whose subject is a function name rather than a Case.
    assert target.qualified in reached, (
        f"{target.qualified} is not on the path from {spine_source.qualified}: "
        f"{describe(path)}"
    )
    return tuple(path[: reached.index(target.qualified) + 1])


def fans_out_between(spine_source: Source, target: Source, path: JoinPath) -> bool:
    """True when walking `path` from `spine_source` to `target` multiplies `target`'s rows.

    The predicate behind `check_fan_out`, exposed separately so a caller holding a resolved
    path can ask about one Source without provoking a refusal about all of them - a tool
    explaining why a Case was refused wants the answer, not the exception.

    It is NOT the question `grain.determines` asks. That one needs the stretch from a
    Metric's Source to a Dimension's Source, which on a branching Join path is not a prefix
    of `path` and may run backwards along it; this reads forward from the spine only. The
    two agree on a chain and differ on a tree, so grain.py walks the path itself.

    Read carefully, this is the SPINE's question, and `check_fan_out` asks the Metric's: here
    a step counts when it hands the left-hand side several rows where it had one
    (ONE_TO_MANY or MANY_TO_MANY as the path walks it), because that is precisely when the
    Dimension on the far end splits a spine row instead of labelling it. A MANY_TO_ONE hop
    is False here and can still be a `FanOut` for a Metric measured on its right-hand side.
    """
    return any(step.fans_out for step in steps_between(spine_source, target, path))


def apply(select: exp.Select, path: JoinPath) -> exp.Select:
    """Add one JOIN clause per step to a SELECT that already has its FROM.

    Each step becomes `JOIN db.table ON <keys>` with `join_type` taken from `JoinStep.kind`
    ("inner" or "left"), and the ON condition built from `JoinStep.on()` - column nodes on
    both sides, never text.

    Tables are never explicitly aliased. The Registry refuses two Sources sharing a bare
    table name, so the bare name is unique within any Case, every column node in the library
    is qualified by it, and `qualify()` supplies `AS \\`table\\`` itself. Returns a new
    Select; does not mutate the one passed in.

    `Select.join` copies by default, so each step returns a fresh tree and the Select handed
    in is still renderable afterwards - which is what makes this safe to call on a tree a
    caller is holding.
    """
    joined = select
    for step in path:
        joined = joined.join(
            step.to.to_sqlglot(),
            on=step.on(),
            join_type=step.kind,
            copy=True,
        )
    return joined


def describe(path: JoinPath) -> tuple[str, ...]:
    """The path as Join names - what a refusal prints and the Lineage records.

    This is the form `Case(via=...)` takes, so the output of a refusal can be pasted
    straight into a Case with no translation.
    """
    return tuple(step.name for step in path)


# ======================================================================================
# Private helpers
# ======================================================================================


def _declared_steps(registry: Registry) -> Mapping[str, JoinStep]:
    """Every declared edge by name, in declared orientation."""
    return {step.name: step for step in registry.joins()}


def _require_declared(built: networkx.MultiGraph, sources: Iterable[Source]) -> None:
    """Refuse a Source that is not in the Registry the graph was built from."""
    for source in sources:
        if source.qualified not in built:
            raise UndeclaredSource(qualified=source.qualified, known=sorted(built.nodes))


def _walk(
    declared: Mapping[str, JoinStep],
    anchor: Source,
    names: Iterable[str],
) -> tuple[JoinPath, set[str], set[str]]:
    """Order Join names into a path leaving `anchor`, as far as they will go.

    Greedy by name among the edges whose near end has been reached and whose far end has
    not, which gives every edge set exactly one spelling. Returns the path, the qualified
    names it reaches (including `anchor`) and the pinned edges it could not walk - a gap, a
    cycle back into a Source already reached, or an edge touching neither end. Walking as
    far as possible rather than giving up at the first stuck edge is what lets the `via=`
    refusal name the Sources a stale pin fails to reach.
    """
    remaining = set(names)
    reached = {anchor.qualified}
    path: list[JoinStep] = []
    while remaining:
        chosen: JoinStep | None = None
        for name in sorted(remaining):
            step = declared[name]
            if step.frm.qualified in reached and step.to.qualified not in reached:
                chosen = step
            elif step.to.qualified in reached and step.frm.qualified not in reached:
                chosen = step.inverted()
            if chosen is not None:
                break
        if chosen is None:
            break
        path.append(chosen)
        reached.add(chosen.to.qualified)
        remaining.discard(chosen.name)
    return tuple(path), reached, remaining


def _orient(
    declared: Mapping[str, JoinStep],
    anchor: Source,
    names: Iterable[str],
) -> JoinPath | None:
    """`_walk`, refusing a partial result: None when the names form no path from `anchor`."""
    wanted = set(names)
    path, _reached, leftover = _walk(declared, anchor, wanted)
    return None if leftover else path


def _path_from_via(
    registry: Registry,
    case: Case,
    *,
    anchor: Source,
    needed: frozenset[Source],
    paths: tuple[JoinPath, ...],
) -> JoinPath:
    """The candidate path `case.via` pins, or a refusal explaining why it pins none."""
    declared = _declared_steps(registry)
    for name in case.via:
        if name not in declared:
            raise UnknownJoin(case=case.name, join=name, known=sorted(declared))

    repeated = tuple(sorted({name for name in case.via if case.via.count(name) > 1}))
    if repeated:
        # Naming the same edge twice cannot be honoured as written - the second traversal
        # would re-enter a Source the first already reached - and silently deduplicating it
        # would mean `via=` no longer says what the path is.
        raise NoJoinPath(case=case.name, anchor=anchor.qualified, unreachable=repeated)

    pinned = frozenset(case.via)
    for candidate in paths:
        if frozenset(describe(candidate)) == pinned:
            return candidate

    # No candidate matches, so say which of the mistakes it is.
    walked, reached, leftover = _walk(declared, anchor, pinned)
    wanted = {source.qualified for source in needed}
    missed = tuple(sorted(wanted - reached))
    if leftover:
        # A gap, or a cycle: some pinned edge never became walkable.
        raise NoJoinPath(
            case=case.name,
            anchor=anchor.qualified,
            unreachable=missed or tuple(sorted(leftover)),
        )
    detours = tuple(sorted({step.to.qualified for step in walked} - wanted))
    raise NoJoinPath(
        case=case.name,
        anchor=anchor.qualified,
        unreachable=missed or detours,
    )


def _unreachable(
    built: networkx.MultiGraph,
    anchor: Source,
    needed: frozenset[Source],
) -> tuple[str, ...]:
    """The needed Sources no chain of declared edges reaches from `anchor`."""
    if anchor.qualified in built:
        component = networkx.node_connected_component(built, anchor.qualified)
    else:  # pragma: no cover - _require_declared refuses this first
        component = {anchor.qualified}
    missed = tuple(
        sorted(source.qualified for source in needed if source.qualified not in component)
    )
    return missed or tuple(
        sorted(source.qualified for source in needed if source.qualified != anchor.qualified)
    )


def _duplicating_step(spine_source: Source, path: JoinPath) -> dict[str, JoinStep | None]:
    """Per Source reached by `path`, the first step that lets its rows repeat, or None.

    The whole of Fan-out detection, carried forward in path order. Joining `to` onto `frm`:

    * `to`'s rows repeat when several `frm` rows share one `to` row - the edge inverted
      fans out - or when `frm`'s rows could already repeat, in which case the blame stays
      with the step that first caused it rather than moving to this innocent one;
    * a step that fans out multiplies every Source already reached, and only those: the
      Source it brings in gets one row per matching left row, so it is not itself multiplied
      by its own arrival.

    Keyed by qualified name, and a Source absent from the result is one the path never
    reaches.
    """
    blame: dict[str, JoinStep | None] = {spine_source.qualified: None}
    for step in path:
        arriving = step.to.qualified
        if step.cardinality.inverted().fans_out:
            blame[arriving] = step
        else:
            blame[arriving] = blame.get(step.frm.qualified)
        if step.fans_out:
            for qualified in list(blame):
                if qualified != arriving and blame[qualified] is None:
                    blame[qualified] = step
    return blame
