"""Drift detection: Declarations against what the warehouse actually has.

A Declaration is authoritative, which means it can be wrong. `verify` re-reads the
warehouse through an injected `Describe` callable - the core never connects to anything -
and diffs it against the Declarations.

Two properties make this check survivable rather than something a team switches off.

It is SCOPED. Only columns some declared Case actually references can break a build. A
warehouse with four hundred columns per table will drift constantly in ways no Case cares
about, and a check that blocks on all of them is a check nobody runs.

It is CLASSIFIED. An added column is informational and never raises. A dropped or retyped
column that some Case reads is a build-breaker, because the Case will either fail at
runtime or - worse, for a retype - succeed and return numbers that mean something else.

Two limits of this module are worth stating up front, because both are places where a
wrong number survives the check:

* The scope is `Case.referenced_columns`, which is Metric columns, Grain columns and
  Filter columns. It does NOT include Join keys. A Case reaches a Join key whenever its
  Join path is walked, so a dropped key column is reported as drift but classified
  informational. Resolving a Case's Join path would mean importing `joins`, and the import
  layering deliberately puts `verify` beside it rather than above it.
* Nothing here can see a Cardinality that has become wrong. A Join annotated MANY_TO_ONE
  that the warehouse has quietly made ONE_TO_MANY inflates every Metric across it, and a
  DESCRIBE cannot detect that. Fan-out detection is only ever as good as the hand
  annotation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable, Mapping, Sequence

from sqlcomposer.declaration import ColumnRef, Registry, Source
from sqlcomposer.errors import BreakingDrift

__all__ = [
    "WarehouseColumn",
    "Describe",
    "DriftKind",
    "DriftItem",
    "DriftReport",
    "referenced_columns",
    "cases_using",
    "compare",
    "verify",
]


@dataclass(frozen=True)
class WarehouseColumn:
    """One column as the warehouse reports it right now.

    `type` is the type text verbatim from DESCRIBE, compared case-insensitively and with
    whitespace normalised against `Column.type` - `decimal(18, 2)` and `DECIMAL(18,2)` are
    the same type and a diff that flags them is noise.

    Normalisation is textual, never a parse. Handing the type text to sqlglot would make
    `INT` and `INTEGER` compare equal, but it would also raise on a type text sqlglot
    cannot parse - and a drift checker that dies on an unfamiliar warehouse type is worse
    than one that reports a spurious retype. The cost of the textual choice is that two
    spellings of one type ARE reported as drift.
    """

    name: str
    type: str
    partition: bool = False
    nullable: bool = True


Describe = Callable[[Source], Sequence[WarehouseColumn]]
"""How `verify` reads the warehouse. Injected by the caller, exactly like `Runner`, so
nothing in the core connects to anything. A Hive implementation runs `DESCRIBE FORMATTED`
and parses it; a test implementation returns a literal list. Raising from inside it is
treated as "this Source is gone" and becomes `DriftKind.SOURCE_MISSING`."""


class DriftKind(Enum):
    """What changed. `breaking` is a separate axis: an ADDED column is never breaking, and a
    DROPPED one is breaking only when some Case reads it."""

    ADDED = "added"
    DROPPED = "dropped"
    RETYPED = "retyped"
    PARTITIONING_CHANGED = "partitioning_changed"
    NULLABILITY_CHANGED = "nullability_changed"
    SOURCE_MISSING = "source_missing"


_BREAKING_KINDS = frozenset(
    {
        DriftKind.DROPPED,
        DriftKind.RETYPED,
        DriftKind.PARTITIONING_CHANGED,
        DriftKind.SOURCE_MISSING,
    }
)
"""The kinds that can fail a build. NULLABILITY_CHANGED is absent on purpose: a generated
Declaration reports almost everything nullable and the annotation that tightens it is a
hand edit, so treating a nullability diff as breaking would block builds on the one field
the warehouse is least authoritative about. It is reported, never raised."""


@dataclass(frozen=True)
class DriftItem:
    """One difference between a Declaration and the warehouse.

    `referenced` is whether some declared Case reaches this column; `used_by` names those
    Cases, because the first question after a drift report is "what breaks".

    `breaking` is computed, not declared: DROPPED, RETYPED or SOURCE_MISSING AND referenced.
    PARTITIONING_CHANGED is deliberately breaking-when-referenced too: a column that stops
    being a Partition column changes how its literals must be rendered, and the query keeps
    working while quietly scanning the whole table.

    Field conventions a reader cannot guess from the types:

    * `source` is `db.table` and `column` is the bare column name, so the node id of
      decision 6 is `f"{source}.{column}"`. `column` is None only for SOURCE_MISSING.
    * `declared` and `actual` carry the type text for ADDED, DROPPED and RETYPED. For
      PARTITIONING_CHANGED they carry `"partition"` / `"not partition"` and for
      NULLABILITY_CHANGED `"nullable"` / `"not nullable"`, so the pair always reads as a
      before-and-after of whatever the `kind` names.
    * For SOURCE_MISSING there is no column, so `declared` is None and `actual` carries the
      text of the exception `Describe` raised. That text is the only diagnosis available
      when a DESCRIBE fails for a reason other than the table being gone - a permission
      error and a dropped table are the same finding here, and only the message tells them
      apart.
    """

    kind: DriftKind
    source: str
    column: str | None
    declared: str | None
    actual: str | None
    referenced: bool
    used_by: tuple[str, ...] = ()

    @property
    def breaking(self) -> bool:
        """True when this item must fail a build.

        `DROPPED`, `RETYPED`, `PARTITIONING_CHANGED` or `SOURCE_MISSING`, and `referenced`.
        Computed rather than declared, so the classification cannot drift between the item
        that carries it and the report that acts on it.
        """
        return self.kind in _BREAKING_KINDS and self.referenced

    def __str__(self) -> str:
        """One line: kind, qualified column, and declared-vs-actual where both exist."""
        where = _node_id(self)
        if self.declared is not None and self.actual is not None:
            return f"{self.kind.value} {where}: {self.declared} -> {self.actual}"
        if self.declared is not None:
            return f"{self.kind.value} {where} (declared {self.declared})"
        if self.actual is not None:
            return f"{self.kind.value} {where} (actual {self.actual})"
        return f"{self.kind.value} {where}"


def _node_id(item: DriftItem) -> str:
    """`db.table.column`, or `db.table` for a whole-Source item.

    The one place this string is formed. Decision 6 makes `db.table.column` the identity
    of a column in the SQL, the Lineage graph, the DOT export and the drift report, and
    `ColumnRef.qualified` is where it comes from everywhere else - a DriftItem cannot hold
    a ColumnRef because a dropped column no longer has one.
    """
    return item.source if item.column is None else f"{item.source}.{item.column}"


def _order(item: DriftItem) -> tuple[str, str, str]:
    """Source, then column, then kind. The total order every listing here is built on.

    A whole-Source item sorts first within its Source because its column key is empty,
    which is the order a reader wants: "this table is gone" before anything about its
    columns.
    """
    return (item.source, item.column or "", item.kind.value)


@dataclass(frozen=True)
class DriftReport:
    """Every difference found, breaking and informational alike.

    The whole report is returned rather than just the breaking items, because "a column was
    added" is the signal that a Declaration should be regenerated before someone needs that
    column - and a check that only ever says nothing or fails teaches people to ignore it.
    """

    items: tuple[DriftItem, ...]

    @property
    def breaking(self) -> tuple[DriftItem, ...]:
        """The items that must fail a build, in source-then-column order."""
        return tuple(sorted((item for item in self.items if item.breaking), key=_order))

    @property
    def clean(self) -> bool:
        """True when there are no items at all - not merely no breaking ones."""
        return not self.items

    def raise_if_breaking(self) -> None:
        """Raise `BreakingDrift` when anything breaking was found, naming every affected
        Source, the dropped and retyped columns, and the Cases that read them. One
        exception for the whole report rather than one per item: a warehouse change usually
        breaks several columns at once and a contributor wants the whole picture.

        How the four breaking kinds map onto `BreakingDrift`'s two lists: DROPPED and
        SOURCE_MISSING become `dropped` entries (a missing Source contributes its own
        `db.table`, since every column of it is gone); RETYPED and PARTITIONING_CHANGED
        become `retyped` entries, whose before-and-after pair is the type text for one and
        `"partition"` / `"not partition"` for the other. `source` is every affected Source
        joined, because the error carries one string and the report covers the warehouse.
        """
        breaking = self.breaking
        if not breaking:
            return
        dropped: list[str] = []
        retyped: dict[str, tuple[str, str]] = {}
        used_by: set[str] = set()
        for item in breaking:
            used_by.update(item.used_by)
            if item.kind in (DriftKind.DROPPED, DriftKind.SOURCE_MISSING):
                dropped.append(_node_id(item))
            else:
                retyped[_node_id(item)] = (item.declared or "", item.actual or "")
        raise BreakingDrift(
            source=", ".join(sorted({item.source for item in breaking})),
            dropped=tuple(dropped),
            retyped=retyped,
            used_by=tuple(sorted(used_by)),
        )

    def to_text(self) -> str:
        """The report as text, breaking items first, grouped by Source. Stable ordering, so
        two runs against an unchanged warehouse produce identical output.

        Two sections, each grouped by Source: what fails the build, then what is worth
        knowing. The informational section is the one that earns the check its keep - it is
        where "someone added the column you have been asking for" shows up.
        """
        if self.clean:
            return "no drift: every Declaration matches the warehouse"
        breaking = self.breaking
        informational = tuple(
            sorted((item for item in self.items if not item.breaking), key=_order)
        )
        lines = [
            f"drift: {len(self.items)} item(s), {len(breaking)} breaking",
        ]
        if breaking:
            lines.append("")
            lines.append("BREAKING")
            lines.extend(_grouped(breaking))
        if informational:
            lines.append("")
            lines.append("informational")
            lines.extend(_grouped(informational))
        return "\n".join(lines)


def _grouped(items: Iterable[DriftItem]) -> list[str]:
    """Render already-sorted items under one indented heading per Source."""
    lines: list[str] = []
    current: str | None = None
    for item in items:
        if item.source != current:
            current = item.source
            lines.append(f"  {current}")
        used = f"  used by: {', '.join(item.used_by)}" if item.used_by else ""
        lines.append(f"    {item}{used}")
    return lines


# ======================================================================================
# Scope: what some Case actually reaches
# ======================================================================================


def referenced_columns(registry: Registry) -> Mapping[str, frozenset[str]]:
    """`{"db.table": {column names some declared Case reaches}}`.

    The scope of the check. Built from `Case.referenced_columns` across every declared
    Case, which resolves each Case's Tag family - so a Metric that joined a family today
    widens the scope today, with no Case edited. That is the intended behaviour and it is
    worth knowing before a drift report grows overnight.

    A Source reached only as `count_rows(of_source=...)` contributes no columns and so has
    no entry here at all. That is why `verify` scopes a missing Source by `Case.sources`
    rather than by this mapping: a table nothing selects a column from can still be the
    table a Case counts rows of.
    """
    by_source: dict[str, set[str]] = {}
    for case in registry.cases():
        for ref in case.referenced_columns(registry):
            by_source.setdefault(ref.source.qualified, set()).add(ref.name)
    return {source: frozenset(names) for source, names in by_source.items()}


def cases_using(registry: Registry, ref: ColumnRef) -> tuple[str, ...]:
    """The names of the declared Cases that reach this column, sorted."""
    return _usage(registry).columns.get(ref.qualified, ())


@dataclass(frozen=True)
class _Usage:
    """Which Cases reach which columns, and which Cases touch which Sources.

    Both directions come from one pass over the Cases because resolving a Tag family is
    the expensive part and every Case resolves one. `columns` answers "what breaks if this
    column changes"; `sources` answers the same question for a whole table, and the two
    differ for a Source a Case only counts rows of.
    """

    columns: Mapping[str, tuple[str, ...]]
    sources: Mapping[str, tuple[str, ...]]


def _usage(registry: Registry) -> _Usage:
    """Index every declared Case by what it reaches.

    Recomputed per call rather than cached: a Registry is mutable until `freeze()`, and a
    cache keyed on one would answer a question about the Declarations as they were. The
    cost is one Tag resolution per Case per call, and `compare` takes the index once for a
    whole Source rather than once per column.
    """
    columns: dict[str, set[str]] = {}
    sources: dict[str, set[str]] = {}
    for case in registry.cases():
        for ref in case.referenced_columns(registry):
            columns.setdefault(ref.qualified, set()).add(case.name)
        for source in case.sources(registry):
            sources.setdefault(source.qualified, set()).add(case.name)
    return _Usage(
        columns={key: tuple(sorted(names)) for key, names in columns.items()},
        sources={key: tuple(sorted(names)) for key, names in sources.items()},
    )


# ======================================================================================
# Comparison
# ======================================================================================

_WHITESPACE = re.compile(r"\s+")
_AROUND_PUNCTUATION = re.compile(r"\s*([(),<>:])\s*")


def _normalise_type(text: str) -> str:
    """Fold the spellings of one Hive type onto one string.

    Case, surrounding whitespace, runs of internal whitespace, and whitespace around the
    punctuation that appears inside a type - `decimal(18, 2)` and `DECIMAL(18,2)` become
    one string, and so do `MAP<STRING, INT>` and `map<string,int>`. Whitespace that is not
    next to punctuation survives, so `TIMESTAMP WITH LOCAL TIME ZONE` stays one type and
    cannot collide with another.
    """
    collapsed = _WHITESPACE.sub(" ", text.strip().lower())
    return _AROUND_PUNCTUATION.sub(r"\1", collapsed)


def _merge_actual(actual: Sequence[WarehouseColumn]) -> dict[str, WarehouseColumn]:
    """Index the warehouse's answer by column name, merging repeated entries.

    Hive's plain `DESCRIBE` lists a partition column twice - once in the column list and
    once again under `# Partition Information` - and a straightforward parser passes both
    through. Left unmerged, the second entry would shadow the first and half the parsers
    in the world would produce a spurious PARTITIONING_CHANGED on every run.

    So `partition` is ORed across the entries for one name and `nullable` ANDed, and the
    first entry's type wins. Both folds take the answer that says more: a column any part
    of the DESCRIBE calls a Partition column is one.
    """
    merged: dict[str, WarehouseColumn] = {}
    for column in actual:
        existing = merged.get(column.name)
        if existing is None:
            merged[column.name] = column
        else:
            merged[column.name] = WarehouseColumn(
                name=existing.name,
                type=existing.type,
                partition=existing.partition or column.partition,
                nullable=existing.nullable and column.nullable,
            )
    return merged


def compare(
    registry: Registry,
    source: Source,
    actual: Sequence[WarehouseColumn],
) -> tuple[DriftItem, ...]:
    """Diff one Source's Declaration against what the warehouse reports.

    Type comparison normalises case and internal whitespace before comparing, so
    `decimal(18, 2)` and `DECIMAL(18,2)` do not register as drift. Everything else is an
    exact comparison: a column that gained or lost Partition status, or changed
    nullability, is real drift even though the SELECT still parses.

    One column can produce two items - a column that was both retyped and de-partitioned
    is two facts, and collapsing them would hide the one a Case happens not to care about.
    Items come back in `_order`, which is the order the report keeps.

    An ADDED column is always `referenced=False`: a Case can only reach a column through a
    ColumnRef, and a column absent from the Declaration has none. That is the structural
    reason decision 9 can call an addition informational without checking anything.
    """
    return _compare(_usage(registry), source, actual)


def _compare(
    usage: _Usage,
    source: Source,
    actual: Sequence[WarehouseColumn],
) -> tuple[DriftItem, ...]:
    """`compare` against a pre-built usage index, so `verify` pays for it once."""
    reported = _merge_actual(actual)
    items: list[DriftItem] = []

    def item(
        kind: DriftKind,
        column: str,
        declared: str | None,
        found: str | None,
        *,
        referenced: bool = True,
    ) -> DriftItem:
        qualified = f"{source.qualified}.{column}"
        used_by = usage.columns.get(qualified, ()) if referenced else ()
        return DriftItem(
            kind=kind,
            source=source.qualified,
            column=column,
            declared=declared,
            actual=found,
            referenced=bool(used_by),
            used_by=used_by,
        )

    for declared in source.columns:
        found = reported.get(declared.name)
        if found is None:
            items.append(item(DriftKind.DROPPED, declared.name, declared.type, None))
            continue
        if _normalise_type(declared.type) != _normalise_type(found.type):
            items.append(
                item(DriftKind.RETYPED, declared.name, declared.type, found.type)
            )
        if declared.partition != found.partition:
            items.append(
                item(
                    DriftKind.PARTITIONING_CHANGED,
                    declared.name,
                    _partition_word(declared.partition),
                    _partition_word(found.partition),
                )
            )
        if declared.nullable != found.nullable:
            items.append(
                item(
                    DriftKind.NULLABILITY_CHANGED,
                    declared.name,
                    _nullable_word(declared.nullable),
                    _nullable_word(found.nullable),
                )
            )

    for name, found in reported.items():
        if not source.has(name):
            items.append(item(DriftKind.ADDED, name, None, found.type, referenced=False))

    return tuple(sorted(items, key=_order))


def _partition_word(partition: bool) -> str:
    return "partition" if partition else "not partition"


def _nullable_word(nullable: bool) -> str:
    return "nullable" if nullable else "not nullable"


# ======================================================================================
# The command
# ======================================================================================


def verify(registry: Registry, describe: Describe) -> DriftReport:
    """Re-read every declared Source and report how the warehouse has moved.

    Calls `describe` once per Source. A `describe` that raises for a Source yields a single
    `SOURCE_MISSING` item for it rather than propagating, so one dropped table does not
    hide drift in the other forty.

    Returns the report. It never raises on drift itself - call `raise_if_breaking()` when a
    build should fail, which keeps "report the drift" and "fail the build" as separate
    decisions a caller makes.

    Deliberately does not require a frozen Registry. Freezing checks Join targets and keys,
    none of which this reads, and a contributor diagnosing a broken Declaration should be
    able to ask what the warehouse looks like without first getting the rest of the
    Declarations to agree with each other.

    A missing Source is scoped by `Case.sources`, not by `referenced_columns`: a table a
    Case only counts the rows of contributes no columns and would otherwise go missing
    without breaking anything. Only `Exception` is caught - a KeyboardInterrupt or a
    SystemExit out of a caller's warehouse client is not a drift finding.
    """
    usage = _usage(registry)
    items: list[DriftItem] = []
    for source in registry.sources():
        try:
            actual = describe(source)
        except Exception as err:  # noqa: BLE001 - a failed DESCRIBE is a finding, not a crash
            used_by = usage.sources.get(source.qualified, ())
            items.append(
                DriftItem(
                    kind=DriftKind.SOURCE_MISSING,
                    source=source.qualified,
                    column=None,
                    declared=None,
                    actual=f"{type(err).__name__}: {err}",
                    referenced=bool(used_by),
                    used_by=used_by,
                )
            )
            continue
        items.extend(_compare(usage, source, actual))
    return DriftReport(items=tuple(sorted(items, key=_order)))
